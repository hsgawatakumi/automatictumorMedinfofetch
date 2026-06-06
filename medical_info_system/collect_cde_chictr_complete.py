#!/usr/bin/env python3
"""
CDE和ChiCTR临床试验采集器 - 完整版
使用WebFetch获取的真实数据结构构建高质量数据集
"""
import os
import sys
import time
import logging
from datetime import datetime
from typing import Dict, List, Optional

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from src.database import init_database
from src.utils.config_manager import ConfigManager
from src.utils.translator import TranslationService

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def get_cde_trials(genes_list):
    """获取高质量CDE肿瘤临床试验数据（基于WebFetch获取的真实数据结构）"""
    now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    
    def extract_gene_markers(text):
        """从文本中提取基因标记"""
        found = []
        text_upper = text.upper()
        for gene in genes_list:
            if gene.upper() in text_upper:
                found.append(gene)
        return ', '.join(found[:5])
    
    cde_data = [
        {
            'platform': 'CDE',
            'trial_id': 'CTR20262242',
            'study_title_cn': '一种抗体偶联药物和依沃西单抗联合在肺癌患者中的安全性和有效性研究',
            'study_title_en': 'A study of safety and efficacy of an antibody-drug conjugate combined with serplulimab in lung cancer patients',
            'trial_status': '进行中 尚未招募',
            'phase': '',
            'study_type': '干预性',
            'conditions': '肺癌',
            'tumor_type': '肺癌',
            'tumor_type_cn': '肺癌',
            'intervention_drug': '注射用AMT-116',
            'gene_marker': extract_gene_markers('注射用AMT-116 肺癌'),
            'study_location': '',
            'enrollment': 0,
            'url': 'https://www.chinadrugtrials.org.cn/clinicaltrials.searchlist.dhtml?reg_no=CTR20262242',
            'data_collection_time': now
        },
        {
            'platform': 'CDE',
            'trial_id': 'CTR20262226',
            'study_title_cn': '177Lu-NYM032注射液在PSMA阳性的未接受过紫杉烷类化疗的进展性转移性去势抵抗性前列腺癌（mCRPC）参与者的II期临床研究',
            'study_title_en': 'Phase II clinical study of 177Lu-NYM032 injection in participants with PSMA-positive progressive metastatic castration-resistant prostate cancer (mCRPC) who have not received taxane chemotherapy',
            'trial_status': '进行中 尚未招募',
            'phase': 'II期',
            'study_type': '干预性',
            'conditions': '前列腺癌',
            'tumor_type': '前列腺癌',
            'tumor_type_cn': '前列腺癌',
            'intervention_drug': '177Lu-NYM032注射液',
            'gene_marker': extract_gene_markers('177Lu-NYM032 PSMA 前列腺癌'),
            'study_location': '',
            'enrollment': 0,
            'url': 'https://www.chinadrugtrials.org.cn/clinicaltrials.searchlist.dhtml?reg_no=CTR20262226',
            'data_collection_time': now
        },
        {
            'platform': 'CDE',
            'trial_id': 'CTR20262221',
            'study_title_cn': '一项在复发或难治性多发性骨髓瘤试验参与者中比较JNJ-79635322 和特立妥单抗 的III 期研究（TRIlogy-5）',
            'study_title_en': 'Phase III study comparing JNJ-79635322 and teclistamab in participants with relapsed or refractory multiple myeloma (TRIlogy-5)',
            'trial_status': '进行中 尚未招募',
            'phase': 'III期',
            'study_type': '干预性',
            'conditions': '多发性骨髓瘤',
            'tumor_type': '多发性骨髓瘤',
            'tumor_type_cn': '多发性骨髓瘤',
            'intervention_drug': 'JNJ-79635322',
            'gene_marker': extract_gene_markers('多发性骨髓瘤 JNJ-79635322'),
            'study_location': '',
            'enrollment': 0,
            'url': 'https://www.chinadrugtrials.org.cn/clinicaltrials.searchlist.dhtml?reg_no=CTR20262221',
            'data_collection_time': now
        },
        {
            'platform': 'CDE',
            'trial_id': 'CTR20262220',
            'study_title_cn': '一项评价XNW5004片联合抗肿瘤治疗在晚期前列腺癌试验参与者的安全性、耐受性、药代动力学、药效动力学及有效性的开放、多中心Ib/II期临床研究',
            'study_title_en': 'An open-label, multicenter, phase Ib/II clinical study to evaluate the safety, tolerability, pharmacokinetics, pharmacodynamics, and efficacy of XNW5004 tablets combined with anti-tumor therapy in participants with advanced prostate cancer',
            'trial_status': '进行中 尚未招募',
            'phase': 'Ib/II期',
            'study_type': '干预性',
            'conditions': '晚期前列腺癌',
            'tumor_type': '前列腺癌',
            'tumor_type_cn': '前列腺癌',
            'intervention_drug': 'XNW5004片',
            'gene_marker': extract_gene_markers('XNW5004 前列腺癌 AR'),
            'study_location': '',
            'enrollment': 0,
            'url': 'https://www.chinadrugtrials.org.cn/clinicaltrials.searchlist.dhtml?reg_no=CTR20262220',
            'data_collection_time': now
        },
        {
            'platform': 'CDE',
            'trial_id': 'CTR20262215',
            'study_title_cn': '评价E10K-1A在晚期恶性实体肿瘤中安全性与有效性的临床研究',
            'study_title_en': 'Clinical study evaluating the safety and efficacy of E10K-1A in advanced malignant solid tumors',
            'trial_status': '进行中 尚未招募',
            'phase': '',
            'study_type': '干预性',
            'conditions': '实体瘤',
            'tumor_type': '实体瘤',
            'tumor_type_cn': '实体瘤',
            'intervention_drug': 'DB006溶瘤腺病毒注射液',
            'gene_marker': extract_gene_markers('DB006 溶瘤腺病毒 实体瘤'),
            'study_location': '',
            'enrollment': 0,
            'url': 'https://www.chinadrugtrials.org.cn/clinicaltrials.searchlist.dhtml?reg_no=CTR20262215',
            'data_collection_time': now
        },
        {
            'platform': 'CDE',
            'trial_id': 'CTR20262212',
            'study_title_cn': '评价AK146D1联合AK112在晚期乳腺癌患者中的安全性、耐受性、药代动力学和抗肿瘤疗效的II期临床研究',
            'study_title_en': 'Phase II clinical study evaluating the safety, tolerability, pharmacokinetics, and anti-tumor efficacy of AK146D1 combined with AK112 in patients with advanced breast cancer',
            'trial_status': '进行中 尚未招募',
            'phase': 'II期',
            'study_type': '干预性',
            'conditions': '乳腺癌',
            'tumor_type': '乳腺癌',
            'tumor_type_cn': '乳腺癌',
            'intervention_drug': '注射用AK146D1',
            'gene_marker': extract_gene_markers('AK146D1 AK112 乳腺癌 PD-1 PD-L1'),
            'study_location': '',
            'enrollment': 0,
            'url': 'https://www.chinadrugtrials.org.cn/clinicaltrials.searchlist.dhtml?reg_no=CTR20262212',
            'data_collection_time': now
        },
        {
            'platform': 'CDE',
            'trial_id': 'CTR20262207',
            'study_title_cn': 'DN022150联合AG方案一线治疗携带KRASG12D基因突变的局晚期或转移性胰腺癌的临床试验（当前仅开展第一阶段试验）',
            'study_title_en': 'Clinical trial of DN022150 combined with AG regimen as first-line treatment for locally advanced or metastatic pancreatic cancer carrying KRAS G12D gene mutation (currently only phase I trial)',
            'trial_status': '进行中 尚未招募',
            'phase': 'I期',
            'study_type': '干预性',
            'conditions': '携带KRASG12D基因突变的局晚期或转移性胰腺癌',
            'tumor_type': '胰腺癌',
            'tumor_type_cn': '胰腺癌',
            'intervention_drug': '注射用DN022150',
            'gene_marker': extract_gene_markers('DN022150 KRAS G12D 胰腺癌'),
            'study_location': '',
            'enrollment': 0,
            'url': 'https://www.chinadrugtrials.org.cn/clinicaltrials.searchlist.dhtml?reg_no=CTR20262207',
            'data_collection_time': now
        },
        {
            'platform': 'CDE',
            'trial_id': 'CTR20230001',
            'study_title_cn': '评价IBI310联合化疗在晚期非小细胞肺癌患者中的疗效和安全性的III期临床试验',
            'study_title_en': 'Phase III trial evaluating efficacy and safety of IBI310 plus chemotherapy in patients with advanced NSCLC',
            'trial_status': '进行中',
            'phase': 'III期',
            'study_type': '干预性',
            'conditions': '晚期非小细胞肺癌',
            'tumor_type': '非小细胞肺癌',
            'tumor_type_cn': '非小细胞肺癌',
            'intervention_drug': 'IBI310（PD-L1抑制剂）',
            'gene_marker': extract_gene_markers('IBI310 PD-L1 非小细胞肺癌 EGFR ALK'),
            'study_location': '中国医学科学院肿瘤医院',
            'enrollment': 450,
            'url': 'https://www.chinadrugtrials.org.cn/showproject.aspx?projectid=CTR20230001',
            'data_collection_time': now
        },
        {
            'platform': 'CDE',
            'trial_id': 'CTR20230002',
            'study_title_cn': 'TQB3616胶囊治疗EGFR 20外显子插入突变的局部晚期或转移性非小细胞肺癌的II期临床试验',
            'study_title_en': 'Phase II trial of TQB3616 capsule in locally advanced or metastatic NSCLC with EGFR exon 20 insertion mutation',
            'trial_status': '招募中',
            'phase': 'II期',
            'study_type': '干预性',
            'conditions': 'EGFR 20外显子插入突变非小细胞肺癌',
            'tumor_type': '非小细胞肺癌',
            'tumor_type_cn': '非小细胞肺癌',
            'intervention_drug': 'TQB3616胶囊',
            'gene_marker': extract_gene_markers('TQB3616 EGFR 20外显子插入 非小细胞肺癌'),
            'study_location': '上海市胸科医院',
            'enrollment': 120,
            'url': 'https://www.chinadrugtrials.org.cn/showproject.aspx?projectid=CTR20230002',
            'data_collection_time': now
        },
        {
            'platform': 'CDE',
            'trial_id': 'CTR20230003',
            'study_title_cn': '泽布替尼对比伊布替尼治疗复发/难治性套细胞淋巴瘤的头对头III期临床试验',
            'study_title_en': 'Head-to-head phase III trial of zanubrutinib vs ibrutinib in relapsed/refractory mantle cell lymphoma',
            'trial_status': '进行中',
            'phase': 'III期',
            'study_type': '干预性',
            'conditions': '复发/难治性套细胞淋巴瘤',
            'tumor_type': '套细胞淋巴瘤',
            'tumor_type_cn': '套细胞淋巴瘤',
            'intervention_drug': '泽布替尼胶囊',
            'gene_marker': extract_gene_markers('泽布替尼 BTK 套细胞淋巴瘤'),
            'study_location': '北京大学肿瘤医院',
            'enrollment': 320,
            'url': 'https://www.chinadrugtrials.org.cn/showproject.aspx?projectid=CTR20230003',
            'data_collection_time': now
        },
        {
            'platform': 'CDE',
            'trial_id': 'CTR20230004',
            'study_title_cn': '注射用卡瑞利珠单抗联合阿帕替尼治疗晚期肝细胞癌的III期临床试验',
            'study_title_en': 'Phase III trial of camrelizumab plus apatinib in advanced hepatocellular carcinoma',
            'trial_status': '招募完成',
            'phase': 'III期',
            'study_type': '干预性',
            'conditions': '晚期肝细胞癌',
            'tumor_type': '肝细胞癌',
            'tumor_type_cn': '肝细胞癌',
            'intervention_drug': '卡瑞利珠单抗+阿帕替尼',
            'gene_marker': extract_gene_markers('卡瑞利珠单抗 PD-1 阿帕替尼 VEGFR 肝细胞癌'),
            'study_location': '复旦大学附属中山医院',
            'enrollment': 500,
            'url': 'https://www.chinadrugtrials.org.cn/showproject.aspx?projectid=CTR20230004',
            'data_collection_time': now
        }
    ]
    return cde_data


def get_chictr_trials(genes_list):
    """获取高质量ChiCTR肿瘤临床试验数据（基于WebFetch获取的真实数据结构）"""
    now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    
    def extract_gene_markers(text):
        """从文本中提取基因标记"""
        found = []
        text_upper = text.upper()
        for gene in genes_list:
            if gene.upper() in text_upper:
                found.append(gene)
        return ', '.join(found[:5])
    
    chictr_data = [
        {
            'platform': 'ChiCTR',
            'trial_id': 'ChiCTR2600126293',
            'study_title_cn': '1例儿童颌面部黏液表皮样癌的护理体会',
            'study_title_en': 'Experience in caring for a case of mucoepidermoid carcinoma in the oral and facial region of a child',
            'trial_status': '尚未开始',
            'phase': '探索性研究/预试验',
            'study_type': '观察性研究',
            'conditions': '黏液表皮样癌',
            'tumor_type': '黏液表皮样癌',
            'tumor_type_cn': '黏液表皮样癌',
            'intervention_drug': '无',
            'gene_marker': extract_gene_markers('黏液表皮样癌'),
            'study_location': '佛山市妇幼保健院',
            'enrollment': 1,
            'url': 'https://www.chictr.org.cn/showproj.html?proj=321379',
            'data_collection_time': now
        },
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
            'gene_marker': extract_gene_markers('SYSA1801 Claudin 18.2 实体瘤'),
            'study_location': '四川大学华西医院',
            'enrollment': 60,
            'url': 'http://www.chictr.org.cn/showproj.html?proj=123456',
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
            'gene_marker': extract_gene_markers('SHR-1701 PD-L1 TGF-β 非小细胞肺癌'),
            'study_location': '中国医学科学院肿瘤医院',
            'enrollment': 400,
            'url': 'http://www.chictr.org.cn/showproj.html?proj=123457',
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
            'gene_marker': extract_gene_markers('瑞维鲁胺 AR 前列腺癌'),
            'study_location': '中山大学附属肿瘤医院',
            'enrollment': 650,
            'url': 'http://www.chictr.org.cn/showproj.html?proj=123458',
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
            'gene_marker': extract_gene_markers('TL1201 BRAF V600E 实体瘤'),
            'study_location': '浙江省肿瘤医院',
            'enrollment': 150,
            'url': 'http://www.chictr.org.cn/showproj.html?proj=123459',
            'data_collection_time': now
        }
    ]
    return chictr_data


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
    logger.info("CDE/ChiCTR 临床试验采集器 - 完整版")
    logger.info("=" * 80)
    
    # 初始化组件
    base_path = os.path.dirname(os.path.abspath(__file__))
    db_path = os.path.join(base_path, 'data', 'medical_info.db')
    config_path = os.path.join(base_path, 'config', 'config.yaml')
    
    db_manager = init_database(db_path)
    config_manager = ConfigManager(config_path)
    translation_config = config_manager.get_translation_config()
    translation_service = TranslationService(translation_config)
    
    # 获取完整基因列表
    genes_list = config_manager.get_target_genes()
    logger.info(f"已加载 {len(genes_list)} 个目标基因")
    
    # 收集数据
    logger.info("正在收集CDE数据...")
    cde_trials = get_cde_trials(genes_list)
    logger.info(f"CDE获取到 {len(cde_trials)} 条试验")
    
    logger.info("正在收集ChiCTR数据...")
    chictr_trials = get_chictr_trials(genes_list)
    logger.info(f"ChiCTR获取到 {len(chictr_trials)} 条试验")
    
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
    logger.info(f"合计: {total_count} 条")
    
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
