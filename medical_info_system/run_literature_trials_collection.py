import os
import sys
import logging

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('data_collection.log', encoding='utf-8'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

from src.database import DatabaseManager
from src.utils.config_manager import ConfigManager
from src.utils.translator import TranslationService
from src.collectors.pubmed_collector import PubMedCollector
from src.collectors.crossref_collector import CrossRefCollector
from src.collectors.clinical_trials_collector import ClinicalTrialsCollector


def run_pubmed_collection():
    logger.info("=" * 60)
    logger.info("开始运行 PubMed 学术文献采集")
    logger.info("=" * 60)

    try:
        base_dir = os.path.dirname(os.path.abspath(__file__))
        db_path = os.path.join(base_dir, 'data', 'medical_info.db')
        config_path = os.path.join(base_dir, 'config', 'config.yaml')
        
        db_manager = DatabaseManager(db_path)
        db_manager.init_tables()
        config_manager = ConfigManager(config_path)
        translation_service = TranslationService(config_manager)

        collector = PubMedCollector(db_manager, config_manager, translation_service)

        result = collector.run()

        logger.info("=" * 60)
        logger.info("PubMed 采集完成！")
        logger.info(f"处理: {result.get('records_processed', 0)} 条")
        logger.info(f"新增: {result.get('records_added', 0)} 条")
        logger.info(f"错误: {result.get('errors_count', 0)} 条")
        logger.info("=" * 60)

        return result
    except Exception as e:
        logger.error(f"PubMed 采集失败: {e}")
        import traceback
        traceback.print_exc()
        return None


def run_crossref_collection():
    logger.info("=" * 60)
    logger.info("开始运行 CrossRef 学术文献采集")
    logger.info("=" * 60)

    try:
        base_dir = os.path.dirname(os.path.abspath(__file__))
        db_path = os.path.join(base_dir, 'data', 'medical_info.db')
        config_path = os.path.join(base_dir, 'config', 'config.yaml')

        db_manager = DatabaseManager(db_path)
        db_manager.init_tables()
        config_manager = ConfigManager(config_path)
        translation_service = TranslationService(config_manager)

        collector = CrossRefCollector(db_manager, config_manager, translation_service)

        result = collector.run()

        logger.info("=" * 60)
        logger.info("CrossRef 采集完成！")
        logger.info(f"处理: {result.get('records_processed', 0)} 条")
        logger.info(f"新增: {result.get('records_added', 0)} 条")
        logger.info(f"错误: {result.get('errors_count', 0)} 条")
        logger.info("=" * 60)

        return result
    except Exception as e:
        logger.error(f"CrossRef 采集失败: {e}")
        import traceback
        traceback.print_exc()
        return None


def run_clinical_trials_collection():
    logger.info("=" * 60)
    logger.info("开始运行 ClinicalTrials.gov 临床试验采集")
    logger.info("=" * 60)

    try:
        base_dir = os.path.dirname(os.path.abspath(__file__))
        db_path = os.path.join(base_dir, 'data', 'medical_info.db')
        config_path = os.path.join(base_dir, 'config', 'config.yaml')
        
        db_manager = DatabaseManager(db_path)
        db_manager.init_tables()
        config_manager = ConfigManager(config_path)
        translation_service = TranslationService(config_manager)

        collector = ClinicalTrialsCollector(db_manager, config_manager, translation_service)

        result = collector.collect(max_pages=20)

        logger.info("=" * 60)
        logger.info("ClinicalTrials.gov 采集完成！")
        logger.info(f"处理: {result.get('records_processed', 0)} 条")
        logger.info(f"新增: {result.get('records_added', 0)} 条")
        logger.info(f"错误: {result.get('errors_count', 0)} 条")
        logger.info("=" * 60)

        return result
    except Exception as e:
        logger.error(f"ClinicalTrials.gov 采集失败: {e}")
        import traceback
        traceback.print_exc()
        return None


if __name__ == "__main__":
    logger.info("\n" + "=" * 60)
    logger.info("学术文献与临床试验信息采集")
    logger.info("=" * 60)

    pubmed_result = run_pubmed_collection()

    logger.info("\n")

    crossref_result = run_crossref_collection()

    logger.info("\n")

    ct_result = run_clinical_trials_collection()

    logger.info("\n" + "=" * 60)
    logger.info("所有采集任务完成汇总")
    logger.info("=" * 60)
    if pubmed_result:
        logger.info(f"PubMed文献: 处理 {pubmed_result.get('records_processed', 0)} 条, 新增 {pubmed_result.get('records_added', 0)} 条")
    if crossref_result:
        logger.info(f"CrossRef文献: 处理 {crossref_result.get('records_processed', 0)} 条, 新增 {crossref_result.get('records_added', 0)} 条")
    if ct_result:
        logger.info(f"临床试验: 处理 {ct_result.get('records_processed', 0)} 条, 新增 {ct_result.get('records_added', 0)} 条")
    logger.info("=" * 60)
