#!/usr/bin/env python3
"""
医学信息收集系统 - 主启动脚本
Medical Information Collection System - Main Entry Point
"""

import os
import sys
import logging
import argparse

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from src.database import init_database
from src.utils.config_manager import create_config_manager
from src.utils.translator import create_translation_service
from src.scheduler import create_scheduler_manager, run_scheduler_standalone


def setup_logging(log_level: str = 'INFO'):
    """配置日志"""
    log_dir = 'data/logs'
    os.makedirs(log_dir, exist_ok=True)

    log_file = os.path.join(log_dir, 'system.log')

    logging.basicConfig(
        level=getattr(logging, log_level.upper()),
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(log_file),
            logging.StreamHandler()
        ]
    )


def init_system():
    """初始化系统并返回核心组件（不关闭数据库）"""
    print("=" * 60)
    print("医学信息收集系统 - Medical Information Collection System")
    print("=" * 60)
    print()

    base_path = os.path.dirname(os.path.abspath(__file__))
    db_path = os.path.join(base_path, 'data', 'medical_info.db')
    config_path = os.path.join(base_path, 'config', 'config.yaml')

    print("正在初始化数据库...")
    db_manager = init_database(db_path)

    tables = db_manager.execute_query("SELECT name FROM sqlite_master WHERE type='table'")
    print(f"数据库初始化完成，创建 {len(tables)} 个数据表")

    print("正在加载配置...")
    config_manager = create_config_manager(config_path)

    config_info = config_manager.get_system_info()
    print(f"配置加载完成:")
    print(f"  - 目标基因数: {config_info['target_genes_count']}")
    print(f"  - 肿瘤类型数: {config_info['tumor_types_count']}")
    print(f"  - 翻译服务: {config_info['translation_provider']}")

    print("正在初始化翻译服务...")
    translation_config = config_manager.get_translation_config()
    translation_service = create_translation_service(translation_config)

    stats = translation_service.get_stats()
    print(f"翻译服务初始化完成:")
    print(f"  - 百度翻译: {'已配置' if stats['baidu_configured'] else '未配置'}")
    print(f"  - Helsinki模型: {'可用' if stats['helsinki_available'] else '待加载'}")

    print()
    print("系统初始化完成！")
    print()

    return db_manager, config_manager, translation_service


def run_web():
    """运行Web界面"""
    print("正在启动Web界面...")
    print()
    print("访问地址: http://localhost:8501")
    print()

    os.chdir(os.path.dirname(os.path.abspath(__file__)))

    import streamlit.web.cli as stcli

    sys.argv = [
        "streamlit",
        "run",
        "src/web/app.py",
        "--server.port=8501",
        "--server.address=localhost"
    ]

    stcli.main()


def run_scheduler():
    """运行定时任务调度器"""
    print("正在启动定时任务调度器...")
    print()

    run_scheduler_standalone()


def run_collect_once(
    module: str,
    db_manager,
    config_manager,
    translation_service
):
    """使用已有组件运行一次采集"""
    print(f"正在执行采集任务: {module}")
    print()

    scheduler_manager = create_scheduler_manager(
        db_manager,
        config_manager,
        translation_service
    )

    if module == 'all':
        scheduler_manager.run_all_now()
    else:
        module_map = {
            'fda': 'fda_approved',
            'pubmed': 'academic_papers',
            'clinical_trials': 'clinical_trials',
        }
        collector_key = module_map.get(module)
        if collector_key and collector_key in scheduler_manager.collectors:
            scheduler_manager.collectors[collector_key].run()
        else:
            print(f"未知模块: {module}")
            print("可用模块: fda, pubmed, clinical_trials, all")

    scheduler_manager.stop()

    print()
    print("采集任务完成！")


def show_status(db_manager, config_manager):
    """显示系统状态"""
    print("系统状态:")
    print()

    stats = {
        'approved_drugs': db_manager.get_record_count('approved_drugs'),
        'nda_drugs': db_manager.get_record_count('nda_drugs'),
        'cde_special': db_manager.get_record_count('cde_special_drugs'),
        'academic_papers': db_manager.get_record_count('academic_papers'),
        'conference_abstracts': db_manager.get_record_count('conference_abstracts'),
        'clinical_trials': db_manager.get_record_count('clinical_trials'),
    }

    print("数据统计:")
    for table, count in stats.items():
        print(f"  - {table}: {count} 条记录")

    print()

    config_info = config_manager.get_system_info()
    print("配置信息:")
    for key, value in config_info.items():
        print(f"  - {key}: {value}")


def main():
    """主函数"""
    parser = argparse.ArgumentParser(
        description='医学信息收集系统 - Medical Information Collection System'
    )

    parser.add_argument(
        'command',
        choices=['init', 'web', 'scheduler', 'collect', 'status'],
        help='执行命令: init(初始化), web(Web界面), scheduler(定时任务), collect(采集), status(状态)'
    )

    parser.add_argument(
        '--module',
        default='all',
        help='采集模块: fda, pubmed, clinical_trials, all'
    )

    parser.add_argument(
        '--log-level',
        default='INFO',
        help='日志级别: DEBUG, INFO, WARNING, ERROR'
    )

    args = parser.parse_args()

    setup_logging(args.log_level)

    if args.command in ('init',):
        db_manager, config_manager, translation_service = init_system()
        db_manager.close()
        return

    if args.command == 'web':
        init_system()
        run_web()
        return

    if args.command == 'scheduler':
        run_scheduler()
        return

    db_manager, config_manager, translation_service = init_system()

    try:
        if args.command == 'collect':
            run_collect_once(args.module, db_manager, config_manager, translation_service)
        elif args.command == 'status':
            show_status(db_manager, config_manager)
    finally:
        db_manager.close()


if __name__ == "__main__":
    main()
