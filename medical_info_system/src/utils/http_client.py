"""
HTTP请求工具模块
实现反爬虫策略和代理轮换
"""

import time
import random
import logging
import requests
from typing import Dict, Optional, List, Tuple
from datetime import datetime
import hashlib

logger = logging.getLogger(__name__)


class ProxyManager:
    """代理管理类"""
    
    def __init__(self, proxy_list: List[str] = None):
        """
        初始化代理管理器
        
        Args:
            proxy_list: 代理列表
        """
        self.proxy_list = proxy_list or []
        self.failed_proxies: set = set()
        self.proxy_stats: Dict = {}
        
        # 内置免费代理池（备用）
        self.builtin_proxies = [
            # 这里可以添加一些免费代理，实际使用时需要验证
            # 由于免费代理不稳定，建议用户配置自己的代理
        ]
        
        if not self.proxy_list:
            logger.info("使用内置代理池（免费代理可能不稳定）")
            self.proxy_list = self.builtin_proxies
    
    def get_proxy(self) -> Optional[str]:
        """获取可用代理"""
        available = [p for p in self.proxy_list if p not in self.failed_proxies]
        
        if not available:
            logger.warning("没有可用代理")
            return None
        
        # 随机选择
        proxy = random.choice(available)
        return proxy
    
    def mark_failed(self, proxy: str):
        """标记代理失败"""
        self.failed_proxies.add(proxy)
        logger.warning(f"代理失败: {proxy}")
    
    def reset_failed(self):
        """重置失败代理列表"""
        self.failed_proxies.clear()
        logger.info("重置失败代理列表")
    
    def add_proxy(self, proxy: str):
        """添加代理"""
        if proxy not in self.proxy_list:
            self.proxy_list.append(proxy)
            logger.info(f"添加代理: {proxy}")
    
    def remove_proxy(self, proxy: str):
        """移除代理"""
        if proxy in self.proxy_list:
            self.proxy_list.remove(proxy)
            logger.info(f"移除代理: {proxy}")


class UserAgentRotator:
    """User-Agent轮换类"""
    
    def __init__(self):
        """初始化User-Agent轮换器"""
        self.user_agents = [
            # Chrome
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36",
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            # Firefox
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:121.0) Gecko/20100101 Firefox/121.0",
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:121.0) Gecko/20100101 Firefox/121.0",
            # Safari
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.2 Safari/605.1.15",
            # Edge
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36 Edg/120.0.0.0",
            # 爬虫友好
            "Mozilla/5.0 (compatible; MedicalInfoBot/1.0; +http://example.com/bot)",
        ]
    
    def get_random(self) -> str:
        """获取随机User-Agent"""
        return random.choice(self.user_agents)
    
    def get_browser_like(self) -> str:
        """获取浏览器风格的User-Agent"""
        browser_agents = [ua for ua in self.user_agents if 'compatible' not in ua]
        return random.choice(browser_agents)


class RequestManager:
    """HTTP请求管理类"""
    
    def __init__(self, config: Dict):
        """
        初始化请求管理器
        
        Args:
            config: 代理配置
        """
        self.config = config
        self.use_proxy = config.get('use_proxy', False)
        self.delay_min = config.get('request_delay_min', 3)
        self.delay_max = config.get('request_delay_max', 5)
        self.max_retries = config.get('max_retries', 3)
        self.retry_delay_base = config.get('retry_delay_base', 2)
        
        self.proxy_manager = ProxyManager(config.get('proxy_list', []))
        self.ua_rotator = UserAgentRotator()
        
        self.request_count = 0
        self.success_count = 0
        self.failure_count = 0
        
        # 创建session
        self.session = requests.Session()
        
        logger.info(f"请求管理器初始化: 代理={self.use_proxy}, 重试={self.max_retries}")
    
    def _add_random_delay(self):
        """添加随机延迟"""
        delay = random.uniform(self.delay_min, self.delay_max)
        time.sleep(delay)
    
    def _get_headers(self, url: str) -> Dict:
        """构建请求头"""
        headers = {
            'User-Agent': self.ua_rotator.get_browser_like(),
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5,zh-CN;q=0.3,zh;q=0.2',
            'Accept-Encoding': 'gzip, deflate, br',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
        }
        
        # 添加Referer
        if url:
            headers['Referer'] = url
        
        return headers
    
    def _get_proxies(self) -> Optional[Dict]:
        """获取代理配置"""
        if not self.use_proxy:
            return None
        
        proxy = self.proxy_manager.get_proxy()
        if proxy:
            return {
                'http': proxy,
                'https': proxy
            }
        
        return None
    
    def request(self, method: str, url: str, **kwargs) -> Optional[requests.Response]:
        """
        发送请求（带重试机制）
        
        Args:
            method: 请求方法
            url: 请求URL
            **kwargs: 其他请求参数
            
        Returns:
            响应对象
        """
        self.request_count += 1
        
        # 合并默认参数
        headers = self._get_headers(url)
        if 'headers' in kwargs:
            headers.update(kwargs['headers'])
        kwargs['headers'] = headers
        
        # 设置超时
        if 'timeout' not in kwargs:
            kwargs['timeout'] = 30
        
        # 设置代理
        proxies = self._get_proxies()
        if proxies:
            kwargs['proxies'] = proxies
        
        # 重试机制
        for attempt in range(self.max_retries):
            try:
                # 添加随机延迟（模拟人类行为）
                self._add_random_delay()
                
                # 发送请求
                response = self.session.request(method, url, **kwargs)
                
                # 检查响应状态
                if response.status_code == 200:
                    self.success_count += 1
                    logger.debug(f"请求成功: {url}")
                    return response
                
                elif response.status_code == 429:
                    # 请求过于频繁
                    wait_time = self.retry_delay_base ** (attempt + 2)
                    logger.warning(f"请求频率限制，等待 {wait_time} 秒")
                    time.sleep(wait_time)
                    continue
                
                elif response.status_code in [403, 404, 500, 502, 503]:
                    # 服务器错误
                    if attempt < self.max_retries - 1:
                        wait_time = self.retry_delay_base ** (attempt + 1)
                        logger.warning(f"服务器错误 {response.status_code}, 重试 {attempt + 1}/{self.max_retries}")
                        time.sleep(wait_time)
                        continue
                
                else:
                    logger.warning(f"请求失败: {url}, 状态码: {response.status_code}")
                    self.failure_count += 1
                    return None
                    
            except requests.exceptions.ProxyError as e:
                # 代理错误
                if proxies:
                    proxy = list(proxies.values())[0]
                    self.proxy_manager.mark_failed(proxy)
                logger.warning(f"代理错误: {e}")
                
                if attempt < self.max_retries - 1:
                    continue
                    
            except requests.exceptions.Timeout as e:
                logger.warning(f"请求超时: {url}")
                if attempt < self.max_retries - 1:
                    wait_time = self.retry_delay_base ** (attempt + 1)
                    time.sleep(wait_time)
                    continue
                    
            except requests.exceptions.RequestException as e:
                logger.error(f"请求异常: {e}")
                if attempt < self.max_retries - 1:
                    wait_time = self.retry_delay_base ** (attempt + 1)
                    time.sleep(wait_time)
                    continue
        
        self.failure_count += 1
        logger.error(f"请求最终失败: {url}")
        return None
    
    def get(self, url: str, **kwargs) -> Optional[requests.Response]:
        """GET请求"""
        return self.request('GET', url, **kwargs)
    
    def post(self, url: str, **kwargs) -> Optional[requests.Response]:
        """POST请求"""
        return self.request('POST', url, **kwargs)
    
    def get_json(self, url: str, **kwargs) -> Optional[Dict]:
        """获取JSON响应"""
        response = self.get(url, **kwargs)
        if response:
            try:
                return response.json()
            except Exception as e:
                logger.error(f"JSON解析失败: {e}")
        return None
    
    def get_content(self, url: str, **kwargs) -> Optional[str]:
        """获取文本内容"""
        response = self.get(url, **kwargs)
        if response:
            return response.text
        return None
    
    def download_file(self, url: str, save_path: str, **kwargs) -> bool:
        """
        下载文件
        
        Args:
            url: 文件URL
            save_path: 保存路径
            
        Returns:
            是否成功
        """
        response = self.get(url, stream=True, **kwargs)
        if response:
            try:
                # 确保目录存在
                import os
                os.makedirs(os.path.dirname(save_path), exist_ok=True)
                
                # 写入文件
                with open(save_path, 'wb') as f:
                    for chunk in response.iter_content(chunk_size=8192):
                        if chunk:
                            f.write(chunk)
                
                logger.info(f"文件下载成功: {save_path}")
                return True
                
            except Exception as e:
                logger.error(f"文件保存失败: {e}")
        
        return False
    
    def get_stats(self) -> Dict:
        """获取请求统计"""
        return {
            'total_requests': self.request_count,
            'success_count': self.success_count,
            'failure_count': self.failure_count,
            'success_rate': self.success_count / self.request_count if self.request_count > 0 else 0,
            'proxy_enabled': self.use_proxy,
            'available_proxies': len(self.proxy_manager.proxy_list) - len(self.proxy_manager.failed_proxies)
        }
    
    def reset_stats(self):
        """重置统计"""
        self.request_count = 0
        self.success_count = 0
        self.failure_count = 0
    
    def close(self):
        """关闭session"""
        self.session.close()


def create_request_manager(config: Dict) -> RequestManager:
    """
    创建请求管理器实例
    
    Args:
        config: 配置字典
        
    Returns:
        请求管理器实例
    """
    return RequestManager(config)


if __name__ == "__main__":
    # 测试请求管理器
    import sys
    logging.basicConfig(level=logging.INFO)
    
    test_config = {
        'use_proxy': False,
        'request_delay_min': 1,
        'request_delay_max': 2,
        'max_retries': 3,
        'retry_delay_base': 2
    }
    
    manager = create_request_manager(test_config)
    
    # 测试请求
    test_url = "https://api.fda.gov/drug/drugsfda.json?limit=1"
    result = manager.get_json(test_url)
    
    if result:
        print("请求成功!")
        print(f"结果: {result}")
    
    stats = manager.get_stats()
    print(f"请求统计: {stats}")
    
    manager.close()