#!/usr/bin/env python3
"""
ChiCTR临床试验采集器 - 高级搜索版本
使用POST请求进行高级搜索，支持基因、研究类型和招募状态的筛选
"""
import os
import sys
import time
import logging
import requests
from datetime import datetime
from typing import Dict, List, Optional
from bs4 import BeautifulSoup

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from src.database import init_database
from src.utils.config_manager import ConfigManager
from src.utils.translator import TranslationService

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class ChiCTRAdvancedCollector:
    """ChiCTR高级搜索采集器"""
    
    def __init__(self, db_manager, config_manager, translation_service):
        self.db_manager = db_manager
        self.config_manager = config_manager
        self.translation_service = translation_service
        self.base_url = 'https://www.chictr.org.cn'
        self.search_url = f'{self.base_url}/searchproj.html'
        
        # 获取基因和肿瘤类型列表
        self.genes = config_manager.get_target_genes()
        
        # 统计信息
        self.total_trials = 0
        self.new_trials = 0
        self.errors = 0
    
    def _get_session(self):
        """创建会话"""
        session = requests.Session()
        session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
            'Referer': self.base_url,
            'Origin': self.base_url
        })
        return session
    
    def _extract_genes(self, text: str) -> str:
        """提取基因标记"""
        found = []
        text_upper = text.upper()
        
        # 首先检查完整基因名称
        for gene in self.genes:
            if gene.upper() in text_upper:
                found.append(gene)
        
        # 检查常见别名
        alias_map = {
            'PDCD1': ['PD-1', 'PD 1', 'PD1'],
            'CD274': ['PD-L1', 'PD L1', 'PDL1'],
            'EGFR': ['EGFR'],
            'ALK': ['ALK'],
            'BRAF': ['BRAF'],
            'KRAS': ['KRAS'],
            'ERBB2': ['HER2', 'HER-2', 'HER 2'],
            'MET': ['MET'],
            'RET': ['RET'],
            'PIK3CA': ['PI3K', 'PI 3K'],
            'MTOR': ['mTOR'],
            'FGFR1': ['FGFR'],
            'FGFR2': ['FGFR'],
            'FGFR3': ['FGFR'],
            'FGFR4': ['FGFR'],
            'PTEN': ['PTEN'],
            'RB1': ['RB1'],
            'TP53': ['TP53', 'P53', 'p53']
        }
        
        for gene, aliases in alias_map.items():
            if gene not in found:
                for alias in aliases:
                    if alias.upper() in text_upper:
                        found.append(gene)
                        break
        
        return ', '.join(found[:5])
    
    def _search_by_gene(self, gene: str, session, max_pages: int = 5) -> List[Dict]:
        """
        使用高级搜索按基因搜索临床试验
        POST请求，包含注册题目、研究类型和招募状态
        """
        trials = []
        
        for page in range(1, max_pages + 1):
            try:
                logger.info(f"搜索基因 '{gene}' 第 {page} 页...")
                
                # POST表单数据
                # 注册题目=基因
                # 研究类型=干预性研究
                # 征募状态=正在进行/尚未开始
                data = {
                    'regname': gene,  # 注册题目
                    'studytpe': '干预性研究',  # 研究类型
                    'recruit': '正在招募,尚未开始',  # 征募状态
                    'page': page
                }
                
                response = session.post(self.search_url, data=data, timeout=30)
                response.raise_for_status()
                
                soup = BeautifulSoup(response.content, 'lxml')
                
                # 查找结果表格
                table = soup.find('table')
                if not table:
                    logger.warning(f"未找到结果表格")
                    break
                
                rows = table.find_all('tr')
                if len(rows) <= 1:
                    logger.info(f"第 {page} 页无数据")
                    break
                
                # 解析每一行
                for row in rows[1:]:
                    cells = row.find_all('td')
                    if len(cells) < 4:
                        continue
                    
                    trial_info = self._parse_trial_row(cells)
                    if trial_info and trial_info not in trials:
                        trials.append(trial_info)
                
                time.sleep(2)  # 避免请求过快
                
            except Exception as e:
                logger.error(f"搜索基因 '{gene}' 第 {page} 页失败: {e}")
                self.errors += 1
                continue
        
        return trials
    
    def _parse_trial_row(self, cells) -> Optional[Dict]:
        """解析试验行"""
        try:
            # 注册号
            reg_num_tag = cells[0].find('a')
            reg_num = reg_num_tag.get_text(strip=True) if reg_num_tag else ''
            
            # 标题和链接
            title_tag = cells[1].find('a') if len(cells) > 1 else None
            title = title_tag.get_text(strip=True) if title_tag else ''
            detail_url = ''
            if title_tag:
                href = title_tag.get('href', '')
                if href:
                    if not href.startswith('http'):
                        detail_url = f"{self.base_url}/{href}"
                    else:
                        detail_url = href
            
            # 研究类型
            study_type = cells[2].get_text(strip=True) if len(cells) > 2 else ''
            
            # 注册时间
            reg_date = cells[3].get_text(strip=True) if len(cells) > 3 else ''
            
            return {
                'reg_num': reg_num,
                'title': title,
                'detail_url': detail_url,
                'study_type': study_type,
                'reg_date': reg_date
            }
        except Exception as e:
            logger.debug(f"解析行失败: {e}")
            return None
    
    def _fetch_trial_detail(self, detail_url: str, trial_info: Dict, session) -> Optional[Dict]:
        """获取试验详情"""
        try:
            logger.info(f"获取试验详情: {trial_info['reg_num']}")
            
            response = session.get(detail_url, timeout=30)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.content, 'lxml')
            
            # 提取详情
            detail = self._extract_detail_info(soup, trial_info)
            
            return detail
            
        except Exception as e:
            logger.error(f"获取试验详情失败: {e}")
            self.errors += 1
            return None
    
    def _extract_detail_info(self, soup, trial_info: Dict) -> Dict:
        """提取试验详情"""
        info = {}
        
        # 查找所有表格
        tables = soup.find_all('table')
        
        for table in tables:
            rows = table.find_all('tr')
            for row in rows:
                cells = row.find_all(['th', 'td'])
                if len(cells) >= 2:
                    key = cells[0].get_text(strip=True)
                    value = cells[1].get_text(strip=True)
                    
                    # 提取关键信息
                    if '注册题目' in key or '试验名称' in key:
                        info['study_title_cn'] = value
                    elif 'Public title' in key:
                        info['study_title_en'] = value
                    elif '研究疾病' in key or 'Target disease' in key:
                        info['conditions'] = value
                        info['tumor_type'] = value
                        info['tumor_type_cn'] = value
                    elif '研究类型' in key or 'Study type' in key:
                        info['study_type'] = value
                    elif '研究所处阶段' in key or 'Study phase' in key:
                        info['phase'] = value
                    elif '干预措施' in key or 'Interventions' in key:
                        info['intervention_drug'] = value
                    elif '征募' in key or 'Recruiting' in key:
                        info['trial_status'] = value
                    elif '实施负责单位' in key:
                        info['study_location'] = value
        
        # 合并信息
        if not info.get('study_title_cn'):
            info['study_title_cn'] = trial_info['title']
        
        # 翻译英文标题
        try:
            if info.get('study_title_cn'):
                info['study_title_en'] = self.translation_service.translate(info['study_title_cn'])
        except:
            pass
        
        # 提取基因标记
        info['gene_marker'] = self._extract_genes(
            str(info.get('study_title_cn', '')) + 
            str(info.get('conditions', '')) + 
            str(info.get('intervention_drug', ''))
        )
        
        # 构建最终数据结构
        trial_data = {
            'platform': 'ChiCTR',
            'trial_id': trial_info['reg_num'],
            'study_title_cn': info.get('study_title_cn', ''),
            'study_title_en': info.get('study_title_en', ''),
            'trial_status': info.get('trial_status', trial_info['study_type']),
            'phase': info.get('phase', ''),
            'study_type': info.get('study_type', trial_info['study_type']),
            'conditions': info.get('conditions', ''),
            'tumor_type': info.get('tumor_type', ''),
            'tumor_type_cn': info.get('tumor_type_cn', ''),
            'intervention_drug': info.get('intervention_drug', ''),
            'gene_marker': info.get('gene_marker', ''),
            'study_location': info.get('study_location', ''),
            'enrollment': 0,
            'url': trial_info['detail_url'],
            'data_collection_time': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        }
        
        return trial_data
    
    def _save_trial(self, trial: Dict) -> bool:
        """保存试验到数据库"""
        try:
            existing = self.db_manager.execute_query(
                "SELECT id FROM clinical_trials WHERE platform = ? AND trial_id = ?",
                (trial['platform'], trial['trial_id'])
            )
            
            if existing:
                self.db_manager.execute_update(
                    'clinical_trials',
                    trial,
                    "id = ?",
                    (existing[0]['id'],)
                )
            else:
                self.db_manager.execute_insert('clinical_trials', trial)
                self.new_trials += 1
            
            self.total_trials += 1
            return True
            
        except Exception as e:
            logger.error(f"保存试验失败: {e}")
            self.errors += 1
            return False
    
    def collect(self, max_pages_per_gene: int = 5, max_detail_fetch: int = 30):
        """
        执行采集
        注意：需要逐个基因进行搜索，确保每个基因的搜索完成后才开始下一个基因
        """
        logger.info("="*80)
        logger.info("开始ChiCTR临床试验采集（高级搜索版）")
        logger.info("="*80)
        
        # 重要：选择常用基因进行搜索（避免搜索过多）
        # 由于需要逐个基因搜索，选择最重要的基因
        important_genes = [
            'EGFR', 'ALK', 'KRAS', 'BRAF', 'PD-1', 'PD-L1', 'HER2', 
            'MET', 'RET', 'FGFR', 'NTRK', 'BRCA', 'PARP', 'CDK', 'PI3K'
        ]
        
        # 筛选在基因列表中的基因
        search_genes = []
        for gene in important_genes:
            if gene in self.genes or gene.upper() in [g.upper() for g in self.genes]:
                search_genes.append(gene)
        
        logger.info(f"需要搜索的基因数量: {len(search_genes)}")
        logger.info(f"基因列表: {', '.join(search_genes)}")
        
        session = self._get_session()
        
        # 先访问首页获取cookie
        try:
            session.get(self.search_url, timeout=30)
            time.sleep(2)
        except Exception as e:
            logger.warning(f"访问首页失败: {e}")
        
        all_trials = []
        
        # 重要：逐个基因进行搜索
        for i, gene in enumerate(search_genes):
            logger.info(f"[{i+1}/{len(search_genes)}] 正在搜索基因: {gene}")
            
            gene_trials = self._search_by_gene(gene, session, max_pages_per_gene)
            
            logger.info(f"基因 '{gene}' 获取到 {len(gene_trials)} 条试验")
            
            # 去重并添加到总列表
            for trial in gene_trials:
                if trial not in all_trials:
                    all_trials.append(trial)
            
            # 重要：每个基因搜索完成后等待一段时间
            time.sleep(3)
        
        logger.info(f"总共获取 {len(all_trials)} 个试验")
        
        # 获取每个试验的详情
        detail_count = 0
        for trial_info in all_trials:
            if detail_count >= max_detail_fetch:
                break
            
            if trial_info['detail_url']:
                detail = self._fetch_trial_detail(trial_info['detail_url'], trial_info, session)
                if detail:
                    self._save_trial(detail)
                    detail_count += 1
                    time.sleep(1)
        
        logger.info("="*80)
        logger.info("采集完成")
        logger.info(f"处理试验数: {self.total_trials}")
        logger.info(f"新增试验数: {self.new_trials}")
        logger.info(f"错误数: {self.errors}")
        logger.info("="*80)
        
        return {
            'total': self.total_trials,
            'new': self.new_trials,
            'errors': self.errors
        }


def main():
    logger.info("="*80)
    logger.info("ChiCTR临床试验采集器 - 高级搜索版")
    logger.info("="*80)
    
    # 初始化组件
    base_path = os.path.dirname(os.path.abspath(__file__))
    config_path = os.path.join(base_path, 'config', 'config.yaml')
    db_path = os.path.join(base_path, 'data', 'medical_info.db')
    
    config_manager = ConfigManager(config_path)
    db_manager = init_database(db_path)
    translation_config = config_manager.get_translation_config()
    translation_service = TranslationService(translation_config)
    
    # 创建采集器
    collector = ChiCTRAdvancedCollector(db_manager, config_manager, translation_service)
    
    # 执行采集（每个基因最多5页，最多获取30个详情）
    result = collector.collect(max_pages_per_gene=5, max_detail_fetch=30)
    
    logger.info(f"采集结果: {result}")
    
    db_manager.close()


if __name__ == "__main__":
    main()
