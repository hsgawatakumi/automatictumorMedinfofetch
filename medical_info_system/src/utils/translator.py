"""
翻译服务模块
实现百度翻译API和Helsinki-NLP开源模型的双备份机制
"""

import hashlib
import random
import time
import json
import os
import logging
import requests
from typing import Optional, Dict, Tuple
from functools import lru_cache
from datetime import datetime

logger = logging.getLogger(__name__)


class TranslationCache:
    """翻译缓存管理类"""
    
    def __init__(self, cache_file: str):
        """
        初始化翻译缓存
        
        Args:
            cache_file: 缓存文件路径
        """
        self.cache_file = cache_file
        self.cache: Dict[str, str] = {}
        self._load_cache()
    
    def _load_cache(self):
        """加载缓存文件"""
        if os.path.exists(self.cache_file):
            try:
                with open(self.cache_file, 'r', encoding='utf-8') as f:
                    self.cache = json.load(f)
                logger.info(f"加载翻译缓存: {len(self.cache)} 条记录")
            except Exception as e:
                logger.warning(f"加载翻译缓存失败: {e}")
                self.cache = {}
    
    def _save_cache(self):
        """保存缓存文件"""
        try:
            cache_dir = os.path.dirname(self.cache_file)
            if cache_dir and not os.path.exists(cache_dir):
                os.makedirs(cache_dir, exist_ok=True)
            
            with open(self.cache_file, 'w', encoding='utf-8') as f:
                json.dump(self.cache, f, ensure_ascii=False, indent=2)
            logger.debug(f"保存翻译缓存: {len(self.cache)} 条记录")
        except Exception as e:
            logger.warning(f"保存翻译缓存失败: {e}")
    
    def get(self, text: str) -> Optional[str]:
        """
        从缓存获取翻译
        
        Args:
            text: 原文
            
        Returns:
            翻译结果（如果存在）
        """
        key = self._make_key(text)
        return self.cache.get(key)
    
    def set(self, text: str, translation: str):
        """
        设置翻译缓存
        
        Args:
            text: 原文
            translation: 翻译结果
        """
        key = self._make_key(text)
        self.cache[key] = translation
        self._save_cache()
    
    def _make_key(self, text: str) -> str:
        """生成缓存键"""
        return hashlib.md5(text.encode('utf-8')).hexdigest()


class BaiduTranslator:
    """百度翻译API类"""
    
    def __init__(self, app_id: str, app_key: str, api_url: str, char_limit: int = 6000):
        """
        初始化百度翻译
        
        Args:
            app_id: 百度翻译APP ID
            app_key: 百度翻译密钥
            api_url: API地址
            char_limit: 单次请求字符限制
        """
        self.app_id = app_id
        self.app_key = app_key
        self.api_url = api_url
        self.char_limit = char_limit
        self.total_chars_used = 0
        self.total_requests = 0
    
    def is_configured(self) -> bool:
        """检查是否已配置"""
        return bool(self.app_id and self.app_key)
    
    def translate(self, text: str, from_lang: str = 'en', to_lang: str = 'zh') -> Tuple[Optional[str], int]:
        """
        翻译文本
        
        Args:
            text: 待翻译文本
            from_lang: 源语言
            to_lang: 目标语言
            
        Returns:
            (翻译结果, 翻译字符数)
        """
        if not self.is_configured():
            logger.warning("百度翻译未配置APP ID")
            return None, 0
        
        if not text or not text.strip():
            return "", 0
        
        # 截断超长文本
        if len(text) > self.char_limit:
            text = text[:self.char_limit]
            logger.warning(f"文本超过字符限制，截断至 {self.char_limit} 字符")
        
        try:
            # 生成随机数和签名
            salt = str(random.randint(32768, 65536))
            sign_str = self.app_id + text + salt + self.app_key
            sign = hashlib.md5(sign_str.encode('utf-8')).hexdigest()
            
            # 构建请求参数
            params = {
                'q': text,
                'from': from_lang,
                'to': to_lang,
                'appid': self.app_id,
                'salt': salt,
                'sign': sign
            }
            
            # 发送请求
            response = requests.get(self.api_url, params=params, timeout=30)
            response.raise_for_status()
            
            result = response.json()
            
            # 检查错误
            if 'error_code' in result:
                error_code = result['error_code']
                error_msg = result.get('error_msg', '未知错误')
                logger.error(f"百度翻译API错误: {error_code} - {error_msg}")
                return None, 0
            
            # 提取翻译结果
            if 'trans_result' in result and result['trans_result']:
                translations = result['trans_result']
                translated_text = '\n'.join([t['dst'] for t in translations])
                chars_count = len(text)
                
                self.total_chars_used += chars_count
                self.total_requests += 1
                
                logger.debug(f"百度翻译成功: {chars_count} 字符")
                return translated_text, chars_count
            
            return None, 0
            
        except requests.RequestException as e:
            logger.error(f"百度翻译请求失败: {e}")
            return None, 0
        except Exception as e:
            logger.error(f"百度翻译处理失败: {e}")
            return None, 0
    
    def get_usage_stats(self) -> Dict:
        """获取使用统计"""
        return {
            'total_chars': self.total_chars_used,
            'total_requests': self.total_requests,
            'configured': self.is_configured()
        }


class HelsinkiTranslator:
    """Helsinki-NLP开源翻译模型类"""
    
    def __init__(self, model_name: str = "Helsinki-NLP/opus-mt-en-zh", cache_dir: str = None):
        """
        初始化Helsinki翻译器
        
        Args:
            model_name: 模型名称
            cache_dir: 模型缓存目录
        """
        self.model_name = model_name
        self.cache_dir = cache_dir or "data/models"
        self.model = None
        self.tokenizer = None
        self._initialized = False
        self.total_chars_used = 0
        self.total_requests = 0
    
    def _initialize(self):
        """初始化模型（延迟加载）"""
        if self._initialized:
            return
        
        try:
            # 尝试导入transformers库
            from transformers import MarianMTModel, MarianTokenizer
            
            logger.info(f"加载Helsinki-NLP翻译模型: {self.model_name}")
            
            # 设置缓存目录
            if self.cache_dir:
                os.makedirs(self.cache_dir, exist_ok=True)
            
            # 加载模型和tokenizer
            self.tokenizer = MarianTokenizer.from_pretrained(
                self.model_name,
                cache_dir=self.cache_dir
            )
            self.model = MarianMTModel.from_pretrained(
                self.model_name,
                cache_dir=self.cache_dir
            )
            
            self._initialized = True
            logger.info("Helsinki-NLP翻译模型加载成功")
            
        except ImportError:
            logger.warning("transformers库未安装，无法使用Helsinki翻译")
            self._initialized = False
        except Exception as e:
            logger.error(f"加载Helsinki翻译模型失败: {e}")
            self._initialized = False
    
    def is_available(self) -> bool:
        """检查模型是否可用"""
        if not self._initialized:
            self._initialize()
        return self._initialized and self.model is not None
    
    def translate(self, text: str) -> Tuple[Optional[str], int]:
        """
        翻译文本（仅支持英译中）
        
        Args:
            text: 待翻译文本
            
        Returns:
            (翻译结果, 翻译字符数)
        """
        if not self.is_available():
            return None, 0
        
        if not text or not text.strip():
            return "", 0
        
        try:
            # 分批处理长文本
            max_length = 512
            if len(text) > max_length:
                # 分段翻译
                segments = self._split_text(text, max_length)
                translated_segments = []
                
                for segment in segments:
                    translated = self._translate_segment(segment)
                    if translated:
                        translated_segments.append(translated)
                    else:
                        translated_segments.append(segment)  # 保留原文
                    
                    # 添加小延迟避免内存问题
                    time.sleep(0.1)
                
                result = ' '.join(translated_segments)
            else:
                result = self._translate_segment(text)
            
            if result:
                chars_count = len(text)
                self.total_chars_used += chars_count
                self.total_requests += 1
                return result, chars_count
            
            return None, 0
            
        except Exception as e:
            logger.error(f"Helsinki翻译失败: {e}")
            return None, 0
    
    def _translate_segment(self, text: str) -> Optional[str]:
        """翻译单个文本段"""
        try:
            # 编码
            inputs = self.tokenizer(text, return_tensors="pt", max_length=512, truncation=True)
            
            # 翻译
            outputs = self.model.generate(**inputs, max_length=512)
            
            # 解码
            translated = self.tokenizer.decode(outputs[0], skip_special_tokens=True)
            
            return translated
        except Exception as e:
            logger.error(f"翻译段落失败: {e}")
            return None
    
    def _split_text(self, text: str, max_length: int) -> list:
        """分割长文本"""
        # 按句子分割（简单实现）
        sentences = text.replace('\n', ' ').split('. ')
        segments = []
        current_segment = ""
        
        for sentence in sentences:
            if len(current_segment) + len(sentence) < max_length:
                current_segment += sentence + '. '
            else:
                if current_segment:
                    segments.append(current_segment.strip())
                current_segment = sentence + '. '
        
        if current_segment:
            segments.append(current_segment.strip())
        
        return segments
    
    def get_usage_stats(self) -> Dict:
        """获取使用统计"""
        return {
            'total_chars': self.total_chars_used,
            'total_requests': self.total_requests,
            'available': self.is_available()
        }


class TranslationService:
    """翻译服务主类 - 双备份机制"""
    
    def __init__(self, config: Dict):
        """
        初始化翻译服务
        
        Args:
            config: 翻译配置字典
        """
        self.config = config
        self.provider = config.get('provider', 'auto')
        
        # 初始化缓存
        cache_file = config.get('cache_file', 'data/translation_cache.json')
        self.cache = TranslationCache(cache_file) if config.get('cache_enabled', True) else None
        
        # 初始化百度翻译
        baidu_config = config.get('baidu', {})
        self.baidu = BaiduTranslator(
            app_id=baidu_config.get('app_id', ''),
            app_key=baidu_config.get('app_key', ''),
            api_url=baidu_config.get('api_url', 'https://fanyi-api.baidu.com/api/trans/vip/translate'),
            char_limit=baidu_config.get('char_limit_per_request', 6000)
        )
        
        # 初始化Helsinki翻译（延迟加载）
        helsinki_config = config.get('helsinki', {})
        self.helsinki = HelsinkiTranslator(
            model_name=helsinki_config.get('model_name', 'Helsinki-NLP/opus-mt-en-zh'),
            cache_dir=helsinki_config.get('cache_dir', 'data/models')
        )
        
        # 统计文件
        self.stats_file = config.get('stats_file', 'data/translation_stats.json')
        
        logger.info(f"翻译服务初始化完成，模式: {self.provider}")
    
    def translate(self, text: str, from_lang: str = 'en', to_lang: str = 'zh') -> str:
        """
        翻译文本（自动选择翻译服务）
        
        Args:
            text: 待翻译文本
            from_lang: 源语言
            to_lang: 目标语言
            
        Returns:
            翻译结果
        """
        if not text or not text.strip():
            return ""
        
        # 检查是否为中文（无需翻译）
        if self._is_chinese(text):
            return text
        
        # 检查缓存
        if self.cache:
            cached = self.cache.get(text)
            if cached:
                logger.debug("使用翻译缓存")
                return cached
        
        # 根据配置选择翻译服务
        result = None
        chars_count = 0
        provider_used = None
        
        if self.provider == 'auto':
            # 优先使用百度翻译
            if self.baidu.is_configured():
                result, chars_count = self.baidu.translate(text, from_lang, to_lang)
                provider_used = 'baidu'
            
            # 百度失败则降级到Helsinki
            if result is None:
                if self.helsinki.is_available():
                    result, chars_count = self.helsinki.translate(text)
                    provider_used = 'helsinki'
                    logger.info("百度翻译失败，降级使用Helsinki翻译")
        
        elif self.provider == 'baidu':
            result, chars_count = self.baidu.translate(text, from_lang, to_lang)
            provider_used = 'baidu'
        
        elif self.provider == 'helsinki':
            result, chars_count = self.helsinki.translate(text)
            provider_used = 'helsinki'
        
        # 翻译失败则返回原文
        if result is None:
            logger.warning(f"翻译失败，返回原文: {text[:50]}...")
            return text
        
        # 保存到缓存
        if self.cache:
            self.cache.set(text, result)
        
        # 更新统计
        self._update_stats(provider_used, chars_count)
        
        return result
    
    def batch_translate(self, texts: list, from_lang: str = 'en', to_lang: str = 'zh') -> list:
        """
        批量翻译
        
        Args:
            texts: 待翻译文本列表
            from_lang: 源语言
            to_lang: 目标语言
            
        Returns:
            翻译结果列表
        """
        results = []
        for text in texts:
            result = self.translate(text, from_lang, to_lang)
            results.append(result)
            # 添加小延迟避免请求过快
            time.sleep(0.1)
        return results
    
    def _is_chinese(self, text: str) -> bool:
        """检查文本是否主要是中文"""
        chinese_chars = sum(1 for char in text if '\u4e00' <= char <= '\u9fff')
        return chinese_chars > len(text) * 0.5
    
    def _update_stats(self, provider: str, chars_count: int):
        """更新翻译统计"""
        try:
            stats = self._load_stats()
            today = datetime.now().strftime('%Y-%m-%d')
            
            if today not in stats:
                stats[today] = {'baidu': 0, 'helsinki': 0, 'requests': 0}
            
            if provider:
                stats[today][provider] = stats[today].get(provider, 0) + chars_count
                stats[today]['requests'] = stats[today].get('requests', 0) + 1
            
            self._save_stats(stats)
        except Exception as e:
            logger.warning(f"更新翻译统计失败: {e}")
    
    def _load_stats(self) -> Dict:
        """加载统计数据"""
        if os.path.exists(self.stats_file):
            try:
                with open(self.stats_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except:
                return {}
        return {}
    
    def _save_stats(self, stats: Dict):
        """保存统计数据"""
        try:
            stats_dir = os.path.dirname(self.stats_file)
            if stats_dir and not os.path.exists(stats_dir):
                os.makedirs(stats_dir, exist_ok=True)
            
            with open(self.stats_file, 'w', encoding='utf-8') as f:
                json.dump(stats, f, ensure_ascii=False, indent=2)
        except Exception as e:
            logger.warning(f"保存翻译统计失败: {e}")
    
    def get_stats(self) -> Dict:
        """获取翻译统计信息"""
        stats = self._load_stats()
        baidu_stats = self.baidu.get_usage_stats()
        helsinki_stats = self.helsinki.get_usage_stats()
        
        # 计算今日统计
        today = datetime.now().strftime('%Y-%m-%d')
        today_stats = stats.get(today, {'baidu': 0, 'helsinki': 0, 'requests': 0})
        
        return {
            'today': today_stats,
            'baidu': baidu_stats,
            'helsinki': helsinki_stats,
            'current_provider': self.provider,
            'baidu_configured': self.baidu.is_configured(),
            'helsinki_available': self.helsinki.is_available()
        }
    
    def set_baidu_app_id(self, app_id: str):
        """设置百度翻译APP ID"""
        self.baidu.app_id = app_id
        logger.info(f"更新百度翻译APP ID: {app_id[:5]}...")
    
    def set_provider(self, provider: str):
        """设置翻译服务提供商"""
        if provider in ['auto', 'baidu', 'helsinki']:
            self.provider = provider
            logger.info(f"切换翻译服务: {provider}")


def create_translation_service(config: Dict) -> TranslationService:
    """
    创建翻译服务实例
    
    Args:
        config: 配置字典
        
    Returns:
        翻译服务实例
    """
    return TranslationService(config)


if __name__ == "__main__":
    # 测试翻译服务
    import sys
    logging.basicConfig(level=logging.INFO)
    
    # 测试配置
    test_config = {
        'provider': 'auto',
        'baidu': {
            'app_id': '',  # 需要填写
            'app_key': 'Xxuy_d8fa3va3233eom482cbg',
            'api_url': 'https://fanyi-api.baidu.com/api/trans/vip/translate'
        },
        'helsinki': {
            'model_name': 'Helsinki-NLP/opus-mt-en-zh',
            'cache_dir': 'data/models'
        },
        'cache_enabled': True,
        'cache_file': 'data/translation_cache.json',
        'stats_file': 'data/translation_stats.json'
    }
    
    service = create_translation_service(test_config)
    
    # 测试翻译
    test_texts = [
        "This is a test sentence for translation.",
        "Lung cancer is the leading cause of cancer-related deaths worldwide.",
        "EGFR mutations are common in non-small cell lung cancer."
    ]
    
    for text in test_texts:
        result = service.translate(text)
        print(f"原文: {text}")
        print(f"翻译: {result}")
        print("-" * 50)
    
    # 显示统计
    stats = service.get_stats()
    print(f"翻译统计: {stats}")