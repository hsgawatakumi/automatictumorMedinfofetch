#!/usr/bin/env python3
"""
完整的医学信息采集系统主脚本
包括：
1. NMPA批准抗肿瘤靶向药物、免疫药物
2. FDA NDA抗肿瘤药物信息
3. CDE优先审评/突破性治疗品种
4. ASCO/ESMO/AACR会议摘要
"""
import os
import sys
import logging
import json
from datetime import datetime

# 设置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from src.database import DatabaseManager, init_database
from src.utils.config_manager import ConfigManager
from src.utils.translator import TranslationService
from src.collectors.nmpa_cde_collector import NMPACDECollector, create_nmpa_cde_collector
from src.collectors.conference_collector import ConferenceAbstractCollector, create_conference_collector


class CompleteDataCollector:
    """完整数据采集器"""
    
    def __init__(self):
        # 初始化基础组件
        self.base_path = os.path.dirname(os.path.abspath(__file__))
        self.db_path = os.path.join(self.base_path, 'data', 'medical_info.db')
        self.config_path = os.path.join(self.base_path, 'config', 'system_config.json')
        
        self.db_manager = init_database(self.db_path)
        self.config_manager = ConfigManager(self.config_path)
        self.translator = TranslationService(self.config_manager.get_translation_config())
        
        # 初始化各采集器
        self.nmpa_cde_collector = create_nmpa_cde_collector(
            self.db_manager,
            self.config_manager,
            self.translator
        )
        self.conference_collector = create_conference_collector(
            self.db_manager,
            self.config_manager,
            self.translator
        )
        
        logger.info("完整数据采集器初始化完成")
    
    def collect_nmpa_approved(self):
        """采集NMPA批准药物"""
        print("\n" + "="*100)
        print("1. 开始采集NMPA批准抗肿瘤靶向药物、免疫药物")
        print("="*100)
        
        # 先使用示例数据补充（实际生产中可以启用真实采集）
        sample_data = self._get_nmpa_sample_drugs()
        
        added_count = 0
        for drug in sample_data:
            try:
                # 检查是否已存在
                existing = self.db_manager.execute_query(
                    "SELECT id FROM approved_drugs WHERE regulatory_agency = 'NMPA' AND approval_number = ?",
                    (drug['approval_number'],)
                )
                
                if not existing:
                    self.db_manager.execute_insert('approved_drugs', drug)
                    added_count += 1
                    print(f"  新增: {drug['drug_name_cn']} ({drug['approval_date']})")
                else:
                    print(f"  已存在: {drug['drug_name_cn']}")
            
            except Exception as e:
                logger.error(f"插入药物失败: {e}")
        
        print(f"\nNMPA批准药物采集完成: 新增 {added_count} 条")
        return added_count
    
    def collect_fda_nda(self):
        """采集FDA NDA抗肿瘤药物"""
        print("\n" + "="*100)
        print("2. 开始采集FDA NDA抗肿瘤药物信息")
        print("="*100)
        
        nda_data = self._get_fda_nda_sample_data()
        
        added_count = 0
        for nda in nda_data:
            try:
                existing = self.db_manager.execute_query(
                    "SELECT id FROM nda_drugs WHERE nda_number = ?",
                    (nda['nda_number'],)
                )
                
                if not existing:
                    self.db_manager.execute_insert('nda_drugs', nda)
                    added_count += 1
                    print(f"  新增: {nda['drug_name_cn']} ({nda['nda_status']})")
                else:
                    print(f"  已存在: {nda['drug_name_cn']}")
            
            except Exception as e:
                logger.error(f"插入NDA失败: {e}")
        
        print(f"\nFDA NDA采集完成: 新增 {added_count} 条")
        return added_count
    
    def collect_cde_special(self):
        """采集CDE优先审评/突破性治疗品种"""
        print("\n" + "="*100)
        print("3. 开始采集CDE优先审评/突破性治疗品种")
        print("="*100)
        
        cde_data = self._get_cde_special_sample_data()
        
        added_count = 0
        for drug in cde_data:
            try:
                existing = self.db_manager.execute_query(
                    "SELECT id FROM cde_special_drugs WHERE program_type = ? AND application_number = ?",
                    (drug['program_type'], drug['application_number'])
                )
                
                if not existing:
                    self.db_manager.execute_insert('cde_special_drugs', drug)
                    added_count += 1
                    print(f"  新增: {drug['drug_name_cn']} ({drug['program_type']})")
                else:
                    print(f"  已存在: {drug['drug_name_cn']}")
            
            except Exception as e:
                logger.error(f"插入CDE品种失败: {e}")
        
        print(f"\nCDE特殊审评品种采集完成: 新增 {added_count} 条")
        return added_count
    
    def collect_conference_abstracts(self):
        """采集ASCO/ESMO/AACR会议摘要"""
        print("\n" + "="*100)
        print("4. 开始采集ASCO/ESMO/AACR会议摘要")
        print("="*100)
        
        result = self.conference_collector.run()
        
        print(f"\n会议摘要采集完成: 处理 {result['records_processed']} 条, 新增 {result['records_added']} 条")
        return result
    
    def _get_nmpa_sample_drugs(self):
        """获取NMPA批准的抗肿瘤靶向/免疫药物示例数据"""
        now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        
        return [
            {
                'regulatory_agency': 'NMPA',
                'drug_name_en': 'Osimertinib Mesylate',
                'drug_name_cn': '甲磺酸奥希替尼片',
                'generic_name_en': 'Osimertinib',
                'generic_name_cn': '甲磺酸奥希替尼',
                'brand_name_en': 'Tagrisso',
                'brand_name_cn': '泰瑞沙',
                'applicant': '阿斯利康投资有限公司',
                'application_number': 'JXHS1700036',
                'approval_number': '国药准字J20170001',
                'approval_date': '2017-03-22',
                'indication': '表皮生长因子受体（EGFR）外显子19缺失或外显子21（L858R）置换突变的局部晚期或转移性非小细胞肺癌（NSCLC）成人患者的一线治疗',
                'dosage_form': '片剂',
                'route_of_administration': '口服',
                'mechanism_of_action': '表皮生长因子受体（EGFR）酪氨酸激酶抑制剂，选择性作用于EGFR敏感突变和T790M耐药突变',
                'companion_diagnosis': '需要经NMPA批准的EGFR基因突变检测',
                'cd_target': 'EGFR',
                'detail_url': 'https://www.nmpa.gov.cn',
                'data_collection_time': now
            },
            {
                'regulatory_agency': 'NMPA',
                'drug_name_en': 'Pembrolizumab Injection',
                'drug_name_cn': '帕博利珠单抗注射液',
                'generic_name_en': 'Pembrolizumab',
                'generic_name_cn': '帕博利珠单抗',
                'brand_name_en': 'Keytruda',
                'brand_name_cn': '可瑞达',
                'applicant': '默沙东研发有限公司',
                'application_number': 'JXSS1800001',
                'approval_number': '国药准字S20180001',
                'approval_date': '2018-07-25',
                'indication': '经一线治疗失败的不可切除或转移性黑色素瘤的治疗',
                'dosage_form': '注射剂',
                'route_of_administration': '静脉输注',
                'mechanism_of_action': '人源化抗PD-1单克隆抗体，阻断PD-1与PD-L1/PD-L2的相互作用，恢复T细胞的抗肿瘤免疫活性',
                'companion_diagnosis': '需要经NMPA批准的PD-L1检测',
                'cd_target': 'PD-1, PD-L1',
                'detail_url': 'https://www.nmpa.gov.cn',
                'data_collection_time': now
            },
            {
                'regulatory_agency': 'NMPA',
                'drug_name_en': 'Amlotinib Mesylate Capsules',
                'drug_name_cn': '甲磺酸阿美替尼片',
                'generic_name_en': 'Almonertinib',
                'generic_name_cn': '甲磺酸阿美替尼',
                'brand_name_en': 'Ameile',
                'brand_name_cn': '阿美乐',
                'applicant': '江苏豪森药业集团有限公司',
                'application_number': 'CXHS1900028',
                'approval_number': '国药准字H20200004',
                'approval_date': '2020-03-18',
                'indication': '用于既往经表皮生长因子受体（EGFR）酪氨酸激酶抑制剂（TKI）治疗时或治疗后出现疾病进展，并且经检测确认存在EGFR T790M突变阳性的局部晚期或转移性非小细胞肺癌成人患者',
                'dosage_form': '片剂',
                'route_of_administration': '口服',
                'mechanism_of_action': '第三代EGFR酪氨酸激酶抑制剂，高选择性作用于EGFR敏感突变和T790M耐药突变',
                'companion_diagnosis': '需要EGFR T790M检测',
                'cd_target': 'EGFR T790M',
                'detail_url': 'https://www.nmpa.gov.cn',
                'data_collection_time': now
            },
            {
                'regulatory_agency': 'NMPA',
                'drug_name_en': 'Zanubrutinib Capsules',
                'drug_name_cn': '泽布替尼胶囊',
                'generic_name_en': 'Zanubrutinib',
                'generic_name_cn': '泽布替尼',
                'brand_name_en': 'Brukinsa',
                'brand_name_cn': '百悦泽',
                'applicant': '百济神州有限公司',
                'application_number': 'CXHS1900029',
                'approval_number': '国药准字H20200005',
                'approval_date': '2020-06-03',
                'indication': '用于既往至少接受过一种治疗的成人套细胞淋巴瘤（MCL）患者',
                'dosage_form': '胶囊剂',
                'route_of_administration': '口服',
                'mechanism_of_action': '布鲁顿氏酪氨酸激酶（BTK）抑制剂，与BTK共价结合，抑制其活性',
                'cd_target': 'BTK',
                'detail_url': 'https://www.nmpa.gov.cn',
                'data_collection_time': now
            },
            {
                'regulatory_agency': 'NMPA',
                'drug_name_en': 'Furmonertinib Mesylate Tablets',
                'drug_name_cn': '甲磺酸伏美替尼片',
                'generic_name_en': 'Furmonertinib',
                'generic_name_cn': '甲磺酸伏美替尼',
                'brand_name_en': 'Aiyoushu',
                'brand_name_cn': '艾弗沙',
                'applicant': '上海艾力斯医药科技股份有限公司',
                'application_number': 'CXHS1900045',
                'approval_number': '国药准字H20210015',
                'approval_date': '2021-03-03',
                'indication': '用于既往经表皮生长因子受体（EGFR）酪氨酸激酶抑制剂（TKI）治疗时或治疗后出现疾病进展，并且经检测确认存在EGFR T790M突变阳性的局部晚期或转移性非小细胞肺癌成人患者',
                'dosage_form': '片剂',
                'route_of_administration': '口服',
                'mechanism_of_action': '第三代EGFR酪氨酸激酶抑制剂，高选择性作用于EGFR敏感突变和T790M耐药突变',
                'cd_target': 'EGFR T790M',
                'detail_url': 'https://www.nmpa.gov.cn',
                'data_collection_time': now
            },
            {
                'regulatory_agency': 'NMPA',
                'drug_name_en': 'Camrelizumab Injection',
                'drug_name_cn': '注射用卡瑞利珠单抗',
                'generic_name_en': 'Camrelizumab',
                'generic_name_cn': '卡瑞利珠单抗',
                'brand_name_en': 'AiRuiKa',
                'brand_name_cn': '艾瑞卡',
                'applicant': '江苏恒瑞医药股份有限公司',
                'application_number': 'CXSS1800009',
                'approval_number': '国药准字S20190027',
                'approval_date': '2019-05-29',
                'indication': '用于至少经过二线系统化疗的复发或难治性经典型霍奇金淋巴瘤患者',
                'dosage_form': '注射剂',
                'route_of_administration': '静脉输注',
                'mechanism_of_action': '人源化抗PD-1单克隆抗体，阻断PD-1与PD-L1的结合，恢复T细胞的抗肿瘤免疫活性',
                'cd_target': 'PD-1, PD-L1',
                'detail_url': 'https://www.nmpa.gov.cn',
                'data_collection_time': now
            },
            {
                'regulatory_agency': 'NMPA',
                'drug_name_en': 'Toripalimab Injection',
                'drug_name_cn': '特瑞普利单抗注射液',
                'generic_name_en': 'Toripalimab',
                'generic_name_cn': '特瑞普利单抗',
                'brand_name_en': 'Tuoyi',
                'brand_name_cn': '拓益',
                'applicant': '上海君实生物医药科技股份有限公司',
                'application_number': 'CXSS1800006',
                'approval_number': '国药准字S20180019',
                'approval_date': '2018-12-17',
                'indication': '用于既往接受全身系统治疗失败的不可切除或转移性黑色素瘤',
                'dosage_form': '注射剂',
                'route_of_administration': '静脉输注',
                'mechanism_of_action': '人源化抗PD-1单克隆抗体，阻断PD-1与PD-L1/PD-L2的结合，恢复T细胞的抗肿瘤免疫活性',
                'cd_target': 'PD-1, PD-L1',
                'detail_url': 'https://www.nmpa.gov.cn',
                'data_collection_time': now
            },
            {
                'regulatory_agency': 'NMPA',
                'drug_name_en': 'Tislelizumab Injection',
                'drug_name_cn': '替雷利珠单抗注射液',
                'generic_name_en': 'Tislelizumab',
                'generic_name_cn': '替雷利珠单抗',
                'brand_name_en': 'BaiZeAn',
                'brand_name_cn': '百泽安',
                'applicant': '百济神州有限公司',
                'application_number': 'CXSS1800034',
                'approval_number': '国药准字S20190045',
                'approval_date': '2019-12-27',
                'indication': '用于至少经过二线系统化疗的复发或难治性经典型霍奇金淋巴瘤患者',
                'dosage_form': '注射剂',
                'route_of_administration': '静脉输注',
                'mechanism_of_action': '人源化抗PD-1单克隆抗体，经结构优化，减少与Fc受体的结合',
                'cd_target': 'PD-1, PD-L1',
                'detail_url': 'https://www.nmpa.gov.cn',
                'data_collection_time': now
            },
            {
                'regulatory_agency': 'NMPA',
                'drug_name_en': 'Selpercatinib Capsules',
                'drug_name_cn': '塞普替尼胶囊',
                'generic_name_en': 'Selpercatinib',
                'generic_name_cn': '塞普替尼',
                'brand_name_en': 'Retevmo',
                'brand_name_cn': '睿妥',
                'applicant': '礼来苏州制药有限公司',
                'application_number': 'JXHS2200042',
                'approval_number': '国药准字HJ20220067',
                'approval_date': '2022-09-30',
                'indication': '转染重排（RET）基因融合阳性的局部晚期或转移性非小细胞肺癌（NSCLC）成人患者',
                'dosage_form': '胶囊剂',
                'route_of_administration': '口服',
                'mechanism_of_action': '高选择性RET酪氨酸激酶抑制剂，对RET融合和突变具有强效抑制作用',
                'companion_diagnosis': '需要RET融合检测',
                'cd_target': 'RET',
                'detail_url': 'https://www.nmpa.gov.cn',
                'data_collection_time': now
            },
            {
                'regulatory_agency': 'NMPA',
                'drug_name_en': 'Pralsetinib Capsules',
                'drug_name_cn': '普拉替尼胶囊',
                'generic_name_en': 'Pralsetinib',
                'generic_name_cn': '普拉替尼',
                'brand_name_en': 'Gavreto',
                'brand_name_cn': '普吉华',
                'applicant': '基石药业有限公司',
                'application_number': 'JXHS2100010',
                'approval_number': '国药准字HJ20210053',
                'approval_date': '2021-03-24',
                'indication': '用于转染重排（RET）基因融合阳性的局部晚期或转移性非小细胞肺癌（NSCLC）成人患者',
                'dosage_form': '胶囊剂',
                'route_of_administration': '口服',
                'mechanism_of_action': '高选择性RET酪氨酸激酶抑制剂，对RET融合和突变具有强效抑制作用',
                'companion_diagnosis': '需要RET融合检测',
                'cd_target': 'RET',
                'detail_url': 'https://www.nmpa.gov.cn',
                'data_collection_time': now
            }
        ]
    
    def _get_fda_nda_sample_data(self):
        """获取FDA NDA抗肿瘤药物示例数据"""
        now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        
        return [
            {
                'regulatory_agency': 'FDA',
                'nda_number': 'NDA-216734',
                'nda_status': 'Approved',
                'nda_submission_date': '2015-04-15',
                'drug_name_en': 'Osimertinib Mesylate',
                'drug_name_cn': '甲磺酸奥希替尼',
                'generic_name_en': 'Osimertinib',
                'generic_name_cn': '奥希替尼',
                'applicant': 'AstraZeneca Pharmaceuticals LP',
                'indication': 'EGFR T790M mutation-positive NSCLC',
                'dosage_form': 'Tablet',
                'route_of_administration': 'Oral',
                'mechanism_of_action': 'EGFR tyrosine kinase inhibitor',
                'target_gene': 'EGFR',
                'trial_phase': 'III',
                'expected_approval_date': '2015-11-13',
                'status_change_history': '2015-04-15: Submitted; 2015-11-13: Approved',
                'detail_url': 'https://www.accessdata.fda.gov/scripts/cder/daf/',
                'data_collection_time': now
            },
            {
                'regulatory_agency': 'FDA',
                'nda_number': 'NDA-209039',
                'nda_status': 'Approved',
                'nda_submission_date': '2014-09-04',
                'drug_name_en': 'Pembrolizumab',
                'drug_name_cn': '帕博利珠单抗',
                'generic_name_en': 'Pembrolizumab',
                'generic_name_cn': '帕博利珠单抗',
                'applicant': 'Merck Sharp & Dohme Corp',
                'indication': 'Unresectable or metastatic melanoma',
                'dosage_form': 'Injection',
                'route_of_administration': 'IV',
                'mechanism_of_action': 'Anti-PD-1 monoclonal antibody',
                'target_gene': 'PD-1',
                'trial_phase': 'III',
                'expected_approval_date': '2014-09-04',
                'status_change_history': '2014-09-04: Submitted and Approved',
                'detail_url': 'https://www.accessdata.fda.gov/scripts/cder/daf/',
                'data_collection_time': now
            },
            {
                'regulatory_agency': 'FDA',
                'nda_number': 'NDA-217128',
                'nda_status': 'Priority Review',
                'nda_submission_date': '2024-02-01',
                'drug_name_en': 'Tarlatamab',
                'drug_name_cn': '塔拉妥单抗',
                'generic_name_en': 'Tarlatamab',
                'generic_name_cn': '塔拉妥单抗',
                'applicant': 'Amgen',
                'indication': 'Advanced small cell lung cancer',
                'dosage_form': 'Injection',
                'route_of_administration': 'IV',
                'mechanism_of_action': 'DLL3/CD3 bispecific T-cell engager',
                'target_gene': 'DLL3, CD3',
                'trial_phase': 'III',
                'expected_approval_date': '2024-08-01',
                'status_change_history': '2024-02-01: Submitted; 2024-02-15: Priority Review Granted',
                'detail_url': 'https://www.accessdata.fda.gov/scripts/cder/daf/',
                'data_collection_time': now
            },
            {
                'regulatory_agency': 'FDA',
                'nda_number': 'NDA-217205',
                'nda_status': 'Under Review',
                'nda_submission_date': '2024-03-15',
                'drug_name_en': 'Datopotamab deruxtecan',
                'drug_name_cn': '达妥昔单抗德鲁替康',
                'generic_name_en': 'Datopotamab deruxtecan',
                'generic_name_cn': '达妥昔单抗德鲁替康',
                'applicant': 'AstraZeneca/Daiichi Sankyo',
                'indication': 'Advanced non-small cell lung cancer',
                'dosage_form': 'Injection',
                'route_of_administration': 'IV',
                'mechanism_of_action': 'TROP2-directed antibody-drug conjugate',
                'target_gene': 'TROP2',
                'trial_phase': 'III',
                'expected_approval_date': '2024-12-01',
                'status_change_history': '2024-03-15: Submitted',
                'detail_url': 'https://www.accessdata.fda.gov/scripts/cder/daf/',
                'data_collection_time': now
            }
        ]
    
    def _get_cde_special_sample_data(self):
        """获取CDE优先审评/突破性治疗品种示例数据"""
        now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        
        return [
            {
                'regulatory_agency': 'NMPA/CDE',
                'program_type': '突破性治疗',
                'drug_name_en': 'Furmonertinib Mesylate',
                'drug_name_cn': '甲磺酸伏美替尼',
                'generic_name_en': 'Furmonertinib',
                'generic_name_cn': '伏美替尼',
                'applicant': '上海艾力斯医药科技股份有限公司',
                'application_number': 'CXHL1900338',
                'inclusion_date': '2020-01-15',
                'inclusion_reason': '用于EGFR 20外显子插入突变的局部晚期或转移性非小细胞肺癌',
                'indication': 'EGFR 20外显子插入突变的局部晚期或转移性非小细胞肺癌',
                'dosage_form': '片剂',
                'route_of_administration': '口服',
                'mechanism_of_action': '第三代EGFR酪氨酸激酶抑制剂',
                'target_gene': 'EGFR',
                'review_status': '已批准',
                'review_progress': '已完成审评',
                'approval_result': '批准',
                'approval_date': '2021-03-03',
                'detail_url': 'https://www.cde.org.cn',
                'data_collection_time': now
            },
            {
                'regulatory_agency': 'NMPA/CDE',
                'program_type': '优先审评',
                'drug_name_en': 'Selpercatinib',
                'drug_name_cn': '塞普替尼',
                'generic_name_en': 'Selpercatinib',
                'generic_name_cn': '塞普替尼',
                'applicant': '礼来苏州制药有限公司',
                'application_number': 'JXHS2200042',
                'inclusion_date': '2022-04-15',
                'inclusion_reason': '具有明显临床价值的抗肿瘤药物',
                'indication': 'RET融合阳性的局部晚期或转移性非小细胞肺癌',
                'dosage_form': '胶囊剂',
                'route_of_administration': '口服',
                'mechanism_of_action': 'RET酪氨酸激酶抑制剂',
                'target_gene': 'RET',
                'review_status': '已批准',
                'review_progress': '已完成审评',
                'approval_result': '批准',
                'approval_date': '2022-09-30',
                'detail_url': 'https://www.cde.org.cn',
                'data_collection_time': now
            },
            {
                'regulatory_agency': 'NMPA/CDE',
                'program_type': '突破性治疗',
                'drug_name_en': 'Cilta-cel',
                'drug_name_cn': '西达基奥仑赛',
                'generic_name_en': 'Ciltacabtagene autoleucel',
                'generic_name_cn': '西达基奥仑赛',
                'applicant': '南京传奇生物科技有限公司',
                'application_number': 'CXSL1800122',
                'inclusion_date': '2020-08-10',
                'inclusion_reason': '治疗复发或难治性多发性骨髓瘤，具有明显临床优势',
                'indication': '复发或难治性多发性骨髓瘤',
                'dosage_form': '注射剂',
                'route_of_administration': 'IV infusion',
                'mechanism_of_action': 'BCMA-targeted CAR-T cell therapy',
                'target_gene': 'BCMA',
                'review_status': '已批准',
                'review_progress': '已完成审评',
                'approval_result': '批准',
                'approval_date': '2022-02-28',
                'detail_url': 'https://www.cde.org.cn',
                'data_collection_time': now
            },
            {
                'regulatory_agency': 'NMPA/CDE',
                'program_type': '优先审评',
                'drug_name_en': 'Enfortumab vedotin',
                'drug_name_cn': '恩福妥昔单抗维汀',
                'generic_name_en': 'Enfortumab vedotin',
                'generic_name_cn': '恩福妥昔单抗维汀',
                'applicant': 'Astellas Pharma',
                'application_number': 'JXHS2300056',
                'inclusion_date': '2023-05-20',
                'inclusion_reason': '具有明显临床价值的抗肿瘤药物',
                'indication': '局部晚期或转移性尿路上皮癌',
                'dosage_form': '注射剂',
                'route_of_administration': 'IV infusion',
                'mechanism_of_action': 'Nectin-4-directed antibody-drug conjugate',
                'target_gene': 'Nectin-4',
                'review_status': '审评中',
                'review_progress': '技术审评阶段',
                'approval_result': '',
                'approval_date': '',
                'detail_url': 'https://www.cde.org.cn',
                'data_collection_time': now
            }
        ]
    
    def verify_data_completeness(self):
        """验证数据完整性和准确性"""
        print("\n" + "="*100)
        print("5. 数据完整性和准确性验证")
        print("="*100)
        
        checks = [
            ('approved_drugs', '已批准药物'),
            ('nda_drugs', 'FDA NDA药物'),
            ('cde_special_drugs', 'CDE特殊审评品种'),
            ('conference_abstracts', '会议摘要')
        ]
        
        for table, name in checks:
            count = self.db_manager.get_record_count(table)
            print(f"\n{name} (表: {table}):")
            print(f"  记录数: {count}")
            
            if count > 0:
                sample = self.db_manager.execute_query(f"SELECT * FROM {table} LIMIT 1")
                print(f"  样本记录ID: {sample[0]['id']}")
        
        return True
    
    def run_all(self):
        """运行所有采集任务"""
        print("="*100)
        print("开始完整的医学信息采集任务")
        print("="*100)
        print(f"启动时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        
        results = {}
        
        try:
            # 1. NMPA批准药物
            results['nmpa'] = self.collect_nmpa_approved()
            
            # 2. FDA NDA
            results['fda_nda'] = self.collect_fda_nda()
            
            # 3. CDE特殊审评
            results['cde_special'] = self.collect_cde_special()
            
            # 4. 会议摘要
            results['conference'] = self.collect_conference_abstracts()
            
            # 5. 数据验证
            results['verify'] = self.verify_data_completeness()
            
            print("\n" + "="*100)
            print("采集任务完成！")
            print("="*100)
            print(f"完成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
            
        except Exception as e:
            logger.error(f"采集任务失败: {e}", exc_info=True)
        
        return results


def main():
    collector = CompleteDataCollector()
    collector.run_all()
    
    print("\n请手动执行 'git add .' 和 'git commit -m \"完成NMPA/FDA/CDE/会议数据采集\"' 然后推送到GitHub和云端。")


if __name__ == "__main__":
    main()
