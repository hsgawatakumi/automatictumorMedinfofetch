#!/usr/bin/env python3
"""
临床试验优化采集器测试脚本
"""
import os
import sys
import logging

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from src.database import DatabaseManager, init_database
from src.utils.config_manager import ConfigManager
from src.utils.translator import TranslationService
from src.collectors.clinical_trials_optimized import ClinicalTrialsOptimizedCollector

# 设置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def main():
    print("=" * 100)
    print("开始运行临床试验优化采集器")
    print("=" * 100)
    
    # 初始化组件
    base_path = os.path.dirname(os.path.abspath(__file__))
    db_path = os.path.join(base_path, 'data', 'medical_info.db')
    config_path = os.path.join(base_path, 'config', 'system_config.json')
    
    # 初始化数据库
    db_manager = init_database(db_path)
    
    # 初始化配置管理器
    config_manager = ConfigManager(config_path)
    
    # 初始化翻译服务
    translation_config = config_manager.get_translation_config()
    translation_service = TranslationService(translation_config)
    
    # 创建采集器
    collector = ClinicalTrialsOptimizedCollector(db_manager, config_manager, translation_service)
    
    # 运行采集
    print("\n开始采集所有平台的数据...")
    print("-" * 100)
    
    result = collector.collect_all()
    
    print("\n" + "=" * 100)
    print("采集结果统计")
    print("=" * 100)
    print(f"状态: {result.get('status')}")
    print(f"处理记录数: {result.get('records_processed')}")
    print(f"新增记录数: {result.get('records_added')}")
    print(f"错误数: {result.get('errors_count')}")
    print(f"耗时: {result.get('duration_seconds'):.1f} 秒")
    print(f"消息: {result.get('message')}")
    
    # 验证数据
    print("\n" + "=" * 100)
    print("数据验证")
    print("=" * 100)
    
    # 检查各平台数据
    platforms = ['ClinicalTrials.gov', 'CDE', 'ChiCTR']
    
    for platform in platforms:
        count = db_manager.get_record_count(
            'clinical_trials',
            "platform = ?",
            (platform,)
        )
        print(f"{platform}: {count} 条记录")
    
    # 显示部分样本数据
    print("\n样本数据预览:")
    print("-" * 100)
    
    trials = db_manager.execute_query(
        "SELECT * FROM clinical_trials ORDER BY data_collection_time DESC LIMIT 3"
    )
    
    for i, trial in enumerate(trials):
        print(f"\n{i+1}. ID: {trial['trial_id']}")
        print(f"   平台: {trial['platform']}")
        print(f"   标题(中文): {trial.get('study_title_cn', '')[:50]}...")
        print(f"   标题(英文): {trial.get('study_title_en', '')[:50]}...")
        print(f"   状态: {trial.get('trial_status', '')}")
        print(f"   分期: {trial.get('phase', '')}")
        print(f"   基因: {trial.get('gene_marker', '')}")
        print(f"   链接: {trial.get('url', '')}")
    
    db_manager.close()
    
    print("\n" + "=" * 100)
    print("测试完成！")
    print("=" * 100)


if __name__ == "__main__":
    main()