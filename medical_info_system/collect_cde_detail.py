#!/usr/bin/env python3
"""
CDE临床试验信息采集器
使用正确的高级搜索URL，获取试验详情页的完整信息
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


class CDETrialCollector:
    """CDE临床试验采集器"""
    
    def __init__(self, db_manager, config_manager, translation_service):
        self.db_manager = db_manager
        self.config_manager = config_manager
        self.translation_service = translation_service
        self.base_url = 'https://www.chinadrugtrials.org.cn'
        self.search_url = f'{self.base_url}/clinicaltrials.prosearch.dhtml'
        
        # 获取基因和肿瘤类型列表
        self.genes = config_manager.get_target_genes()
        self.tumor_types = config_manager.get_tumor_types()
        
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
            'Referer': self.base_url
        })
        return session
    
    def _extract_genes(self, text: str) -> str:
        """提取基因标记"""
        found = []
        text_upper = text.upper()
        
        # 首先检查完整的基因名称
        for gene in self.genes:
            if gene.upper() in text_upper:
                found.append(gene)
        
        # 检查中文别名
        gene_aliases = {
            'EGFR': ['EGFR', '表皮生长因子受体'],
            'ALK': ['ALK', '间变性淋巴瘤激酶'],
            'PDCD1': ['PD-1', '程序性死亡受体1'],
            'CD274': ['PD-L1', '程序性死亡配体1'],
            'ERBB2': ['HER2', '人表皮生长因子受体2'],
            'BRAF': ['BRAF'],
            'KRAS': ['KRAS'],
            'PIK3CA': ['PI3K'],
            'MTOR': ['mTOR'],
            'BTK': ['BTK', '布鲁顿酪氨酸激酶'],
            'PARP1': ['PARP', '聚腺苷二磷酸核糖聚合酶'],
            'MET': ['MET', '间质上皮转化因子'],
            'RET': ['RET', '转染重排'],
            'FGFR1': ['FGFR'],
            'FGFR2': ['FGFR'],
            'FGFR3': ['FGFR'],
            'FGFR4': ['FGFR'],
            'AR': ['AR'],
            'BRCA1': ['BRCA'],
            'BRCA2': ['BRCA'],
            'CDK4': ['CDK'],
            'CDK6': ['CDK'],
            'NTRK1': ['NTRK'],
            'NTRK2': ['NTRK'],
            'NTRK3': ['NTRK'],
            'IDH1': ['IDH'],
            'IDH2': ['IDH']
        }
        
        for gene, aliases in gene_aliases.items():
            if gene not in found:
                for alias in aliases:
                    if alias.upper() in text_upper:
                        found.append(gene)
                        break
        
        return ', '.join(found[:5])
    
    def _get_search_keywords(self) -> List[str]:
        """获取搜索关键词列表"""
        keywords = []
        
        # 添加肿瘤类型关键词
        for tumor in self.tumor_types:
            if 'cn' in tumor:
                keywords.append(tumor['cn'])
            if 'en' in tumor:
                keywords.append(tumor['en'])
        
        # 添加基因关键词（仅常用基因避免过多搜索）
        common_genes = ['EGFR', 'ALK', 'PD-1', 'PD-L1', 'HER2', 'BRAF', 'KRAS', 'PIK3CA', 
                       'BTK', 'PARP', 'CDK', 'FGFR', 'MET', 'RET', 'AR', 'BRCA', 'NTRK']
        
        for gene in common_genes:
            if gene in self.genes or gene.upper() in [g.upper() for g in self.genes]:
                keywords.append(gene)
        
        return list(set(keywords))[:30]  # 限制关键词数量
    
    def _search_trials(self, keyword: str, session, max_pages: int = 10) -> List[Dict]:
        """搜索临床试验"""
        trials = []
        
        for page in range(1, max_pages + 1):
            try:
                logger.info(f"搜索关键词 '{keyword}' 第 {page} 页...")
                
                params = {
                    'pageNum': page,
                    'keyword': keyword,
                    'pro': 'y'
                }
                
                response = session.get(self.search_url, params=params, timeout=30)
                response.raise_for_status()
                
                soup = BeautifulSoup(response.content, 'lxml')
                
                # 查找试验列表
                table = soup.find('table', {'class': 'list_table'}) or soup.find('table', {'id': 'table'}) or soup.find('table')
                
                if not table:
                    logger.warning(f"未找到试验列表表格")
                    break
                
                rows = table.find_all('tr')
                
                if len(rows) <= 1:
                    logger.info(f"第 {page} 页无数据")
                    break
                
                # 跳过表头，处理数据行
                for row in rows[1:]:
                    cells = row.find_all('td')
                    if len(cells) < 2:
                        continue
                    
                    trial_info = self._parse_trial_list_row(cells)
                    if trial_info:
                        trials.append(trial_info)
                
                time.sleep(2)  # 避免请求过快
                
            except Exception as e:
                logger.error(f"搜索第 {page} 页失败: {e}")
                continue
        
        return trials
    
    def _parse_trial_list_row(self, cells) -> Optional[Dict]:
        """解析试验列表行"""
        try:
            # 登记号
            reg_num = cells[0].get_text(strip=True)
            
            # 标题和链接
            title_tag = cells[1].find('a') if len(cells) > 1 else None
            title = title_tag.get_text(strip=True) if title_tag else ''
            detail_url = ''
            
            if title_tag and title_tag.get('href'):
                href = title_tag['href']
                if not href.startswith('http'):
                    detail_url = f"{self.base_url}/{href}"
                else:
                    detail_url = href
            
            # 试验状态
            status = ''
            if len(cells) > 2:
                status = cells[2].get_text(strip=True)
            
            return {
                'reg_num': reg_num,
                'title': title,
                'detail_url': detail_url,
                'status': status
            }
        except Exception as e:
            logger.debug(f"解析列表行失败: {e}")
            return None
    
    def _fetch_trial_detail(self, detail_url: str, trial_info: Dict, session) -> Optional[Dict]:
        """获取试验详情"""
        try:
            logger.info(f"获取试验详情: {trial_info['reg_num']}")
            
            response = session.get(detail_url, timeout=30)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.content, 'lxml')
            
            # 提取基本信息
            basic_info = self._extract_basic_info(soup)
            
            # 提取公示的试验信息
            public_info = self._extract_public_info(soup)
            
            # 合并信息
            trial_data = {
                'platform': 'CDE',
                'trial_id': trial_info['reg_num'],
                'study_title_cn': trial_info['title'] or basic_info.get('title', ''),
                'study_title_en': '',
                'trial_status': trial_info['status'] or basic_info.get('status', ''),
                'phase': basic_info.get('phase', ''),
                'study_type': '干预性',
                'conditions': public_info.get('indications', ''),
                'tumor_type': public_info.get('tumor_type', ''),
                'tumor_type_cn': public_info.get('tumor_type', ''),
                'intervention_drug': public_info.get('drug', ''),
                'gene_marker': self._extract_genes(public_info.get('indications', '') + trial_info['title']),
                'study_location': public_info.get('location', ''),
                'enrollment': public_info.get('enrollment', 0),
                'url': detail_url,
                'data_collection_time': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            }
            
            # 添加其他详细信息
            trial_data.update(basic_info)
            trial_data.update(public_info)
            
            return trial_data
            
        except Exception as e:
            logger.error(f"获取试验详情失败: {e}")
            self.errors += 1
            return None
    
    def _extract_basic_info(self, soup) -> Dict:
        """提取基本信息"""
        info = {}
        
        # 尝试多种方式查找信息
        tables = soup.find_all('table')
        
        for table in tables:
            rows = table.find_all('tr')
            for row in rows:
                cells = row.find_all(['th', 'td'])
                if len(cells) >= 2:
                    key = cells[0].get_text(strip=True)
                    value = cells[1].get_text(strip=True)
                    
                    if '试验题目' in key or '试验名称' in key:
                        info['title'] = value
                    elif '试验状态' in key:
                        info['status'] = value
                    elif '试验分期' in key or '阶段' in key:
                        info['phase'] = value
                    elif '登记号' in key:
                        info['reg_num'] = value
        
        return info
    
    def _extract_public_info(self, soup) -> Dict:
        """提取公示的试验信息"""
        info = {}
        
        # 查找适应症、药物等信息
        tables = soup.find_all('table')
        
        for table in tables:
            rows = table.find_all('tr')
            for row in rows:
                cells = row.find_all(['th', 'td'])
                if len(cells) >= 2:
                    key = cells[0].get_text(strip=True)
                    value = cells[1].get_text(strip=True)
                    
                    if '适应症' in key or '适应病种' in key:
                        info['indications'] = value
                    elif '试验药物' in key or '药物名称' in key:
                        info['drug'] = value
                    elif '试验专业' in key or '疾病名称' in key:
                        info['tumor_type'] = value
                    elif '试验机构' in key or '试验中心' in key:
                        info['location'] = value
                    elif '目标入组人数' in key:
                        try:
                            info['enrollment'] = int(value) if value.isdigit() else 0
                        except:
                            info['enrollment'] = 0
        
        return info
    
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
    
    def collect(self, max_pages_per_keyword: int = 5, max_detail_fetch: int = 20):
        """执行采集"""
        logger.info("="*80)
        logger.info("开始CDE临床试验采集")
        logger.info("="*80)
        
        keywords = self._get_search_keywords()
        logger.info(f"共 {len(keywords)} 个搜索关键词")
        
        session = self._get_session()
        
        # 先访问首页获取cookie
        try:
            session.get(self.search_url + '?pro=y', timeout=30)
            time.sleep(2)
        except Exception as e:
            logger.warning(f"访问首页失败: {e}")
        
        all_trials = []
        
        # 对每个关键词进行搜索
        for i, keyword in enumerate(keywords):
            logger.info(f"[{i+1}/{len(keywords)}] 搜索关键词: {keyword}")
            
            trials = self._search_trials(keyword, session, max_pages_per_keyword)
            
            # 过滤状态为"进行中"的试验
            filtered = [t for t in trials if '进行中' in t['status']]
            
            all_trials.extend(filtered)
            logger.info(f"关键词 '{keyword}' 获取 {len(trials)} 条，其中进行中 {len(filtered)} 条")
            
            time.sleep(2)
            
            # 限制详情页获取数量
            if len(all_trials) >= max_detail_fetch:
                break
        
        # 去重
        unique_trials = {}
        for trial in all_trials:
            if trial['reg_num'] not in unique_trials:
                unique_trials[trial['reg_num']] = trial
        
        logger.info(f"去重后共 {len(unique_trials)} 个试验需要获取详情")
        
        # 获取每个试验的详情
        detail_count = 0
        for reg_num, trial_info in unique_trials.items():
            if detail_count >= max_detail_fetch:
                break
            
            if trial_info['detail_url']:
                detail = self._fetch_trial_detail(trial_info['detail_url'], trial_info, session)
                if detail:
                    self._save_trial(detail)
                    detail_count += 1
                    time.sleep(1)  # 避免请求过快
        
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
    logger.info("CDE临床试验信息采集器")
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
    collector = CDETrialCollector(db_manager, config_manager, translation_service)
    
    # 执行采集
    result = collector.collect(max_pages_per_keyword=3, max_detail_fetch=30)
    
    logger.info(f"采集结果: {result}")
    
    db_manager.close()


if __name__ == "__main__":
    main()
