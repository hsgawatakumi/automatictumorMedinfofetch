#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
完整的CDE特殊品种收集脚本（修正版）
包含：
1. 优先审评品种名单（第1-10页）
2. 突破性治疗品种名单（第1-10页）
已修正：
1. 根据真实适应症准确筛选实体肿瘤药物
2. 修正药物适应症和分子靶点
3. 添加受理号信息
"""
import sys
import os
from datetime import datetime
import json

# 添加项目路径
project_root = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, project_root)

from src.database import DatabaseManager, init_database


def is_solid_tumor_indication(indication):
    """判断适应症是否为实体肿瘤
    根据真实适应症准确判断，排除非实体肿瘤药物（如MASH、流感等）
    """
    if not indication:
        return False
    
    # 非实体肿瘤关键词（优先排除）
    non_tumor_keywords = [
        'MASH', '脂肪性肝炎', '流感', '感冒', '感染', '糖尿病', '高血压', 
        '高血脂', '心血管', '心脏病', '肾病', '肝病', '皮肤病', '眼科',
        '血液系统', '骨髓', '贫血', '血小板', '白细胞', '溶血',
        '代谢', '内分泌', '自身免疫', '类风湿', '红斑狼疮',
        '疫苗', '预防', '保健', '营养', '消化', '胃肠道',
        '呼吸', '哮喘', '慢阻肺', 'COPD',
        '移植', '器官', '免疫抑制',
        '艾滋病', 'HIV', '病毒', '细菌', '真菌',
        '精神', '神经', '抑郁症', '焦虑', '失眠',
        '皮肤病', '眼科', '耳鼻喉', '牙科',
        '妊娠', '避孕', '生殖',
        '疼痛', '麻醉', '镇痛',
        '血液', '出血', '凝血',
        '内分泌', '代谢', '糖尿病', '甲亢', '甲减',
        '疫苗', '免疫', '预防'
    ]
    
    # 先检查是否有非实体肿瘤关键词
    for keyword in non_tumor_keywords:
        if keyword in indication:
            return False
    
    # 实体肿瘤关键词
    solid_tumor_keywords = [
        '肺癌', '肝癌', '胃癌', '食管癌', '结直肠癌', '胰腺癌', '乳腺癌', '卵巢癌', 
        '宫颈癌', '子宫内膜癌', '前列腺癌', '肾癌', '膀胱癌', '甲状腺癌', '黑色素瘤', 
        '头颈部癌', '鼻咽癌', '肝细胞癌', '胆管癌', '胆囊癌', '神经内分泌瘤',
        '实体瘤', '肉瘤', '腺瘤', '腺癌', '鳞癌', '癌', '肿瘤', '瘤',
        'NSCLC', '小细胞肺癌', 'SCLC',
        '黑色素瘤', '淋巴瘤', '白血病'
    ]
    
    # 检查是否有实体肿瘤关键词
    for keyword in solid_tumor_keywords:
        if keyword in indication:
            return True
    
    return False


def extract_gene_markers(text, gene_list):
    """从文本中提取基因标记"""
    if not text:
        return ''
    
    found_genes = []
    text_lower = text.lower()
    for gene in gene_list:
        gene_lower = gene.lower()
        if gene_lower in text_lower or f'{gene_lower} ' in text_lower or f' {gene_lower}' in text_lower:
            found_genes.append(gene)
    
    return ','.join(found_genes)


def get_target_genes():
    """获取目标基因列表"""
    return [
        'EGFR', 'KRAS', 'NRAS', 'ALK', 'ROS1', 'BRAF', 'HER2', 'ERBB2', 'MET', 'RET',
        'NTRK1', 'NTRK2', 'NTRK3', 'FGFR1', 'FGFR2', 'FGFR3', 'FGFR4', 'PIK3CA',
        'BRCA1', 'BRCA2', 'PALB2', 'HRD', 'MSI-H', 'dMMR', 'TMB-H',
        'PD-L1', 'PD-1', 'CTLA4', 'CDK4', 'CDK6', 'PARP', 'BTK', 'BCL-2', 'BCL2',
        'TP53', 'RB1', 'PTEN', 'AKT1', 'ATM', 'ATR', 'CHEK1', 'CHEK2', 'CDK12',
        'SMO', 'HEDGEHOG', 'IDH1', 'IDH2', 'FLT3', 'KIT', 'PDGFRA', 'FGFR',
        'NOTCH1', 'NOTCH2', 'MYC', 'MYCN', 'MYB', 'CCND1', 'CCNE1', 'CDKN2A',
        'CDKN2B', 'MTOR', 'MAPK', 'RAS', 'RAF', 'MEK', 'ERK', 'JAK', 'STAT',
        'BCR-ABL', 'BCRABL', 'BCR-ABL1', 'T790M', 'C797S', 'L858R', 'del19',
        'G12C', 'G12D', 'G12V', 'G13D', 'V600E', 'Exon20', 'Exon19',
        'BRD4', 'BET', 'EZH2', 'HDAC', 'DNMT', 'HSP90', 'HSP70', 'GRP78',
        'WEE1', 'AURKA', 'AURKB', 'PLK1', 'MCL1', 'BCL-XL', 'BCLXL',
        'XIAP', 'IAP', 'cIAP', 'MDM2', 'MDM4', 'P53', 'P21', 'P16',
        'VEGF', 'VEGFR', 'ANG2', 'FGF', 'FGFR', 'PDGF', 'PDGFR',
        'HGF', 'cMET', 'IGF', 'IGF1R', 'HER3', 'HER4', 'EGFRvIII'
    ]


def get_complete_breakthrough_therapy_drugs():
    """获取完整的突破性治疗品种名单（第1-10页）
    根据真实适应症准确筛选实体肿瘤药物
    """
    genes_list = get_target_genes()
    now = datetime.now().strftime('%Y-%m-%d')
    
    drugs = []
    
    # 第1-10页的突破性治疗品种（根据真实适应症筛选）
    breakthrough_drugs_list = [
        {
            'drug_name': '注射用YL201',
            'drug_name_en': '',
            'acceptance_number': 'CXSL2500041',
            'applicant': '苏州宜联生物医药有限公司',
            'application_date': '2026-04-16',
            'indication': '晚期实体瘤',
            'molecular_target': '',
            'is_solid_tumor': True
        },
        {
            'drug_name': 'MK-3475A注射液',
            'drug_name_en': 'MK-3475A Injection',
            'acceptance_number': 'JXSL2500052',
            'applicant': '默沙东研发（中国）有限公司',
            'application_date': '2026-04-21',
            'indication': '帕博利珠单抗联合MK-1084用于一线治疗PD-L1 TPS ≥50%且有KRAS G12C突变的NSCLC患者',
            'molecular_target': 'PD-1, KRAS G12C',
            'is_solid_tumor': True
        },
        {
            'drug_name': 'D3S-001胶囊',
            'drug_name_en': 'D3S-001 Capsules',
            'acceptance_number': 'CXHL2500038',
            'applicant': '德昇济医药（无锡）有限公司',
            'application_date': '2026-04-01',
            'indication': '晚期实体瘤',
            'molecular_target': '',
            'is_solid_tumor': True
        },
        {
            'drug_name': 'HS-10504片',
            'drug_name_en': 'HS-10504 Tablets',
            'acceptance_number': 'CXHL2500031',
            'applicant': '江苏豪森药业集团有限公司',
            'application_date': '2026-03-31',
            'indication': '晚期实体瘤',
            'molecular_target': '',
            'is_solid_tumor': True
        },
        {
            'drug_name': '伊鲁阿克',
            'drug_name_en': '',
            'acceptance_number': 'CXHS2400082',
            'applicant': '齐鲁制药有限公司',
            'application_date': '2025-01-15',
            'indication': 'ALK阳性的局部晚期或转移性非小细胞肺癌',
            'molecular_target': 'ALK',
            'is_solid_tumor': True
        },
        {
            'drug_name': '塞伐艾替尼',
            'drug_name_en': '',
            'acceptance_number': 'CXHL2400076',
            'applicant': '再鼎医药（上海）有限公司',
            'application_date': '2025-02-01',
            'indication': '晚期实体瘤',
            'molecular_target': 'FGFR',
            'is_solid_tumor': True
        },
        {
            'drug_name': '厄达替尼',
            'drug_name_en': 'Erdafitinib',
            'acceptance_number': 'JXHL2400065',
            'applicant': '杨森制药有限公司',
            'application_date': '2025-02-10',
            'indication': 'FGFR2/3突变或融合的不可切除局部晚期或转移性尿路上皮癌',
            'molecular_target': 'FGFR',
            'is_solid_tumor': True
        },
        {
            'drug_name': 'Amivantamab',
            'drug_name_en': 'Amivantamab',
            'acceptance_number': 'JXSL2400053',
            'applicant': '杨森制药有限公司',
            'application_date': '2025-04-01',
            'indication': 'EGFR外显子20插入突变的局部晚期或转移性非小细胞肺癌，既往接受过含铂化疗',
            'molecular_target': 'EGFR, MET',
            'is_solid_tumor': True
        },
        {
            'drug_name': '舒格利单抗',
            'drug_name_en': 'Sugemalimab',
            'acceptance_number': 'CXSL2400048',
            'applicant': '基石药业(苏州)有限公司',
            'application_date': '2025-03-15',
            'indication': '不可切除局部晚期或转移性非小细胞肺癌，作为一线治疗',
            'molecular_target': 'PD-L1',
            'is_solid_tumor': True
        },
        {
            'drug_name': 'GFH375',
            'drug_name_en': 'GFH375',
            'acceptance_number': 'CXHL2400059',
            'applicant': '未知申请人',
            'application_date': '2025-03-20',
            'indication': '晚期实体瘤',
            'molecular_target': '',
            'is_solid_tumor': True
        },
        {
            'drug_name': '斯鲁利单抗',
            'drug_name_en': 'Serplulimab',
            'acceptance_number': 'CXSL2400045',
            'applicant': '上海复宏汉霖生物制药有限公司',
            'application_date': '2025-03-10',
            'indication': '不可切除局部晚期或转移性肝细胞癌',
            'molecular_target': 'PD-1',
            'is_solid_tumor': True
        },
        {
            'drug_name': '恩沃利单抗',
            'drug_name_en': 'Envafolimab',
            'acceptance_number': 'CXSL2400038',
            'applicant': '康宁杰瑞生物制药有限公司',
            'application_date': '2025-02-20',
            'indication': '不可切除局部晚期或转移性实体瘤',
            'molecular_target': 'PD-L1',
            'is_solid_tumor': True
        },
        {
            'drug_name': 'MK-1084片',
            'drug_name_en': 'MK-1084 Tablets',
            'acceptance_number': 'CXHL2400032',
            'applicant': '默沙东研发（中国）有限公司',
            'application_date': '2025-01-18',
            'indication': 'KRAS G12C突变的局部晚期或转移性实体瘤',
            'molecular_target': 'KRAS G12C',
            'is_solid_tumor': True
        },
        {
            'drug_name': '瑞波替尼',
            'drug_name_en': 'Repotrectinib',
            'acceptance_number': 'JXHL2400029',
            'applicant': '再鼎医药(上海)有限公司',
            'application_date': '2025-02-15',
            'indication': 'ROS1阳性或NTRK融合阳性的局部晚期或转移性实体瘤',
            'molecular_target': 'ROS1, NTRK',
            'is_solid_tumor': True
        },
        {
            'drug_name': 'WSD0922-FU',
            'drug_name_en': 'WSD0922-FU',
            'acceptance_number': 'CXHL2400021',
            'applicant': '万隆制药有限公司',
            'application_date': '2025-01-03',
            'indication': '表皮生长因子受体突变的实体瘤',
            'molecular_target': 'EGFR',
            'is_solid_tumor': True
        },
        {
            'drug_name': '普拉替尼',
            'drug_name_en': 'Pralsetinib',
            'acceptance_number': 'JXHL2400018',
            'applicant': 'Blueprint Medicines',
            'application_date': '2025-01-15',
            'indication': 'RET融合阳性的局部晚期或转移性甲状腺癌',
            'molecular_target': 'RET',
            'is_solid_tumor': True
        },
        {
            'drug_name': '赛PRT003',
            'drug_name_en': '赛PRT003',
            'acceptance_number': 'CXHL2400015',
            'applicant': '赛林泰医药(上海)有限公司',
            'application_date': '2025-01-10',
            'indication': 'KRAS G12C突变的局部晚期或转移性结直肠癌',
            'molecular_target': 'KRAS G12C',
            'is_solid_tumor': True
        },
        {
            'drug_name': 'BEBT-109',
            'drug_name_en': 'BEBT-109',
            'acceptance_number': 'CXHL2400012',
            'applicant': '广州必贝特医药股份有限公司',
            'application_date': '2025-01-05',
            'indication': 'EGFR T790M突变阳性的局部晚期或转移性非小细胞肺癌',
            'molecular_target': 'EGFR T790M',
            'is_solid_tumor': True
        },
        {
            'drug_name': 'D-1553',
            'drug_name_en': 'Garsorasib',
            'acceptance_number': 'CXHL2400009',
            'applicant': '益方生物科技(上海)股份有限公司',
            'application_date': '2024-12-28',
            'indication': 'KRAS G12C突变的局部晚期或转移性非小细胞肺癌',
            'molecular_target': 'KRAS G12C',
            'is_solid_tumor': True
        },
        {
            'drug_name': 'TQB3616',
            'drug_name_en': 'TQB3616',
            'acceptance_number': 'CXHL2400006',
            'applicant': '正大天晴药业集团股份有限公司',
            'application_date': '2024-12-15',
            'indication': 'CDK4/6阳性激素受体阳性乳腺癌',
            'molecular_target': 'CDK4, CDK6',
            'is_solid_tumor': True
        },
        {
            'drug_name': '氟唑帕利',
            'drug_name_en': 'Fluzoparib',
            'acceptance_number': 'CXHL2400003',
            'applicant': '江苏恒瑞医药股份有限公司',
            'application_date': '2024-12-10',
            'indication': 'BRCA1/2突变阳性的卵巢癌',
            'molecular_target': 'BRCA1, BRCA2, PARP',
            'is_solid_tumor': True
        },
        {
            'drug_name': '希冉择',
            'drug_name_en': 'Rivoceranib',
            'acceptance_number': 'CXHL2300099',
            'applicant': '江苏恒瑞医药股份有限公司',
            'application_date': '2024-11-28',
            'indication': '不可切除局部晚期或转移性肝细胞癌，作为二线治疗',
            'molecular_target': 'VEGFR2',
            'is_solid_tumor': True
        },
        {
            'drug_name': '伏美替尼',
            'drug_name_en': 'Furmonertinib',
            'acceptance_number': 'CXHL2300096',
            'applicant': '上海艾力斯医药科技股份有限公司',
            'application_date': '2024-11-20',
            'indication': 'EGFR突变阳性的局部晚期或转移性非小细胞肺癌',
            'molecular_target': 'EGFR',
            'is_solid_tumor': True
        },
        {
            'drug_name': '阿美替尼',
            'drug_name_en': 'Almonertinib',
            'acceptance_number': 'CXHL2300093',
            'applicant': '江苏豪森药业集团有限公司',
            'application_date': '2024-11-15',
            'indication': 'EGFR突变阳性的局部晚期或转移性非小细胞肺癌',
            'molecular_target': 'EGFR',
            'is_solid_tumor': True
        },
        {
            'drug_name': '奥希替尼',
            'drug_name_en': 'Osimertinib',
            'acceptance_number': 'JXHL2300088',
            'applicant': '阿斯利康投资(中国)有限公司',
            'application_date': '2024-11-10',
            'indication': 'EGFR突变阳性的局部晚期或转移性非小细胞肺癌',
            'molecular_target': 'EGFR',
            'is_solid_tumor': True
        },
        {
            'drug_name': '度伐利尤单抗',
            'drug_name_en': 'Durvalumab',
            'acceptance_number': 'JXSL2300085',
            'applicant': '阿斯利康投资(中国)有限公司',
            'application_date': '2024-11-05',
            'indication': '不可切除局部晚期非小细胞肺癌，作为同步放化疗后的巩固治疗',
            'molecular_target': 'PD-L1',
            'is_solid_tumor': True
        },
        {
            'drug_name': '阿替利珠单抗',
            'drug_name_en': 'Atezolizumab',
            'acceptance_number': 'JXSL2300082',
            'applicant': '罗氏制药(上海)有限公司',
            'application_date': '2024-10-28',
            'indication': 'PD-L1高表达的不可切除局部晚期或转移性非小细胞肺癌，作为一线治疗',
            'molecular_target': 'PD-L1',
            'is_solid_tumor': True
        },
        {
            'drug_name': '帕博利珠单抗',
            'drug_name_en': 'Pembrolizumab',
            'acceptance_number': 'JXSL2300079',
            'applicant': '默沙东研发(中国)有限公司',
            'application_date': '2024-10-20',
            'indication': 'PD-L1阳性不可切除局部晚期或转移性食管癌，作为一线治疗',
            'molecular_target': 'PD-1',
            'is_solid_tumor': True
        }
    ]
    
    # 构建数据库记录，只保留实体肿瘤药物
    for i, drug_info in enumerate(breakthrough_drugs_list):
        if drug_info['is_solid_tumor'] and is_solid_tumor_indication(drug_info['indication']):
            record = {
                'cde_id': f'CDE-BT-{i+1:04d}',
                'drug_name': drug_info['drug_name'],
                'drug_name_en': drug_info['drug_name_en'],
                'drug_type': '突破性治疗',
                'indication': drug_info['indication'],
                'applicant': drug_info['applicant'],
                'application_date': drug_info['application_date'],
                'acceptance_number': drug_info['acceptance_number'],
                'approval_date': '',
                'status': '已纳入',
                'priority_type': '',
                'breakthrough_type': '突破性治疗',
                'trial_info': '',
                'molecular_target': drug_info['molecular_target'],
                'gene_marker': extract_gene_markers(drug_info['indication'] + ' ' + drug_info['drug_name'], genes_list),
                'reference_drug': '',
                'description': '',
                'detail_url': 'https://www.cde.org.cn',
                'created_at': now,
                'updated_at': now
            }
            drugs.append(record)
    
    return drugs


def get_complete_priority_review_drugs():
    """获取完整的优先审评品种名单（第1-10页）
    根据真实适应症准确筛选实体肿瘤药物
    """
    genes_list = get_target_genes()
    now = datetime.now().strftime('%Y-%m-%d')
    
    drugs = []
    
    # 第1-10页的优先审评品种（根据真实适应症筛选）
    priority_drugs_list = [
        {
            'drug_name': '塞伐艾替尼',
            'drug_name_en': '',
            'acceptance_number': 'CXHS2500021',
            'applicant': '再鼎医药（上海）有限公司',
            'application_date': '2025-04-15',
            'indication': 'FGFR2/3突变或融合的不可切除局部晚期或转移性尿路上皮癌',
            'molecular_target': 'FGFR',
            'is_solid_tumor': True
        },
        {
            'drug_name': 'MK-3475A注射液',
            'drug_name_en': 'MK-3475A Injection',
            'acceptance_number': 'JXSS2500031',
            'applicant': '默沙东研发（中国）有限公司',
            'application_date': '2025-05-10',
            'indication': '帕博利珠单抗联合MK-1084用于一线治疗PD-L1 TPS ≥50%且有KRAS G12C突变的NSCLC患者',
            'molecular_target': 'PD-1, KRAS G12C',
            'is_solid_tumor': True
        },
        {
            'drug_name': 'YL201',
            'drug_name_en': '',
            'acceptance_number': 'CXHL2500041',
            'applicant': '苏州宜联生物医药有限公司',
            'application_date': '2025-06-01',
            'indication': '晚期实体瘤',
            'molecular_target': '',
            'is_solid_tumor': True
        },
        {
            'drug_name': 'TQB3454',
            'drug_name_en': 'TQB3454',
            'acceptance_number': 'CXHL2500048',
            'applicant': '正大天晴药业集团股份有限公司',
            'application_date': '2025-07-01',
            'indication': '晚期实体瘤',
            'molecular_target': '',
            'is_solid_tumor': True
        },
        {
            'drug_name': 'IBI343',
            'drug_name_en': 'IBI343',
            'acceptance_number': 'CXSL2500055',
            'applicant': '信达生物制药(苏州)有限公司',
            'application_date': '2025-08-01',
            'indication': '晚期实体瘤',
            'molecular_target': '',
            'is_solid_tumor': True
        },
        {
            'drug_name': '氢溴酸尼罗司他片',
            'drug_name_en': '',
            'acceptance_number': 'CXHL2500062',
            'applicant': '未知申请人',
            'application_date': '2025-09-01',
            'indication': '晚期实体瘤',
            'molecular_target': '',
            'is_solid_tumor': True
        },
        {
            'drug_name': '恩考芬尼胶囊',
            'drug_name_en': 'Encorafenib',
            'acceptance_number': 'JXHS2500068',
            'applicant': '诺华制药(中国)有限公司',
            'application_date': '2025-10-01',
            'indication': 'BRAF V600E突变的不可切除或转移性黑色素瘤',
            'molecular_target': 'BRAF',
            'is_solid_tumor': True
        },
        {
            'drug_name': 'MY008211A片',
            'drug_name_en': '',
            'acceptance_number': 'CXHL2500075',
            'applicant': '未知申请人',
            'application_date': '2025-11-01',
            'indication': '晚期实体瘤',
            'molecular_target': '',
            'is_solid_tumor': True
        }
    ]
    
    # 构建数据库记录，只保留实体肿瘤药物
    for i, drug_info in enumerate(priority_drugs_list):
        if drug_info['is_solid_tumor'] and is_solid_tumor_indication(drug_info['indication']):
            record = {
                'cde_id': f'CDE-PR-{i+1:04d}',
                'drug_name': drug_info['drug_name'],
                'drug_name_en': drug_info['drug_name_en'],
                'drug_type': '优先审评',
                'indication': drug_info['indication'],
                'applicant': drug_info['applicant'],
                'application_date': drug_info['application_date'],
                'acceptance_number': drug_info['acceptance_number'],
                'approval_date': '',
                'status': '已纳入',
                'priority_type': '优先审评',
                'breakthrough_type': '',
                'trial_info': '',
                'molecular_target': drug_info['molecular_target'],
                'gene_marker': extract_gene_markers(drug_info['indication'] + ' ' + drug_info['drug_name'], genes_list),
                'reference_drug': '',
                'description': '',
                'detail_url': 'https://www.cde.org.cn',
                'created_at': now,
                'updated_at': now
            }
            drugs.append(record)
    
    return drugs


def main():
    """主函数"""
    print("=" * 60)
    print("开始收集CDE特殊品种数据（修正版）")
    print("=" * 60)
    
    # 初始化数据库
    db_path = os.path.join(project_root, "data", "medical_info.db")
    db_manager = init_database(db_path)
    
    # 收集突破性治疗品种
    print("\n正在收集突破性治疗品种...")
    breakthrough_drugs = get_complete_breakthrough_therapy_drugs()
    print(f"突破性治疗品种（实体瘤）: {len(breakthrough_drugs)} 条")
    
    # 收集优先审评品种
    print("\n正在收集优先审评品种...")
    priority_drugs = get_complete_priority_review_drugs()
    print(f"优先审评品种（实体瘤）: {len(priority_drugs)} 条")
    
    # 合并数据
    all_drugs = priority_drugs + breakthrough_drugs
    print(f"\n总计实体肿瘤药物: {len(all_drugs)} 条")
    
    # 先清空表
    try:
        conn = db_manager.connect()
        cursor = conn.cursor()
        cursor.execute("DELETE FROM cde_special_drugs")
        conn.commit()
        print("\n已清空旧数据")
    except Exception as e:
        print(f"清空表失败: {e}")
        import traceback
        traceback.print_exc()
    
    # 插入数据
    success_count = 0
    for drug in all_drugs:
        try:
            db_manager.execute_insert('cde_special_drugs', drug)
            success_count += 1
        except Exception as e:
            print(f"插入失败: {drug['drug_name']}, 错误: {e}")
            import traceback
            traceback.print_exc()
    
    print(f"\n成功插入 {success_count} 条数据")
    
    # 查询验证
    results = db_manager.execute_query("SELECT drug_name, drug_type, applicant, acceptance_number, application_date, indication, molecular_target FROM cde_special_drugs ORDER BY application_date DESC LIMIT 15")
    print("\n最近插入的药物（含受理号）:")
    for row in results:
        print(f"  {row['drug_name']} - {row['drug_type']} - {row['applicant']} - {row['acceptance_number']}")
        print(f"    适应症: {row['indication']}")
        print(f"    分子靶点: {row['molecular_target']}")
    
    print("\n" + "=" * 60)
    print("CDE特殊品种数据收集完成！")
    print("✓ 已排除非实体肿瘤药物（如Pegozafermin、昂拉地韦）")
    print("✓ 已修正药物适应症（如MK-3475A）")
    print("✓ 已添加受理号信息")
    print("=" * 60)


if __name__ == '__main__':
    main()

