"""
CrossRef学术文献检索模块
使用CrossRef API检索抗肿瘤药物相关学术文献
"""

import os
import sys
import time
import logging
import requests
from datetime import datetime, timedelta
from typing import Dict, List, Optional

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from src.database import DatabaseManager
from src.utils.config_manager import ConfigManager
from src.utils.translator import TranslationService

logger = logging.getLogger(__name__)


class CrossRefCollector:
    """CrossRef文献采集类"""

    def __init__(
        self,
        db_manager: DatabaseManager,
        config_manager: ConfigManager,
        translation_service: TranslationService
    ):
        """初始化CrossRef采集器"""
        self.db_manager = db_manager
        self.config_manager = config_manager
        self.translation_service = translation_service

        # CrossRef API配置
        self.base_url = 'https://api.crossref.org'
        self.mailto = config_manager.get('crossref.mailto', 'research@example.com')
        self.user_agent = config_manager.get('crossref.user_agent', 'MedicalInfoCollector/1.0')
        self.max_results = config_manager.get('crossref.max_results', 100)
        self.request_delay = config_manager.get('crossref.request_delay', 1.0)

        # 目标期刊ISSN
        self.target_journals = {
            'New England Journal of Medicine': '0028-4793',
            'The Lancet': '0140-6736',
            'Nature Medicine': '1078-8956',
            'Cancer Discovery': '2159-8274',
            'The Lancet Oncology': '1470-2045',
            'Annals of Oncology': '0923-7534',
            'Journal of Clinical Oncology': '0732-183X',
            'Clinical Cancer Research': '1078-0432',
            'JCO Precision Oncology': '2473-4276',
            'npj Precision Oncology': '2397-768X',
            'Journal of Thoracic Oncology': '1556-0864',
            'Molecular Cancer': '1476-4598',
            'European Journal of Cancer': '0959-8049',
        }

        # 统计
        self.records_processed = 0
        self.records_added = 0
        self.errors_count = 0

        logger.info("CrossRef采集器初始化完成")

    def build_search_query(
        self,
        genes: List[str] = None,
        tumor_types: List[Dict] = None
    ) -> str:
        """
        构建CrossRef检索式

        Args:
            genes: 基因列表
            tumor_types: 肿瘤类型列表

        Returns:
            CrossRef检索式
        """
        if genes is None:
            genes = self.config_manager.get_target_genes()[:20]

        if tumor_types is None:
            tumor_types = self.config_manager.get_tumor_types()[:20]

        query_parts = []

        # 添加基因
        gene_terms = []
        for gene in genes[:15]:
            gene_terms.append(gene)
        if gene_terms:
            query_parts.append(' OR '.join(gene_terms))

        # 添加肿瘤类型
        tumor_terms = []
        for tumor in tumor_types[:15]:
            en_name = tumor.get('en', '')
            if en_name:
                tumor_terms.append(en_name)
        if tumor_terms:
            query_parts.append(' OR '.join(tumor_terms))

        # 添加治疗相关关键词
        treatment_terms = [
            'targeted therapy', 'immunotherapy', 'drug treatment',
            'chemotherapy', 'anticancer', 'antitumor', 'oncology'
        ]
        query_parts.append(' OR '.join(treatment_terms))

        return ' AND '.join(query_parts)

    def search_works(self, query: str, rows: int = 100, filter_params: dict = None) -> Optional[Dict]:
        """
        搜索CrossRef文献

        Args:
            query: 检索式
            rows: 返回数量
            filter_params: 过滤参数

        Returns:
            API响应数据
        """
        try:
            url = f"{self.base_url}/works"

            headers = {
                'User-Agent': f'{self.user_agent} (mailto:{self.mailto})'
            }

            params = {
                'query': query,
                'rows': rows,
                'select': 'DOI,title,author,published-print,published-online,container-title,journal,abstract,subject,type',
            }

            if filter_params:
                params.update(filter_params)

            response = requests.get(url, headers=headers, params=params, timeout=60)
            response.raise_for_status()

            data = response.json()

            logger.info(f"CrossRef搜索成功: {data.get('message', {}).get('total-results', 0)} 条结果")

            time.sleep(self.request_delay)

            return data

        except Exception as e:
            logger.error(f"CrossRef搜索失败: {e}")
            self.errors_count += 1
            return None

    def fetch_journal_works(self, issn: str, from_date: str = None, rows: int = 100) -> Optional[Dict]:
        """
        获取特定期刊的文献

        Args:
            issn: 期刊ISSN
            from_date: 开始日期 (YYYY-MM-DD)
            rows: 返回数量

        Returns:
            API响应数据
        """
        try:
            url = f"{self.base_url}/journals/{issn}/works"

            headers = {
                'User-Agent': f'{self.user_agent} (mailto:{self.mailto})'
            }

            params = {
                'rows': rows,
                'select': 'DOI,title,author,published-print,published-online,container-title,abstract,subject,type',
            }

            if from_date:
                params['filter'] = f'from-pub-date:{from_date}'

            response = requests.get(url, headers=headers, params=params, timeout=60)
            response.raise_for_status()

            data = response.json()

            logger.info(f"期刊 {issn} 搜索成功")

            time.sleep(self.request_delay)

            return data

        except Exception as e:
            logger.error(f"期刊 {issn} 搜索失败: {e}")
            self.errors_count += 1
            return None

    def parse_article(self, article: Dict) -> Optional[Dict]:
        """解析单篇文献"""
        try:
            msg = article.get('message', {})

            # DOI
            doi = msg.get('DOI', '')

            # 标题
            titles = msg.get('title', [])
            title_en = titles[0] if titles else ''

            # 作者
            authors = []
            for author in msg.get('author', []):
                given = author.get('given', '')
                family = author.get('family', '')
                if given and family:
                    authors.append(f"{family}, {given}")
                elif family:
                    authors.append(family)
            authors_str = ', '.join(authors[:10])

            # 发表日期
            published = msg.get('published-print') or msg.get('published-online') or {}
            date_parts = published.get('date-parts', [[]])[0]
            pub_date = ''
            if len(date_parts) >= 3:
                pub_date = f"{date_parts[0]}-{date_parts[1]:02d}-{date_parts[2]:02d}"
            elif len(date_parts) >= 2:
                pub_date = f"{date_parts[0]}-{date_parts[1]:02d}"

            # 期刊
            container_titles = msg.get('container-title', [])
            journal_name = container_titles[0] if container_titles else ''

            # 摘要
            abstract_en = msg.get('abstract', '')
            if abstract_en:
                abstract_en = abstract_en.replace('<jats:p>', '').replace('</jats:p>', '').replace('<jats:sec>', '').replace('</jats:sec>', '')
                abstract_en = abstract_en.strip()

            # URL
            url = f"https://doi.org/{doi}" if doi else ''

            # 构建文献数据
            article_data = {
                'doi': doi,
                'title_en': title_en,
                'title_cn': '',
                'authors': authors_str,
                'journal_name': journal_name,
                'publication_date': pub_date,
                'pmid': '',
                'abstract_en': abstract_en[:2000] if abstract_en else '',
                'abstract_cn': '',
                'target_gene': '',
                'tumor_type': '',
                'tumor_type_cn': '',
                'drug_name': '',
                'study_type': '',
                'key_findings': '',
                'url': url,
                'data_collection_time': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                'source': 'CrossRef'
            }

            return article_data

        except Exception as e:
            logger.warning(f"解析文献失败: {e}")
            return None

    def annotate_article(self, article: Dict) -> Dict:
        """标注文献的目标基因、肿瘤类型和药物"""
        genes = self.config_manager.get_target_genes()
        tumor_types = self.config_manager.get_tumor_types()

        text = f"{article.get('title_en', '')} {article.get('abstract_en', '')}"

        # 搜索基因
        found_genes = []
        for gene in genes:
            if gene.upper() in text.upper():
                found_genes.append(gene)
        article['target_gene'] = ', '.join(found_genes[:5])

        # 搜索肿瘤类型
        found_tumors = []
        found_tumors_cn = []
        for tumor in tumor_types:
            en_name = tumor.get('en', '')
            cn_name = tumor.get('cn', '')

            if en_name and en_name.lower() in text.lower():
                found_tumors.append(en_name)
                found_tumors_cn.append(cn_name)

            aliases = tumor.get('aliases_en', [])
            for alias in aliases:
                if alias.lower() in text.lower():
                    if en_name not in found_tumors:
                        found_tumors.append(en_name)
                        found_tumors_cn.append(cn_name)
                    break

        article['tumor_type'] = ', '.join(found_tumors[:3])
        article['tumor_type_cn'] = ', '.join(found_tumors_cn[:3])

        return article

    def translate_article(self, article: Dict) -> Dict:
        """翻译文献标题和摘要"""
        try:
            if article.get('title_en'):
                article['title_cn'] = self.translation_service.translate(article['title_en'])

            if article.get('abstract_en'):
                abstract = article['abstract_en'][:500]
                article['abstract_cn'] = self.translation_service.translate(abstract)
        except Exception as e:
            logger.warning(f"翻译失败: {e}")

        return article

    def save_to_database(self, article: Dict) -> bool:
        """保存文献到数据库"""
        try:
            existing = self.db_manager.execute_query(
                "SELECT id FROM academic_papers WHERE doi = ?",
                (article.get('doi', ''),)
            )

            if existing:
                self.db_manager.execute_update(
                    'academic_papers',
                    article,
                    "id = ?",
                    (existing[0]['id'],)
                )
                logger.debug(f"更新文献: {article.get('doi')}")
            else:
                self.db_manager.execute_insert('academic_papers', article)
                self.records_added += 1
                logger.debug(f"添加文献: {article.get('doi')}")

            self.records_processed += 1
            return True

        except Exception as e:
            logger.error(f"保存文献失败: {e}")
            self.errors_count += 1
            return False

    def collect_weekly(self) -> Dict:
        """采集上周发表的文献"""
        logger.info("开始CrossRef每周文献采集")

        start_time = datetime.now()

        # 重置统计
        self.records_processed = 0
        self.records_added = 0
        self.errors_count = 0

        # 计算上周日期范围
        today = datetime.now()
        week_start = today - timedelta(days=7)
        from_date = week_start.strftime('%Y-%m-%d')

        logger.info(f"检索日期范围: {from_date} 至今")

        total_collected = 0

        # 遍历目标期刊
        for journal_name, issn in self.target_journals.items():
            try:
                logger.info(f"检索期刊: {journal_name} ({issn})")

                data = self.fetch_journal_works(issn, from_date=from_date, rows=self.max_results)

                if not data or 'message' not in data:
                    continue

                items = data.get('message', {}).get('items', [])
                logger.info(f"  获取到 {len(items)} 条文献")

                for item in items:
                    article = self.parse_article(item)
                    if not article:
                        continue

                    article = self.annotate_article(article)
                    article = self.translate_article(article)
                    self.save_to_database(article)
                    total_collected += 1

                time.sleep(self.request_delay)

            except Exception as e:
                logger.error(f"  期刊 {journal_name} 采集失败: {e}")
                continue

        end_time = datetime.now()
        duration = (end_time - start_time).total_seconds()

        logger.info(f"CrossRef采集完成: 处理 {self.records_processed} 条, 新增 {self.records_added} 条, 耗时 {duration:.1f}秒")

        return {
            'status': 'success',
            'records_processed': self.records_processed,
            'records_added': self.records_added,
            'errors_count': self.errors_count,
            'duration_seconds': duration
        }

    def run(self) -> Dict:
        """运行采集"""
        return self.collect_weekly()


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)

    base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    db_path = os.path.join(base_dir, 'data', 'medical_info.db')
    config_path = os.path.join(base_dir, 'config', 'config.yaml')

    config_manager = ConfigManager(config_path)
    db_manager = DatabaseManager(db_path)
    db_manager.init_tables()

    translation_service = TranslationService(config_manager)

    collector = CrossRefCollector(db_manager, config_manager, translation_service)

    result = collector.run()

    logger.info(f"采集结果: {result}")
