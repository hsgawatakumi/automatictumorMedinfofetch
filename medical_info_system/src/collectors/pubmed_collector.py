"""
PubMed学术文献检索模块
使用PubMed E-utilities API检索抗肿瘤药物相关学术文献
"""

import os
import sys
import time
import logging
import requests
from datetime import datetime, timedelta
from typing import Dict, List, Optional
import xml.etree.ElementTree as ET

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from src.database import DatabaseManager
from src.utils.config_manager import ConfigManager
from src.utils.translator import TranslationService

logger = logging.getLogger(__name__)


class PubMedCollector:
    """PubMed文献采集类"""
    
    def __init__(
        self,
        db_manager: DatabaseManager,
        config_manager: ConfigManager,
        translation_service: TranslationService
    ):
        """初始化PubMed采集器"""
        self.db_manager = db_manager
        self.config_manager = config_manager
        self.translation_service = translation_service
        
        # PubMed API配置
        self.base_url = config_manager.get('pubmed.base_url', 'https://eutils.ncbi.nlm.nih.gov/entrez/eutils')
        self.api_key = config_manager.get('pubmed.api_key', '')
        self.max_results = config_manager.get('pubmed.max_results_per_query', 100)
        self.request_delay = config_manager.get('pubmed.request_delay', 0.5)
        
        # 目标期刊列表
        self.target_journals = [
            'New England Journal of Medicine',
            'The Lancet',
            'Nature Medicine',
            'Cancer Discovery',
            'The Lancet Oncology',
            'Annals of Oncology',
            'Journal of Clinical Oncology',
            'Clinical Cancer Research',
            'JCO Precision Oncology',
            'npj Precision Oncology',
            'Journal of Thoracic Oncology',
            'Molecular Cancer',
            'European Journal of Cancer'
        ]
        
        # 统计
        self.records_processed = 0
        self.records_added = 0
        self.errors_count = 0
        
        logger.info("PubMed采集器初始化完成")
    
    def build_search_query(
        self,
        genes: List[str] = None,
        tumor_types: List[Dict] = None,
        date_range: tuple = None
    ) -> str:
        """
        构建PubMed检索式
        
        Args:
            genes: 基因列表
            tumor_types: 肿瘤类型列表（中英文对照）
            date_range: 日期范围
            
        Returns:
            PubMed检索式
        """
        # 使用配置中的基因和肿瘤类型
        if genes is None:
            genes = self.config_manager.get_target_genes()[:20]
        
        if tumor_types is None:
            tumor_types = self.config_manager.get_tumor_types()[:30]
        
        # 构建基因部分
        gene_terms = ' OR '.join([f'"{g}"[Gene]' for g in genes[:15]])
        
        # 构建肿瘤类型部分（中英文双语检索）
        tumor_terms = []
        for tumor in tumor_types[:20]:
            # 添加英文名称
            en_name = tumor.get('en', '')
            if en_name:
                tumor_terms.append(f'"{en_name}"[Title/Abstract]')
            
            # 添加英文别名
            aliases = tumor.get('aliases_en', [])
            for alias in aliases[:2]:
                tumor_terms.append(f'"{alias}"[Title/Abstract]')
        
        tumor_query = ' OR '.join(tumor_terms)
        
        # 构建治疗类型部分
        treatment_terms = [
            '"targeted therapy"[Title/Abstract]',
            '"immunotherapy"[Title/Abstract]',
            '"drug treatment"[Title/Abstract]',
            '"chemotherapy"[Title/Abstract]',
            '"antineoplastic"[Title/Abstract]',
            '"clinical trial"[Title/Abstract]',
            '"therapeutic"[Title/Abstract]'
        ]
        treatment_query = ' OR '.join(treatment_terms)
        
        # 构建期刊限制
        journal_terms = []
        for journal in self.target_journals[:10]:
            journal_terms.append(f'"{journal}"[Journal]')
        journal_query = ' OR '.join(journal_terms)
        
        # 组合检索式
        query = f"(({gene_terms}) OR ({tumor_query})) AND ({treatment_query}) AND ({journal_query})"
        
        # 添加日期范围
        if date_range:
            start_date, end_date = date_range
            query += f' AND ("{start_date}"[Date - Publication] : "{end_date}"[Date - Publication])'
        
        return query
    
    def search_pubmed(self, query: str, retmax: int = 100) -> List[str]:
        """
        搜索PubMed获取PMID列表
        
        Args:
            query: 检索式
            retmax: 最大返回数量
            
        Returns:
            PMID列表
        """
        try:
            # ESearch请求
            url = f"{self.base_url}/esearch.fcgi"
            
            params = {
                'db': 'pubmed',
                'term': query,
                'retmax': retmax,
                'retmode': 'json',
                'usehistory': 'y'
            }
            
            if self.api_key:
                params['api_key'] = self.api_key
            
            response = requests.get(url, params=params, timeout=30)
            response.raise_for_status()
            
            data = response.json()
            
            pmids = data.get('esearchresult', {}).get('idlist', [])
            
            logger.info(f"PubMed搜索成功: {len(pmids)} 条结果")
            
            # 添加延迟
            time.sleep(self.request_delay)
            
            return pmids
            
        except Exception as e:
            logger.error(f"PubMed搜索失败: {e}")
            self.errors_count += 1
            return []
    
    def fetch_pubmed_details(self, pmids: List[str]) -> List[Dict]:
        """
        获取PubMed文献详细信息
        
        Args:
            pmids: PMID列表
            
        Returns:
            文献详情列表
        """
        if not pmids:
            return []
        
        try:
            # EFetch请求
            url = f"{self.base_url}/efetch.fcgi"
            
            params = {
                'db': 'pubmed',
                'id': ','.join(pmids),
                'retmode': 'xml',
                'rettype': 'abstract'
            }
            
            if self.api_key:
                params['api_key'] = self.api_key
            
            response = requests.get(url, params=params, timeout=60)
            response.raise_for_status()
            
            # 解析XML
            root = ET.fromstring(response.content)
            
            articles = []
            for article_elem in root.findall('.//PubmedArticle'):
                article = self._parse_article_xml(article_elem)
                if article:
                    articles.append(article)
            
            logger.info(f"获取文献详情成功: {len(articles)} 条")
            
            time.sleep(self.request_delay)
            
            return articles
            
        except Exception as e:
            logger.error(f"获取文献详情失败: {e}")
            self.errors_count += 1
            return []
    
    def _parse_article_xml(self, article_elem) -> Optional[Dict]:
        """解析单篇文献XML"""
        try:
            # 提取PMID
            pmid = article_elem.find('.//PMID').text if article_elem.find('.//PMID') is not None else ''
            
            # 提取标题
            title_elem = article_elem.find('.//ArticleTitle')
            title_en = title_elem.text if title_elem is not None else ''
            
            # 提取作者
            authors = []
            for author_elem in article_elem.findall('.//Author'):
                last_name = author_elem.find('LastName')
                fore_name = author_elem.find('ForeName')
                if last_name is not None and fore_name is not None:
                    authors.append(f"{last_name.text} {fore_name.text}")
            
            # 提取期刊
            journal_elem = article_elem.find('.//Journal/Title')
            journal_name = journal_elem.text if journal_elem is not None else ''
            
            # 提取发表日期
            pub_date = ''
            year_elem = article_elem.find('.//PubDate/Year')
            month_elem = article_elem.find('.//PubDate/Month')
            day_elem = article_elem.find('.//PubDate/Day')
            
            if year_elem is not None:
                pub_date = year_elem.text
                if month_elem is not None:
                    pub_date += f"-{month_elem.text}"
                if day_elem is not None:
                    pub_date += f"-{day_elem.text}"
            
            # 提取DOI
            doi = ''
            for eloc in article_elem.findall('.//ELocationID'):
                if eloc.attrib.get('EIdType') == 'doi':
                    doi = eloc.text
            
            # 提取摘要
            abstract_en = ''
            abstract_elem = article_elem.find('.//Abstract/AbstractText')
            if abstract_elem is not None:
                abstract_en = abstract_elem.text or ''
            
            # 提取关键词
            keywords = []
            for keyword_elem in article_elem.findall('.//Keyword'):
                if keyword_elem.text:
                    keywords.append(keyword_elem.text)
            
            # 构建文献数据
            article_data = {
                'pmid': pmid,
                'title_en': title_en,
                'title_cn': '',
                'authors': ', '.join(authors[:10]),
                'journal_name': journal_name,
                'publication_date': pub_date,
                'doi': doi,
                'abstract_en': abstract_en[:2000] if abstract_en else '',
                'abstract_cn': '',
                'target_gene': '',
                'tumor_type': '',
                'tumor_type_cn': '',
                'drug_name': '',
                'study_type': '',
                'key_findings': '',
                'url': f'https://pubmed.ncbi.nlm.nih.gov/{pmid}/',
                'data_collection_time': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            }
            
            return article_data
            
        except Exception as e:
            logger.warning(f"解析文献XML失败: {e}")
            return None
    
    def annotate_article(self, article: Dict) -> Dict:
        """
        标注文献的目标基因、肿瘤类型和药物
        
        Args:
            article: 文献数据
            
        Returns:
            标注后的文献数据
        """
        # 获取基因和肿瘤类型列表
        genes = self.config_manager.get_target_genes()
        tumor_types = self.config_manager.get_tumor_types()
        
        # 搜索标题和摘要中的基因
        text = f"{article.get('title_en', '')} {article.get('abstract_en', '')}"
        
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
            
            # 搜索别名
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
        # 翻译标题
        if article.get('title_en'):
            article['title_cn'] = self.translation_service.translate(article['title_en'])
        
        # 翻译摘要（截取前500字符）
        if article.get('abstract_en'):
            abstract = article['abstract_en'][:500]
            article['abstract_cn'] = self.translation_service.translate(abstract)
        
        return article
    
    def save_to_database(self, article: Dict) -> bool:
        """保存文献到数据库"""
        try:
            # 检查是否已存在
            existing = self.db_manager.execute_query(
                "SELECT id FROM academic_papers WHERE pmid = ? OR doi = ?",
                (article.get('pmid', ''), article.get('doi', ''))
            )
            
            if existing:
                # 更新
                self.db_manager.execute_update(
                    'academic_papers',
                    article,
                    "id = ?",
                    (existing[0]['id'],)
                )
                logger.debug(f"更新文献: {article.get('pmid')}")
            else:
                # 插入
                self.db_manager.execute_insert('academic_papers', article)
                self.records_added += 1
                logger.debug(f"添加文献: {article.get('pmid')}")
            
            self.records_processed += 1
            return True
            
        except Exception as e:
            logger.error(f"保存文献失败: {e}")
            self.errors_count += 1
            return False
    
    def collect_weekly(self) -> Dict:
        """每周文献采集"""
        logger.info("开始PubMed每周文献采集")
        
        start_time = datetime.now()
        
        # 重置统计
        self.records_processed = 0
        self.records_added = 0
        self.errors_count = 0
        
        # 构建日期范围（上周）
        today = datetime.now()
        week_start = today - timedelta(days=7)
        date_range = (
            week_start.strftime('%Y/%m/%d'),
            today.strftime('%Y/%m/%d')
        )
        
        # 构建检索式
        query = self.build_search_query(date_range=date_range)
        
        logger.info(f"检索式: {query[:200]}...")
        
        # 搜索PubMed
        pmids = self.search_pubmed(query, retmax=self.max_results)
        
        if not pmids:
            logger.info("无新文献")
            return {'status': 'success', 'records_added': 0}
        
        # 获取文献详情
        articles = self.fetch_pubmed_details(pmids)
        
        # 处理每篇文献
        for article in articles:
            # 标注
            article = self.annotate_article(article)
            
            # 翻译
            article = self.translate_article(article)
            
            # 保存
            self.save_to_database(article)
            
            time.sleep(0.3)
        
        end_time = datetime.now()
        duration = (end_time - start_time).total_seconds()
        
        # 记录日志
        self.db_manager.execute_insert('system_logs', {
            'module_name': 'academic_papers',
            'action': 'weekly_collection',
            'status': 'success',
            'message': 'PubMed每周文献采集完成',
            'records_processed': self.records_processed,
            'records_added': self.records_added,
            'error_count': self.errors_count,
            'start_time': start_time.strftime('%Y-%m-%d %H:%M:%S'),
            'end_time': end_time.strftime('%Y-%m-%d %H:%M:%S'),
            'duration_seconds': duration
        })
        
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
    
    config_path = "config/config.yaml"
    db_path = "data/medical_info.db"
    
    config_manager = ConfigManager(config_path)
    db_manager = DatabaseManager(db_path)
    db_manager.init_tables()
    
    translation_config = config_manager.get_translation_config()
    translation_service = TranslationService(translation_config)
    
    collector = PubMedCollector(db_manager, config_manager, translation_service)
    
    # 测试搜索
    query = collector.build_search_query()
    print(f"检索式: {query[:300]}...")
    
    pmids = collector.search_pubmed(query, retmax=10)
    print(f"找到 {len(pmids)} 条PMID")
    
    if pmids:
        articles = collector.fetch_pubmed_details(pmids[:5])
        for article in articles:
            print(f"\n标题: {article.get('title_en', '')[:100]}")
            print(f"期刊: {article.get('journal_name')}")
            print(f"PMID: {article.get('pmid')}")
    
    db_manager.close()