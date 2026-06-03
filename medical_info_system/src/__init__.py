"""
医学信息收集系统 - 主入口文件
"""

__version__ = "1.0.0"
__author__ = "TRAE SOLO Coder"

from .database import DatabaseManager, init_database
from .utils import (
    TranslationService,
    create_translation_service,
    ConfigManager,
    create_config_manager,
    RequestManager,
    create_request_manager
)

__all__ = [
    'DatabaseManager',
    'init_database',
    'TranslationService',
    'create_translation_service',
    'ConfigManager',
    'create_config_manager',
    'RequestManager',
    'create_request_manager'
]