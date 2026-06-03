"""
配置管理模块
加载、保存和管理系统配置
"""

import yaml
import os
import json
import logging
from typing import Dict, List, Any, Optional
from datetime import datetime

logger = logging.getLogger(__name__)


class ConfigManager:
    """配置管理类"""

    def __init__(self, config_path: str):
        """
        初始化配置管理器

        Args:
            config_path: 配置文件路径
        """
        self.config_path = config_path
        self.config: Dict = {}
        self._load_config()
        self._apply_env_overrides()

    def _load_config(self):
        """加载配置文件"""
        if os.path.exists(self.config_path):
            try:
                with open(self.config_path, 'r', encoding='utf-8') as f:
                    self.config = yaml.safe_load(f)
                logger.info(f"配置加载成功: {self.config_path}")
            except Exception as e:
                logger.error(f"配置加载失败: {e}")
                self.config = {}
        else:
            logger.warning(f"配置文件不存在: {self.config_path}")
            self.config = {}

    def _apply_env_overrides(self):
        """从 .env 文件和系统环境变量中加载敏感配置并覆盖 YAML 配置"""
        try:
            from dotenv import load_dotenv

            project_root = os.path.dirname(
                os.path.dirname(
                    os.path.dirname(os.path.abspath(self.config_path))
                )
            )
            env_path = os.path.join(project_root, '.env')
            if os.path.exists(env_path):
                load_dotenv(env_path)
                logger.info(f"已加载环境变量: {env_path}")
        except ImportError:
            logger.debug("python-dotenv 未安装，跳过 .env 文件加载")

        env_mapping = {
            'PUBMED_API_KEY': ('pubmed.api_key', str),
            'BAIDU_TRANSLATE_APP_ID': ('translation.baidu.app_id', str),
            'BAIDU_TRANSLATE_APP_KEY': ('translation.baidu.app_key', str),
            'TRANSLATION_PROVIDER': ('translation.provider', str),
            'USE_PROXY': ('proxy.use_proxy', lambda v: v.lower() in ('true', '1', 'yes')),
        }

        for env_key, (config_path_key, converter) in env_mapping.items():
            env_value = os.getenv(env_key)
            if env_value:
                yaml_value = self.get(config_path_key, '')
                converted_value = converter(env_value)
                if not yaml_value or yaml_value != converted_value:
                    self.set(config_path_key, converted_value, save=False)
                    logger.debug(f"环境变量覆盖: {config_path_key}")
    
    def _save_config(self):
        """保存配置文件"""
        try:
            config_dir = os.path.dirname(self.config_path)
            if config_dir and not os.path.exists(config_dir):
                os.makedirs(config_dir, exist_ok=True)
            
            with open(self.config_path, 'w', encoding='utf-8') as f:
                yaml.dump(self.config, f, default_flow_style=False, allow_unicode=True)
            logger.info(f"配置保存成功: {self.config_path}")
        except Exception as e:
            logger.error(f"配置保存失败: {e}")
    
    def get(self, key: str, default: Any = None) -> Any:
        """
        获取配置值
        
        Args:
            key: 配置键（支持多级，如 'pubmed.api_key'）
            default: 默认值
            
        Returns:
            配置值
        """
        keys = key.split('.')
        value = self.config
        
        for k in keys:
            if isinstance(value, dict) and k in value:
                value = value[k]
            else:
                return default
        
        return value
    
    def set(self, key: str, value: Any, save: bool = True):
        """
        设置配置值
        
        Args:
            key: 配置键（支持多级）
            value: 配置值
            save: 是否立即保存
        """
        keys = key.split('.')
        config = self.config
        
        # 遍历到最后一级的父级
        for k in keys[:-1]:
            if k not in config:
                config[k] = {}
            config = config[k]
        
        # 设置值
        config[keys[-1]] = value
        
        if save:
            self._save_config()
    
    def get_pubmed_config(self) -> Dict:
        """获取PubMed配置"""
        return self.get('pubmed', {})
    
    def get_translation_config(self) -> Dict:
        """获取翻译配置"""
        return self.get('translation', {})
    
    def get_target_genes(self) -> List[str]:
        """获取目标基因列表"""
        return self.get('target_genes', [])
    
    def set_target_genes(self, genes: List[str]):
        """设置目标基因列表"""
        self.set('target_genes', genes)
    
    def add_target_gene(self, gene: str):
        """添加目标基因"""
        genes = self.get_target_genes()
        if gene not in genes:
            genes.append(gene)
            self.set_target_genes(genes)
    
    def remove_target_gene(self, gene: str):
        """移除目标基因"""
        genes = self.get_target_genes()
        if gene in genes:
            genes.remove(gene)
            self.set_target_genes(genes)
    
    def get_tumor_types(self) -> List[Dict]:
        """获取肿瘤类型列表"""
        return self.get('tumor_types', [])
    
    def set_tumor_types(self, tumor_types: List[Dict]):
        """设置肿瘤类型列表"""
        self.set('tumor_types', tumor_types)
    
    def add_tumor_type(self, cn: str, en: str, aliases_en: List[str] = None):
        """添加肿瘤类型"""
        tumor_types = self.get_tumor_types()
        new_type = {'cn': cn, 'en': en}
        if aliases_en:
            new_type['aliases_en'] = aliases_en
        tumor_types.append(new_type)
        self.set_tumor_types(tumor_types)
    
    def remove_tumor_type(self, cn: str):
        """移除肿瘤类型"""
        tumor_types = self.get_tumor_types()
        tumor_types = [t for t in tumor_types if t.get('cn') != cn]
        self.set_tumor_types(tumor_types)
    
    def get_scheduler_config(self) -> Dict:
        """获取定时任务配置"""
        return self.get('scheduler', {})
    
    def set_scheduler_time(self, task_name: str, cron_expression: str):
        """设置定时任务时间"""
        scheduler = self.get_scheduler_config()
        scheduler[task_name] = cron_expression
        self.set('scheduler', scheduler)
    
    def get_proxy_config(self) -> Dict:
        """获取代理配置"""
        return self.get('proxy', {})
    
    def get_storage_config(self) -> Dict:
        """获取存储配置"""
        return self.get('storage', {})
    
    def get_database_path(self) -> str:
        """获取数据库路径"""
        return self.get('storage.database_path', 'data/medical_info.db')
    
    def get_labels_path(self) -> str:
        """获取说明书存储路径"""
        return self.get('storage.labels_path', 'data/labels/')
    
    def get_exports_path(self) -> str:
        """获取导出文件路径"""
        return self.get('storage.exports_path', 'data/exports/')
    
    def get_fda_config(self) -> Dict:
        """获取FDA配置"""
        return self.get('fda', {})
    
    def get_clinical_trials_config(self) -> Dict:
        """获取临床试验配置"""
        return self.get('clinical_trials_gov', {})
    
    def get_conferences_config(self) -> Dict:
        """获取会议配置"""
        return self.get('conferences', {})
    
    def get_cancer_keywords(self) -> List[str]:
        """获取癌症关键词列表"""
        return self.get('fda.cancer_keywords', [])
    
    def set_baidu_app_id(self, app_id: str):
        """设置百度翻译APP ID"""
        translation = self.get_translation_config()
        if 'baidu' not in translation:
            translation['baidu'] = {}
        translation['baidu']['app_id'] = app_id
        self.set('translation', translation)
    
    def get_baidu_config(self) -> Dict:
        """获取百度翻译配置"""
        return self.get('translation.baidu', {})
    
    def set_translation_provider(self, provider: str):
        """设置翻译服务提供商"""
        self.set('translation.provider', provider)
    
    def set_proxy_list(self, proxy_list: List[str]):
        """设置代理列表"""
        proxy = self.get_proxy_config()
        proxy['proxy_list'] = proxy_list
        self.set('proxy', proxy)
    
    def get_search_query_template(self) -> str:
        """获取检索式模板"""
        genes = self.get_target_genes()
        tumor_types = self.get_tumor_types()
        
        # 构建基因检索部分
        gene_query = ' OR '.join(genes[:20])  # 限制基因数量避免查询过长
        
        # 构建肿瘤类型检索部分（包含中英文）
        tumor_terms = []
        for tumor in tumor_types[:30]:  # 限制肿瘤类型数量
            tumor_terms.append(tumor.get('cn', ''))
            tumor_terms.append(tumor.get('en', ''))
            if tumor.get('aliases_en'):
                tumor_terms.extend(tumor['aliases_en'])
        
        tumor_query = ' OR '.join([t for t in tumor_terms if t])
        
        # 构建完整检索式
        query = f"({gene_query}) AND ({tumor_query}) AND (targeted therapy OR immunotherapy OR drug treatment)"
        
        return query
    
    def build_pubmed_query(self, genes: List[str] = None, tumor_types: List[str] = None) -> str:
        """
        构建PubMed检索式
        
        Args:
            genes: 基因列表（可选，默认使用配置中的基因）
            tumor_types: 肿瘤类型列表（可选）
            
        Returns:
            PubMed检索式
        """
        if genes is None:
            genes = self.get_target_genes()[:20]
        
        if tumor_types is None:
            tumor_types = self.get_tumor_types()[:30]
        
        # 构建基因部分
        gene_part = ' OR '.join(genes)
        
        # 构建肿瘤类型部分（中英文）
        tumor_terms = []
        for tumor in tumor_types:
            tumor_terms.append(tumor.get('cn', ''))
            tumor_terms.append(tumor.get('en', ''))
            if tumor.get('aliases_en'):
                tumor_terms.extend(tumor['aliases_en'])
        
        tumor_part = ' OR '.join([t for t in tumor_terms if t])
        
        # 构建治疗类型部分
        treatment_part = "targeted therapy OR immunotherapy OR drug treatment OR chemotherapy"
        
        # 组合检索式
        query = f"(({gene_part}) AND ({tumor_part}) AND ({treatment_part})) AND (clinical trial OR therapeutic OR treatment)"
        
        return query
    
    def build_clinical_trials_query(self, genes: List[str] = None, tumor_types: List[str] = None) -> str:
        """
        构建临床试验检索条件
        
        Args:
            genes: 基因列表
            tumor_types: 肿瘤类型列表
            
        Returns:
            检索条件字符串
        """
        if genes is None:
            genes = self.get_target_genes()[:15]
        
        if tumor_types is None:
            tumor_types = self.get_tumor_types()[:20]
        
        # 构建肿瘤类型条件
        tumor_terms = []
        for tumor in tumor_types:
            tumor_terms.append(tumor.get('en', ''))
            if tumor.get('aliases_en'):
                tumor_terms.extend(tumor['aliases_en'])
        
        # 返回检索条件
        conditions = {
            'genes': genes,
            'tumors': tumor_terms
        }
        
        return conditions
    
    def get_all_config(self) -> Dict:
        """获取完整配置"""
        return self.config
    
    def reload_config(self):
        """重新加载配置"""
        self._load_config()
    
    def export_config(self, export_path: str):
        """导出配置到文件"""
        try:
            with open(export_path, 'w', encoding='utf-8') as f:
                yaml.dump(self.config, f, default_flow_style=False, allow_unicode=True)
            logger.info(f"配置导出成功: {export_path}")
        except Exception as e:
            logger.error(f"配置导出失败: {e}")
    
    def import_config(self, import_path: str):
        """从文件导入配置"""
        try:
            with open(import_path, 'r', encoding='utf-8') as f:
                imported_config = yaml.safe_load(f)
            
            # 合并配置
            self.config.update(imported_config)
            self._save_config()
            logger.info(f"配置导入成功: {import_path}")
        except Exception as e:
            logger.error(f"配置导入失败: {e}")
    
    def validate_config(self) -> List[str]:
        """验证配置完整性"""
        errors = []
        
        # 检查必要配置项
        required_keys = [
            'pubmed.api_key',
            'storage.database_path',
            'target_genes',
            'tumor_types'
        ]
        
        for key in required_keys:
            if not self.get(key):
                errors.append(f"缺少必要配置: {key}")
        
        # 检查百度翻译配置
        translation = self.get_translation_config()
        if translation.get('provider') == 'baidu':
            if not translation.get('baidu', {}).get('app_id'):
                errors.append("百度翻译模式需要配置APP ID")
        
        return errors
    
    def get_system_info(self) -> Dict:
        """获取系统信息摘要"""
        return {
            'config_path': self.config_path,
            'target_genes_count': len(self.get_target_genes()),
            'tumor_types_count': len(self.get_tumor_types()),
            'translation_provider': self.get('translation.provider', 'auto'),
            'baidu_configured': bool(self.get('translation.baidu.app_id')),
            'proxy_enabled': self.get('proxy.use_proxy', False),
            'database_path': self.get_database_path(),
            'scheduler_tasks': list(self.get_scheduler_config().keys())
        }


def create_config_manager(config_path: str) -> ConfigManager:
    """
    创建配置管理器实例
    
    Args:
        config_path: 配置文件路径
        
    Returns:
        配置管理器实例
    """
    return ConfigManager(config_path)


if __name__ == "__main__":
    # 测试配置管理
    import sys
    logging.basicConfig(level=logging.INFO)
    
    config_path = "config/config.yaml"
    manager = create_config_manager(config_path)
    
    print("配置信息:")
    info = manager.get_system_info()
    for key, value in info.items():
        print(f"  {key}: {value}")
    
    print("\n目标基因数量:", len(manager.get_target_genes()))
    print("肿瘤类型数量:", len(manager.get_tumor_types()))
    
    print("\nPubMed检索式示例:")
    query = manager.build_pubmed_query()
    print(query[:200] + "...")