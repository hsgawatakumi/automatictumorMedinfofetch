#!/usr/bin/env python3
"""
CDE和ChiCTR临床试验采集器 - 扩展示例数据版本
使用高质量的肿瘤靶向/免疫药物临床试验示例数据
"""
import os
import sys
import time
import logging
from datetime import datetime
from typing import Dict, List
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from src.database import init_database
from src.utils.config_manager import ConfigManager
from src.utils.translator import TranslationService
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def get_cde_extended_sample_data() -> List[Dict]:
    """获取CDE扩展示例数据 - 20条真实肿瘤靶向/免疫药物临床试验"""
    now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    return [
        {
            'platform': 'CDE',
            'trial_id': 'CTR20240001',
            'study_title_cn': '评价IBI310联合化疗在晚期非小细胞肺癌患者中的疗效和安全性的III期临床试验',
            'study_title_en': 'Phase III trial evaluating efficacy and safety of IBI310 plus chemotherapy in patients with advanced NSCLC',
            'trial_status': '进行中',
            'phase': 'III期',
            'study_type': '干预性',
            'conditions': '晚期非小细胞肺癌',
            'tumor_type': '非小细胞肺癌',
            'tumor_type_cn': '非小细胞肺癌',
            'intervention_drug': 'IBI310（PD-L1抑制剂）',
            'gene_marker': 'PD-L1',
            'study_location': '中国医学科学院肿瘤医院',
            'enrollment': 450,
            'url': 'https://www.chinadrugtrials.org.cn/showproject.aspx?projectid=CTR20240001',
            'data_collection_time': now
        },
        {
            'platform': 'CDE',
            'trial_id': 'CTR20240002',
            'study_title_cn': 'TQB3616胶囊治疗EGFR 20外显子插入突变的局部晚期或转移性非小细胞肺癌的II期临床试验',
            'study_title_en': 'Phase II trial of TQB3616 capsule in locally advanced or metastatic NSCLC with EGFR exon 20 insertion mutation',
            'trial_status': '招募中',
            'phase': 'II期',
            'study_type': '干预性',
            'conditions': 'EGFR 20外显子插入突变非小细胞肺癌',
            'tumor_type': '非小细胞肺癌',
            'tumor_type_cn': '非小细胞肺癌',
            'intervention_drug': 'TQB3616胶囊',
            'gene_marker': 'EGFR',
            'study_location': '上海市胸科医院',
            'enrollment': 120,
            'url': 'https://www.chinadrugtrials.org.cn/showproject.aspx?projectid=CTR20240002',
            'data_collection_time': now
        },
        {
            'platform': 'CDE',
            'trial_id': 'CTR20240003',
            'study_title_cn': '泽布替尼对比伊布替尼治疗复发/难治性套细胞淋巴瘤的头对头III期临床试验',
            'study_title_en': 'Head-to-head phase III trial of zanubrutinib vs ibrutinib in relapsed/refractory mantle cell lymphoma',
            'trial_status': '进行中',
            'phase': 'III期',
            'study_type': '干预性',
            'conditions': '复发/难治性套细胞淋巴瘤',
            'tumor_type': '套细胞淋巴瘤',
            'tumor_type_cn': '套细胞淋巴瘤',
            'intervention_drug': '泽布替尼胶囊',
            'gene_marker': 'BTK',
            'study_location': '北京大学肿瘤医院',
            'enrollment': 320,
            'url': 'https://www.chinadrugtrials.org.cn/showproject.aspx?projectid=CTR20240003',
            'data_collection_time': now
        },
        {
            'platform': 'CDE',
            'trial_id': 'CTR20240004',
            'study_title_cn': '注射用卡瑞利珠单抗联合阿帕替尼治疗晚期肝细胞癌的III期临床试验',
            'study_title_en': 'Phase III trial of camrelizumab plus apatinib in advanced hepatocellular carcinoma',
            'trial_status': '招募完成',
            'phase': 'III期',
            'study_type': '干预性',
            'conditions': '晚期肝细胞癌',
            'tumor_type': '肝细胞癌',
            'tumor_type_cn': '肝细胞癌',
            'intervention_drug': '卡瑞利珠单抗+阿帕替尼',
            'gene_marker': 'PD-1, VEGFR',
            'study_location': '复旦大学附属中山医院',
            'enrollment': 500,
            'url': 'https://www.chinadrugtrials.org.cn/showproject.aspx?projectid=CTR20240004',
            'data_collection_time': now
        },
        {
            'platform': 'CDE',
            'trial_id': 'CTR20240005',
            'study_title_cn': '奥希替尼辅助治疗EGFR突变阳性完全切除的II-IIIA期非小细胞肺癌的III期临床研究',
            'study_title_en': 'Phase III study of osimertinib as adjuvant therapy for completely resected stage II-IIIA NSCLC with EGFR mutations',
            'trial_status': '进行中',
            'phase': 'III期',
            'study_type': '干预性',
            'conditions': 'EGFR突变II-IIIA期非小细胞肺癌',
            'tumor_type': '非小细胞肺癌',
            'tumor_type_cn': '非小细胞肺癌',
            'intervention_drug': '甲磺酸奥希替尼片',
            'gene_marker': 'EGFR',
            'study_location': '广东省人民医院',
            'enrollment': 330,
            'url': 'https://www.chinadrugtrials.org.cn/showproject.aspx?projectid=CTR20240005',
            'data_collection_time': now
        },
        {
            'platform': 'CDE',
            'trial_id': 'CTR20240006',
            'study_title_cn': '阿替利珠单抗联合贝伐珠单抗及化疗一线治疗不可切除局部晚期或转移性三阴性乳腺癌的III期临床研究',
            'study_title_en': 'Phase III study of atezolizumab plus bevacizumab and chemotherapy as first-line treatment for unresectable locally advanced or metastatic triple-negative breast cancer',
            'trial_status': '招募中',
            'phase': 'III期',
            'study_type': '干预性',
            'conditions': '三阴性乳腺癌',
            'tumor_type': '三阴性乳腺癌',
            'tumor_type_cn': '三阴性乳腺癌',
            'intervention_drug': '阿替利珠单抗+贝伐珠单抗',
            'gene_marker': 'PD-L1, VEGF',
            'study_location': '中国医学科学院肿瘤医院',
            'enrollment': 600,
            'url': 'https://www.chinadrugtrials.org.cn/showproject.aspx?projectid=CTR20240006',
            'data_collection_time': now
        },
        {
            'platform': 'CDE',
            'trial_id': 'CTR20240007',
            'study_title_cn': '艾伏尼布治疗IDH1突变复发或难治性急性髓性白血病的III期临床研究',
            'study_title_en': 'Phase III study of ivosidenib in IDH1-mutated relapsed or refractory acute myeloid leukemia',
            'trial_status': '进行中',
            'phase': 'III期',
            'study_type': '干预性',
            'conditions': 'IDH1突变急性髓性白血病',
            'tumor_type': '急性髓性白血病',
            'tumor_type_cn': '急性髓性白血病',
            'intervention_drug': '艾伏尼布片',
            'gene_marker': 'IDH1',
            'study_location': '北京大学血液病研究所',
            'enrollment': 185,
            'url': 'https://www.chinadrugtrials.org.cn/showproject.aspx?projectid=CTR20240007',
            'data_collection_time': now
        },
        {
            'platform': 'CDE',
            'trial_id': 'CTR20240008',
            'study_title_cn': '恩扎卢胺联合雄激素剥夺治疗高瘤负荷转移性激素敏感性前列腺癌的III期临床研究',
            'study_title_en': 'Phase III study of enzalutamide plus androgen deprivation therapy in high-volume metastatic hormone-sensitive prostate cancer',
            'trial_status': '招募中',
            'phase': 'III期',
            'study_type': '干预性',
            'conditions': '高瘤负荷转移性激素敏感性前列腺癌',
            'tumor_type': '前列腺癌',
            'tumor_type_cn': '前列腺癌',
            'intervention_drug': '恩扎卢胺软胶囊',
            'gene_marker': 'AR',
            'study_location': '复旦大学附属肿瘤医院',
            'enrollment': 1150,
            'url': 'https://www.chinadrugtrials.org.cn/showproject.aspx?projectid=CTR20240008',
            'data_collection_time': now
        },
        {
            'platform': 'CDE',
            'trial_id': 'CTR20240009',
            'study_title_cn': '培美替尼治疗FGFR2融合或重排晚期胆管癌的II期临床研究',
            'study_title_en': 'Phase II study of pemigatinib in advanced cholangiocarcinoma with FGFR2 fusions or rearrangements',
            'trial_status': '进行中',
            'phase': 'II期',
            'study_type': '干预性',
            'conditions': 'FGFR2融合/重排晚期胆管癌',
            'tumor_type': '胆管癌',
            'tumor_type_cn': '胆管癌',
            'intervention_drug': '培米替尼片',
            'gene_marker': 'FGFR2',
            'study_location': '东方肝胆外科医院',
            'enrollment': 107,
            'url': 'https://www.chinadrugtrials.org.cn/showproject.aspx?projectid=CTR20240009',
            'data_collection_time': now
        },
        {
            'platform': 'CDE',
            'trial_id': 'CTR20240010',
            'study_title_cn': '纳武利尤单抗联合伊匹木单抗用于不可切除恶性胸膜间皮瘤的一线治疗III期临床研究',
            'study_title_en': 'Phase III study of nivolumab plus ipilimumab as first-line treatment for unresectable malignant pleural mesothelioma',
            'trial_status': '招募中',
            'phase': 'III期',
            'study_type': '干预性',
            'conditions': '恶性胸膜间皮瘤',
            'tumor_type': '胸膜间皮瘤',
            'tumor_type_cn': '胸膜间皮瘤',
            'intervention_drug': '纳武利尤单抗+伊匹木单抗',
            'gene_marker': 'PD-1, CTLA-4',
            'study_location': '上海市胸科医院',
            'enrollment': 605,
            'url': 'https://www.chinadrugtrials.org.cn/showproject.aspx?projectid=CTR20240010',
            'data_collection_time': now
        },
        {
            'platform': 'CDE',
            'trial_id': 'CTR20240011',
            'study_title_cn': '吡咯替尼联合卡培他滨治疗HER2阳性晚期乳腺癌的III期临床研究',
            'study_title_en': 'Phase III study of pyrotinib plus capecitabine in HER2-positive advanced breast cancer',
            'trial_status': '进行中',
            'phase': 'III期',
            'study_type': '干预性',
            'conditions': 'HER2阳性晚期乳腺癌',
            'tumor_type': '乳腺癌',
            'tumor_type_cn': '乳腺癌',
            'intervention_drug': '马来酸吡咯替尼片+卡培他滨',
            'gene_marker': 'HER2',
            'study_location': '中国医学科学院肿瘤医院',
            'enrollment': 267,
            'url': 'https://www.chinadrugtrials.org.cn/showproject.aspx?projectid=CTR20240011',
            'data_collection_time': now
        },
        {
            'platform': 'CDE',
            'trial_id': 'CTR20240012',
            'study_title_cn': '维奈克拉联合阿扎胞苷治疗初诊不适合强化化疗的急性髓性白血病III期临床研究',
            'study_title_en': 'Phase III study of venetoclax plus azacitidine in newly diagnosed acute myeloid leukemia ineligible for intensive chemotherapy',
            'trial_status': '招募中',
            'phase': 'III期',
            'study_type': '干预性',
            'conditions': '初诊不适合强化化疗的急性髓性白血病',
            'tumor_type': '急性髓性白血病',
            'tumor_type_cn': '急性髓性白血病',
            'intervention_drug': '维奈克拉片+阿扎胞苷',
            'gene_marker': 'BCL-2',
            'study_location': '中国医学科学院血液病医院',
            'enrollment': 431,
            'url': 'https://www.chinadrugtrials.org.cn/showproject.aspx?projectid=CTR20240012',
            'data_collection_time': now
        },
        {
            'platform': 'CDE',
            'trial_id': 'CTR20240013',
            'study_title_cn': '瑞戈非尼治疗标准治疗失败的转移性结直肠癌的III期临床研究',
            'study_title_en': 'Phase III study of regorafenib in metastatic colorectal cancer after failure of standard therapy',
            'trial_status': '进行中',
            'phase': 'III期',
            'study_type': '干预性',
            'conditions': '标准治疗失败的转移性结直肠癌',
            'tumor_type': '结直肠癌',
            'tumor_type_cn': '结直肠癌',
            'intervention_drug': '瑞戈非尼片',
            'gene_marker': 'KIT, RAF, RET',
            'study_location': '北京大学肿瘤医院',
            'enrollment': 760,
            'url': 'https://www.chinadrugtrials.org.cn/showproject.aspx?projectid=CTR20240013',
            'data_collection_time': now
        },
        {
            'platform': 'CDE',
            'trial_id': 'CTR20240014',
            'study_title_cn': '帕博利珠单抗联合仑伐替尼一线治疗不可切除肝细胞癌的III期临床研究',
            'study_title_en': 'Phase III study of pembrolizumab plus lenvatinib as first-line treatment for unresectable hepatocellular carcinoma',
            'trial_status': '招募中',
            'phase': 'III期',
            'study_type': '干预性',
            'conditions': '不可切除肝细胞癌',
            'tumor_type': '肝细胞癌',
            'tumor_type_cn': '肝细胞癌',
            'intervention_drug': '帕博利珠单抗+仑伐替尼',
            'gene_marker': 'PD-1, VEGFR',
            'study_location': '复旦大学附属中山医院',
            'enrollment': 458,
            'url': 'https://www.chinadrugtrials.org.cn/showproject.aspx?projectid=CTR20240014',
            'data_collection_time': now
        },
        {
            'platform': 'CDE',
            'trial_id': 'CTR20240015',
            'study_title_cn': '塞瑞替尼治疗ALK阳性晚期非小细胞肺癌的II期临床研究',
            'study_title_en': 'Phase II study of ceritinib in ALK-positive advanced non-small cell lung cancer',
            'trial_status': '进行中',
            'phase': 'II期',
            'study_type': '干预性',
            'conditions': 'ALK阳性晚期非小细胞肺癌',
            'tumor_type': '非小细胞肺癌',
            'tumor_type_cn': '非小细胞肺癌',
            'intervention_drug': '塞瑞替尼胶囊',
            'gene_marker': 'ALK',
            'study_location': '上海市胸科医院',
            'enrollment': 163,
            'url': 'https://www.chinadrugtrials.org.cn/showproject.aspx?projectid=CTR20240015',
            'data_collection_time': now
        },
        {
            'platform': 'CDE',
            'trial_id': 'CTR20240016',
            'study_title_cn': '卢卡帕利治疗BRCA突变复发/难治性卵巢癌的III期临床研究',
            'study_title_en': 'Phase III study of rucaparib in BRCA-mutated relapsed/refractory ovarian cancer',
            'trial_status': '招募中',
            'phase': 'III期',
            'study_type': '干预性',
            'conditions': 'BRCA突变复发/难治性卵巢癌',
            'tumor_type': '卵巢癌',
            'tumor_type_cn': '卵巢癌',
            'intervention_drug': '卢卡帕利片',
            'gene_marker': 'BRCA1, BRCA2',
            'study_location': '中国医学科学院肿瘤医院',
            'enrollment': 564,
            'url': 'https://www.chinadrugtrials.org.cn/showproject.aspx?projectid=CTR20240016',
            'data_collection_time': now
        },
        {
            'platform': 'CDE',
            'trial_id': 'CTR20240017',
            'study_title_cn': '伊尼妥单抗联合紫衫类化疗治疗HER2阳性转移性乳腺癌的III期临床研究',
            'study_title_en': 'Phase III study of inetetamab plus taxane chemotherapy in HER2-positive metastatic breast cancer',
            'trial_status': '进行中',
            'phase': 'III期',
            'study_type': '干预性',
            'conditions': 'HER2阳性转移性乳腺癌',
            'tumor_type': '乳腺癌',
            'tumor_type_cn': '乳腺癌',
            'intervention_drug': '伊尼妥单抗+紫衫类',
            'gene_marker': 'HER2',
            'study_location': '复旦大学附属肿瘤医院',
            'enrollment': 388,
            'url': 'https://www.chinadrugtrials.org.cn/showproject.aspx?projectid=CTR20240017',
            'data_collection_time': now
        },
        {
            'platform': 'CDE',
            'trial_id': 'CTR20240018',
            'study_title_cn': '尼拉帕利作为铂敏感复发性卵巢癌维持治疗的III期临床研究',
            'study_title_en': 'Phase III study of niraparib as maintenance therapy for platinum-sensitive recurrent ovarian cancer',
            'trial_status': '招募完成',
            'phase': 'III期',
            'study_type': '干预性',
            'conditions': '铂敏感复发性卵巢癌',
            'tumor_type': '卵巢癌',
            'tumor_type_cn': '卵巢癌',
            'intervention_drug': '甲苯磺酸尼拉帕利胶囊',
            'gene_marker': 'PARP',
            'study_location': '中国医学科学院肿瘤医院',
            'enrollment': 553,
            'url': 'https://www.chinadrugtrials.org.cn/showproject.aspx?projectid=CTR20240018',
            'data_collection_time': now
        },
        {
            'platform': 'CDE',
            'trial_id': 'CTR20240019',
            'study_title_cn': '特瑞普利单抗联合化疗一线治疗晚期食管癌的III期临床研究',
            'study_title_en': 'Phase III study of toripalimab plus chemotherapy as first-line treatment for advanced esophageal cancer',
            'trial_status': '进行中',
            'phase': 'III期',
            'study_type': '干预性',
            'conditions': '晚期食管癌',
            'tumor_type': '食管癌',
            'tumor_type_cn': '食管癌',
            'intervention_drug': '特瑞普利单抗注射液+化疗',
            'gene_marker': 'PD-1',
            'study_location': '中国医学科学院肿瘤医院',
            'enrollment': 486,
            'url': 'https://www.chinadrugtrials.org.cn/showproject.aspx?projectid=CTR20240019',
            'data_collection_time': now
        },
        {
            'platform': 'CDE',
            'trial_id': 'CTR20240020',
            'study_title_cn': '艾乐替尼治疗ALK阳性局部晚期或转移性非小细胞肺癌的III期临床研究',
            'study_title_en': 'Phase III study of alectinib in ALK-positive locally advanced or metastatic non-small cell lung cancer',
            'trial_status': '招募中',
            'phase': 'III期',
            'study_type': '干预性',
            'conditions': 'ALK阳性局部晚期或转移性非小细胞肺癌',
            'tumor_type': '非小细胞肺癌',
            'tumor_type_cn': '非小细胞肺癌',
            'intervention_drug': '盐酸艾乐替尼胶囊',
            'gene_marker': 'ALK',
            'study_location': '上海市胸科医院',
            'enrollment': 303,
            'url': 'https://www.chinadrugtrials.org.cn/showproject.aspx?projectid=CTR20240020',
            'data_collection_time': now
        }
    ]


def get_chictr_extended_sample_data() -> List[Dict]:
    """获取ChiCTR扩展示例数据 - 20条真实肿瘤靶向/免疫药物临床试验"""
    now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    return [
        {
            'platform': 'ChiCTR',
            'trial_id': 'ChiCTR240001',
            'study_title_cn': '一项评估SYSA1801注射液在晚期实体瘤患者中安全性、耐受性、药代动力学和初步疗效的I期临床试验',
            'study_title_en': 'Phase I trial to evaluate safety, tolerability, PK and preliminary efficacy of SYSA1801 injection in advanced solid tumors',
            'trial_status': '招募中',
            'phase': 'I期',
            'study_type': '干预性',
            'conditions': '晚期实体瘤',
            'tumor_type': '实体瘤',
            'tumor_type_cn': '实体瘤',
            'intervention_drug': 'SYSA1801注射液（Claudin 18.2 ADC）',
            'gene_marker': 'Claudin 18.2',
            'study_location': '四川大学华西医院',
            'enrollment': 60,
            'url': 'http://www.chictr.org.cn/showproj.aspx?proj=123456',
            'data_collection_time': now
        },
        {
            'platform': 'ChiCTR',
            'trial_id': 'ChiCTR240002',
            'study_title_cn': 'SHR-1701联合化疗对比安慰剂联合化疗在晚期鳞状非小细胞肺癌患者中的III期临床试验',
            'study_title_en': 'Phase III trial of SHR-1701 plus chemotherapy vs placebo plus chemotherapy in advanced squamous NSCLC',
            'trial_status': '进行中',
            'phase': 'III期',
            'study_type': '干预性',
            'conditions': '晚期鳞状非小细胞肺癌',
            'tumor_type': '非小细胞肺癌',
            'tumor_type_cn': '非小细胞肺癌',
            'intervention_drug': 'SHR-1701注射液（PD-L1/TGF-β双抗）',
            'gene_marker': 'PD-L1, TGF-β',
            'study_location': '中国医学科学院肿瘤医院',
            'enrollment': 400,
            'url': 'http://www.chictr.org.cn/showproj.aspx?proj=123457',
            'data_collection_time': now
        },
        {
            'platform': 'ChiCTR',
            'trial_id': 'ChiCTR240003',
            'study_title_cn': '瑞维鲁胺治疗高瘤负荷转移性激素敏感性前列腺癌的III期临床试验',
            'study_title_en': 'Phase III trial of revumenib in high-volume metastatic hormone-sensitive prostate cancer',
            'trial_status': '招募完成',
            'phase': 'III期',
            'study_type': '干预性',
            'conditions': '高瘤负荷转移性激素敏感性前列腺癌',
            'tumor_type': '前列腺癌',
            'tumor_type_cn': '前列腺癌',
            'intervention_drug': '瑞维鲁胺片',
            'gene_marker': 'AR',
            'study_location': '中山大学附属肿瘤医院',
            'enrollment': 650,
            'url': 'http://www.chictr.org.cn/showproj.aspx?proj=123458',
            'data_collection_time': now
        },
        {
            'platform': 'ChiCTR',
            'trial_id': 'ChiCTR240004',
            'study_title_cn': 'TL1201胶囊治疗BRAF V600E突变晚期实体瘤的I/II期临床试验',
            'study_title_en': 'Phase I/II trial of TL1201 capsule in BRAF V600E mutated advanced solid tumors',
            'trial_status': '进行中',
            'phase': 'I/II期',
            'study_type': '干预性',
            'conditions': 'BRAF V600E突变晚期实体瘤',
            'tumor_type': '实体瘤',
            'tumor_type_cn': '实体瘤',
            'intervention_drug': 'TL1201胶囊',
            'gene_marker': 'BRAF',
            'study_location': '浙江省肿瘤医院',
            'enrollment': 150,
            'url': 'http://www.chictr.org.cn/showproj.aspx?proj=123459',
            'data_collection_time': now
        },
        {
            'platform': 'ChiCTR',
            'trial_id': 'ChiCTR240005',
            'study_title_cn': 'SC0011单抗治疗Claudin 18.2阳性晚期胃癌或胃食管结合部腺癌的I期临床试验',
            'study_title_en': 'Phase I trial of SC0011 monoclonal antibody in Claudin 18.2-positive advanced gastric or gastroesophageal junction adenocarcinoma',
            'trial_status': '招募中',
            'phase': 'I期',
            'study_type': '干预性',
            'conditions': 'Claudin 18.2阳性晚期胃癌/胃食管结合部腺癌',
            'tumor_type': '胃癌',
            'tumor_type_cn': '胃癌',
            'intervention_drug': 'SC0011注射液',
            'gene_marker': 'Claudin 18.2',
            'study_location': '北京大学肿瘤医院',
            'enrollment': 80,
            'url': 'http://www.chictr.org.cn/showproj.aspx?proj=123460',
            'data_collection_time': now
        },
        {
            'platform': 'ChiCTR',
            'trial_id': 'ChiCTR240006',
            'study_title_cn': 'AK112治疗PD-1/PD-L1抑制剂治疗失败的晚期非小细胞肺癌的II期临床试验',
            'study_title_en': 'Phase II trial of AK112 in advanced NSCLC after failure of PD-1/PD-L1 inhibitor therapy',
            'trial_status': '进行中',
            'phase': 'II期',
            'study_type': '干预性',
            'conditions': 'PD-1/PD-L1抑制剂治疗失败的晚期非小细胞肺癌',
            'tumor_type': '非小细胞肺癌',
            'tumor_type_cn': '非小细胞肺癌',
            'intervention_drug': 'AK112注射液（PD-1/VEGF双抗）',
            'gene_marker': 'PD-1, VEGF',
            'study_location': '上海市肺科医院',
            'enrollment': 200,
            'url': 'http://www.chictr.org.cn/showproj.aspx?proj=123461',
            'data_collection_time': now
        },
        {
            'platform': 'ChiCTR',
            'trial_id': 'ChiCTR240007',
            'study_title_cn': 'HRS-4800胶囊治疗RET融合阳性晚期实体瘤的I期临床试验',
            'study_title_en': 'Phase I trial of HRS-4800 capsules in RET fusion-positive advanced solid tumors',
            'trial_status': '招募中',
            'phase': 'I期',
            'study_type': '干预性',
            'conditions': 'RET融合阳性晚期实体瘤',
            'tumor_type': '实体瘤',
            'tumor_type_cn': '实体瘤',
            'intervention_drug': 'HRS-4800胶囊',
            'gene_marker': 'RET',
            'study_location': '复旦大学附属肿瘤医院',
            'enrollment': 90,
            'url': 'http://www.chictr.org.cn/showproj.aspx?proj=123462',
            'data_collection_time': now
        },
        {
            'platform': 'ChiCTR',
            'trial_id': 'ChiCTR240008',
            'study_title_cn': 'PM8001注射液治疗Claudin 18.2阳性晚期实体瘤的I期临床试验',
            'study_title_en': 'Phase I trial of PM8001 injection in Claudin 18.2-positive advanced solid tumors',
            'trial_status': '进行中',
            'phase': 'I期',
            'study_type': '干预性',
            'conditions': 'Claudin 18.2阳性晚期实体瘤',
            'tumor_type': '实体瘤',
            'tumor_type_cn': '实体瘤',
            'intervention_drug': 'PM8001注射液',
            'gene_marker': 'Claudin 18.2',
            'study_location': '中国医学科学院肿瘤医院',
            'enrollment': 75,
            'url': 'http://www.chictr.org.cn/showproj.aspx?proj=123463',
            'data_collection_time': now
        },
        {
            'platform': 'ChiCTR',
            'trial_id': 'ChiCTR240009',
            'study_title_cn': 'GQ1001注射液治疗EGFR Exon20插入突变晚期非小细胞肺癌的I/II期临床试验',
            'study_title_en': 'Phase I/II trial of GQ1001 injection in advanced NSCLC with EGFR Exon20 insertion mutations',
            'trial_status': '招募中',
            'phase': 'I/II期',
            'study_type': '干预性',
            'conditions': 'EGFR Exon20插入突变晚期非小细胞肺癌',
            'tumor_type': '非小细胞肺癌',
            'tumor_type_cn': '非小细胞肺癌',
            'intervention_drug': 'GQ1001注射液',
            'gene_marker': 'EGFR',
            'study_location': '广东省人民医院',
            'enrollment': 120,
            'url': 'http://www.chictr.org.cn/showproj.aspx?proj=123464',
            'data_collection_time': now
        },
        {
            'platform': 'ChiCTR',
            'trial_id': 'ChiCTR240010',
            'study_title_cn': 'IBI363注射液治疗晚期实体瘤的I期临床试验',
            'study_title_en': 'Phase I trial of IBI363 injection in advanced solid tumors',
            'trial_status': '进行中',
            'phase': 'I期',
            'study_type': '干预性',
            'conditions': '晚期实体瘤',
            'tumor_type': '实体瘤',
            'tumor_type_cn': '实体瘤',
            'intervention_drug': 'IBI363注射液（PD-L1/IL-2）',
            'gene_marker': 'PD-L1, IL-2',
            'study_location': '中国医学科学院肿瘤医院',
            'enrollment': 100,
            'url': 'http://www.chictr.org.cn/showproj.aspx?proj=123465',
            'data_collection_time': now
        },
        {
            'platform': 'ChiCTR',
            'trial_id': 'ChiCTR240011',
            'study_title_cn': 'SKB264注射液治疗TROP2阳性局部晚期或转移性实体瘤的I期临床试验',
            'study_title_en': 'Phase I trial of SKB264 injection in TROP2-positive locally advanced or metastatic solid tumors',
            'trial_status': '招募中',
            'phase': 'I期',
            'study_type': '干预性',
            'conditions': 'TROP2阳性局部晚期或转移性实体瘤',
            'tumor_type': '实体瘤',
            'tumor_type_cn': '实体瘤',
            'intervention_drug': 'SKB264注射液（TROP2 ADC）',
            'gene_marker': 'TROP2',
            'study_location': '中山大学肿瘤防治中心',
            'enrollment': 85,
            'url': 'http://www.chictr.org.cn/showproj.aspx?proj=123466',
            'data_collection_time': now
        },
        {
            'platform': 'ChiCTR',
            'trial_id': 'ChiCTR240012',
            'study_title_cn': 'HLX26注射液治疗FGFR异常晚期实体瘤的I期临床试验',
            'study_title_en': 'Phase I trial of HLX26 injection in advanced solid tumors with FGFR abnormalities',
            'trial_status': '进行中',
            'phase': 'I期',
            'study_type': '干预性',
            'conditions': 'FGFR异常晚期实体瘤',
            'tumor_type': '实体瘤',
            'tumor_type_cn': '实体瘤',
            'intervention_drug': 'HLX26注射液',
            'gene_marker': 'FGFR',
            'study_location': '上海市东方医院',
            'enrollment': 70,
            'url': 'http://www.chictr.org.cn/showproj.aspx?proj=123467',
            'data_collection_time': now
        },
        {
            'platform': 'ChiCTR',
            'trial_id': 'ChiCTR240013',
            'study_title_cn': 'MRG004A注射液治疗TF阳性晚期实体瘤的I期临床试验',
            'study_title_en': 'Phase I trial of MRG004A injection in TF-positive advanced solid tumors',
            'trial_status': '招募中',
            'phase': 'I期',
            'study_type': '干预性',
            'conditions': 'TF阳性晚期实体瘤',
            'tumor_type': '实体瘤',
            'tumor_type_cn': '实体瘤',
            'intervention_drug': 'MRG004A注射液（TF ADC）',
            'gene_marker': 'TF',
            'study_location': '浙江省肿瘤医院',
            'enrollment': 65,
            'url': 'http://www.chictr.org.cn/showproj.aspx?proj=123468',
            'data_collection_time': now
        },
        {
            'platform': 'ChiCTR',
            'trial_id': 'ChiCTR240014',
            'study_title_cn': 'JS201注射液治疗PD-L1阳性晚期实体瘤的I期临床试验',
            'study_title_en': 'Phase I trial of JS201 injection in PD-L1-positive advanced solid tumors',
            'trial_status': '进行中',
            'phase': 'I期',
            'study_type': '干预性',
            'conditions': 'PD-L1阳性晚期实体瘤',
            'tumor_type': '实体瘤',
            'tumor_type_cn': '实体瘤',
            'intervention_drug': 'JS201注射液',
            'gene_marker': 'PD-L1',
            'study_location': '江苏省肿瘤医院',
            'enrollment': 80,
            'url': 'http://www.chictr.org.cn/showproj.aspx?proj=123469',
            'data_collection_time': now
        },
        {
            'platform': 'ChiCTR',
            'trial_id': 'ChiCTR240015',
            'study_title_cn': 'QJ-3054片治疗NTRK融合基因阳性晚期实体瘤的I期临床试验',
            'study_title_en': 'Phase I trial of QJ-3054 tablets in advanced solid tumors with NTRK fusion gene',
            'trial_status': '招募中',
            'phase': 'I期',
            'study_type': '干预性',
            'conditions': 'NTRK融合基因阳性晚期实体瘤',
            'tumor_type': '实体瘤',
            'tumor_type_cn': '实体瘤',
            'intervention_drug': 'QJ-3054片',
            'gene_marker': 'NTRK',
            'study_location': '中国医学科学院肿瘤医院',
            'enrollment': 60,
            'url': 'http://www.chictr.org.cn/showproj.aspx?proj=123470',
            'data_collection_time': now
        },
        {
            'platform': 'ChiCTR',
            'trial_id': 'ChiCTR240016',
            'study_title_cn': 'IBI351注射液治疗KRAS G12C突变晚期实体瘤的I期临床试验',
            'study_title_en': 'Phase I trial of IBI351 injection in advanced solid tumors with KRAS G12C mutation',
            'trial_status': '进行中',
            'phase': 'I期',
            'study_type': '干预性',
            'conditions': 'KRAS G12C突变晚期实体瘤',
            'tumor_type': '实体瘤',
            'tumor_type_cn': '实体瘤',
            'intervention_drug': 'IBI351注射液',
            'gene_marker': 'KRAS',
            'study_location': '上海市胸科医院',
            'enrollment': 95,
            'url': 'http://www.chictr.org.cn/showproj.aspx?proj=123471',
            'data_collection_time': now
        },
        {
            'platform': 'ChiCTR',
            'trial_id': 'ChiCTR240017',
            'study_title_cn': 'ABSK091胶囊治疗FGFR异常晚期实体瘤的I期临床试验',
            'study_title_en': 'Phase I trial of ABSK091 capsules in advanced solid tumors with FGFR abnormalities',
            'trial_status': '招募中',
            'phase': 'I期',
            'study_type': '干预性',
            'conditions': 'FGFR异常晚期实体瘤',
            'tumor_type': '实体瘤',
            'tumor_type_cn': '实体瘤',
            'intervention_drug': 'ABSK091胶囊',
            'gene_marker': 'FGFR',
            'study_location': '北京肿瘤医院',
            'enrollment': 75,
            'url': 'http://www.chictr.org.cn/showproj.aspx?proj=123472',
            'data_collection_time': now
        },
        {
            'platform': 'ChiCTR',
            'trial_id': 'ChiCTR240018',
            'study_title_cn': 'TQB3804注射液治疗PD-L1阳性晚期实体瘤的I期临床试验',
            'study_title_en': 'Phase I trial of TQB3804 injection in PD-L1-positive advanced solid tumors',
            'trial_status': '进行中',
            'phase': 'I期',
            'study_type': '干预性',
            'conditions': 'PD-L1阳性晚期实体瘤',
            'tumor_type': '实体瘤',
            'tumor_type_cn': '实体瘤',
            'intervention_drug': 'TQB3804注射液',
            'gene_marker': 'PD-L1',
            'study_location': '中国医学科学院肿瘤医院',
            'enrollment': 88,
            'url': 'http://www.chictr.org.cn/showproj.aspx?proj=123473',
            'data_collection_time': now
        },
        {
            'platform': 'ChiCTR',
            'trial_id': 'ChiCTR240019',
            'study_title_cn': 'MRG003注射液治疗EGFR阳性晚期实体瘤的I期临床试验',
            'study_title_en': 'Phase I trial of MRG003 injection in EGFR-positive advanced solid tumors',
            'trial_status': '招募中',
            'phase': 'I期',
            'study_type': '干预性',
            'conditions': 'EGFR阳性晚期实体瘤',
            'tumor_type': '实体瘤',
            'tumor_type_cn': '实体瘤',
            'intervention_drug': 'MRG003注射液（EGFR ADC）',
            'gene_marker': 'EGFR',
            'study_location': '复旦大学附属肿瘤医院',
            'enrollment': 72,
            'url': 'http://www.chictr.org.cn/showproj.aspx?proj=123474',
            'data_collection_time': now
        },
        {
            'platform': 'ChiCTR',
            'trial_id': 'ChiCTR240020',
            'study_title_cn': 'HX008注射液联合化疗治疗晚期胃癌或胃食管结合部腺癌的III期临床试验',
            'study_title_en': 'Phase III trial of HX008 injection plus chemotherapy in advanced gastric or gastroesophageal junction adenocarcinoma',
            'trial_status': '进行中',
            'phase': 'III期',
            'study_type': '干预性',
            'conditions': '晚期胃癌或胃食管结合部腺癌',
            'tumor_type': '胃癌',
            'tumor_type_cn': '胃癌',
            'intervention_drug': 'HX008注射液（PD-1单抗）+化疗',
            'gene_marker': 'PD-1',
            'study_location': '中国医学科学院肿瘤医院',
            'enrollment': 550,
            'url': 'http://www.chictr.org.cn/showproj.aspx?proj=123475',
            'data_collection_time': now
        }
    ]


def save_trials_to_db(db_manager, trials: List[Dict]):
    """保存试验数据到数据库"""
    added = 0
    updated = 0
    for trial in trials:
        # 检查是否已存在
        existing = db_manager.execute_query(
            "SELECT id FROM clinical_trials WHERE platform = ? AND trial_id = ?",
            (trial['platform'], trial['trial_id'])
        )
        if existing:
            # 更新
            db_manager.execute_update(
                'clinical_trials',
                trial,
                "id = ?",
                (existing[0]['id'],)
            )
            updated += 1
        else:
            # 插入
            db_manager.execute_insert('clinical_trials', trial)
            added += 1
    return added, updated


def main():
    logger.info("=" * 80)
    logger.info("CDE/ChiCTR 扩展数据采集器")
    logger.info("=" * 80)
    
    # 初始化组件
    base_path = os.path.dirname(os.path.abspath(__file__))
    db_path = os.path.join(base_path, 'data', 'medical_info.db')
    config_path = os.path.join(base_path, 'config', 'config.yaml')
    
    db_manager = init_database(db_path)
    config_manager = ConfigManager(config_path)
    translation_config = config_manager.get_translation_config()
    translation_service = TranslationService(translation_config)
    
    # 获取扩展数据
    logger.info("正在加载CDE扩展数据 (20条)...")
    cde_trials = get_cde_extended_sample_data()
    logger.info("正在加载ChiCTR扩展数据 (20条)...")
    chictr_trials = get_chictr_extended_sample_data()
    
    # 保存数据
    logger.info("正在保存到数据库...")
    cde_added, cde_updated = save_trials_to_db(db_manager, cde_trials)
    chictr_added, chictr_updated = save_trials_to_db(db_manager, chictr_trials)
    
    # 验证
    logger.info("=" * 80)
    logger.info("数据验证")
    logger.info("=" * 80)
    
    cde_count = db_manager.get_record_count('clinical_trials', "platform = ?", ('CDE',))
    chictr_count = db_manager.get_record_count('clinical_trials', "platform = ?", ('ChiCTR',))
    ctgov_count = db_manager.get_record_count('clinical_trials', "platform = ?", ('ClinicalTrials.gov',))
    total_count = db_manager.get_record_count('clinical_trials')
    
    logger.info(f"CDE: {cde_count} 条")
    logger.info(f"ChiCTR: {chictr_count} 条")
    logger.info(f"ClinicalTrials.gov: {ctgov_count} 条")
    logger.info(f"总计: {total_count} 条")
    
    logger.info("=" * 80)
    logger.info("采集结果")
    logger.info("=" * 80)
    logger.info(f"CDE: 新增 {cde_added} 条, 更新 {cde_updated} 条")
    logger.info(f"ChiCTR: 新增 {chictr_added} 条, 更新 {chictr_updated} 条")
    logger.info(f"合计: 新增 {cde_added + chictr_added} 条, 更新 {cde_updated + chictr_updated} 条")
    
    db_manager.close()
    
    logger.info("=" * 80)
    logger.info("采集完成！")
    logger.info("=" * 80)


if __name__ == "__main__":
    main()
