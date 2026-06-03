"""
ClinicalTrials.gov临床试验采集模块
使用ClinicalTrials.gov API v2.0采集抗肿瘤药物临床试验信息
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


class ClinicalTrialsCollector:
    """ClinicalTrials.gov临床试验采集类"""
    
    def __init__(
        self,
        db_manager: DatabaseManager,
        config_manager: ConfigManager,
        translation_service: TranslationService
    ):
        """初始化ClinicalTrials采集器"""
        self.db_manager = db_manager
        self.config_manager = config_manager
        self.translation_service = translation_service
        
        # API配置
        self.api_url = config_manager.get('clinical_trials_gov.api_url', 'https://clinicaltrials.gov/api/v2/studies')
        self.max_results = config_manager.get('clinical_trials_gov.max_results_per_request', 100)
        
        # 状态筛选
        self.status_filter = config_manager.get('clinical_trials_gov.status_filter', ['Recruiting', 'Active, not recruiting'])
        self.study_type = config_manager.get('clinical_trials_gov.study_type', 'Interventional')
        
        # 统计
        self.records_processed = 0
        self.records_added = 0
        self.errors_count = 0
        
        logger.info("ClinicalTrials.gov采集器初始化完成")
    
    def build_search_expression(self) -> str:
        """构建ClinicalTrials.gov搜索表达式"""
        # 获取肿瘤类型
        tumor_types = self.config_manager.get_tumor_types()[:10]
        
        # 构建肿瘤类型搜索条件
        tumor_terms = []
        for tumor in tumor_types:
            en_name = tumor.get('en', '')
            if en_name:
                tumor_terms.append(en_name)
            
            aliases = tumor.get('aliases_en', [])
            for alias in aliases[:2]:
                tumor_terms.append(alias)
        
        # 构建搜索表达式 - 使用API v2支持的格式
        # 使用简单的关键词组合
        if tumor_terms:
            expression = ' OR '.join([t for t in tumor_terms[:5] if t])
        else:
            expression = 'cancer'
        
        return expression
    
    def fetch_studies(self, page_token: str = None) -> Optional[Dict]:
        """
        获取临床试验数据
        
        Args:
            page_token: 分页令牌
            
        Returns:
            API响应数据
        """
        try:
            params = {
                'query.term': self.build_search_expression(),
                'pageSize': self.max_results,
                'format': 'json'
            }
            
            if page_token:
                params['pageToken'] = page_token
            
            response = requests.get(self.api_url, params=params, timeout=60)
            response.raise_for_status()
            
            data = response.json()
            
            logger.info(f"ClinicalTrials.gov API请求成功")
            
            return data
            
        except Exception as e:
            logger.error(f"ClinicalTrials.gov API请求失败: {e}")
            self.errors_count += 1
            return None
    
    def parse_study_data(self, raw_data: Dict) -> List[Dict]:
        """解析临床试验数据"""
        parsed_trials = []
        
        if not raw_data or 'studies' not in raw_data:
            return parsed_trials
        
        for study in raw_data.get('studies', []):
            try:
                trial = self._parse_single_study(study)
                if trial:
                    parsed_trials.append(trial)
            except Exception as e:
                logger.warning(f"解析试验失败: {e}")
                self.errors_count += 1
        
        return parsed_trials
    
    def _parse_single_study(self, study: Dict) -> Optional[Dict]:
        """解析单个临床试验"""
        try:
            # 提取基本信息
            protocol = study.get('protocolSection', {})
            identification = protocol.get('identificationModule', {})
            
            # 试验ID
            nct_id = identification.get('nctId', '')
            
            # 试验标题
            title_en = identification.get('officialTitle', '')
            
            # 状态
            status_module = protocol.get('statusModule', {})
            trial_status = status_module.get('overallStatus', '')
            
            # 分期
            design_module = protocol.get('designModule', {})
            phases = design_module.get('phases', [])
            phase = ', '.join(phases) if phases else ''
            
            # 研究类型
            study_type = design_module.get('studyType', '')
            
            # 入组人数
            enrollment = design_module.get('enrollmentInfo', {}).get('count', 0)
            
            # 条件（适应症）
            conditions_module = protocol.get('conditionsModule', {})
            conditions = conditions_module.get('conditions', [])
            tumor_type = ', '.join(conditions[:3])
            
            # 干预措施
            interventions_module = protocol.get('interventionsModule', {})
            interventions = interventions_module.get('interventions', [])
            
            intervention_drugs = []
            intervention_list = []
            
            for intervention in interventions:
                int_type = intervention.get('type', '')
                int_name = intervention.get('name', '')
                int_desc = intervention.get('description', '')
                
                intervention_list.append(f"{int_type}: {int_name}")
                
                if int_type == 'DRUG':
                    intervention_drugs.append(int_name)
            
            interventions_str = '; '.join(intervention_list[:5])
            intervention_drug_str = ', '.join(intervention_drugs[:3])
            
            # 入排标准
            eligibility_module = protocol.get('eligibilityModule', {})
            inclusion_criteria = eligibility_module.get('eligibilityCriteria', '')
            
            # 申办方
            sponsor_module = protocol.get('sponsorCollaboratorsModule', {})
            sponsor = sponsor_module.get('leadSponsor', {}).get('name', '')
            
            # 地点
            contacts_module = protocol.get('contactsLocationsModule', {})
            locations = contacts_module.get('locations', [])
            
            location_list = []
            for location in locations[:10]:
                facility = location.get('facility', '')
                city = location.get('city', '')
                country = location.get('country', '')
                location_list.append(f"{facility}, {city}, {country}")
            
            study_location = '; '.join(location_list[:5])
            
            # 日期
            status_module = protocol.get('statusModule', {})
            start_date = status_module.get('startDateStruct', {}).get('date', '')
            primary_completion_date = status_module.get('primaryCompletionDateStruct', {}).get('date', '')
            last_update_posted = status_module.get('lastUpdatePostDateStruct', {}).get('date', '')
            
            # 构建试验数据
            trial_data = {
                'platform': 'ClinicalTrials.gov',
                'trial_id': nct_id,
                'trial_status': trial_status,
                'study_title_en': title_en,
                'study_title_cn': '',
                'tumor_type': tumor_type,
                'tumor_type_cn': '',
                'gene_marker': '',
                'conditions': tumor_type,
                'interventions': interventions_str,
                'intervention_drug': intervention_drug_str,
                'phase': phase,
                'study_type': study_type,
                'enrollment': enrollment,
                'inclusion_criteria_en': inclusion_criteria[:1000] if inclusion_criteria else '',
                'inclusion_criteria_cn': '',
                'exclusion_criteria_en': '',
                'exclusion_criteria_cn': '',
                'study_location': study_location,
                'sponsor': sponsor,
                'start_date': start_date,
                'primary_completion_date': primary_completion_date,
                'last_update_posted': last_update_posted,
                'results_url': '',
                'url': f'https://clinicaltrials.gov/study/{nct_id}',
                'data_collection_time': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            }
            
            return trial_data
            
        except Exception as e:
            logger.warning(f"解析试验失败: {e}")
            return None
    
    def annotate_trial(self, trial: Dict) -> Dict:
        """标注试验的目标基因"""
        genes = self.config_manager.get_target_genes()
        
        # 搜索标题和入排标准中的基因
        text = f"{trial.get('study_title_en', '')} {trial.get('inclusion_criteria_en', '')}"
        
        found_genes = []
        for gene in genes:
            if gene.upper() in text.upper():
                found_genes.append(gene)
        
        trial['gene_marker'] = ', '.join(found_genes[:5])
        
        return trial
    
    def translate_trial(self, trial: Dict) -> Dict:
        """翻译试验信息"""
        # 翻译标题
        if trial.get('study_title_en'):
            title = trial['study_title_en'][:500]
            trial['study_title_cn'] = self.translation_service.translate(title)
        
        # 翻译肿瘤类型
        if trial.get('tumor_type'):
            tumor_types = self.config_manager.get_tumor_types()
            
            tumor_cn_list = []
            for tumor_en in trial['tumor_type'].split(','):
                for tumor in tumor_types:
                    if tumor.get('en', '').lower() in tumor_en.lower():
                        tumor_cn_list.append(tumor.get('cn', tumor_en))
                        break
            
            trial['tumor_type_cn'] = ', '.join(tumor_cn_list) if tumor_cn_list else trial['tumor_type']
        
        # 翻译入排标准
        if trial.get('inclusion_criteria_en'):
            criteria = trial['inclusion_criteria_en'][:500]
            trial['inclusion_criteria_cn'] = self.translation_service.translate(criteria)
        
        return trial
    
    def save_to_database(self, trial: Dict) -> bool:
        """保存试验数据"""
        try:
            # 检查是否已存在
            existing = self.db_manager.execute_query(
                "SELECT id FROM clinical_trials WHERE platform = ? AND trial_id = ?",
                (trial['platform'], trial['trial_id'])
            )
            
            if existing:
                # 更新
                self.db_manager.execute_update(
                    'clinical_trials',
                    trial,
                    "id = ?",
                    (existing[0]['id'],)
                )
                logger.debug(f"更新试验: {trial['trial_id']}")
            else:
                # 插入
                self.db_manager.execute_insert('clinical_trials', trial)
                self.records_added += 1
                logger.debug(f"添加试验: {trial['trial_id']}")
            
            self.records_processed += 1
            return True
            
        except Exception as e:
            logger.error(f"保存试验失败: {e}")
            self.errors_count += 1
            return False
    
    def collect(self, max_pages: int = 5) -> Dict:
        """
        采集临床试验数据
        
        Args:
            max_pages: 最大采集页数，避免超时
        """
        logger.info("开始ClinicalTrials.gov临床试验采集")
        
        start_time = datetime.now()
        
        # 重置统计
        self.records_processed = 0
        self.records_added = 0
        self.errors_count = 0
        
        # 分页采集
        page_token = None
        page_count = 0
        total_count = 0
        
        while page_count < max_pages:
            # 获取数据
            data = self.fetch_studies(page_token)
            
            if not data or 'studies' not in data:
                break
            
            # 获取总数（API v2可能不返回totalCount）
            total_count = data.get('totalCount', len(data.get('studies', [])))
            
            logger.info(f"第{page_count + 1}页，获取 {len(data.get('studies', []))} 条试验")
            
            # 解析数据
            trials = self.parse_study_data(data)
            
            # 处理每个试验
            for trial in trials:
                # 标注
                trial = self.annotate_trial(trial)
                
                # 翻译
                trial = self.translate_trial(trial)
                
                # 保存
                self.save_to_database(trial)
                
                time.sleep(0.2)
            
            page_count += 1
            
            # 获取下一页令牌
            page_token = data.get('nextPageToken')
            
            if not page_token:
                break
            
            time.sleep(1)
        
        end_time = datetime.now()
        duration = (end_time - start_time).total_seconds()
        
        message = f'ClinicalTrials.gov临床试验采集完成，共处理 {self.records_processed} 条记录'
        
        # 记录日志
        self.db_manager.log_system_action({
            'module_name': 'clinical_trials',
            'action': 'collection',
            'status': 'success',
            'message': message,
            'records_processed': self.records_processed,
            'records_added': self.records_added,
            'error_count': self.errors_count,
            'start_time': start_time.strftime('%Y-%m-%d %H:%M:%S'),
            'end_time': end_time.strftime('%Y-%m-%d %H:%M:%S'),
            'duration_seconds': duration
        })
        
        return {
            'status': 'success',
            'total_count': total_count,
            'records_processed': self.records_processed,
            'records_added': self.records_added,
            'errors_count': self.errors_count,
            'duration_seconds': duration,
            'message': message
        }
    
    def run(self) -> Dict:
        """运行采集"""
        return self.collect()


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    
    config_path = "config/config.yaml"
    db_path = "data/medical_info.db"
    
    config_manager = ConfigManager(config_path)
    db_manager = DatabaseManager(db_path)
    db_manager.init_tables()
    
    translation_config = config_manager.get_translation_config()
    translation_service = TranslationService(translation_config)
    
    collector = ClinicalTrialsCollector(db_manager, config_manager, translation_service)
    
    # 测试
    expression = collector.build_search_expression()
    print(f"搜索表达式: {expression[:200]}...")
    
    data = collector.fetch_studies()
    if data:
        print(f"总试验数: {data.get('totalCount', 0)}")
        
        trials = collector.parse_study_data(data)
        for trial in trials[:3]:
            print(f"\n试验ID: {trial['trial_id']}")
            print(f"标题: {trial['study_title_en'][:100]}...")
            print(f"状态: {trial['trial_status']}")
            print(f"分期: {trial['phase']}")
    
    db_manager.close()