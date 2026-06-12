#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
优化CDE特殊品种数据处理
1. 改进抗肿瘤药物筛选策略（添加排除关键词）
2. 完善 molecular_target、gene_marker、drug_name_en 列信息
"""

import csv
import re
import os
import logging
from datetime import datetime

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# ========== 优化后的抗肿瘤筛选策略 ==========

# 正向关键词 - 必须明确指向肿瘤/癌症
CANCER_POSITIVE_KEYWORDS = [
    # 癌症/肿瘤通用词
    '癌', '肿瘤', '癌症', '恶性肿瘤', '瘤',
    # 血液肿瘤
    '白血病', '淋巴瘤', '骨髓瘤', '多发性骨髓瘤', '骨髓增生异常综合征',
    'MDS', '急性髓系白血病', 'AML', '急性淋巴细胞白血病', 'ALL',
    '慢性髓细胞白血病', 'CML', '慢性淋巴细胞白血病', 'CLL',
    '霍奇金', '非霍奇金', '滤泡性淋巴瘤', '弥漫大B细胞淋巴瘤',
    # 实体瘤 - 具体癌症类型
    '非小细胞肺癌', 'NSCLC', '小细胞肺癌', 'SCLC', '肺癌',
    '乳腺癌', '三阴性乳腺癌', 'HER2阳性乳腺癌',
    '肝细胞癌', '肝癌', 'HCC',
    '胃癌', '胃食管结合部癌', '食管鳞癌', '食管癌',
    '结直肠癌', '结肠癌', '直肠癌', 'CRC',
    '胰腺癌', '胰腺导管腺癌',
    '胆管癌', '胆道癌', '胆囊癌',
    '肾癌', '肾细胞癌', 'RCC',
    '尿路上皮癌', '肾盂癌', '输尿管癌', '膀胱癌',
    '前列腺癌', '去势抵抗性前列腺癌', 'CRPC',
    '卵巢癌', '宫颈癌', '子宫内膜癌', '子宫癌',
    '黑色素瘤', '恶性黑色素瘤',
    '脑癌', '胶质瘤', '胶质母细胞瘤', 'GBM',
    '头颈癌', '鼻咽癌', '甲状腺癌', '甲状腺髓样癌',
    '间皮瘤', '胸膜间皮瘤',
    '骨肉瘤', '尤文肉瘤', '脂肪肉瘤', '滑膜肉瘤',
    '胃肠道间质瘤', 'GIST',
    '壶腹癌', '十二指肠癌',
    '神经内分泌瘤', 'NET', '神经内分泌肿瘤',
    '默克尔细胞癌', '基底细胞癌', '鳞状细胞癌',
    '腺癌', '鳞癌', '实体瘤',
    # 转移相关
    '转移性', '晚期', '复发', '难治性',
    # 基因/靶点相关（仅作辅助，需要结合癌症词）
    'EGFR', 'ALK', 'ROS1', 'RET', 'MET', 'HER2', 'ERBB2',
    'PD-1', 'PD-L1', 'BCMA', 'CD38', 'CD20', 'CD19',
    'VEGFR', 'FGFR', 'NTRK', 'KRAS', 'BRAF', 'MEK',
    'CDK4', 'CDK6', 'PIK3CA', 'PTEN', 'BRCA', 'PARP',
    'IDH1', 'IDH2', 'mTOR', 'AKT', 'BTK', 'JAK',
    'FLT3', 'KIT', 'PDGFR', 'TKI',
    # 免疫治疗相关（辅助）
    '免疫检查点抑制剂', '免疫治疗', 'CAR-T', 'CAR T',
    'ADC', '抗体药物偶联物', '单抗', '单克隆抗体',
    '抑制剂', '激动剂', '拮抗剂'
]

# 反向排除词 - 明确非肿瘤疾病
CANCER_NEGATIVE_KEYWORDS = [
    # 感染/传染病
    '肺炎', '结核', '麻风', 'HIV', '艾滋病', '乙肝',
    '肝炎', '感染', '抗菌', '抗病毒', '抗生素',
    '细菌', '病毒', '真菌', '寄生虫', '疟疾', '流感',
    '新冠', 'COVID', '冠状病毒',
    # 心血管
    '高血压', '心力衰竭', '心衰', '心肌', '心肌病',
    '冠心病', '心绞痛', '心肌梗死', '心律失常',
    '肥厚型', '扩张型', '缺血性', '瓣膜病',
    # 代谢/内分泌
    '糖尿病', '甲状腺功能', '甲亢', '甲减',
    '骨质疏松', '肥胖', '高脂血症', '痛风',
    # 自身免疫/炎症
    '类风湿', '关节炎', '红斑狼疮', 'SLE',
    '重症肌无力', '自身免疫', '免疫性', '银屑病',
    '强直性脊柱炎', '干燥综合征', '硬皮病',
    '多发性硬化', 'MS', '炎症性肠病', '克罗恩',
    '溃疡性结肠炎', 'UC',
    # 呼吸
    '哮喘', 'COPD', '慢性阻塞', '肺气肿',
    '支气管炎', '过敏性鼻炎',
    # 消化
    '胃病', '胃炎', '胃溃疡', '肠道', '肠易激',
    # 血液（非肿瘤）
    '贫血', '溶血性贫血', '缺铁性', '凝血', '血友病',
    '血小板减少', '中性粒细胞减少',
    # 神经/精神
    '癫痫', '偏头痛', '阿尔茨海默', '帕金森',
    '抑郁症', '精神分裂', '焦虑', '失眠',
    # 眼科
    '青光眼', '白内障', '黄斑', '视网膜',
    # 肾/泌尿
    '肾移植', '肾衰', '肾病', '前列腺增生',
    # 生殖/产科
    '避孕', '不孕', '月经', '妊娠', '早产',
    # 皮肤
    '湿疹', '皮炎', '痤疮', '白癜风',
    # 其他
    '高血压', '糖尿病', '痛风', '骨质疏松',
    '疫苗', '脱敏', '器官移植', '排斥反应',
    '伤口愈合', '镇痛', '麻醉', '止吐', '止泻'
]

# 肿瘤相关疾病类型词（用于更精准的匹配）
CANCER_DISEASE_TYPES = [
    '癌', '肿瘤', '瘤', '白血病', '淋巴瘤', '骨髓瘤',
    '肺癌', '肝癌', '胃癌', '肠癌', '乳腺癌', '胰腺癌',
    '食管癌', '肾癌', '膀胱癌', '前列腺癌', '卵巢癌',
    '宫颈癌', '黑色素瘤', '胶质瘤', '头颈癌', '鼻咽癌',
    '甲状腺癌', '肉瘤', '神经内分泌', '间皮瘤',
    'NSCLC', 'SCLC', 'HCC', 'CRC', 'RCC', 'MDS', 'AML', 'ALL', 'CML', 'CLL',
    'GIST', 'NET', 'GBM', 'CRPC', 'ADC',
    '非小细胞', '小细胞', '腺鳞', '鳞状细胞', '基底细胞',
    '默克尔细胞', '胶质母细胞瘤', '少突胶质',
    '导管腺癌', '乳头状', '滤泡状', '髓样癌',
    '尿路上皮', '移行细胞', '肾细胞', '肝细胞',
    '胰腺导管', '胰腺神经内分泌', '胃肠胰神经内分泌',
    '霍奇金', '非霍奇金', '弥漫大B', '滤泡性淋巴瘤',
    '套细胞', '边缘区', '小淋巴细胞', '淋巴浆细胞',
    '华氏巨球蛋白血症', '原发纵隔大B',
    '急性髓系', '急性淋巴', '慢性髓系', '慢性淋巴',
    '骨髓增殖', '骨髓增生异常', '浆细胞骨髓瘤',
    '尤文肉瘤', '骨肉瘤', '软骨肉瘤', '横纹肌肉瘤',
    '脂肪肉瘤', '滑膜肉瘤', '恶性胸膜间皮瘤',
    '促结缔组织增生性小圆细胞肿瘤', '横纹肌样',
    '视网膜母细胞瘤', '神经母细胞瘤', '肾母细胞瘤',
    '肝母细胞瘤', '胰母细胞瘤', '胸膜肺母细胞瘤'
]

# 强癌症特异性信号（这些几乎只在癌症适应症中出现）
STRONG_CANCER_SIGNALS = [
    # 癌症特异性基因突变
    'KRAS G12C', 'KRAS G12D', 'KRAS G12V',
    'BRAF V600', 'BRAF V600E', 'BRAF V600K',
    'EGFR T790M', 'EGFR C797S', 'EGFR L858R', 'EGFR 19del',
    'EGFR 20号外显子插入', 'EGFR 20外显子插入',
    'exon 19 deletion', 'exon 20 insertion',
    'IDH1突变', 'IDH2突变',
    'BRCA突变', 'BRCA1突变', 'BRCA2突变',
    'HRD阳性', '同源重组缺陷',
    'PIK3CA突变',
    'NTRK融合', 'NTRK基因融合',
    'ALK融合', 'ROS1融合', 'RET融合',
    'FGFR2融合', 'FGFR融合',
    'FLT3-ITD', 'FLT3突变',
    'NPM1突变', 'CEBPA突变',
    'MET exon 14', 'MET 14外显子', 'MET扩增',
    'HER2扩增', 'HER2过表达', 'HER2阳性',
    'PD-L1 TPS', 'PD-L1 CPS', 'PD-L1阳性',
    # 癌症特异性生物标志物
    'MSI-H', 'dMMR', 'TMB-H', '微卫星不稳定性', '错配修复缺陷',
    # 化疗药物组合（仅用于癌症）
    '奥沙利铂', '伊立替康', '顺铂', '卡铂', '紫杉醇', '多西他赛',
    '吉西他滨', '氟尿嘧啶', '5-FU', '卡培他滨',
    '培美曲塞', '依托泊苷', '伊立替康', '拓扑替康',
    '阿糖胞苷', '柔红霉素', '去甲氧柔红霉素',
    '美法仑', '环磷酰胺', '异环磷酰胺',
    # CLDN18.2是胃癌特异性靶点
    'CLDN18.2', 'Claudin 18.2', 'CLDN18',
    # 癌症疾病描述的中文表达
    '晚期实体瘤', '实体瘤', '恶性肿瘤', '复发难治', '复发/难治',
    '复发或难治', '转移性', '不可切除', '局部晚期'
]

# 化疗药物（这些药物本身就是化疗药，出现即强暗示癌症治疗）
CHEMOTHERAPY_DRUGS = [
    '奥沙利铂', '伊立替康', '顺铂', '卡铂', '紫杉醇', '多西他赛',
    '吉西他滨', '氟尿嘧啶', '卡培他滨', '培美曲塞', '依托泊苷',
    '阿糖胞苷', '柔红霉素', '美法仑', '环磷酰胺', '异环磷酰胺',
    '拓扑替康', '长春瑞滨', '长春新碱', '达卡巴嗪', '替莫唑胺',
    '丝裂霉素', '博来霉素', '表柔比星', '多柔比星', '米托蒽醌',
    '左亚叶酸钙', '亚叶酸钙', '奥曲肽', '兰瑞肽'
]


def is_anticancer_drug(drug_name: str, indication: str) -> bool:
    """
    优化后的抗肿瘤药物判断
    策略：
    1. 检查是否有强癌症特异性信号（如KRAS G12C、化疗药物组合等）
    2. 检查是否有明确的肿瘤/癌症相关词
    3. 检查是否有反向排除词，且没有癌症相关词
    """
    if not indication and not drug_name:
        return False

    name_lower = drug_name.lower() if drug_name else ''
    indication_lower = indication.lower() if indication else ''
    combined_lower = name_lower + ' ' + indication_lower

    # 特殊情况："氯法齐明软胶囊"中的"瘤"只是"麻风瘤"的一部分，单独处理
    if '氯法齐明' in combined_lower or '麻风' in combined_lower:
        # 麻风病不是癌症，除非同时有其他癌症词
        has_real_cancer = False
        for disease in ['癌', '肿瘤', '白血病', '淋巴瘤', '骨髓瘤',
                        '肺癌', '肝癌', '胃癌', 'NSCLC', 'SCLC', '黑色素瘤',
                        '胰腺癌', '结直肠癌', 'CRC', '乳腺癌', 'HCC']:
            if disease.lower() in combined_lower:
                has_real_cancer = True
                break
        if not has_real_cancer:
            return False

    # 特殊情况：子宫肌（如子宫肌瘤）- 不是癌症
    if '子宫肌' in combined_lower and not any(
        disease in combined_lower for disease in
        ['癌', '白血病', '淋巴瘤', '骨髓瘤', '肿瘤', 'NSCLC', 'SCLC']
    ):
        return False

    # 特殊情况：GBM在肾病中表示"肾小球基底膜"，不是胶质母细胞瘤
    if ('肾小球' in combined_lower or '基底膜' in combined_lower or
        '抗gbm' in combined_lower or 'gbm病' in combined_lower):
        # 检查是否同时有真正的癌症词
        has_real_cancer_for_gbm = False
        for disease in ['癌', '肿瘤', '白血病', '淋巴瘤', '骨髓瘤',
                        'NSCLC', 'SCLC', '黑色素瘤', '胶质母细胞瘤']:
            if disease.lower() in combined_lower:
                has_real_cancer_for_gbm = True
                break
        if not has_real_cancer_for_gbm:
            return False

    # 步骤1：检查强癌症特异性信号 → 直接判定为抗肿瘤
    for signal in STRONG_CANCER_SIGNALS:
        if signal.lower() in combined_lower:
            # 但要排除一些明确的非肿瘤情况
            # 如"HIV-1暴露前预防"不应该被KRAS相关词影响
            if 'HIV' in combined_lower and not any(
                disease in combined_lower for disease in
                ['癌', '肿瘤', '白血病', '淋巴瘤', '骨髓瘤', '肉瘤']
            ):
                continue
            return True

    # 检查"含铂化疗"、"PD-(L)1抑制剂"等组合治疗模式
    if ('含铂化疗' in combined_lower or '铂类化疗' in combined_lower or
        'PD-（L）1' in combined_lower or 'PD-(L)1' in combined_lower or
        'pd-(l)1' in combined_lower):
        # 同时需要检查是否有反向词覆盖
        has_override_negative = False
        for neg in ['HIV', '感染', '肺炎', '类风湿', '自身免疫',
                     '糖尿病', '高血压', '移植', '疫苗']:
            if neg.lower() in combined_lower:
                has_override_negative = True
                break
        if not has_override_negative:
            return True

    # 步骤2：检查是否有明确的肿瘤/癌症词
    has_cancer_disease = False
    for disease in CANCER_DISEASE_TYPES:
        if disease.lower() in combined_lower:
            has_cancer_disease = True
            break

    if has_cancer_disease:
        return True

    # 步骤3：检查化疗药物组合（2种或以上化疗药同时出现）
    chemo_count = 0
    for drug in CHEMOTHERAPY_DRUGS:
        if drug in combined_lower:
            chemo_count += 1
            if chemo_count >= 2:
                return True

    # 步骤4：如果有反向词且没有癌症词 → 不是抗肿瘤
    has_negative = False
    for neg_kw in CANCER_NEGATIVE_KEYWORDS:
        if neg_kw.lower() in combined_lower:
            has_negative = True
            break

    if has_negative:
        return False

    # 步骤5：如果只有分子靶点词但没有癌症词 → 保守判定不是抗肿瘤
    # （如某些自身免疫病药物也会使用"单抗"、"抑制剂"等词）
    return False


# ========== 提取 molecular_target、gene_marker、drug_name_en ==========

# 分子靶点关键词
MOLECULAR_TARGETS = [
    'EGFR', 'HER2', 'ERBB2', 'HER3', 'HER4',
    'ALK', 'ROS1', 'RET', 'MET', 'NTRK', 'NTRK1', 'NTRK2', 'NTRK3',
    'KRAS', 'HRAS', 'NRAS', 'BRAF', 'MEK', 'MAPK',
    'PIK3CA', 'PI3K', 'AKT', 'mTOR', 'PTEN',
    'BRCA', 'BRCA1', 'BRCA2', 'PARP', 'ATM', 'ATR',
    'VEGFA', 'VEGFR', 'VEGFR1', 'VEGFR2', 'VEGFR3',
    'FGFR', 'FGFR1', 'FGFR2', 'FGFR3', 'FGFR4',
    'PD-1', 'PD-L1', 'PD1', 'PDL1',
    'CTLA-4', 'CTLA4', 'LAG-3', 'LAG3', 'TIGIT', 'TIM-3',
    'CD38', 'CD20', 'CD19', 'CD22', 'CD30', 'CD33', 'CD123',
    'BCMA', 'GPRC5D', 'FAP', 'CEA', 'MUC1',
    'DLL3', 'DLL4', 'Jagged', 'Notch',
    'Wnt', 'Beta-catenin',
    'JAK', 'JAK1', 'JAK2', 'TYK2', 'STAT',
    'FLT3', 'KIT', 'PDGFR', 'PDGFRA', 'PDGFRB',
    'c-Met', 'cMET', 'c-MYC', 'MYC',
    'IDH1', 'IDH2', 'IDH',
    'BTK', 'ITK', 'TXK',
    'Bcl-2', 'BCL2', 'Bcl-xL', 'BCL-xL', 'MCL-1',
    'APRIL', 'BAFF', 'BAFF-R',
    'CCR4', 'CCR5', 'CCR8', 'CXCR4', 'CXCR7',
    'CEACAM5', 'TROP2', 'TF', '组织因子',
    'Claudin 18.2', 'CLDN18.2', 'CLDN18',
    'HER2-low', 'HER2低表达'
]

# 基因标志物相关模式
GENE_MARKER_PATTERNS = [
    # 基因突变
    r'(EGFR|KRAS|BRAF|PIK3CA|NRAS|HRAS|FLT3|NPM1|RUNX1|DNMT3A|TET2|IDH1|IDH2|JAK2|CALR|MPL|KIT|TP53|BRCA1|BRCA2|PTEN|ATM|ATR|MYC|MYCN|RB|APC|CTNNB1|SMAD4|ARID1A|PIK3R1|NF1|STK11|KEAP1|NFE2L2|SMARCA4|ARID2|PBRM1|SETD2|KMT2C|KMT2D)\s*[突突变变]',
    # 融合基因
    r'(ALK|ROS1|RET|NTRK1|NTRK2|NTRK3|FGFR1|FGFR2|FGFR3|BCR|ABL|BCR-ABL|ETV6|RUNX1|MLL|KMT2A)\s*[融融]合',
    # 扩增/过表达
    r'(HER2|ERBB2|MYC|MYCN|MET|EGFR|CCND1|CCNE1|MDM2|MDM4)\s*[扩扩]增',
    # 蛋白表达/状态
    r'(HER2|ERBB2)\s*(阳性|阴性|低表达|过表达|\+\+\+|\+\+|\+|3\+|2\+|1\+|0)',
    r'(PD-L1|PDL1)\s*(阳性|阴性|表达|\%|TPS|CPS)',
    # MSI/dMMR
    r'(MSI-H|MSI|dMMR|MMR|pMMR|MSI-L)',
    # TMB
    r'(TMB|肿瘤突变负荷)',
    # 其他标志物
    r'(HRD|同源重组缺陷|BRCAness)',
    r'(NTRK|神经营养受体酪氨酸激酶)\s*[融融]合',
    r'(FGFR|成纤维细胞生长因子受体)\s*[融融]合|突突变变',
    r'(PIK3CA)\s*[突突变变]',
    r'(KRAS)\s*G12[CDAVRS]',
    r'(BRAF)\s*V600E',
    r'(EGFR)\s*(外显子|exon)\s*19\s*缺失',
    r'(EGFR)\s*(外显子|exon)\s*21\s*(L858R|L861Q)',
    r'(EGFR)\s*(外显子|exon)\s*20\s*插入',
    r'(T790M|C797S|L858R|19del|ex19del)',
    # 中文基因名
    r'(表皮生长因子受体|人表皮生长因子受体2|间变性淋巴瘤激酶|c-ros癌基因1|转染期间重排|酪氨酸激酶受体|B-Raf原癌基因|KRAS原癌基因|磷脂酰肌醇-3-激酶催化亚基α|蛋白激酶B|雷帕霉素靶蛋白|乳腺癌基因|聚腺苷二磷酸核糖聚合酶|布鲁顿酪氨酸激酶|FMS样酪氨酸激酶3|Janus激酶|信号转导及转录激活蛋白|程序性死亡受体1|程序性死亡配体1|细胞毒性T淋巴细胞相关蛋白4|B淋巴细胞抗原|B细胞成熟抗原|分化簇)\s*[突突变变|融融]合|阳阳|阴阴|过过|表表]',
]

# 从药物名称中提取英文部分
def extract_english_name(drug_name: str) -> str:
    """从药物名称中提取英文部分作为drug_name_en"""
    if not drug_name:
        return ''
    
    # 模式1：括号中的英文 如"氢溴酸尼罗司他片（Nirogacestat）"
    paren_match = re.search(r'[（(]\s*([A-Za-z][A-Za-z0-9\-]*)\s*[)）]', drug_name)
    if paren_match:
        return paren_match.group(1).strip()
    
    # 模式2：纯英文或英文开头的药名 如"Aficamten片"、"TQB3454片"
    eng_match = re.search(r'^([A-Za-z][A-Za-z0-9\s\-_/]*[A-Za-z0-9])', drug_name)
    if eng_match and len(eng_match.group(1)) > 2:
        return eng_match.group(1).strip()
    
    # 模式3：名称中的大写字母+数字代码 如"注射用KJ103"、"BAY 2433334片"
    code_match = re.search(r'([A-Z]{2,5}[\s\-]?\d{3,6}[A-Za-z]?)', drug_name)
    if code_match:
        return code_match.group(1).strip()
    
    # 模式4：完全英文药名
    if all(not ('\u4e00' <= c <= '\u9fff') for c in drug_name):
        return drug_name.strip()
    
    return ''


def extract_molecular_target(drug_name: str, indication: str) -> str:
    """从药物名称和适应症中提取分子靶点"""
    if not indication and not drug_name:
        return ''
    
    combined_text = (drug_name + ' ' + indication)
    combined_lower = combined_text.lower()
    
    found_targets = []
    
    for target in MOLECULAR_TARGETS:
        target_lower = target.lower()
        # 使用词边界匹配避免部分匹配
        if re.search(r'\b' + re.escape(target_lower) + r'\b', combined_lower):
            if target not in found_targets:
                found_targets.append(target)
        # 中文匹配
        elif target_lower in combined_lower and len(target) > 3:
            normalized = target.upper().replace('-', '')
            if normalized not in [t.upper().replace('-', '') for t in found_targets]:
                found_targets.append(target)
    
    # 去重（处理PD-1和PD1等同义）
    normalized_targets = []
    seen = set()
    for target in found_targets:
        norm = target.upper().replace('-', '').replace(' ', '')
        if norm not in seen:
            seen.add(norm)
            normalized_targets.append(target)
    
    return '; '.join(normalized_targets) if normalized_targets else ''


def extract_gene_marker(drug_name: str, indication: str) -> str:
    """从药物名称和适应症中提取基因标志物"""
    if not indication and not drug_name:
        return ''

    combined_text = (drug_name + ' ' + indication)
    combined_lower = combined_text.lower()

    found_markers = []

    # 关键词列表 - (搜索关键词, 标准化显示名称)
    marker_keywords = [
        # RAS突变
        ('KRAS G12C', 'KRAS G12C突变'),
        ('KRAS G12D', 'KRAS G12D突变'),
        ('KRAS G12V', 'KRAS G12V突变'),
        ('KRAS突变', 'KRAS突变'),
        ('BRAF V600E', 'BRAF V600E突变'),
        ('BRAF V600', 'BRAF V600突变'),
        ('BRAF突变', 'BRAF突变'),
        ('NRAS突变', 'NRAS突变'),
        ('HRAS突变', 'HRAS突变'),

        # EGFR相关
        ('EGFR 20号外显子插入', 'EGFR 20号外显子插入突变'),
        ('EGFR 20外显子插入', 'EGFR 20号外显子插入突变'),
        ('EGFR外显子20插入', 'EGFR 20号外显子插入突变'),
        ('EGFR 19外显子缺失', 'EGFR 19号外显子缺失'),
        ('EGFR外显子19缺失', 'EGFR 19号外显子缺失'),
        ('EGFR L858R', 'EGFR L858R突变'),
        ('EGFR T790M', 'EGFR T790M突变'),
        ('EGFR C797S', 'EGFR C797S突变'),
        ('EGFR突变', 'EGFR突变'),
        ('表皮生长因子受体突变', 'EGFR突变'),

        # IDH相关
        ('IDH1突变', 'IDH1突变'),
        ('IDH2突变', 'IDH2突变'),

        # BRCA相关
        ('BRCA突变', 'BRCA突变'),
        ('BRCA1突变', 'BRCA1突变'),
        ('BRCA2突变', 'BRCA2突变'),
        ('HRD阳性', 'HRD阳性'),
        ('同源重组缺陷', '同源重组缺陷(HRD)'),

        # HER2相关
        ('HER2阳性', 'HER2阳性'),
        ('HER2阴性', 'HER2阴性'),
        ('HER2低表达', 'HER2低表达'),
        ('HER2过表达', 'HER2过表达'),
        ('HER2扩增', 'HER2扩增'),

        # ALK/ROS1/RET/NTRK融合
        ('ALK融合', 'ALK融合'),
        ('ALK阳性', 'ALK阳性'),
        ('ROS1融合', 'ROS1融合'),
        ('ROS1阳性', 'ROS1阳性'),
        ('RET融合', 'RET融合'),
        ('RET阳性', 'RET阳性'),
        ('NTRK融合', 'NTRK融合'),
        ('NTRK基因融合', 'NTRK基因融合'),
        ('FGFR融合', 'FGFR融合'),
        ('FGFR2融合', 'FGFR2融合'),
        ('FGFR突变', 'FGFR突变'),

        # PD-L1相关
        ('PD-L1 TPS', 'PD-L1 TPS表达'),
        ('PD-L1 CPS', 'PD-L1 CPS表达'),
        ('PD-L1阳性', 'PD-L1阳性'),
        ('PDL1阳性', 'PD-L1阳性'),
        ('PD-L1表达', 'PD-L1表达'),

        # MET相关
        ('MET扩增', 'MET扩增'),
        ('MET 14外显子跳跃', 'MET 14外显子跳跃突变'),
        ('MET外显子14', 'MET 14外显子跳跃突变'),
        ('MET突变', 'MET突变'),

        # PIK3CA
        ('PIK3CA突变', 'PIK3CA突变'),

        # FLT3/NPM1
        ('FLT3-ITD', 'FLT3-ITD突变'),
        ('FLT3突变', 'FLT3突变'),
        ('NPM1突变', 'NPM1突变'),

        # MSI/dMMR/TMB
        ('MSI-H', 'MSI-H（高微卫星不稳定性）'),
        ('MSI-High', 'MSI-H'),
        ('微卫星不稳定性高', 'MSI-H'),
        ('dMMR', 'dMMR（错配修复缺陷）'),
        ('错配修复缺陷', 'dMMR（错配修复缺陷）'),
        ('TMB-H', 'TMB-H（高肿瘤突变负荷）'),
        ('TMB高', 'TMB-H（高肿瘤突变负荷）'),
        ('肿瘤突变负荷高', 'TMB-H（高肿瘤突变负荷）'),

        # CEA
        ('CEA阳性', 'CEA阳性'),
        ('CEACAM5阳性', 'CEACAM5阳性'),

        # CLDN18.2
        ('CLDN18.2阳性', 'CLDN18.2阳性'),
        ('CLDN18.2', 'CLDN18.2阳性'),

        # p53
        ('TP53突变', 'TP53突变'),
        ('p53突变', 'p53突变'),
    ]

    for search_kw, display_name in marker_keywords:
        if search_kw.lower() in combined_lower:
            if display_name not in found_markers:
                found_markers.append(display_name)

    # 去重并限制数量
    unique_markers = list(dict.fromkeys(found_markers))

    return '; '.join(unique_markers[:5]) if unique_markers else ''


# ========== 主处理流程 ==========

def process_csv_data(input_path: str, output_path: str):
    """处理CSV数据，优化筛选并完善信息列"""
    logger.info(f"读取 {input_path}...")
    
    all_rows = []
    with open(input_path, 'r', encoding='utf-8-sig') as f:
        reader = csv.DictReader(f)
        for row in reader:
            all_rows.append(row)
    
    logger.info(f"原始数据: {len(all_rows)} 条")
    
    # 统计
    stats = {
        '优先审评_total': 0,
        '优先审评_anti': 0,
        '突破性治疗_total': 0,
        '突破性治疗_anti': 0,
        'targets_filled': 0,
        'gene_markers_filled': 0,
        'english_names_filled': 0,
        'excluded_drugs': []
    }
    
    # 处理每条记录
    processed_rows = []
    for idx, row in enumerate(all_rows):
        drug_name = row['药物名称']
        indication = row['拟定适应症']
        drug_type = row['名单类型']
        
        # 优化的抗肿瘤判定
        is_cancer = is_anticancer_drug(drug_name, indication)
        
        # 提取信息
        molecular_target = extract_molecular_target(drug_name, indication)
        gene_marker = extract_gene_marker(drug_name, indication)
        drug_name_en = extract_english_name(drug_name)
        
        # 统计
        if drug_type == '优先审评':
            stats['优先审评_total'] += 1
            if is_cancer:
                stats['优先审评_anti'] += 1
        elif drug_type == '突破性治疗':
            stats['突破性治疗_total'] += 1
            if is_cancer:
                stats['突破性治疗_anti'] += 1
        
        if molecular_target:
            stats['targets_filled'] += 1
        if gene_marker:
            stats['gene_markers_filled'] += 1
        if drug_name_en:
            stats['english_names_filled'] += 1
        
        # 记录被排除的药物（之前被误判为True，现在改为False的）
        old_value = str(row.get('是否抗肿瘤', '')).strip().lower()
        if old_value in ['true', 'yes', '1', '是'] and not is_cancer:
            stats['excluded_drugs'].append(drug_name)
        
        processed_row = {
            '名单类型': drug_type,
            '序号': row['序号'],
            '药物名称': drug_name,
            'drug_name_en': drug_name_en,
            '受理号': row['受理号'],
            '申请人': row['申请人'],
            '申请日期': row['申请日期'],
            '拟定适应症': indication,
            'molecular_target': molecular_target,
            'gene_marker': gene_marker,
            '是否抗肿瘤': 'True' if is_cancer else 'False'
        }
        processed_rows.append(processed_row)
    
    # 写入新的CSV
    fieldnames = ['名单类型', '序号', '药物名称', 'drug_name_en', '受理号', '申请人',
                  '申请日期', '拟定适应症', 'molecular_target', 'gene_marker', '是否抗肿瘤']
    
    logger.info(f"写入 {output_path}...")
    with open(output_path, 'w', encoding='utf-8-sig', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(processed_rows)
    
    # 输出统计
    logger.info(f"\n=== 处理结果统计 ===")
    logger.info(f"  优先审评: {stats['优先审评_total']} 条，抗肿瘤: {stats['优先审评_anti']} 条")
    logger.info(f"  突破性治疗: {stats['突破性治疗_total']} 条，抗肿瘤: {stats['突破性治疗_anti']} 条")
    logger.info(f"  总计抗肿瘤: {stats['优先审评_anti'] + stats['突破性治疗_anti']} 条")
    logger.info(f"  填写 molecular_target: {stats['targets_filled']} 条")
    logger.info(f"  填写 gene_marker: {stats['gene_markers_filled']} 条")
    logger.info(f"  填写 drug_name_en: {stats['english_names_filled']} 条")
    
    if stats['excluded_drugs']:
        logger.info(f"\n  被排除的药物（原误判为抗肿瘤）:")
        for drug in stats['excluded_drugs'][:20]:
            logger.info(f"    - {drug}")
        if len(stats['excluded_drugs']) > 20:
            logger.info(f"    ... 还有 {len(stats['excluded_drugs']) - 20} 条")
    
    return processed_rows, stats


def update_database(csv_path: str, db_path: str):
    """从CSV更新数据库"""
    logger.info(f"\n更新数据库 {db_path}...")
    
    import os
    import sys
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    from src.database import init_database
    
    db = init_database(db_path)
    conn = db.connect()
    cursor = conn.cursor()
    
    # 清空旧数据
    cursor.execute("DELETE FROM cde_special_drugs")
    conn.commit()
    
    count = 0
    with open(csv_path, 'r', encoding='utf-8-sig') as f:
        reader = csv.DictReader(f)
        for row in reader:
            is_cancer_val = row.get('是否抗肿瘤', 'False')
            is_cancer = str(is_cancer_val).strip().lower() in ['true', 'yes', '1', '是']
            
            if not is_cancer:
                continue
            
            record = {
                'cde_id': f"CDE-{row['名单类型'][:2]}-{row['序号']}",
                'drug_name': row['药物名称'],
                'drug_name_en': row.get('drug_name_en', ''),
                'drug_type': row['名单类型'],
                'indication': row['拟定适应症'],
                'applicant': row['申请人'],
                'application_date': row['申请日期'],
                'acceptance_number': row['受理号'],
                'approval_date': '',
                'status': '已纳入',
                'priority_type': row['名单类型'] if row['名单类型'] == '优先审评' else '',
                'breakthrough_type': row['名单类型'] if row['名单类型'] == '突破性治疗' else '',
                'trial_info': '',
                'molecular_target': row.get('molecular_target', ''),
                'gene_marker': row.get('gene_marker', ''),
                'reference_drug': '',
                'description': '',
                'detail_url': '',
                'created_at': datetime.now().strftime('%Y-%m-%d'),
                'updated_at': datetime.now().strftime('%Y-%m-%d')
            }
            try:
                db.execute_insert('cde_special_drugs', record)
                count += 1
            except Exception as e:
                logger.error(f"插入失败: {row['药物名称']} - {e}")
    
    conn.commit()
    logger.info(f"数据库更新完成: {count} 条记录")
    
    # 验证
    rows = db.execute_query(
        "SELECT drug_type, COUNT(*) as cnt FROM cde_special_drugs GROUP BY drug_type"
    )
    for row in rows:
        logger.info(f"  {row['drug_type']}: {row['cnt']} 条")
    
    # 检查新列填充情况
    target_count = db.execute_query(
        "SELECT COUNT(*) as cnt FROM cde_special_drugs WHERE molecular_target IS NOT NULL AND molecular_target != ''"
    )[0]['cnt']
    gene_count = db.execute_query(
        "SELECT COUNT(*) as cnt FROM cde_special_drugs WHERE gene_marker IS NOT NULL AND gene_marker != ''"
    )[0]['cnt']
    en_count = db.execute_query(
        "SELECT COUNT(*) as cnt FROM cde_special_drugs WHERE drug_name_en IS NOT NULL AND drug_name_en != ''"
    )[0]['cnt']
    
    logger.info(f"\n新列填充统计:")
    logger.info(f"  molecular_target: {target_count}/{count}")
    logger.info(f"  gene_marker: {gene_count}/{count}")
    logger.info(f"  drug_name_en: {en_count}/{count}")
    
    conn.close()
    return count


def sample_check(csv_path: str, sample_count: int = 10):
    """抽样检查处理结果"""
    logger.info(f"\n=== 抽样检查（前{sample_count}条抗肿瘤药物）===")
    
    with open(csv_path, 'r', encoding='utf-8-sig') as f:
        reader = csv.DictReader(f)
        all_rows = list(reader)
    
    cancer_rows = [r for r in all_rows if str(r['是否抗肿瘤']).strip().lower() in ['true', 'yes', '1', '是']]
    
    for row in cancer_rows[:sample_count]:
        logger.info(f"\n药物: {row['药物名称']} ({row['名单类型']})")
        logger.info(f"  英文药名: {row['drug_name_en'] or '(空)'}")
        logger.info(f"  分子靶点: {row['molecular_target'] or '(空)'}")
        logger.info(f"  基因标志物: {row['gene_marker'] or '(空)'}")
        logger.info(f"  适应症: {row['拟定适应症'][:100]}...")
    
    # 检查被排除的非抗肿瘤药物
    logger.info(f"\n=== 被排除的非抗肿瘤药物示例 ===")
    non_cancer_rows = [r for r in all_rows if str(r['是否抗肿瘤']).strip().lower() not in ['true', 'yes', '1', '是']]
    for row in non_cancer_rows[:10]:
        logger.info(f"  {row['药物名称']} - {row['拟定适应症'][:80]}")


if __name__ == '__main__':
    input_csv = 'data/cde_all_drugs_fixed_v3.csv'
    output_csv = 'data/cde_all_drugs_optimized.csv'
    db_path = 'data/medical_info.db'
    
    # 处理CSV数据
    processed_rows, stats = process_csv_data(input_csv, output_csv)
    
    # 更新数据库
    update_database(output_csv, db_path)
    
    # 抽样检查
    sample_check(output_csv)
    
    logger.info(f"\n完成！请在Streamlit中重新导出Excel文件。")
