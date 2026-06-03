"""
FDA已批准抗肿瘤药物采集模块
使用openFDA API采集FDA批准的抗肿瘤靶向药物和免疫治疗药物
"""

import os
import sys
import json
import time
import logging
import requests
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
import hashlib

# 添加项目路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from src.database import DatabaseManager
from src.utils.config_manager import ConfigManager
from src.utils.translator import TranslationService
from src.utils.http_client import RequestManager

logger = logging.getLogger(__name__)


class FDADrugCollector:
    """FDA药物采集类"""
    
    def __init__(
        self,
        db_manager: DatabaseManager,
        config_manager: ConfigManager,
        translation_service: TranslationService,
        request_manager: RequestManager
    ):
        """
        初始化FDA药物采集器
        
        Args:
            db_manager: 数据库管理器
            config_manager: 配置管理器
            translation_service: 翻译服务
            request_manager: 请求管理器
        """
        self.db_manager = db_manager
        self.config_manager = config_manager
        self.translation_service = translation_service
        self.request_manager = request_manager
        
        # FDA API配置
        self.api_url = config_manager.get('fda.api_url', 'https://api.fda.gov/drug/drugsfda.json')
        self.label_url = config_manager.get('fda.label_url', 'https://api.fda.gov/drug/label.json')
        self.max_results = config_manager.get('fda.max_results_per_request', 100)
        self.start_date = config_manager.get('fda.start_date', '2020-01-01')
        self.cancer_keywords = config_manager.get('fda.cancer_keywords', [])
        
        # 加载药品中文名称映射
        self.drug_name_mapping = self._load_drug_name_mapping()
        
        # 统计信息
        self.records_processed = 0
        self.records_added = 0
        self.records_updated = 0
        self.errors_count = 0
        
        logger.info("FDA药物采集器初始化完成")
    
    def _load_drug_name_mapping(self) -> Dict:
        """加载药品中文名称映射"""
        base_path = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        mapping_file = os.path.join(base_path, 'data', 'drug_name_mapping.json')
        if os.path.exists(mapping_file):
            try:
                with open(mapping_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except Exception as e:
                logger.warning(f"加载药品名称映射失败: {e}")
        return {}
    
    def build_search_query(self, last_collection_time: Optional[str] = None) -> str:
        """
        构建FDA API搜索查询 - 使用更全面的搜索策略
        
        Args:
            last_collection_time: 最后采集时间（用于增量更新）
            
        Returns:
            搜索查询字符串
        """
        # 构建更全面的抗肿瘤药物查询
        # 使用多种可能的关键词组合，确保捕获尽可能多的抗肿瘤药物
        cancer_keywords = [
            'cancer', 'tumor', 'neoplasm', 'malignancy',
            'oncology', 'antineoplastic', 'chemotherapy',
            'carcinoma', 'lymphoma', 'leukemia', 'melanoma',
            'nsclc', 'sclc', 'multiple myeloma', 'aml', 'cll'
        ]
        
        # 构建OR查询
        query_parts = []
        
        # 添加癌症相关查询
        for keyword in cancer_keywords:
            query_parts.append(keyword)
        
        # 还可以尝试添加作用机制相关关键词，提高靶向/免疫药物召回率
        mechanism_keywords = [
            'kinase inhibitor', 'checkpoint inhibitor', 'monoclonal antibody',
            'antibody-drug conjugate', 'immunotherapy', 'targeted therapy'
        ]
        
        for keyword in mechanism_keywords:
            query_parts.append(keyword)
        
        # 组合查询
        query = ' OR '.join(query_parts)
        
        # 如果是增量更新，添加时间筛选
        if last_collection_time:
            try:
                last_date = datetime.strptime(last_collection_time, '%Y-%m-%d')
                query += f' AND submission_status_date:[{last_date.strftime("%Y%m%d")} TO *]'
            except:
                pass
        
        return query
    
    def fetch_drugsfda_data(self, skip: int = 0, limit: int = 100) -> Optional[Dict]:
        """
        从openFDA drugsfda API获取数据
        
        Args:
            skip: 跳过的记录数
            limit: 返回的记录数
            
        Returns:
            API响应数据
        """
        try:
            # 构建查询参数
            params = {
                'search': self.build_search_query(),
                'skip': skip,
                'limit': limit
            }
            
            # 发送请求
            response = requests.get(self.api_url, params=params, timeout=60)
            response.raise_for_status()
            
            data = response.json()
            
            logger.info(f"FDA API请求成功: skip={skip}, limit={limit}")
            
            return data
            
        except requests.RequestException as e:
            logger.error(f"FDA API请求失败: {e}")
            self.errors_count += 1
            return None
        except Exception as e:
            logger.error(f"FDA数据处理失败: {e}")
            self.errors_count += 1
            return None
    
    def fetch_label_data(self, application_number: str) -> Optional[Dict]:
        """
        从openFDA label API获取药品说明书数据
        
        Args:
            application_number: 申请编号
            
        Returns:
            说明书数据
        """
        try:
            # 构建查询 - 尝试多种搜索方式
            # 方式1: 使用application_number精确搜索
            # 方式2: 使用产品名称搜索（当application_number搜索失败时）
            
            search_terms = [
                f'application_number:{application_number}',
                f'openfda.application_number:{application_number}',
            ]
            
            # 清理编号（去掉前缀）
            clean_number = application_number.replace('NDA', '').replace('ANDA', '').replace('BLA', '')
            if clean_number != application_number:
                search_terms.append(f'application_number:{clean_number}')
            
            for search_term in search_terms:
                try:
                    params = {
                        'search': search_term,
                        'limit': 1
                    }
                    
                    response = requests.get(self.label_url, params=params, timeout=10)
                    
                    if response.status_code == 200:
                        data = response.json()
                        if data.get('results'):
                            return data['results'][0]
                except:
                    continue
            
            return None
            
        except Exception as e:
            logger.warning(f"获取说明书失败: {application_number}, {e}")
            return None
    
    def parse_drug_data(self, raw_data: Dict) -> List[Dict]:
        """
        解析FDA药物数据
        
        Args:
            raw_data: API返回的原始数据
            
        Returns:
            解析后的药物数据列表
        """
        parsed_drugs = []
        
        if not raw_data or 'results' not in raw_data:
            return parsed_drugs
        
        for result in raw_data.get('results', []):
            try:
                # 提取基本信息
                products = result.get('products', [])
                
                for product in products:
                    # 解析每个产品
                    drug_data = self._parse_single_product(result, product)
                    
                    if drug_data:
                        # 先获取说明书数据丰富信息
                        drug_data = self.enrich_with_label_data(drug_data)
                        
                        # 检查是否为抗肿瘤药物（基于说明书适应症）
                        if self._is_cancer_drug(drug_data):
                            parsed_drugs.append(drug_data)
                
            except Exception as e:
                logger.warning(f"解析药物数据失败: {e}")
                self.errors_count += 1
        
        return parsed_drugs
    
    def _parse_single_product(self, result: Dict, product: Dict) -> Optional[Dict]:
        """
        解析单个产品数据 - 改进版，保存所有FDA提交信息
        
        Args:
            result: API结果
            product: 产品信息
            
        Returns:
            解析后的药物数据
        """
        try:
            # 提取申请信息
            application_number = result.get('application_number', '')
            
            # 提取所有提交，包含批准日期和相关信息（用于后续适应症日期匹配）
            all_submissions = []
            submissions = result.get('submissions', [])
            initial_approval_date = ''
            
            for submission in submissions:
                status = submission.get('submission_status', '')
                submission_type = submission.get('submission_type', '')
                status_date = submission.get('submission_status_date', '')
                
                # 获取初始批准日期
                if status in ('APPROVED', 'AP') and submission_type in ('ORIG', 'SUPPL') and not initial_approval_date:
                    initial_approval_date = status_date
                
                all_submissions.append({
                    'status': status,
                    'type': submission_type,
                    'date': status_date,
                    'review_priority': submission.get('review_priority', ''),
                    'submission_class_code': submission.get('submission_class_code', '')
                })
            
            # 提取申请人
            applicant = result.get('sponsor_name', '')
            
            # 提取产品信息
            brand_name_en = product.get('brand_name', '')
            generic_name_en = product.get('generic_name', '')
            
            # 提取活性成分（作为通用名补充）
            active_ingredients = product.get('active_ingredients', [])
            if active_ingredients and not generic_name_en:
                generic_name_en = ', '.join([a.get('name', '') for a in active_ingredients])
            
            # 提取剂型和给药途径
            dosage_form = product.get('dosage_form', '')
            route_of_administration = product.get('route', '')
            
            # 提取适应症（从active_ingredient或从说明书获取）
            indication = product.get('active_ingredient', '')
            
            # 提取作用机制（需要从说明书获取）
            mechanism_of_action = ''
            
            # 构建基本数据 - 保存所有提交信息供后续使用
            drug_data = {
                'regulatory_agency': 'FDA',
                'drug_name_en': brand_name_en,
                'drug_name_cn': '',  # 待翻译
                'generic_name_en': generic_name_en,
                'generic_name_cn': '',  # 待翻译
                'brand_name_en': brand_name_en,
                'brand_name_cn': '',  # 待翻译
                'applicant': applicant,
                'application_number': application_number,
                'approval_number': application_number,
                'approval_date': initial_approval_date,
                'all_fda_submissions': all_submissions,  # 保存所有提交记录
                'indication': indication,
                'dosage_form': dosage_form,
                'route_of_administration': route_of_administration,
                'mechanism_of_action': mechanism_of_action,
                'companion_diagnosis': '',
                'cd_target': '',
                'cd_product': '',
                'clinical_trial_data': '',
                'previous_approved_indications': '',
                'previous_withdrawn_indications': '',
                'previous_fda_approvals': '',
                'previous_nmpa_approvals': '',
                'label_download_url': '',
                'label_cloud_path': '',
                'detail_url': f'https://www.accessdata.fda.gov/scripts/cder/daf/index.cfm?event=overview.process&ApplNo={application_number.replace("NDA", "").replace("ANDA", "")}',
                'data_collection_time': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            }
            
            return drug_data
            
        except Exception as e:
            logger.warning(f"解析产品失败: {e}")
            return None
    
    def _extract_companion_diagnostic(self, text: str) -> Dict:
        """
        从适应症文本中提取伴随诊断信息
        
        FDA批准的药物通常在适应症中标注需要FDA批准的检测：
        "as detected by an FDA-approved test"
        "whose tumors express PD-L1"
        "EGFR exon 19 deletions or exon 21 L858R mutations"
        
        Args:
            text: 适应症文本
            
        Returns:
            包含伴随诊断信息的字典
        """
        result = {
            'companion_diagnosis': '',
            'cd_target': '',
            'cd_product': '',
        }
        
        if not text:
            return result
        
        text_lower = text.lower()
        
        # 定义已知的伴随诊断靶点和关键词模式
        # 使用简化的正则，匹配FDA适应症中的常见伴随诊断描述
        cd_patterns = [
            # 基因突变类 - 使用宽松匹配
            (r'EGFR.*exon\s*19.*delet', 'EGFR exon 19 del/exon 21 L858R', 'EGFR基因突变检测'),
            (r'EGFR.*exon\s*21.*L858R', 'EGFR exon 19 del/exon 21 L858R', 'EGFR基因突变检测'),
            (r'ALK.*positive', 'ALK阳性', 'ALK基因重排检测'),
            (r'ROS1.*positive', 'ROS1阳性', 'ROS1基因重排检测'),
            (r'BRAF.*V600', 'BRAF V600E', 'BRAF V600E突变检测'),
            (r'NTRK.*fusion', 'NTRK融合', 'NTRK基因融合检测'),
            (r'HER2.*activating.*mutation', 'HER2突变', 'HER2激酶域突变检测'),
            (r'ERBB2.*activating.*mutation', 'HER2突变', 'HER2激酶域突变检测'),
            (r'PD-L1.*(?:express|positive|score|TPS)', 'PD-L1', 'PD-L1蛋白表达检测'),
            (r'BRCA.*(?:mutation|positive|mutated)', 'BRCA', 'BRCA基因突变检测'),
            (r'MSI.{0,5}H|microsatellite instability.{0,10}high', 'MSI-H', '微卫星不稳定性检测'),
            (r'TMB.{0,5}(?:high|≥\s*10)', 'TMB-H', '肿瘤突变负荷检测'),
            (r'RET.*fusion', 'RET融合', 'RET基因融合检测'),
            (r'MET.*exon\s*14.*skipping', 'MET exon14跳突/扩增', 'MET基因变异检测'),
            (r'MET.*amplification', 'MET扩增', 'MET基因扩增检测'),
            (r'KRAS.*G12C', 'KRAS G12C', 'KRAS基因突变检测'),
            (r'ESR1.*mutat', 'ESR1突变', 'ESR1基因突变检测'),
            (r'IDH1.*mutation|IDH2.*mutation', 'IDH1/IDH2', 'IDH基因突变检测'),
            (r'FLT3.*ITD|FLT3.*mutation', 'FLT3', 'FLT3基因突变检测'),
            (r'c-KIT.*mutation|KIT.*mutation', 'c-KIT', 'KIT基因突变检测'),
            (r'FGFR.*alteration|FGFR.*fusion', 'FGFR', 'FGFR基因变异检测'),
            (r'PIK3CA.*mutation', 'PIK3CA', 'PIK3CA基因突变检测'),
            (r'NRG1.*fusion', 'NRG1融合', 'NRG1基因融合检测'),
            (r'dMMR|mismatch repair.*deficien', 'dMMR', '错配修复缺陷检测'),
            (r'VEGFR|vascular endothelial growth factor', 'VEGFR', 'VEGFR相关检测'),
            (r'HER2.*negative', 'HER2阴性', 'HER2阴性确认'),
            (r'FOLR1.*positive', 'FOLR1阳性', 'FOLR1表达检测'),
            (r'TROP2.*express', 'TROP2', 'TROP2表达检测'),
        ]
        
        import re
        targets_found = []
        
        # 清理文本中的换行符
        clean_text = text.replace('\n', ' ').replace('\r', ' ')
        
        for pattern, target_name, cd_desc in cd_patterns:
            try:
                match = re.search(pattern, clean_text, re.IGNORECASE | re.DOTALL)
                if match:
                    if target_name not in targets_found:
                        targets_found.append(target_name)
            except:
                continue
        
        if targets_found:
            result['cd_target'] = ', '.join(targets_found)
            result['companion_diagnosis'] = f'需要FDA批准的伴随诊断检测: {result["cd_target"]}'
            
            # 尝试提取检测产品描述
            test_match = re.search(r'(?:as detected by an (?:FDA[- ]approved|FDA[- ]authorized) test)', text, re.IGNORECASE)
            if test_match:
                result['cd_product'] = 'FDA批准/授权的伴随诊断检测试剂'
        
        return result
    
    def _is_cancer_drug(self, drug_data: Dict) -> bool:
        """
        检查是否为抗肿瘤药物（改进版）
        大幅放宽判断条件，提高召回率
        
        Args:
            drug_data: 药物数据
            
        Returns:
            是否为抗肿瘤药物
        """
        indication = drug_data.get('indication', '').lower()
        moa = drug_data.get('mechanism_of_action', '').lower()
        brand_name = drug_data.get('brand_name_en', '').lower()
        generic_name = drug_data.get('generic_name_en', '').lower()
        
        # 首先明确排除的非抗肿瘤药物
        excluded_keywords = [
            'anemia', 'chronic kidney disease', 'hepatitis', 'hiv', 'influenza',
            'antibiotic', 'antifungal', 'antiviral', 'vaccine',
            'diagnostic agent', 'contrast agent', 'blood product', 'coagulation',
            'cardiovascular', 'hypertension', 'diabetes', 'obesity',
            'neurological', 'seizure', 'pain management', 'anesthetic',
            'anticoagulant', 'antiplatelet', 'cholesterol',
            'bone density', 'osteoporosis', 'hormone replacement',
            'fertility', 'contraceptive', 'glaucoma',
            'nausea', 'vomiting', 'emesis', 'antiemetic', 'palonosetron', 'netupitant',
            'contraception', 'uterine fibroid', 'endometriosis', 'menorrhagia',
            'heavy menstrual', 'gynecological',
            'complement', 'factor d', 'paroxysmal nocturnal hemoglobinuria', 'pnh',
            'immunoglobulin', 'autoimmune', 'pemphigus', 'immune thrombocytopenia',
            'hemophilia', 'bleeding disorder'
        ]
        
        has_excluded = False
        for keyword in excluded_keywords:
            if keyword in indication:
                has_excluded = True
                break
        
        # 如果有排除关键词，但同时有强烈的癌症关键词，仍然保留
        cancer_signals = False
        strong_cancer_keywords = [
            'malignancy', 'carcinoma', 'lymphoma', 'leukemia', 'melanoma',
            'myeloma', 'nsclc', 'sclc', 'acute myeloid', 'chronic lymphocytic',
            'hodgkin', 'non-small cell', 'small cell', 'multiple myeloma',
            'aml', 'cll', 'mcl', 'fl', 'dlbcl', 'glioblastoma', 'gastrointestinal stromal'
        ]
        
        for keyword in strong_cancer_keywords:
            if keyword in indication or keyword in moa:
                cancer_signals = True
                break
        
        # 有强癌症信号的药物，即使有排除关键词也保留
        if cancer_signals:
            return True
        
        # 有排除关键词且无强癌症信号，排除
        if has_excluded:
            return False
        
        # 检查广谱癌症关键词
        all_cancer_keywords = [
            'cancer', 'tumor', 'neoplasm', 'malignancy', 'carcinoma',
            'lymphoma', 'leukemia', 'sarcoma', 'melanoma', 'myeloma',
            'nsclc', 'sclc', 'non-small cell lung', 'small cell lung',
            'breast cancer', 'colorectal cancer', 'prostate cancer',
            'pancreatic', 'ovarian', 'endometrial', 'cervical',
            'bladder', 'renal cell', 'kidney cancer', 'hepatocellular',
            'glioma', 'glioblastoma', 'astrocytoma', 'medulloblastoma',
            'multiple myeloma', 'chronic lymphocytic', 'cll',
            'acute myeloid', 'aml', 'hodgkin',
            'waldenstrom', 'mantle cell', 'follicular lymphoma',
            'cutaneous', 'merkel cell', 'kaposi sarcoma',
            'gastrointestinal stromal', 'gist', 'neuroendocrine',
            'pheochromocytoma', 'paraganglioma', 'myelofibrosis',
            'polycythemia vera', 'essential thrombocythemia'
        ]
        
        for keyword in all_cancer_keywords:
            if keyword in indication:
                return True
        
        # 检查作用机制关键词
        moa_keywords = [
            # 免疫检查点
            'pd-1', 'pd-l1', 'pd-l2', 'ctla-4', 'lag-3', 'tim-3', 'tigit',
            'checkpoint inhibitor', 'immune checkpoint',
            # 单克隆抗体
            'monoclonal antibody', 'mab',
            # ADC
            'antibody-drug conjugate', 'adc',
            # 激酶抑制剂
            'kinase inhibitor', 'tyrosine kinase', 'kinase',
            'egfr', 'her2', 'her3', 'her4', 'alk', 'ros1', 'braf', 'mek',
            'kras', 'ntrk', 'ret', 'met', 'fgfr', 'vegfr', 'btk',
            'pi3k', 'mtor', 'cdk', 'parp', 'hdac', 'dnmt', 'bcl-2',
            # 靶点
            'cd20', 'cd30', 'cd38', 'cd52', 'cd79b', 'bcma', 'gprc5d',
            # 其他肿瘤药物
            'topoisomerase', 'microtubule', 'alkylating', 'antimetabolite',
            'hormone receptor', 'aromatase', 'anti-androgen',
            'radioligand', 'radiopharmaceutical'
        ]
        
        for keyword in moa_keywords:
            if keyword in moa:
                return True
        
        # 检查药物名称中的线索
        drug_name_keywords = [
            'mab', 'nib', 'umab', 'zumab', 'ximab', 'zumab', 'tuzumab',
            'trastuzumab', 'pembrolizumab', 'nivolumab', 'atezolizumab',
            'durvalumab', 'ipilimumab', 'cetuximab', 'rituximab',
            'ibrutinib', 'imatinib', 'dasatinib', 'erlotinib',
            'gefitinib', 'osimertinib', 'crizotinib'
        ]
        
        for keyword in drug_name_keywords:
            if keyword in brand_name or keyword in generic_name:
                return True
        
        # 放宽最后的判断：只要有任何抗肿瘤相关线索就保留
        # 例如：药物有indication且包含"treatment"，或者moa中包含"inhibitor"和"receptor"
        if indication and 'treatment' in indication:
            return True
        
        if moa and ('inhibitor' in moa or 'receptor' in moa or 'antibody' in moa):
            return True
        
        return False
    
    def enrich_with_label_data(self, drug_data: Dict) -> Dict:
        """
        使用说明书数据丰富药物信息
        
        Args:
            drug_data: 基础药物数据
            
        Returns:
            丰富后的药物数据
        """
        try:
            # 获取说明书数据
            label_data = self.fetch_label_data(drug_data['application_number'])
            
            if label_data:
                openfda = label_data.get('openfda', {})
                
                # 提取适应症
                indications = label_data.get('indications_and_usage', [])
                if indications:
                    drug_data['indication'] = indications[0] if isinstance(indications, list) else indications
                
                # 提取作用机制
                mechanism = label_data.get('mechanism_of_action', [])
                if mechanism:
                    drug_data['mechanism_of_action'] = mechanism[0] if isinstance(mechanism, list) else mechanism
                
                # 提取伴随诊断信息 - 从适应症中查找FDA批准的伴随诊断检测
                indications_text = drug_data.get('indication', '')
                cd_info = self._extract_companion_diagnostic(indications_text)
                if cd_info:
                    drug_data['companion_diagnosis'] = cd_info.get('companion_diagnosis', '')
                    drug_data['cd_target'] = cd_info.get('cd_target', '')
                    drug_data['cd_product'] = cd_info.get('cd_product', '')
                
                # 提取临床试验数据
                clinical_sections = label_data.get('clinical_studies', [])
                if clinical_sections:
                    drug_data['clinical_trial_data'] = clinical_sections[0] if isinstance(clinical_sections, list) else clinical_sections
                
                # 提取说明书链接
                clean_app_no = drug_data['application_number'].replace('NDA', '').replace('ANDA', '')
                drug_data['label_download_url'] = f'https://www.accessdata.fda.gov/scripts/cder/daf/index.cfm?event=overview.process&ApplNo={clean_app_no}'
                
                # 从openfda补充通用名（如果为空）
                if not drug_data.get('generic_name_en'):
                    generic_names = openfda.get('generic_name', [])
                    if generic_names:
                        drug_data['generic_name_en'] = generic_names[0] if isinstance(generic_names, list) else generic_names
                
                # 从openfda补充商品名（如果为空）
                if not drug_data.get('brand_name_en'):
                    brand_names = openfda.get('brand_name', [])
                    if brand_names:
                        drug_data['brand_name_en'] = brand_names[0] if isinstance(brand_names, list) else brand_names
                
                # 从openfda补充substance_name作为通用名
                if not drug_data.get('generic_name_en'):
                    substances = openfda.get('substance_name', [])
                    if substances:
                        drug_data['generic_name_en'] = substances[0] if isinstance(substances, list) else substances
            
        except Exception as e:
            logger.warning(f"丰富说明书数据失败: {e}")
        
        return drug_data
    
    def translate_drug_data(self, drug_data: Dict) -> Dict:
        """
        翻译药物数据中的英文内容
        使用药品中文名称映射表校正中文名
        
        Args:
            drug_data: 药物数据
            
        Returns:
            翻译后的药物数据
        """
        brand_name_en = drug_data.get('brand_name_en', '')
        
        # 优先使用映射表中的中文名称
        if brand_name_en in self.drug_name_mapping:
            mapping = self.drug_name_mapping[brand_name_en]
            drug_data['drug_name_cn'] = mapping.get('drug_name_cn', '')
            drug_data['brand_name_cn'] = mapping.get('brand_name_cn', '')
            drug_data['generic_name_cn'] = mapping.get('generic_name_cn', '')
        else:
            # 映射表中没有，使用机器翻译
            if drug_data.get('drug_name_en'):
                drug_data['drug_name_cn'] = self.translation_service.translate(drug_data['drug_name_en'])
            if drug_data.get('brand_name_en'):
                drug_data['brand_name_cn'] = self.translation_service.translate(drug_data['brand_name_en'])
            if drug_data.get('generic_name_en'):
                drug_data['generic_name_cn'] = self.translation_service.translate(drug_data['generic_name_en'])
        
        # 翻译适应症（完整内容，不截断）
        if drug_data.get('indication'):
            indication = drug_data['indication']
            # 翻译前500字符（避免过长）
            ind_to_translate = indication[:500] if len(indication) > 500 else indication
            drug_data['indication_cn'] = self.translation_service.translate(ind_to_translate)
        
        # 翻译作用机制
        if drug_data.get('mechanism_of_action'):
            moa = drug_data['mechanism_of_action']
            moa_to_translate = moa[:500] if len(moa) > 500 else moa
            drug_data['mechanism_of_action_cn'] = self.translation_service.translate(moa_to_translate)
        
        return drug_data
    
    def split_by_indication(self, drug_data: Dict) -> List[Dict]:
        """
        按适应症拆分药物记录
        从FDA说明书的indications_and_usage中提取每个真正的适应症
        排除"加速批准说明"、"继续批准取决于"等非适应症文字
        每个适应症单独一行，并标注各自的获批时间
        
        Args:
            drug_data: 药物数据
            
        Returns:
            拆分后的药物数据列表
        """
        import re
        
        indication = drug_data.get('indication', '')
        brand_name = drug_data.get('brand_name_en', '')
        
        # 定义需要排除的非适应症模式
        exclusion_patterns = [
            r'This indication is approved under accelerated approval.*?(?=\.|$)',
            r'Continued approval for this indication may be contingent upon.*?(?=\.|$)',
            r'This indication is approved under.*?(?=\.|$)',
            r'\[see \w+ \(\d+\.\d+\)\]',
            r'\(.*?\d{4}\)',  # 括号中的年份引用
        ]
        
        # 清理文本，移除非适应症说明
        clean_indication = indication
        for pattern in exclusion_patterns:
            clean_indication = re.sub(pattern, '', clean_indication, flags=re.IGNORECASE | re.DOTALL)
        
        # 从清理后的文本中提取适应症
        # 策略1: 查找以药品名开头的完整适应症描述（非贪婪匹配，避免跨适应症）
        # 匹配格式: "DRUGNAME is indicated for the treatment of ... [癌症类型]."
        drug_indication_pattern = rf'{re.escape(brand_name)}\s+(?:is|are)\s+(?:a|an\s+)?(?:kinase inhibitor\s+|estrogen receptor antagonist\s+|gonadotropin-releasing hormone\s+)?indicated\s+for\b[^.]*?(?:treatment\s+of|therapy\s+for)\b[^.]*?\.'
        matches = re.findall(drug_indication_pattern, clean_indication, re.IGNORECASE | re.DOTALL)
        
        # 策略2: 查找以"indicated for"开头的句子
        if not matches:
            indicated_pattern = r'(?:is|are)\s+indicated\s+for\b.*?\.'
            matches = re.findall(indicated_pattern, clean_indication, re.IGNORECASE | re.DOTALL)
        
        # 策略3: 按大标题分割（如 "Non-Small Cell Lung Cancer"、"Mantle Cell Lymphoma"）
        if not matches:
            # 查找以癌症类型标题开头的段落
            cancer_types = [
                'Non-Small Cell Lung Cancer', 'NSCLC', 'Small Cell Lung Cancer',
                'Breast Cancer', 'Colorectal Cancer', 'Prostate Cancer',
                'Pancreatic Cancer', 'Ovarian Cancer', 'Gastric Cancer',
                'Mantle Cell Lymphoma', 'Chronic Lymphocytic Leukemia',
                'Acute Myeloid Leukemia', 'Multiple Myeloma',
                'Gastrointestinal Stromal Tumor', 'GIST',
                'Hepatocellular Carcinoma', 'Renal Cell Carcinoma',
                'Melanoma', 'Thyroid Cancer', 'Head and Neck Cancer',
                'Bladder Cancer', 'Cervical Cancer', 'Endometrial Cancer',
                'Neuroendocrine Tumors', 'Soft Tissue Sarcoma',
                'Glioblastoma', 'Brain Tumors'
            ]
            
            for cancer_type in cancer_types:
                pattern = rf'\b{re.escape(cancer_type)}\b.*?\.(?=\s*(?:\b(?:{"|".join(cancer_types)})\b|\Z))'
                type_matches = re.findall(pattern, clean_indication, re.IGNORECASE | re.DOTALL)
                matches.extend(type_matches)
        
        # 策略4: 按bullet points分割
        if not matches:
            bullet_pattern = r'[•\-]\s*([^•\-]+?)(?=[•\-]|\Z)'
            bullets = re.findall(bullet_pattern, clean_indication, re.DOTALL)
            for bullet in bullets:
                bullet = bullet.strip()
                # 只保留包含治疗相关关键词的bullet
                if bullet and any(kw in bullet.lower() for kw in ['treatment', 'therapy', 'indicated', 'patients with']):
                    # 排除过短的片段（可能是引用说明）
                    if len(bullet) > 30:
                        matches.append(bullet)
        
        # 去重并清理 - 使用语义相似度去重
        unique_matches = []
        seen_indications = []
        
        for match in matches:
            match = match.strip()
            # 移除多余的空白
            match = ' '.join(match.split())
            if not match or len(match) <= 20:
                continue
            
            # 检查是否与已保存的适应症语义重复
            is_duplicate = False
            match_lower = match.lower()
            
            for seen in seen_indications:
                seen_lower = seen.lower()
                # 如果一个是另一个的子串，认为是重复
                if match_lower in seen_lower or seen_lower in match_lower:
                    is_duplicate = True
                    break
                # 如果关键词高度重叠（如都包含"adjuvant therapy"和"NSCLC"），认为是重复
                # 提取关键医学术语进行比较
                key_terms = ['adjuvant', 'metastatic', 'locally advanced', 'unresectable', 
                           'first-line', 'combination', 't790m', 'egfr', 'alk', 'her2',
                           'gastrointestinal stromal', 'gist', 'mastocytosis',
                           'prostate cancer', 'breast cancer', 'lung cancer']
                
                match_terms = [t for t in key_terms if t in match_lower]
                seen_terms = [t for t in key_terms if t in seen_lower]
                
                # 如果关键术语重叠超过80%，认为是重复
                if match_terms and seen_terms:
                    overlap = len(set(match_terms) & set(seen_terms))
                    total = len(set(match_terms) | set(seen_terms))
                    if total > 0 and overlap / total >= 0.8:
                        # 保留更长的描述
                        if len(match) > len(seen):
                            # 替换为更长的描述
                            idx = seen_indications.index(seen)
                            seen_indications[idx] = match
                            unique_matches[idx] = match
                        is_duplicate = True
                        break
            
            if not is_duplicate:
                seen_indications.append(match)
                unique_matches.append(match)
        
        if len(unique_matches) > 1:
            split_drugs = []
            for i, match in enumerate(unique_matches):
                new_drug = drug_data.copy()
                new_drug['indication'] = match
                
                # 翻译拆分后的适应症
                ind_to_translate = match[:500] if len(match) > 500 else match
                new_drug['indication_cn'] = self.translation_service.translate(ind_to_translate)
                
                split_drugs.append(new_drug)
            
            return split_drugs
        
        # 不需要拆分，返回原数据
        return [drug_data]
    
    def fetch_fda_approval_history(self, brand_name: str, generic_name: str) -> List[Dict]:
        """
        从FDA网站获取药物的历史获批适应症信息
        
        Args:
            brand_name: 药品商品名
            generic_name: 药品通用名
            
        Returns:
            历史获批适应症列表，每项包含适应症和获批日期
        """
        import requests
        import re
        from bs4 import BeautifulSoup
        
        history = []
        
        try:
            # 方法1: 查询FDA孤儿药数据库
            orphan_url = 'https://www.accessdata.fda.gov/scripts/opdlisting/oopd/detailedIndex.cfm'
            params = {'genericname': generic_name.lower()}
            
            response = requests.get(orphan_url, params=params, timeout=30)
            if response.status_code == 200:
                soup = BeautifulSoup(response.text, 'html.parser')
                # 解析表格数据
                tables = soup.find_all('table')
                for table in tables:
                    rows = table.find_all('tr')
                    for row in rows:
                        cells = row.find_all('td')
                        if len(cells) >= 4:
                            date_text = cells[0].get_text().strip()
                            indication_text = cells[3].get_text().strip()
                            if date_text and indication_text and 'approved' in indication_text.lower():
                                # 解析日期
                                date_match = re.search(r'(\d{2})/(\d{2})/(\d{4})', date_text)
                                if date_match:
                                    date_str = f"{date_match.group(3)}{date_match.group(1)}{date_match.group(2)}"
                                    history.append({
                                        'approval_date': date_str,
                                        'indication': indication_text,
                                        'source': 'FDA Orphan Drug Database'
                                    })
        except Exception as e:
            logger.warning(f"从FDA孤儿药数据库获取历史失败: {e}")
        
        try:
            # 方法2: 查询FDA药物批准数据库
            # 使用Drugs@FDA搜索
            daf_url = 'https://www.accessdata.fda.gov/scripts/cder/daf/index.cfm'
            
            # 尝试通过通用名搜索
            search_params = {
                'event': 'basicSearch.process',
                'searchTerm': generic_name.lower()
            }
            
            response = requests.get(daf_url, params=search_params, timeout=30)
            if response.status_code == 200:
                soup = BeautifulSoup(response.text, 'html.parser')
                # 查找申请历史链接
                links = soup.find_all('a', href=re.compile(r'event=overview\.process'))
                for link in links[:3]:  # 限制查询数量
                    href = link.get('href', '')
                    if 'ApplNo=' in href:
                        # 获取详细页面
                        detail_url = f"https://www.accessdata.fda.gov/scripts/cder/daf/{href}"
                        detail_response = requests.get(detail_url, timeout=30)
                        if detail_response.status_code == 200:
                            detail_soup = BeautifulSoup(detail_response.text, 'html.parser')
                            # 查找历史批准表格
                            hist_tables = detail_soup.find_all('table', {'class': 'table'})
                            for table in hist_tables:
                                rows = table.find_all('tr')
                                for row in rows[1:]:  # 跳过表头
                                    cells = row.find_all('td')
                                    if len(cells) >= 3:
                                        date_cell = cells[0].get_text().strip()
                                        action_cell = cells[1].get_text().strip()
                                        ind_cell = cells[2].get_text().strip()
                                        
                                        if 'Approval' in action_cell and ind_cell:
                                            date_match = re.search(r'(\d{2})/(\d{2})/(\d{4})', date_cell)
                                            if date_match:
                                                date_str = f"{date_match.group(3)}{date_match.group(1)}{date_match.group(2)}"
                                                # 避免重复
                                                if not any(h['approval_date'] == date_str for h in history):
                                                    history.append({
                                                        'approval_date': date_str,
                                                        'indication': ind_cell,
                                                        'source': 'Drugs@FDA'
                                                    })
        except Exception as e:
            logger.warning(f"从Drugs@FDA获取历史失败: {e}")
        
        # 按日期排序
        history.sort(key=lambda x: x['approval_date'])
        
        return history
    
    def save_to_database(self, drug_data: Dict) -> bool:
        """
        保存药物数据到数据库
        将英文和中文翻译合并存储，格式: "英文内容 | 中文翻译"
        
        Args:
            drug_data: 药物数据
            
        Returns:
            是否成功
        """
        try:
            # 定义数据库表存在的字段
            db_fields = [
                'regulatory_agency', 'drug_name_en', 'drug_name_cn', 
                'generic_name_en', 'generic_name_cn', 'brand_name_en', 'brand_name_cn',
                'applicant', 'application_number', 'approval_number', 'approval_date',
                'indication', 'dosage_form', 'route_of_administration', 
                'mechanism_of_action', 'companion_diagnosis', 'cd_target', 'cd_product',
                'clinical_trial_data', 'previous_approved_indications', 
                'previous_withdrawn_indications', 'previous_fda_approvals',
                'previous_nmpa_approvals', 'label_download_url', 'label_cloud_path',
                'detail_url', 'data_collection_time'
            ]
            
            # 过滤只保留数据库表存在的字段（排除临时字段）
            exclude_temp_fields = ['all_fda_submissions', 'approval_history']
            filtered_data = {
                k: v for k, v in drug_data.items() 
                if k in db_fields and k not in exclude_temp_fields
            }
            
            # 合并适应症英文和中文翻译
            indication = filtered_data.get('indication', '')
            indication_cn = drug_data.get('indication_cn', '')
            if indication and indication_cn and indication_cn != indication:
                filtered_data['indication'] = f"{indication} | 中文翻译: {indication_cn}"
            
            # 合并作用机制英文和中文翻译
            moa = filtered_data.get('mechanism_of_action', '')
            moa_cn = drug_data.get('mechanism_of_action_cn', '')
            if moa and moa_cn and moa_cn != moa:
                filtered_data['mechanism_of_action'] = f"{moa} | 中文翻译: {moa_cn}"
            
            # 确保必填字段有值
            if not filtered_data.get('indication'):
                filtered_data['indication'] = 'Antineoplastic Agent'
            
            # 检查是否已存在（基于监管机构+申请号+适应症）
            existing = self.db_manager.execute_query(
                "SELECT id FROM approved_drugs WHERE regulatory_agency = ? AND approval_number = ? AND indication = ?",
                (filtered_data['regulatory_agency'], filtered_data['approval_number'], filtered_data['indication'])
            )
            
            if existing:
                # 更新现有记录
                self.db_manager.execute_update(
                    'approved_drugs',
                    filtered_data,
                    "id = ?",
                    (existing[0]['id'],)
                )
                self.records_updated += 1
                logger.debug(f"更新药物记录: {filtered_data.get('drug_name_en', '')}")
            else:
                # 插入新记录
                self.db_manager.execute_insert('approved_drugs', filtered_data)
                self.records_added += 1
                logger.debug(f"添加药物记录: {filtered_data.get('drug_name_en', '')}")
            
            self.records_processed += 1
            return True
            
        except Exception as e:
            logger.error(f"保存药物数据失败: {e}")
            self.errors_count += 1
            return False
    
    def collect_full(self) -> Dict:
        """
        全量采集FDA已批准药物 - 改进版
        
        Returns:
            采集结果统计
        """
        logger.info("开始FDA已批准药物全量采集")
        
        start_time = datetime.now()
        
        # 重置统计
        self.records_processed = 0
        self.records_added = 0
        self.records_updated = 0
        self.errors_count = 0
        
        # 分批采集
        skip = 0
        total_results = 0
        
        max_records = 1000  # 大幅增加采集数量，获取更多药物
        
        while skip < max_records:
            # 获取数据
            data = self.fetch_drugsfda_data(skip=skip, limit=self.max_results)
            
            if not data:
                break
            
            # 获取总结果数
            total_results = data.get('meta', {}).get('results', {}).get('total', 0)
            
            logger.info(f"总记录数: {total_results}, 当前处理: {skip}")
            
            # 解析数据（内部已包含说明书获取和抗肿瘤判断）
            drugs = self.parse_drug_data(data)
            
            logger.info(f"本页解析到 {len(drugs)} 条抗肿瘤药物")
            
            # 处理每条药物记录
            for drug in drugs:
                # 获取所有FDA批准日期（从已保存的submissions）
                all_submissions = drug.get('all_fda_submissions', [])
                # 整理并排序所有批准日期
                approval_dates = []
                for subm in all_submissions:
                    if subm.get('status') in ('APPROVED', 'AP') and subm.get('date'):
                        approval_dates.append(subm.get('date'))
                # 去重并排序
                approval_dates = sorted(list(set(approval_dates)))
                
                # 翻译
                drug = self.translate_drug_data(drug)
                
                # 按适应症拆分（多适应症分行存储）
                split_drugs = self.split_by_indication(drug)
                
                # 改进的适应症日期匹配逻辑
                if len(split_drugs) > 1 and len(approval_dates) > 1:
                    # 有多个适应症和多个批准日期时，尝试智能分配
                    for i, split_drug in enumerate(split_drugs):
                        # 第一个适应症使用最早的批准日期
                        # 后续的适应症尝试使用之后的日期
                        if i < len(approval_dates):
                            split_drug['approval_date'] = approval_dates[i]
                            split_drug['previous_fda_approvals'] = f"多个批准日期可用，使用第{i+1}个日期: {approval_dates[i]}"
                        else:
                            # 没有足够日期，使用最后一个
                            split_drug['approval_date'] = approval_dates[-1]
                elif len(approval_dates) >= 1:
                    # 没有多个日期，全部使用同一个，但在备注中说明所有日期
                    date_note = f"所有日期: {', '.join(approval_dates)}"
                    for split_drug in split_drugs:
                        split_drug['previous_fda_approvals'] = date_note
                
                # 保存每条拆分后的记录
                for split_drug in split_drugs:
                    self.save_to_database(split_drug)
                
                # 添加延迟避免请求过快
                time.sleep(0.3)
            
            # 更新skip
            skip += self.max_results
            
            # 检查是否完成
            if skip >= total_results:
                break
            
            # 添加批次间延迟
            time.sleep(1)
        
        end_time = datetime.now()
        duration = (end_time - start_time).total_seconds()
        
        # 记录运行日志
        self.db_manager.log_system_action({
            'module_name': 'fda_approved',
            'action': 'full_collection',
            'status': 'success' if self.errors_count == 0 else 'partial_success',
            'message': f'FDA已批准药物全量采集完成',
            'records_processed': self.records_processed,
            'records_added': self.records_added,
            'records_updated': self.records_updated,
            'error_count': self.errors_count,
            'start_time': start_time.strftime('%Y-%m-%d %H:%M:%S'),
            'end_time': end_time.strftime('%Y-%m-%d %H:%M:%S'),
            'duration_seconds': duration
        })
        
        result = {
            'status': 'success',
            'total_results': total_results,
            'records_processed': self.records_processed,
            'records_added': self.records_added,
            'records_updated': self.records_updated,
            'errors_count': self.errors_count,
            'duration_seconds': duration
        }
        
        logger.info(f"FDA全量采集完成: {result}")
        
        return result
    
    def collect_incremental(self) -> Dict:
        """
        增量采集FDA已批准药物
        
        Returns:
            采集结果统计
        """
        logger.info("开始FDA已批准药物增量采集")
        
        start_time = datetime.now()
        
        # 获取最后采集时间
        last_collection_time = self.db_manager.get_last_collection_time('fda_approved')
        
        if last_collection_time:
            logger.info(f"上次采集时间: {last_collection_time}")
        else:
            logger.info("无上次采集记录，执行全量采集")
            return self.collect_full()
        
        # 重置统计
        self.records_processed = 0
        self.records_added = 0
        self.records_updated = 0
        self.errors_count = 0
        
        # 构建增量查询
        # 从上次采集时间开始
        
        # 分批采集
        skip = 0
        total_results = 0
        
        while True:
            # 获取数据（使用增量查询）
            data = self.fetch_drugsfda_data(skip=skip, limit=self.max_results)
            
            if not data:
                break
            
            total_results = data.get('meta', {}).get('results', {}).get('total', 0)
            
            if total_results == 0:
                logger.info("无新增数据")
                break
            
            # 解析和处理数据
            drugs = self.parse_drug_data(data)
            
            for drug in drugs:
                drug = self.enrich_with_label_data(drug)
                drug = self.translate_drug_data(drug)
                split_drugs = self.split_by_indication(drug)
                
                for split_drug in split_drugs:
                    self.save_to_database(split_drug)
                
                time.sleep(0.5)
            
            skip += self.max_results
            
            if skip >= total_results:
                break
            
            time.sleep(2)
        
        end_time = datetime.now()
        duration = (end_time - start_time).total_seconds()
        
        # 记录运行日志
        self.db_manager.log_system_action({
            'module_name': 'fda_approved',
            'action': 'incremental_collection',
            'status': 'success' if self.errors_count == 0 else 'partial_success',
            'message': f'FDA已批准药物增量采集完成',
            'records_processed': self.records_processed,
            'records_added': self.records_added,
            'records_updated': self.records_updated,
            'error_count': self.errors_count,
            'start_time': start_time.strftime('%Y-%m-%d %H:%M:%S'),
            'end_time': end_time.strftime('%Y-%m-%d %H:%M:%S'),
            'duration_seconds': duration
        })
        
        result = {
            'status': 'success',
            'total_results': total_results,
            'records_processed': self.records_processed,
            'records_added': self.records_added,
            'records_updated': self.records_updated,
            'errors_count': self.errors_count,
            'duration_seconds': duration
        }
        
        logger.info(f"FDA增量采集完成: {result}")
        
        return result
    
    def collect_nda(self) -> Dict:
        """
        采集FDA NDA申请数据
        
        Returns:
            采集结果统计
        """
        logger.info("开始FDA NDA申请采集")
        
        start_time = datetime.now()
        
        # 重置统计
        self.records_processed = 0
        self.records_added = 0
        self.records_updated = 0
        self.errors_count = 0
        
        # NDA申请使用drugsfda端点，筛选原始申请(ORIG)
        skip = 0
        total_results = 0
        
        max_records = 100  # 限制最大采集数量，避免超时
        
        try:
            while skip < max_records:
                # 构建NDA查询 - 筛选原始申请
                params = {
                    'search': 'submissions.submission_type:ORIG',
                    'skip': skip,
                    'limit': self.max_results
                }
                
                response = requests.get(self.api_url, params=params, timeout=60)
                response.raise_for_status()
                
                data = response.json()
                total_results = data.get('meta', {}).get('results', {}).get('total', 0)
                
                logger.info(f"NDA总记录数: {total_results}, 当前处理: {skip}")
                
                # 解析数据 - 不过滤抗肿瘤药物，保存所有NDA
                results = data.get('results', [])
                for result in results:
                    try:
                        products = result.get('products', [])
                        submissions = result.get('submissions', [])
                        sponsor_name = result.get('sponsor_name', '')
                        application_number = result.get('application_number', '')
                        
                        for product in products:
                            drug_data = self._parse_single_product(result, product)
                            if drug_data:
                                # 补充原始提交信息
                                drug_data['submissions'] = submissions
                                drug_data['sponsor_name'] = sponsor_name
                                drug_data['application_number'] = application_number
                                self.save_nda_to_database(drug_data)
                    except Exception as e:
                        logger.warning(f"解析NDA记录失败: {e}")
                
                skip += self.max_results
                
                if skip >= total_results or skip >= max_records:
                    break
                
                time.sleep(1)
        
        except Exception as e:
            logger.error(f"NDA采集失败: {e}")
            self.errors_count += 1
        
        end_time = datetime.now()
        duration = (end_time - start_time).total_seconds()
        
        # 记录日志
        self.db_manager.log_system_action({
            'module_name': 'fda_nda',
            'action': 'nda_collection',
            'status': 'success' if self.errors_count == 0 else 'partial_success',
            'message': 'FDA NDA申请采集完成',
            'records_processed': self.records_processed,
            'records_added': self.records_added,
            'records_updated': self.records_updated,
            'error_count': self.errors_count,
            'start_time': start_time.strftime('%Y-%m-%d %H:%M:%S'),
            'end_time': end_time.strftime('%Y-%m-%d %H:%M:%S'),
            'duration_seconds': duration
        })
        
        return {
            'status': 'success',
            'records_processed': self.records_processed,
            'records_added': self.records_added,
            'records_updated': self.records_updated,
            'errors_count': self.errors_count,
            'duration_seconds': duration,
            'message': f'FDA NDA申请采集完成，共处理 {self.records_processed} 条记录'
        }
    
    def save_nda_to_database(self, drug: Dict):
        """保存NDA申请数据到数据库"""
        try:
            # 提取NDA相关信息
            application_number = drug.get('application_number', '')
            if not application_number:
                return
            
            # 获取原始提交信息
            submissions = drug.get('submissions', [])
            orig_submission = None
            for sub in submissions:
                if sub.get('submission_type') == 'ORIG':
                    orig_submission = sub
                    break
            
            if not orig_submission:
                return
            
            # 获取产品信息
            products = drug.get('products', [])
            product = products[0] if products else {}
            
            # 获取通用名
            generic_name = product.get('generic_name', '')
            if not generic_name:
                active_ingredients = product.get('active_ingredients', [])
                generic_name = ', '.join([a.get('name', '') for a in active_ingredients])
            
            # 获取品牌名
            brand_name = product.get('brand_name', '')
            
            # 尝试从说明书获取更多信息
            indication = ''
            mechanism = ''
            try:
                label_data = self.fetch_label_data(application_number)
                if label_data:
                    indications = label_data.get('indications_and_usage', [])
                    if indications:
                        indication = indications[0] if isinstance(indications, list) else indications
                    mechanisms = label_data.get('mechanism_of_action', [])
                    if mechanisms:
                        mechanism = mechanisms[0] if isinstance(mechanisms, list) else mechanisms
            except:
                pass
            
            # 构建NDA记录
            nda_data = {
                'regulatory_agency': 'FDA',
                'nda_number': application_number,
                'nda_status': orig_submission.get('submission_status', ''),
                'nda_submission_date': orig_submission.get('submission_status_date', ''),
                'drug_name_en': brand_name,
                'drug_name_cn': '',  # 待翻译
                'generic_name_en': generic_name,
                'generic_name_cn': '',
                'applicant': drug.get('sponsor_name', ''),
                'indication': indication,
                'dosage_form': product.get('dosage_form', ''),
                'route_of_administration': product.get('route', ''),
                'mechanism_of_action': mechanism,
                'target_gene': '',
                'trial_phase': '',
                'expected_approval_date': None,
                'status_change_history': json.dumps(submissions, ensure_ascii=False)[:2000],
                'detail_url': f"https://www.accessdata.fda.gov/scripts/cder/daf/index.cfm?event=overview.process&varApplNo={application_number}",
                'data_collection_time': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                'created_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                'updated_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            }
            
            # 检查是否已存在
            existing = self.db_manager.execute_query(
                "SELECT id FROM nda_drugs WHERE nda_number = ?",
                (application_number,)
            )
            
            if existing:
                # 更新
                self.db_manager.execute_update(
                    'nda_drugs',
                    nda_data,
                    'nda_number = ?',
                    (application_number,)
                )
                self.records_updated += 1
            else:
                # 插入
                self.db_manager.execute_insert('nda_drugs', nda_data)
                self.records_added += 1
            
            self.records_processed += 1
            
        except Exception as e:
            logger.error(f"保存NDA数据失败: {e}")
            self.errors_count += 1
    
    def run(self, force_full: bool = False, mode: str = 'approved') -> Dict:
        """
        运行采集
        
        Args:
            force_full: 是否强制全量采集
            mode: 采集模式 ('approved' 或 'nda')
            
        Returns:
            采集结果
        """
        if mode == 'nda':
            return self.collect_nda()
        
        if force_full:
            return self.collect_full()
        else:
            # 检查是否有历史数据
            existing_count = self.db_manager.get_record_count('approved_drugs', 'regulatory_agency = ?', ('FDA',))
            
            if existing_count == 0:
                return self.collect_full()
            else:
                return self.collect_incremental()


def create_fda_collector(
    db_manager: DatabaseManager,
    config_manager: ConfigManager,
    translation_service: TranslationService
) -> FDADrugCollector:
    """
    创建FDA药物采集器实例
    
    Args:
        db_manager: 数据库管理器
        config_manager: 配置管理器
        translation_service: 翻译服务
        
    Returns:
        FDA药物采集器实例
    """
    proxy_config = config_manager.get_proxy_config()
    request_manager = RequestManager(proxy_config)
    
    return FDADrugCollector(
        db_manager=db_manager,
        config_manager=config_manager,
        translation_service=translation_service,
        request_manager=request_manager
    )


if __name__ == "__main__":
    # 测试FDA采集
    import sys
    logging.basicConfig(level=logging.INFO)
    
    # 初始化组件
    config_path = "config/config.yaml"
    db_path = "data/medical_info.db"
    
    config_manager = ConfigManager(config_path)
    db_manager = DatabaseManager(db_path)
    db_manager.init_tables()
    
    translation_config = config_manager.get_translation_config()
    translation_service = TranslationService(translation_config)
    
    # 创建采集器
    collector = create_fda_collector(db_manager, config_manager, translation_service)
    
    # 运行采集（测试模式，限制数量）
    print("开始FDA药物采集测试...")
    
    # 仅采集少量数据测试
    test_data = collector.fetch_drugsfda_data(skip=0, limit=10)
    
    if test_data:
        print(f"API响应成功，总记录数: {test_data.get('meta', {}).get('results', {}).get('total', 0)}")
        
        drugs = collector.parse_drug_data(test_data)
        print(f"解析到 {len(drugs)} 条药物记录")
        
        for drug in drugs[:3]:
            print(f"\n药物名称: {drug.get('drug_name_en')}")
            print(f"通用名: {drug.get('generic_name_en')}")
            print(f"适应症: {drug.get('indication', '')[:100]}...")
    
    db_manager.close()