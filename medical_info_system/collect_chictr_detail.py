#!/usr/bin/env python3
"""
ChiCTR临床试验信息采集器
使用正确的搜索URL，获取试验详情页的完整信息
仅抓取"研究类型"为"干预性研究"的临床试验
"""
import os
import sys
import time
import logging
import requests
import re
from datetime import datetime
from typing import Dict, List, Optional
from bs4 import BeautifulSoup

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from src.database import init_database
from src.utils.config_manager import ConfigManager
from src.utils.translator import TranslationService

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class ChiCTRTrialCollector:
    """ChiCTR临床试验采集器"""
    
    def __init__(self, db_manager, config_manager, translation_service):
        self.db_manager = db_manager
        self.config_manager = config_manager
        self.translation_service = translation_service
        self.base_url = 'http://www.chictr.org.cn'
        self.search_url = f'{self.base_url}/searchproj.html'
        
        # 获取基因和肿瘤类型列表
        self.genes = config_manager.get_target_genes()
        self.tumor_types = config_manager.get_tumor_types()
        
        # 统计信息
        self.total_trials = 0
        self.new_trials = 0
        self.errors = 0
        self.interventional_count = 0
    
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
                    'page': page,
                    'keyword': keyword
                }
                
                response = session.get(self.search_url, params=params, timeout=30)
                response.raise_for_status()
                
                soup = BeautifulSoup(response.content, 'lxml')
                
                # 查找试验列表表格
                table = soup.find('table')
                
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
                    if len(cells) < 3:
                        continue
                    
                    trial_info = self._parse_trial_list_row(cells)
                    if trial_info:
                        trials.append(trial_info)
                
                # 检查是否有下一页
                pagination = soup.find('a', text=re.compile(r'下一页|>'))
                if not pagination:
                    break
                
                time.sleep(2)  # 避免请求过快
                
            except Exception as e:
                logger.error(f"搜索第 {page} 页失败: {e}")
                continue
        
        return trials
    
    def _parse_trial_list_row(self, cells) -> Optional[Dict]:
        """解析试验列表行"""
        try:
            # 注册号
            reg_num = ''
            reg_num_tag = cells[0].find('a') if cells else None
            if reg_num_tag:
                reg_num = reg_num_tag.get_text(strip=True)
            
            # 标题和链接
            title = ''
            detail_url = ''
            title_tag = cells[1].find('a') if len(cells) > 1 else None
            if title_tag:
                title = title_tag.get_text(strip=True)
                href = title_tag.get('href', '')
                if not href.startswith('http'):
                    detail_url = f"{self.base_url}/{href}"
                else:
                    detail_url = href
            
            # 研究类型
            study_type = ''
            if len(cells) > 2:
                study_type = cells[2].get_text(strip=True)
            
            # 注册时间
            reg_date = ''
            if len(cells) > 3:
                reg_date = cells[3].get_text(strip=True)
            
            return {
                'reg_num': reg_num,
                'title': title,
                'detail_url': detail_url,
                'study_type': study_type,
                'reg_date': reg_date
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
            
            # 提取详细信息
            detail_info = self._extract_detail_info(soup, trial_info)
            
            return detail_info
            
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
                    
                    if '试验名称' in key or '注册题目' in key:
                        info['study_title_cn'] = value
                    elif '试验状态' in key:
                        info['trial_status'] = value
                    elif '试验分期' in key or '研究阶段' in key:
                        info['phase'] = value
                    elif '适应症' in key or '研究疾病' in key:
                        info['conditions'] = value
                        if not info.get('tumor_type'):
                            info['tumor_type'] = value
                            info['tumor_type_cn'] = value
                    elif '试验药物' in key or '干预措施' in key:
                        info['intervention_drug'] = value
                    elif '试验机构' in key or '试验地点' in key:
                        info['study_location'] = value
                    elif '目标入组人数' in key:
                        try:
                            info['enrollment'] = int(value) if value.isdigit() else 0
                        except:
                            info['enrollment'] = 0
        
        # 合并基本信息
        if not info.get('study_title_cn'):
            info['study_title_cn'] = trial_info['title']
        if not info.get('trial_status'):
            info['trial_status'] = trial_info['study_type']  # 使用研究类型作为状态
        
        # 翻译标题为英文
        try:
            info['study_title_en'] = self.translation_service.translate(info.get('study_title_cn', ''))
        except:
            info['study_title_en'] = ''
        
        # 提取基因标记
        info['gene_marker'] = self._extract_genes(
            str(info.get('study_title_cn', '')) + 
            str(info.get('conditions', '')) + 
            str(info.get('intervention_drug', ''))
        )
        
        # 构建最终的数据结构
        trial_data = {
            'platform': 'ChiCTR',
            'trial_id': trial_info['reg_num'],
            'study_title_cn': info.get('study_title_cn', ''),
            'study_title_en': info.get('study_title_en', ''),
            'trial_status': info.get('trial_status', ''),
            'phase': info.get('phase', ''),
            'study_type': '干预性',  # 确保为干预性
            'conditions': info.get('conditions', ''),
            'tumor_type': info.get('tumor_type', ''),
            'tumor_type_cn': info.get('tumor_type_cn', ''),
            'intervention_drug': info.get('intervention_drug', ''),
            'gene_marker': info.get('gene_marker', ''),
            'study_location': info.get('study_location', ''),
            'enrollment': info.get('enrollment', 0),
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
            self.interventional_count += 1
            return True
            
        except Exception as e:
            logger.error(f"保存试验失败: {e}")
            self.errors += 1
            return False
    
    def collect(self, max_pages_per_keyword: int = 5, max_detail_fetch: int = 20):
        """执行采集"""
        logger.info("="*80)
        logger.info("开始ChiCTR临床试验采集（仅干预性研究）")
        logger.info("="*80)
        
        keywords = self._get_search_keywords()
        logger.info(f"共 {len(keywords)} 个搜索关键词")
        
        session = self._get_session()
        
        # 先访问首页获取cookie
        try:
            session.get(self.search_url, timeout=30)
            time.sleep(2)
        except Exception as e:
            logger.warning(f"访问首页失败: {e}")
        
        all_trials = []
        
        # 对每个关键词进行搜索
        for i, keyword in enumerate(keywords):
            logger.info(f"[{i+1}/{len(keywords)}] 搜索关键词: {keyword}")
            
            trials = self._search_trials(keyword, session, max_pages_per_keyword)
            
            # 过滤研究类型为"干预性研究"的试验
            filtered = [t for t in trials if '干预' in t['study_type']]
            
            all_trials.extend(filtered)
            logger.info(f"关键词 '{keyword}' 获取 {len(trials)} 条，其中干预性研究 {len(filtered)} 条")
            
            time.sleep(2)
            
            # 限制详情页获取数量
            if len(all_trials) >= max_detail_fetch:
                break
        
        # 去重
        unique_trials = {}
        for trial in all_trials:
            if trial['reg_num'] not in unique_trials:
                unique_trials[trial['reg_num']] = trial
        
        logger.info(f"去重后共 {len(unique_trials)} 个干预性试验需要获取详情")
        
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
        logger.info(f"干预性试验数: {self.interventional_count}")
        logger.info(f"错误数: {self.errors}")
        logger.info("="*80)
        
        return {
            'total': self.total_trials,
            'new': self.new_trials,
            'interventional': self.interventional_count,
            'errors': self.errors
        }


def main():
    logger.info("="*80)
    logger.info("ChiCTR临床试验信息采集器（仅干预性研究）")
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
    collector = ChiCTRTrialCollector(db_manager, config_manager, translation_service)
    
    # 执行采集
    result = collector.collect(max_pages_per_keyword=3, max_detail_fetch=30)
    
    logger.info(f"采集结果: {result}")
    
    db_manager.close()


if __name__ == "__main__":
    main()
