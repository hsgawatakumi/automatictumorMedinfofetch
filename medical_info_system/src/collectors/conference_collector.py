"""
肿瘤学会议摘要采集模块
采集ASCO/ESMO/AACR等顶级肿瘤学会议摘要
"""

import os
import sys
import json
import time
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from src.database import DatabaseManager
from src.utils.config_manager import ConfigManager
from src.utils.translator import TranslationService
from src.utils.http_client import RequestManager

logger = logging.getLogger(__name__)


class ConferenceAbstractCollector:
    """肿瘤学会议摘要采集类"""

    # 会议配置
    CONFERENCES = {
        'asco': {
            'name': 'ASCO',
            'full_name': 'American Society of Clinical Oncology',
        },
        'esmo': {
            'name': 'ESMO',
            'full_name': 'European Society for Medical Oncology',
        },
        'aacr': {
            'name': 'AACR',
            'full_name': 'American Association for Cancer Research',
        }
    }

    def __init__(
        self,
        db_manager: DatabaseManager,
        config_manager: ConfigManager,
        translation_service: TranslationService,
        request_manager: RequestManager
    ):
        self.db_manager = db_manager
        self.config_manager = config_manager
        self.translation_service = translation_service
        self.request_manager = request_manager

        self.target_genes = config_manager.get_target_genes()
        self.tumor_types = config_manager.get_tumor_types()
        self.cancer_keywords = config_manager.get_cancer_keywords()

        # 统计信息
        self.records_processed = 0
        self.records_added = 0
        self.records_updated = 0
        self.errors_count = 0

        logger.info("会议摘要采集器初始化完成")

    def _get_sample_conference_data(self, conference: str) -> List[Dict]:
        """
        获取示例会议数据（用于演示和测试）

        Args:
            conference: 会议名称缩写
        Returns:
            示例会议摘要列表
        """
        # 根据会议提供不同的示例数据
        if conference.lower() == 'asco':
            return [
                {
                    'conference_name': 'ASCO',
                    'conference_year': 2025,
                    'abstract_number': 'LBA1',
                    'title_en': 'Final Overall Survival Analysis of KEYNOTE-189: Pembrolizumab Plus Chemotherapy vs Chemotherapy Alone for First-Line Treatment of Metastatic NSCLC',
                    'authors': 'Garassino, et al.',
                    'presentation_type': 'Late Breaking Abstract',
                    'session_name': 'Lung Cancer',
                    'tumor_type': 'Non-Small Cell Lung Cancer (NSCLC)',
                    'target_gene': 'PD-L1',
                    'drug_name': 'Pembrolizumab',
                    'study_phase': 'III',
                    'key_findings_en': 'Final OS analysis showed significant improvement in OS for the pembrolizumab plus chemo arm vs chemo alone. Median OS was 22.0 vs 10.7 months (HR: 0.56; p<0.0001).',
                    'url': 'https://ascopubs.org/doi/full/10.1200/JCO.2025.43.17_suppl.lba1'
                },
                {
                    'conference_name': 'ASCO',
                    'conference_year': 2025,
                    'abstract_number': 'LBA2',
                    'title_en': 'Trastuzumab Deruxtecan vs Trastuzumab Emtansine for HER2+ Metastatic Breast Cancer: Updated Results from DESTINY-Breast03',
                    'authors': 'Cortés, et al.',
                    'presentation_type': 'Oral Abstract',
                    'session_name': 'Breast Cancer',
                    'tumor_type': 'Breast Cancer',
                    'target_gene': 'HER2',
                    'drug_name': 'Trastuzumab Deruxtecan',
                    'study_phase': 'III',
                    'key_findings_en': 'Updated PFS and OS confirmed the superiority of T-DXd vs T-DM1 in HER2+ MBC. Median PFS was 28.8 vs 6.8 months (HR: 0.33).',
                    'url': 'https://ascopubs.org/doi/full/10.1200/JCO.2025.43.17_suppl.lba2'
                }
            ]
        elif conference.lower() == 'esmo':
            return [
                {
                    'conference_name': 'ESMO',
                    'conference_year': 2025,
                    'abstract_number': 'LBA1_PR',
                    'title_en': 'Nivolumab Plus Ipilimumab vs Chemotherapy in First-Line Advanced Melanoma: 5-Year Follow-Up of CheckMate 067',
                    'authors': 'Hodi, et al.',
                    'presentation_type': 'Proffered Paper',
                    'session_name': 'Melanoma and Rare Cancers',
                    'tumor_type': 'Melanoma',
                    'target_gene': 'PD-1, CTLA-4',
                    'drug_name': 'Nivolumab, Ipilimumab',
                    'study_phase': 'III',
                    'key_findings_en': '5-year OS rates were 52% for NIVO+IPI vs 44% for NIVO vs 26% for chemo. Long-term benefits maintained across subgroups.',
                    'url': 'https://www.esmo.org/meetings/esmo-congress-2025'
                }
            ]
        elif conference.lower() == 'aacr':
            return [
                {
                    'conference_name': 'AACR',
                    'conference_year': 2025,
                    'abstract_number': 'CT001',
                    'title_en': 'First-in-Human Study of BNT116, an mRNA Cancer Vaccine, in Patients with Advanced Melanoma',
                    'authors': 'Sharma, et al.',
                    'presentation_type': 'Clinical Trial Abstract',
                    'session_name': 'Immunotherapy',
                    'tumor_type': 'Melanoma',
                    'target_gene': 'Multiple Tumor-Associated Antigens',
                    'drug_name': 'BNT116',
                    'study_phase': 'I',
                    'key_findings_en': 'BNT116 demonstrated acceptable safety profile and preliminary evidence of anti-tumor activity in advanced melanoma patients.',
                    'url': 'https://aacrjournals.org'
                }
            ]
        return []

    def _parse_abstract(self, abstract_data: Dict) -> Optional[Dict]:
        """
        解析会议摘要数据

        Args:
            abstract_data: 原始摘要数据

        Returns:
            解析后的标准化摘要数据
        """
        try:
            # 解析肿瘤类型
            tumor_type = abstract_data.get('tumor_type', '')
            tumor_type_cn = ''
            if tumor_type:
                tumor_type_cn = self.translation_service.translate(
                    tumor_type, from_lang='en', to_lang='zh'
                )

            # 解析标题中文翻译
            title_en = abstract_data.get('title_en', '')
            title_cn = ''
            if title_en:
                title_cn = self.translation_service.translate(
                    title_en, from_lang='en', to_lang='zh'
                )

            # 解析关键发现中文翻译
            key_findings_en = abstract_data.get('key_findings_en', '')
            key_findings_cn = ''
            if key_findings_en:
                key_findings_cn = self.translation_service.translate(
                    key_findings_en, from_lang='en', to_lang='zh'
                )

            return {
                'conference_name': abstract_data.get('conference_name', ''),
                'conference_year': abstract_data.get('conference_year', datetime.now().year),
                'abstract_number': abstract_data.get('abstract_number', ''),
                'title_en': title_en,
                'title_cn': title_cn,
                'authors': abstract_data.get('authors', ''),
                'presentation_type': abstract_data.get('presentation_type', ''),
                'session_name': abstract_data.get('session_name', ''),
                'tumor_type': tumor_type,
                'tumor_type_cn': tumor_type_cn,
                'target_gene': abstract_data.get('target_gene', ''),
                'drug_name': abstract_data.get('drug_name', ''),
                'study_phase': abstract_data.get('study_phase', ''),
                'key_findings_en': key_findings_en,
                'key_findings_cn': key_findings_cn,
                'url': abstract_data.get('url', ''),
                'data_collection_time': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            }
        except Exception as e:
            logger.error(f"解析会议摘要失败: {e}")
            self.errors_count += 1
            return None

    def _save_abstract(self, abstract: Dict) -> None:
        """
        保存会议摘要到数据库

        Args:
            abstract: 解析后的会议摘要数据
        """
        try:
            # 检查是否已存在
            existing = self.db_manager.execute_query(
                "SELECT id FROM conference_abstracts WHERE conference_name = ? AND conference_year = ? AND abstract_number = ?",
                (abstract['conference_name'], abstract['conference_year'], abstract['abstract_number'])
            )

            if existing:
                # 更新现有记录
                self.db_manager.execute_update(
                    'conference_abstracts',
                    abstract,
                    'conference_name = ? AND conference_year = ? AND abstract_number = ?',
                    (abstract['conference_name'], abstract['conference_year'], abstract['abstract_number'])
                )
                self.records_updated += 1
            else:
                # 插入新记录
                self.db_manager.execute_insert('conference_abstracts', abstract)
                self.records_added += 1

            self.records_processed += 1
        except Exception as e:
            logger.error(f"保存会议摘要失败: {e}")
            self.errors_count += 1

    def collect_conference(self, conference: str) -> Dict:
        """
        采集单个会议的摘要数据

        Args:
            conference: 会议名称缩写

        Returns:
            采集结果统计
        """
        logger.info(f"开始采集 {conference.upper()} 会议摘要")
        conference_config = self.CONFERENCES.get(conference.lower())
        
        if not conference_config:
            logger.error(f"未支持的会议: {conference}")
            return {'processed': 0, 'added': 0, 'error': 'Unsupported conference'}

        # 获取示例数据（实际项目中这里会调用会议API或爬虫）
        abstracts = self._get_sample_conference_data(conference)

        logger.info(f"获取到 {len(abstracts)} 条摘要数据")

        for abstract_data in abstracts:
            parsed = self._parse_abstract(abstract_data)
            if parsed:
                self._save_abstract(parsed)
            time.sleep(0.2)  # 延迟避免被限制

        logger.info(f"{conference.upper()} 采集完成: 处理 {self.records_processed} 条, 新增 {self.records_added} 条, 更新 {self.records_updated} 条")

        return {
            'processed': self.records_processed,
            'added': self.records_added,
            'updated': self.records_updated,
            'errors': self.errors_count
        }

    def run(self, conference: Optional[str] = None) -> Dict:
        """
        运行采集任务

        Args:
            conference: 指定采集单个会议，None时采集所有支持的会议

        Returns:
            整体采集结果统计
        """
        start_time = datetime.now()

        # 重置统计
        self.records_processed = 0
        self.records_added = 0
        self.records_updated = 0
        self.errors_count = 0

        results = {}

        # 确定要采集的会议列表
        conferences_to_collect = [conference] if conference else list(self.CONFERENCES.keys())

        for conf in conferences_to_collect:
            try:
                result = self.collect_conference(conf)
                results[conf] = result
            except Exception as e:
                logger.error(f"采集 {conf} 会议摘要时出错: {e}")
                results[conf] = {'error': str(e)}
                self.errors_count += 1

        end_time = datetime.now()
        duration = (end_time - start_time).total_seconds()

        logger.info(f"会议摘要采集任务全部完成: 总处理 {self.records_processed} 条, 总新增 {self.records_added} 条, 总耗时 {duration:.1f} 秒")

        log_data = {
            'module_name': 'conference_abstracts',
            'action': 'collect',
            'status': 'success' if self.errors_count == 0 else 'partial',
            'message': f"处理 {self.records_processed} 条, 新增 {self.records_added} 条",
            'records_processed': self.records_processed,
            'records_added': self.records_added,
            'records_updated': self.records_updated,
            'error_count': self.errors_count,
            'start_time': str(start_time),
            'end_time': str(end_time),
            'duration_seconds': duration,
        }
        self.db_manager.log_system_action(log_data)

        return {
            'records_processed': self.records_processed,
            'records_added': self.records_added,
            'records_updated': self.records_updated,
            'errors': self.errors_count,
            'duration': round(duration, 1),
            'results': results
        }


def create_conference_collector(
    db_manager: DatabaseManager,
    config_manager: ConfigManager,
    translation_service: TranslationService
) -> ConferenceAbstractCollector:
    """
    创建会议摘要采集器实例

    Args:
        db_manager: 数据库管理器
        config_manager: 配置管理器
        translation_service: 翻译服务

    Returns:
        会议摘要采集器实例
    """
    proxy_config = config_manager.get_proxy_config()
    request_manager = RequestManager(proxy_config)
    
    return ConferenceAbstractCollector(
        db_manager=db_manager,
        config_manager=config_manager,
        translation_service=translation_service,
        request_manager=request_manager
    )
