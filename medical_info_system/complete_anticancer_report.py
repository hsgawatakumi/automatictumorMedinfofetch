"""
NMPA抗肿瘤药物完整增强报告系统
功能：
1. 智能筛选抗肿瘤药物（剔除非抗肿瘤药物）
2. 从NMPA/CDE数据补充批准文号
3. 添加伴随诊断生物标志物匹配（EGFR/ALK/PD-L1/MSI-H等）
4. 按适应症分类（肺癌、乳腺癌、血液肿瘤等）生成专题报告
5. 添加FDA/EMA批准情况的国际对比分析
"""
import sqlite3
import pandas as pd
import re
import os
from datetime import datetime

db_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'data', 'medical_info.db')


# ============================
# 第一部分：抗肿瘤药物筛选
# ============================

# 明确非肿瘤的药物名称（前缀匹配）
DRUG_NAME_BLACKLIST_PREFIX = [
    '菖麻熄风', '二冬汤', '半夏泻心', '泻白', '苓桂术甘',
    '枇杷清肺', '养血祛风', '济川煎', '半夏白术', '一贯煎',
    '玉女煎', '升陷', '芪黄明目', '风叶咳喘', '小儿豉翘',
    '紫贝止咳', '奥兰替', '拈痛祛风', '桂枝汤', '小柴胡',
    '逍遥散', '六味地黄', '补中益气', '归脾汤', '四君子',
    '芍药甘草', '三拗汤', '银翘散', '藿香正气', '小青龙',
    '来特莫韦', '莫博赛妥', '莫诺拉韦', '帕洛韦',
    '玛巴洛沙韦', '奥司他韦', '扎那米韦', '帕拉米韦',
    '艾沙康唑', '泊沙康唑', '伏立康唑', '氟康唑', '伊曲康唑',
    '利奈唑胺', '达托霉素', '替加环素',
    '替尔泊肽', '司美格鲁肽', '利拉鲁肽', '艾塞那肽', '杜拉鲁肽',
    '德谷胰岛素', '甘精胰岛素', '门冬胰岛素', '赖脯胰岛素',
    '地特胰岛素', '二甲双胍', '格列本脲', '格列美脲', '格列吡嗪',
    '格列齐特', '西格列汀', '维格列汀', '沙格列汀',
    '达格列净', '恩格列净', '坎格列净', '卡格列净',
    '索马鲁肽', '胰高糖素',
    '比吉利珠', '度普利尤', '乌帕替尼', '托珠单抗', '古塞奇尤',
    '依奇珠单抗', '司库奇尤', '瑞莎珠单抗', '乌司奴单抗',
    '古塞库单抗', '特诺雅单抗', '依克那肽',
    '西罗莫司', '他克莫司', '环孢素', '吗替麦考酚酯',
    '硫唑嘌呤', '甲氨蝶呤', '来氟米特',
    '阿达木单抗', '英夫利昔单抗', '戈利木单抗', '赛妥珠单抗',
    '奥达特罗', '茚达特罗', '噻托溴铵', '沙美特罗', '福莫特罗',
    '布地奈德', '糠酸氟替卡松', '丙酸氟替卡松', '倍氯米松',
    '孟鲁司特', '扎鲁司特', '色甘酸钠', '酮替芬',
    '奥马珠单抗', '美泊利珠单抗', '瑞利珠单抗',
    '氨氯地平', '硝苯地平', '非洛地平', '贝尼地平', '乐卡地平',
    '缬沙坦', '坎地沙坦', '奥美沙坦', '厄贝沙坦', '氯沙坦',
    '培哚普利', '贝那普利', '雷米普利', '福辛普利', '卡托普利',
    '琥珀酸美托洛尔', '酒石酸美托洛尔', '比索洛尔', '阿替洛尔',
    '卡维地洛', '阿利吉仑',
    '阿托伐他汀', '瑞舒伐他汀', '辛伐他汀', '普伐他汀', '匹伐他汀',
    '利伐沙班', '阿哌沙班', '艾多沙班', '达比加群', '华法林',
    '醋酸氟氢可的松', '地塞米松', '甲泼尼龙', '氢化可的松',
    '左甲状腺素', '丙硫氧嘧啶', '甲巯咪唑',
    '阿仑膦酸钠', '唑来膦酸', '利塞膦酸钠', '伊班膦酸钠', '特立帕肽',
    '吡仑帕奈', '拉考沙胺', '左乙拉西坦', '丙戊酸', '奥卡西平',
    '卡马西平', '苯妥英', '加巴喷丁', '普瑞巴林', '氨己烯酸',
    '氯胺酮', '艾司氯胺酮',
    '美金刚', '多奈哌齐', '卡巴拉汀', '加兰他敏', '利凡斯的明',
    '普拉克索', '罗匹尼罗', '雷沙吉兰', '司来吉兰', '恩他卡朋',
    '左旋多巴', '卡比多巴', '托卡朋',
    '喹硫平', '利培酮', '奥氮平', '氯氮平', '阿立哌唑', '帕利哌酮',
    '氟西汀', '舍曲林', '帕罗西汀', '艾司西酞普兰', '文拉法辛',
    '度洛西汀', '米氮平',
    '西诺氨酯', '地西泮', '氯硝西泮', '阿普唑仑', '佐匹克隆',
    '苯海拉明', '氯雷他定', '西替利嗪', '左西替利嗪',
    '奥美拉唑', '兰索拉唑', '泮托拉唑', '雷贝拉唑', '埃索美拉唑',
    '艾普拉唑', '法莫替丁', '雷尼替丁', '西咪替丁',
    '多潘立酮', '莫沙必利', '伊托必利', '普芦卡必利',
    '秋水仙碱', '别嘌醇', '非布司他', '苯溴马隆',
    '对乙酰氨基酚', '布洛芬', '塞来昔布', '艾瑞昔布', '依托考昔',
    '美洛昔康', '双氯芬酸', '萘普生',
    '阿利西尤单抗', '依洛尤单抗', '波生坦', '安立生坦',
    '马昔腾坦', '司来帕格', '利奥西呱',
    '泊马度胺', '沙利度胺',
    '曲格列汀', '艾塞那肽', '利拉鲁肽', '度拉糖肽', '聚乙二醇洛塞那肽',
    '贝那鲁肽',
    '海曲泊帕', '艾曲泊帕', '罗米司亭',
    '重组人凝血因子', '人凝血因子', '注射用重组人', '重组人尿激酶原',
    '注射用A型肉毒毒素',
    '流感病毒', '灭活疫苗', '鼻喷流感', 'Sabin株', 'HPV',
    '吸附破伤风', '九价人乳头瘤病毒', '四价人乳头瘤病毒',
    '注射用重组人尿激酶原', '绒毛膜促性腺激素',
]

# 明确的抗肿瘤靶点/关键词（用于正向判定）
ANTICANCER_TARGET_KWS = [
    'EGFR', 'ALK', 'ROS1', 'BRAF', 'KRAS', 'NTRK', 'MET', 'RET',
    'HER2', 'HER-2', 'VEGFR', 'VEGF', 'FGFR', 'PDGFR', 'KIT',
    'PD-1', 'PD-L1', 'PDL1', 'CTLA-4', 'CLDN18.2', 'CLDN18',
    'PARP', 'BTK', 'JAK', 'FLT3', 'IDH', 'CDK4', 'CDK6',
    'BCL-2', 'BCL2', 'MCL-1', 'PI3K', 'mTOR', 'AKT',
    'CD19', 'CD20', 'CD22', 'CD30', 'CD33', 'CD38', 'BCMA',
    'SLAMF7', 'PSMA', 'TROP2', 'DLL3', 'FRα', '叶酸受体α',
    'Claudin18.2', 'Claudin 18.2',
    'CAR-T', 'CAR-T细胞', 'CAR T', '嵌合抗原受体',
    'ADC', '抗体药物偶联', '单克隆抗体', '单抗',
    '替尼', '替尼片', '替尼胶囊', '拉非尼', '帕尼', '珠单抗', '昔单抗', '尤单抗',
    '利尤单抗', '奇尤单抗', '瑞利珠', '卡非佐米', '伊沙佐米', '硼替佐米',
    '来那度胺', '泊马度胺',
    '奥希替尼', '吉非替尼', '厄洛替尼', '阿法替尼', '达可替尼',
    '奥希替尼', '阿美替尼', '伏美替尼', '舒沃替尼', '莫博赛替尼',
    '塞瑞替尼', '阿来替尼', '劳拉替尼', '恩曲替尼', '普拉替尼',
    '索托拉西布', '阿代格拉西布', '瑞波替尼',
    '伊布替尼', '泽布替尼', '奥布替尼', '替拉鲁替尼',
    '瑞米布替尼', '尼罗布替尼',
    '卡马替尼', '赛沃替尼', '谷美替尼',
    '维莫非尼', '达拉非尼', '曲美替尼', '比美替尼', '恩考芬尼',
    '厄达替尼', '培米替尼', '英菲格拉替尼', '酒石酸凡瑞格拉替尼',
    '他舒替尼', '替恩戈替尼', '洛布替尼',
    '奥拉帕利', '尼拉帕利', '卢卡帕利', '帕米帕利', '氟唑帕利',
    '艾伏尼布', '恩西地平',
    '维莫德吉', '索尼德吉', '格拉吉布',
    '鲁索替尼', '芦可替尼', '杰克替尼',
    '哌柏西利', '阿贝西利', '瑞博西利', '达尔西利', '瑞波西利',
    '索拉非尼', '舒尼替尼', '帕唑帕尼', '仑伐替尼', '瑞戈非尼',
    '安罗替尼', '阿帕替尼', '呋喹替尼', '索凡替尼', '卡博替尼',
    '伊马替尼', '尼洛替尼', '达沙替尼', '博舒替尼', '普纳替尼',
    '氟马替尼', '阿伐替尼', '瑞派替尼',
    '纳武利尤单抗', '帕博利珠单抗', '特瑞普利单抗', '信迪利单抗',
    '替雷利珠单抗', '卡瑞利珠单抗', '派安普利单抗', '赛帕利单抗',
    '斯鲁利单抗', '舒格利单抗', '阿替利珠单抗', '度伐利尤单抗',
    '阿维鲁单抗', '伊匹木单抗', '曲美木单抗',
    '曲妥珠单抗', '帕妥珠单抗', '恩美曲妥珠单抗', '德曲妥珠单抗',
    '维迪西妥单抗', '伊尼妥单抗', '吡咯替尼', '奈拉替尼', '妥卡替尼',
    '佐妥昔单抗', '注射用维恩妥尤单抗', '注射用维特柯妥拜单抗',
    '镥[177Lu]特昔维匹肽', '戈沙妥珠单抗', '索米妥昔单抗',
    '利妥昔单抗', '奥法妥木单抗', '奥瑞珠单抗', '奥妥珠单抗',
    '格菲妥单抗', '艾可瑞妥单抗', '塔戈妥单抗',
    '达雷妥尤单抗', '伊沙妥昔单抗', '埃罗妥珠单抗',
    '本妥昔单抗', '维布妥昔单抗',
    '贝伐珠单抗', '西妥昔单抗', '帕尼单抗', '尼妥珠单抗',
    '雷莫西尤单抗', '拉莫西鲁单抗',
    '吉瑞替尼', '奎扎替尼', '米哚妥林',
    '阿基仑赛', '瑞基奥仑赛', '替沙仑赛', '赫基仑赛',
    '伊基仑赛', '泽沃基奥仑赛', '纳基奥仑赛',
    '拉罗替尼', '瑞普替尼', '卓乐替尼', '安瑞替尼',
    '硼替佐米', '卡非佐米', '伊沙佐米',
    '塞利尼索', '地塞米松', '来那度胺', '泊马度胺',
    '替莫唑胺', '西达本胺',
    '他莫昔芬', '托瑞米芬', '氟维司群',
    '阿那曲唑', '来曲唑', '依西美坦',
    '阿比特龙', '恩扎卢胺', '阿帕鲁胺', '达罗他胺', '比卡鲁胺',
    '维奈克拉', '维奈妥拉', '维奈托克',
    'MK-3475', 'Pembrolizumab', 'Nivolumab', 'Rituximab',
    'Nirogacestat', 'Iberdomide',
]

# 正向适应症关键词（肿瘤相关）
ONCOLOGY_INDICATION_KWS = [
    '癌', '瘤', '肿瘤', '癌症', '恶性', '肉瘤', '黑色素瘤',
    '淋巴瘤', '白血病', '骨髓瘤', '胶质母细胞瘤', '胶质瘤',
    '骨髓增生异常综合征', 'MDS', '骨髓增殖性疾病', 'MPN',
    '实体瘤', '晚期实体瘤', '转移性实体瘤', '复发难治',
    '复发/难治', '复发或难治', '局部晚期', '转移性', '进展期',
    '非小细胞肺癌', 'NSCLC', '小细胞肺癌', 'SCLC', '肺癌',
    '肝细胞癌', 'HCC', '肝癌', '肝内胆管癌', '胆道癌',
    '乳腺癌', '三阴性乳腺癌', 'HER2阳性', '激素受体阳性',
    '结直肠癌', 'CRC', '结肠癌', '直肠癌', '胃癌', '胃食管结合部',
    '胰腺癌', '前列腺癌', '去势抵抗性前列腺癌', 'mCRPC',
    '卵巢癌', '宫颈癌', '子宫内膜癌', '肾癌', '肾细胞癌',
    '尿路上皮癌', '膀胱癌', '鼻咽癌', '头颈癌', '头颈部鳞癌',
    '甲状腺癌', '甲状腺髓样癌', '神经内分泌瘤', 'NET',
    '默克尔细胞癌', '胃肠道间质瘤', 'GIST',
    'EGFR突变', 'ALK阳性', 'ROS1阳性', 'BRAF V600', 'KRAS G12C',
    'NTRK融合', 'PD-L1阳性', 'MSI-H', 'dMMR', 'TMB-H',
    'BRCA突变', 'HRD阳性', 'HER2阳性', 'HER2低表达',
    'CD20阳性', 'CD30阳性', 'BCMA阳性', 'PSMA阳性',
    'Claudin18.2阳性', 'CLDN18.2阳性', 'TROP2阳性', 'DLL3阳性',
    'FLT3突变', 'IDH1突变', 'IDH2突变', 'JAK2突变',
]

# 排除性适应症关键词（明确非肿瘤）
NON_ONCOLOGY_INDICATION_KWS = [
    '糖尿病', '2型糖尿病', '1型糖尿病', '血糖控制',
    '类风湿关节炎', 'RA', '银屑病', '银屑病关节炎',
    '强直性脊柱炎', '系统性红斑狼疮', 'SLE', '干燥综合征',
    '多发性硬化', 'MS', '重症肌无力',
    '哮喘', 'COPD', '慢性阻塞性肺疾病', '过敏性鼻炎',
    '高血压', '冠心病', '心力衰竭', '房颤',
    '高胆固醇血症', '高脂血症', '动脉粥样硬化',
    '流感', '普通感冒', 'COVID-19', '新冠', '呼吸道感染',
    '带状疱疹', 'HIV', '艾滋病', '乙肝', '丙肝', 'CMV',
    '巨细胞病毒', 'EB病毒', '真菌感染', '细菌感染',
    '骨质疏松', '骨密度', '阿尔茨海默', '帕金森', '癫痫',
    '抑郁症', '焦虑症', '精神分裂', '失眠',
    '胃食管反流', '胃溃疡', '十二指肠溃疡', '消化不良',
    '痛风', '高尿酸血症',
    '甲状腺功能减退', '甲状腺功能亢进',
    '青光眼', '干眼症', '过敏性结膜炎',
    '特发性肺纤维化', 'IPF',
    '杜氏肌营养不良', 'DMD',
    '发作性睡病', '纤维肌痛',
    '血小板减少', '非恶性血小板减少', '再生障碍性贫血',
    '慢性肾病', '糖尿病肾病',
    '更年期综合征', '骨质疏松症', '绝经期',
    '风湿性关节炎', '幼年特发性关节炎',
    '慢性荨麻疹', '特发性荨麻疹',
    '移植', '器官移植', '抗排斥',
    '慢性丙型肝炎', '乙型肝炎',
]


def is_anticancer_drug(row):
    """智能判定是否为抗肿瘤药物"""
    name = str(row.get('drug_name_cn') or '').strip()
    indication = str(row.get('indication') or '').strip()
    mechanism = str(row.get('mechanism_of_action') or '').strip()
    target = str(row.get('molecular_target') or '').strip()
    generic = str(row.get('generic_name_cn') or '').strip()
    brand = str(row.get('brand_name_cn') or '').strip()

    all_text = ' '.join([name, indication, mechanism, target, generic, brand]).lower()

    # 简化名称：去除剂型前缀（注射用、片、胶囊等）用于匹配
    # 例："注射用卡瑞利珠单抗" -> "卡瑞利珠单抗"
    simple_name = name
    if simple_name.startswith('注射用'):
        simple_name = simple_name[3:]

    # 黑名单：明确非肿瘤（使用前缀匹配，避免"卡瑞利珠单抗"误匹配"瑞利珠单抗"）
    for prefix in DRUG_NAME_BLACKLIST_PREFIX:
        if name.startswith(prefix):
            return False
        if simple_name.startswith(prefix):
            return False

    # 排除：中药剂型+无肿瘤适应症
    is_tcm_form = any(kw in name for kw in ['汤颗粒', '熄风', '泻白', '半夏泻心',
                                              '二冬汤', '苓桂术甘', '枇杷清肺',
                                              '养血祛风', '济川煎', '一贯煎',
                                              '玉女煎', '升陷汤', '颗粒剂', '中药'])
    if is_tcm_form and not any(kw in all_text for kw in ['癌', '瘤', '肿瘤', '恶性']):
        return False

    # 排除：明确非肿瘤适应症且无肿瘤靶点
    has_non_onco_ind = any(kw.lower() in all_text for kw in NON_ONCOLOGY_INDICATION_KWS)
    has_onco_target = any(kw.lower() in all_text for kw in ANTICANCER_TARGET_KWS)
    has_onco_ind = any(kw.lower() in all_text for kw in ONCOLOGY_INDICATION_KWS)

    if has_non_onco_ind and not has_onco_target and not has_onco_ind:
        return False

    # 正向判定
    if has_onco_target:
        return True

    if has_onco_ind:
        return True

    # 药物名称包含明确抗肿瘤特征词
    if any(kw in name for kw in ['替尼', '单抗', '珠单抗', '昔单抗', '尤单抗',
                                  '利尤单抗', '奇尤单抗', '帕尼', '拉非尼',
                                  '佐米', '非佐米', '帕利', '佐米', '来那度胺',
                                  '泊马度胺', '替莫唑胺', '维奈', '替尼片',
                                  '替尼胶囊', '注射液', '注射用']):
        if not has_non_onco_ind:
            return True
        if has_onco_ind:
            return True

    return False


# ============================
# 第二部分：数据增强系统
# ============================

class DrugDataEnhancer:
    def __init__(self):
        self._init_mappings()

    def _init_mappings(self):
        """初始化所有映射表"""

        # 靶点-生物标志物映射（按优先级）
        self.biomarker_map = {
            'EGFR': ['EGFR 19缺失', 'EGFR exon 19 del', 'EGFR L858R',
                    'EGFR T790M', 'EGFR C797S', 'EGFR exon 20插入'],
            'HER2': ['HER2阳性', 'HER2 3+ IHC', 'HER2扩增', 'HER2过表达', 'HER2低表达'],
            'ALK': ['ALK阳性', 'ALK融合', 'ALK重排', 'EML4-ALK融合'],
            'ROS1': ['ROS1阳性', 'ROS1融合', 'ROS1重排'],
            'NTRK': ['NTRK融合', 'TRK融合', 'TRK阳性', 'NTRK1/NTRK2/NTRK3融合'],
            'BRAF': ['BRAF V600E突变', 'BRAF V600突变', 'BRAF突变阳性'],
            'KRAS': ['KRAS G12C突变', 'KRAS G12D突变', 'KRAS G12V突变', 'KRAS突变'],
            'PI3K': ['PIK3CA突变', 'PI3K通路激活'],
            'mTOR': ['mTOR通路激活', 'TSC1/2突变', 'PTEN缺失'],
            'CDK4': ['CDK4/6扩增', 'RB阳性', 'HR阳性/HER2阴性'],
            'CDK6': ['CDK4/6扩增', 'RB阳性', 'HR阳性/HER2阴性'],
            'VEGF': ['VEGF表达', '微血管密度高'],
            'VEGFR': ['VEGFR表达', 'VEGFR阳性'],
            'FGFR': ['FGFR2融合', 'FGFR3突变', 'FGFR融合', 'FGFR突变'],
            'PARP': ['BRCA突变', 'BRCA阳性', 'HRD阳性', '同源重组修复缺陷',
                    'gBRCA突变', 'sBRCA突变', 'BRCA1突变', 'BRCA2突变', 'PALB2突变'],
            'PD-1': ['PD-L1表达', 'PD-L1阳性', 'PD-L1 TPS≥1%', 'PD-L1 CPS≥1',
                    'PD-L1 TPS≥50%', 'PD-L1 CPS≥10',
                    'MSI-H', 'dMMR', '微卫星高度不稳定',
                    'TMB-H', 'TMB高', '肿瘤突变负荷高'],
            'PD-L1': ['PD-L1阳性', 'PD-L1表达', 'PD-L1 TPS', 'PD-L1 CPS', 'MSI-H', 'dMMR'],
            'CTLA-4': ['PD-L1阳性', 'MSI-H', 'TMB高'],
            'BTK': ['CD20阳性', 'BTK表达', 'B细胞淋巴瘤'],
            'JAK': ['JAK2 V617F突变', 'JAK2突变', 'JAK1激活'],
            'FLT3': ['FLT3-ITD', 'FLT3 TKD突变', 'FLT3突变阳性'],
            'IDH1': ['IDH1 R132H突变', 'IDH1突变阳性'],
            'IDH2': ['IDH2 R140Q突变', 'IDH2突变'],
            'SMO': ['Hedgehog通路激活', 'PTCH1突变', 'SMO突变'],
            'AR': ['AR阳性', 'AR-V7阳性', '去势抵抗性前列腺癌'],
            'ER': ['ER阳性', '雌激素受体阳性', 'HR阳性'],
            'PR': ['PR阳性', '孕激素受体阳性', 'HR阳性'],
            'CLDN18': ['Claudin18.2阳性', 'CLDN18.2阳性', 'Claudin 18.2表达'],
            'DLL3': ['DLL3阳性', 'DLL3表达', 'DLL3高表达'],
            'PSMA': ['PSMA阳性', '前列腺特异性膜抗原表达', 'PSMA PET阳性'],
            'TROP2': ['TROP2阳性', 'TROP2表达'],
            'FR': ['FRα阳性', '叶酸受体α阳性', 'FRα高表达'],
            'MET': ['MET扩增', 'MET exon 14跳变', 'MET 14跳变', 'c-MET阳性'],
            'RET': ['RET融合', 'RET阳性', 'RET重排', 'M918T突变'],
            'BCL-2': ['BCL-2阳性', 'BCL2过表达', 't(14;18)易位'],
            'XPO1': ['XPO1阳性', 'CRM1过表达'],
            'KIT': ['KIT突变', 'KIT D816V', 'CD117阳性'],
            'PDGFR': ['PDGFRα突变', 'PDGFRβ表达'],
        }

        # 伴随诊断检测方法
        self.cd_test_map = {
            'EGFR': ['EGFR PCR检测（如cobas EGFR Mutation Test v2）',
                    'EGFR NGS检测（如FoundationOne CDx）',
                    'EGFR伴随诊断检测'],
            'HER2': ['HER2 IHC检测（如PATHWAY anti-HER2）',
                    'HER2 FISH检测（如INFORM HER2 Dual ISH）',
                    'HER2伴随诊断'],
            'ALK': ['ALK FISH检测（如Vysis ALK Break Apart）',
                    'ALK IHC检测（如VENTANA ALK D5F3）',
                    'ALK NGS检测'],
            'ROS1': ['ROS1 FISH检测', 'ROS1 NGS检测'],
            'NTRK': ['NTRK融合检测（NGS）', 'TRK伴随诊断', 'FoundationOne CDx'],
            'BRAF': ['BRAF V600E检测（如cobas 4800 BRAF V600）', 'BRAF伴随诊断'],
            'KRAS': ['KRAS G12C检测', 'KRAS伴随诊断', 'KRAS NGS检测'],
            'PARP': ['BRCA检测（Myriad myChoice）', 'HRD检测', 'FoundationOne CDx'],
            'PD-1': ['PD-L1 IHC检测（22C3 pharmDx、SP263、SP142、28-8）',
                    'MSI检测（如BAT-25、BAT-26）',
                    'dMMR检测（MLH1、MSH2、MSH6、PMS2）',
                    'TMB检测（NGS panel）'],
            'PD-L1': ['PD-L1 IHC检测（22C3 pharmDx、SP263、SP142）'],
            'FGFR': ['FGFR融合检测（NGS/FISH）', 'FGFR NGS检测'],
            'BTK': ['CD20 IHC检测'],
            'JAK': ['JAK2 V617F检测（PCR/NGS）'],
            'FLT3': ['FLT3 ITD检测', 'FLT3 TKD检测'],
            'IDH1': ['IDH1检测（PCR/NGS）', 'IDH伴随诊断'],
            'CLDN18': ['Claudin18.2 IHC检测（如43-14A抗体）'],
            'MET': ['MET exon 14检测（NGS）', 'MET FISH检测（扩增）'],
            'RET': ['RET融合检测（FISH/NGS）', 'RET NGS检测'],
            'PSMA': ['PSMA PET-CT（如[18F]DCFPyL、[68Ga]PSMA-11）', 'PSMA IHC检测'],
            'DLL3': ['DLL3 IHC检测'],
            'FR': ['FRα IHC检测', '叶酸受体α检测'],
            'KIT': ['KIT D816V检测', 'CD117 IHC检测'],
        }

        # 适应症分类（主分类→子类）
        self.indication_categories = {
            '非小细胞肺癌（NSCLC）': ['非小细胞肺癌', 'NSCLC', '肺腺癌', '肺鳞癌',
                                      '局部晚期肺癌', '转移性肺癌'],
            '小细胞肺癌（SCLC）': ['小细胞肺癌', 'SCLC', '广泛期小细胞肺癌', '局限期小细胞肺癌'],
            '肝癌': ['肝细胞癌', 'HCC', '肝癌', '肝内胆管癌', '胆道癌', '胆管癌'],
            '乳腺癌': ['乳腺癌', 'HER2阳性乳腺癌', '三阴性乳腺癌', 'TNBC',
                             'HR阳性乳腺癌', '激素受体阳性', 'HER2低表达'],
            '结直肠癌': ['结直肠癌', 'CRC', '结肠癌', '直肠癌', '大肠肿瘤', 'mCRC'],
            '胃癌': ['胃癌', '胃腺癌', '胃食管结合部癌', 'GEJ', '食管癌', '食管鳞癌'],
            '胰腺癌': ['胰腺癌', '胰腺导管腺癌', 'PDAC', '胰腺肿瘤', '转移性胰腺癌'],
            '前列腺癌': ['前列腺癌', '去势抵抗性前列腺癌', 'CRPC', 'mCRPC', 'nmCRPC'],
            '卵巢癌': ['卵巢癌', '输卵管癌', '原发性腹膜癌', '铂耐药卵巢癌', '铂敏感卵巢癌'],
            '宫颈癌': ['宫颈癌', '宫颈鳞癌', '宫颈腺癌', '复发性宫颈癌', '转移性宫颈癌'],
            '子宫内膜癌': ['子宫内膜癌', '子宫体癌', '子宫肉瘤'],
            '肾癌': ['肾细胞癌', 'RCC', '肾透明细胞癌', 'ccRCC', '肾癌'],
            '尿路上皮癌': ['尿路上皮癌', '膀胱癌', 'UC', '移行细胞癌', '肾盂癌'],
            '黑色素瘤': ['黑色素瘤', '黑素瘤', '葡萄膜黑色素瘤', '恶性黑色素瘤'],
            '鼻咽癌': ['鼻咽癌', 'NPC', '鼻咽鳞癌'],
            '头颈癌': ['头颈癌', '头颈部肿瘤', '喉癌', '口腔癌', '下咽癌', 'HNSCC'],
            '甲状腺癌': ['甲状腺癌', '甲状腺髓样癌', 'MTC', '乳头状甲状腺癌', 'DTC', 'ATC'],
            '胶质瘤': ['胶质瘤', '胶质母细胞瘤', 'GBM', '星形细胞瘤', '髓母细胞瘤'],
            '软组织肉瘤': ['肉瘤', '骨肉瘤', '软骨肉瘤', '尤因肉瘤', '滑膜肉瘤',
                                '胃肠道间质瘤', 'GIST', '软组织肉瘤', '硬纤维瘤',
                                '恶性胸膜间皮瘤', '上皮样肉瘤', '腺泡状软组织肉瘤'],
            '白血病': ['白血病', '急性淋巴细胞白血病', 'ALL', '急性髓系白血病', 'AML',
                            '慢性淋巴细胞白血病', 'CLL', '慢性髓系白血病', 'CML',
                            '急性早幼粒细胞白血病', 'APL', '骨髓增生异常综合征', 'MDS',
                            '骨髓纤维化', 'MPN'],
            '淋巴瘤': ['淋巴瘤', '霍奇金淋巴瘤', 'HL', '非霍奇金淋巴瘤', 'NHL',
                            '弥漫大B细胞淋巴瘤', 'DLBCL', '滤泡淋巴瘤', 'FL',
                            '套细胞淋巴瘤', 'MCL', '外周T细胞淋巴瘤', 'PTCL',
                            '伯基特淋巴瘤', '淋巴母细胞淋巴瘤'],
            '骨髓瘤': ['骨髓瘤', '多发性骨髓瘤', 'MM', '浆细胞骨髓瘤',
                            '华氏巨球蛋白血症'],
            '儿童肿瘤': ['神经母细胞瘤', '肾母细胞瘤', '横纹肌肉瘤',
                             '视网膜母细胞瘤', '肝母细胞瘤', '儿童肿瘤'],
            '神经内分泌瘤': ['神经内分泌瘤', 'NET', '胰腺神经内分泌瘤', 'pNET',
                                 '类癌', '神经内分泌癌'],
            '默克尔细胞癌': ['默克尔细胞癌', 'Merkel细胞癌', 'MCC'],
        }

        # 药物名称到靶点的直接映射
        self.drug_target_map = {
            '奥希替尼': 'EGFR (T790M)', '吉非替尼': 'EGFR', '厄洛替尼': 'EGFR',
            '埃克替尼': 'EGFR', '阿法替尼': 'EGFR/HER2', '达可替尼': 'EGFR',
            '阿美替尼': 'EGFR (T790M)', '伏美替尼': 'EGFR (T790M)',
            '舒沃替尼': 'EGFR exon 20 ins', '莫博赛替尼': 'EGFR exon 20 ins',
            '克唑替尼': 'ALK/ROS1/MET', '塞瑞替尼': 'ALK', '阿来替尼': 'ALK',
            '塞普替尼': 'RET/ROS1', '劳拉替尼': 'ALK/ROS1',
            '恩曲替尼': 'TRK/ROS1/ALK', '普拉替尼': 'RET',
            '瑞波替尼': 'TRK/ROS1/NTRK',
            '伊布替尼': 'BTK', '泽布替尼': 'BTK', '奥布替尼': 'BTK',
            '替拉鲁替尼': 'BTK', '瑞米布替尼': 'BTK',
            '卡马替尼': 'MET', '赛沃替尼': 'MET', '谷美替尼': 'MET exon 14',
            '索托拉西布': 'KRAS G12C', 'MK-3475': 'PD-1', 'JMKX001899': 'KRAS G12C',
            '维莫非尼': 'BRAF V600', '达拉非尼': 'BRAF V600', '曲美替尼': 'MEK1/2',
            '考比替尼': 'MEK', '比美替尼': 'MEK1/2', '恩考芬尼': 'BRAF',
            '厄达替尼': 'FGFR', '培米替尼': 'FGFR1/2/3', '英菲格拉替尼': 'FGFR',
            '他舒替尼': 'FGFR', '替恩戈替尼': 'FGFR', '酒石酸凡瑞格拉替尼': 'FGFR',
            '洛布替尼': 'FGFR',
            '奥拉帕利': 'PARP1/2', '尼拉帕利': 'PARP1/2', '卢卡帕利': 'PARP',
            '帕米帕利': 'PARP', '氟唑帕利': 'PARP', '维利帕尼': 'PARP',
            '艾伏尼布': 'IDH1', '恩西地平': 'IDH2',
            '维莫德吉': 'SMO', '索尼德吉': 'SMO', '格拉吉布': 'SMO',
            '鲁索替尼': 'JAK1/JAK2', '芦可替尼': 'JAK1/JAK2', '杰克替尼': 'JAK',
            '依维莫司': 'mTOR', '西罗莫司': 'mTOR',
            '哌柏西利': 'CDK4/6', '阿贝西利': 'CDK4/6', '瑞博西利': 'CDK4/6',
            '达尔西利': 'CDK4/6', '瑞波西利': 'CDK4/6',
            '索拉非尼': 'VEGFR/PDGFR/RAF', '舒尼替尼': 'VEGFR/PDGFR/KIT',
            '帕唑帕尼': 'VEGFR/PDGFR', '仑伐替尼': 'VEGFR/FGFR/PDGFR/RET',
            '瑞戈非尼': 'VEGFR/TIE2/KIT/RAF', '安罗替尼': 'VEGFR/PDGFR/FGFR',
            '阿帕替尼': 'VEGFR2', '呋喹替尼': 'VEGFR', '索凡替尼': 'VEGFR/FGFR',
            '卡博替尼': 'VEGFR/MET/RET', '阿昔替尼': 'VEGFR', '培唑帕尼': 'VEGFR/PDGFR',
            '伊马替尼': 'KIT/PDGFR/BCR-ABL', '尼洛替尼': 'BCR-ABL/KIT',
            '达沙替尼': 'BCR-ABL/SRC', '博舒替尼': 'BCR-ABL', '普纳替尼': 'BCR-ABL/FLT3',
            '氟马替尼': 'BCR-ABL', '阿伐替尼': 'KIT/PDGFRα', '瑞派替尼': 'KIT/PDGFRα',
            '纳武利尤单抗': 'PD-1', '帕博利珠单抗': 'PD-1',
            '特瑞普利单抗': 'PD-1', '信迪利单抗': 'PD-1',
            '替雷利珠单抗': 'PD-1', '卡瑞利珠单抗': 'PD-1',
            '派安普利单抗': 'PD-1', '赛帕利单抗': 'PD-1', '斯鲁利单抗': 'PD-1',
            '舒格利单抗': 'PD-L1', '阿替利珠单抗': 'PD-L1',
            '度伐利尤单抗': 'PD-L1', '阿维鲁单抗': 'PD-L1',
            '伊匹木单抗': 'CTLA-4', '曲美木单抗': 'CTLA-4',
            '曲妥珠单抗': 'HER2', '帕妥珠单抗': 'HER2',
            '恩美曲妥珠单抗': 'HER2/微管（ADC）', '德曲妥珠单抗': 'HER2/拓扑异构酶I（ADC）',
            '维迪西妥单抗': 'HER2/微管（ADC）',
            '伊尼妥单抗': 'HER2', '吡咯替尼': 'HER2/EGFR/HER4',
            '奈拉替尼': 'HER2/EGFR/HER4', '拉帕替尼': 'HER2/EGFR', '妥卡替尼': 'HER2',
            '佐妥昔单抗': 'Claudin18.2', '依沃西单抗': 'PD-1/Claudin18.2',
            '维恩妥尤单抗': 'Nectin-4（ADC）',
            '维特柯妥拜单抗': 'Claudin18.2（ADC）',
            '戈沙妥珠单抗': 'TROP2/SN38（ADC）',
            '索米妥昔单抗': 'FRα（ADC）',
            '利妥昔单抗': 'CD20', '奥法妥木单抗': 'CD20', '奥瑞珠单抗': 'CD20',
            '奥妥珠单抗': 'CD20', '格菲妥单抗': 'CD20/CD3',
            '艾可瑞妥单抗': 'CD20/CD3', '塔戈妥单抗': 'CD20/CD3',
            '达雷妥尤单抗': 'CD38', '伊沙妥昔单抗': 'CD38', '埃罗妥珠单抗': 'SLAMF7',
            '本妥昔单抗': 'CD30', '维布妥昔单抗': 'CD30',
            '贝伐珠单抗': 'VEGF', '西妥昔单抗': 'EGFR', '帕尼单抗': 'EGFR',
            '尼妥珠单抗': 'EGFR', '雷莫西尤单抗': 'VEGFR2',
            '吉瑞替尼': 'FLT3', '奎扎替尼': 'FLT3', '米哚妥林': 'FLT3/KIT/PDGFR',
            '维奈克拉': 'BCL-2', '维奈妥拉': 'BCL-2',
            '硼替佐米': '蛋白酶体', '卡非佐米': '蛋白酶体', '伊沙佐米': '蛋白酶体',
            '来那度胺': '免疫调节/Cereblon', '泊马度胺': '免疫调节/Cereblon',
            '塞利尼索': 'XPO1/CRM1', '西达本胺': 'HDAC', '替莫唑胺': 'DNA烷化剂',
            '阿基仑赛': 'CD19 (CAR-T)', '瑞基奥仑赛': 'CD19 (CAR-T)',
            '替沙仑赛': 'CD19 (CAR-T)', '赫基仑赛': 'CD19 (CAR-T)',
            '伊基仑赛': 'BCMA (CAR-T)', '泽沃基奥仑赛': 'BCMA (CAR-T)',
            '纳基奥仑赛': 'CD19 (CAR-T)',
            '拉罗替尼': 'TRK（NTRK融合）', '瑞普替尼': 'TRK/ROS1/ALK',
            '他莫昔芬': 'SERM（ER调节）', '氟维司群': 'SERD（ER降解）',
            '阿那曲唑': '芳香化酶抑制剂', '来曲唑': '芳香化酶抑制剂',
            '依西美坦': '芳香化酶抑制剂（甾体）',
            '阿比特龙': 'CYP17（雄激素合成）', '恩扎卢胺': 'AR抑制剂',
            '阿帕鲁胺': 'AR抑制剂', '达罗他胺': 'AR抑制剂', '比卡鲁胺': 'AR抑制剂',
            'Nirogacestat': 'γ-分泌酶抑制剂（硬纤维瘤）',
            'Iberdomide': 'CRBN E3连接酶调节剂',
            'TQB3454': 'IDH1/2抑制剂', '氢溴酸尼罗司他': 'γ-分泌酶抑制剂',
        }

        # FDA已批准的中国抗肿瘤药物
        self.fda_approved = set([
            '奥希替尼', '吉非替尼', '厄洛替尼', '阿法替尼', '达可替尼',
            '莫博赛替尼', '舒沃替尼',
            '克唑替尼', '塞瑞替尼', '阿来替尼', '塞普替尼', '劳拉替尼',
            '恩曲替尼', '普拉替尼', '瑞波替尼',
            '伊布替尼', '泽布替尼', '奥布替尼', '替拉鲁替尼',
            '卡马替尼', '索托拉西布', '维莫非尼', '达拉非尼', '曲美替尼',
            '考比替尼', '比美替尼', '恩考芬尼',
            '厄达替尼', '培米替尼', '英菲格拉替尼',
            '奥拉帕利', '尼拉帕利', '卢卡帕利',
            '艾伏尼布', '恩西地平', '维莫德吉', '索尼德吉', '格拉吉布',
            '鲁索替尼', '依维莫司', '西罗莫司',
            '哌柏西利', '阿贝西利', '瑞博西利', '瑞波西利',
            '索拉非尼', '舒尼替尼', '帕唑帕尼', '仑伐替尼', '瑞戈非尼',
            '阿昔替尼', '卡博替尼',
            '伊马替尼', '尼洛替尼', '达沙替尼', '博舒替尼', '普纳替尼',
            '阿伐替尼', '瑞派替尼',
            '纳武利尤单抗', '帕博利珠单抗',
            '阿替利珠单抗', '度伐利尤单抗', '阿维鲁单抗',
            '伊匹木单抗', '曲美木单抗',
            '曲妥珠单抗', '帕妥珠单抗', '恩美曲妥珠单抗', '德曲妥珠单抗',
            '维迪西妥单抗',
            '佐妥昔单抗', '戈沙妥珠单抗', '索米妥昔单抗',
            '利妥昔单抗', '奥法妥木单抗', '奥瑞珠单抗', '奥妥珠单抗',
            '格菲妥单抗', '艾可瑞妥单抗',
            '达雷妥尤单抗', '伊沙妥昔单抗', '埃罗妥珠单抗',
            '本妥昔单抗', '维布妥昔单抗',
            '贝伐珠单抗', '西妥昔单抗', '帕尼单抗', '尼妥珠单抗',
            '雷莫西尤单抗',
            '吉瑞替尼', '奎扎替尼', '米哚妥林',
            '维奈克拉', '维奈妥拉',
            '硼替佐米', '卡非佐米', '伊沙佐米',
            '来那度胺', '泊马度胺', '塞利尼索',
            '阿基仑赛', '替沙仑赛', '瑞基奥仑赛',
            '拉罗替尼', '瑞普替尼', '替莫唑胺', '西达本胺',
            'Nirogacestat',
        ])

        # EMA已批准的
        self.ema_approved = set([
            '奥希替尼', '吉非替尼', '厄洛替尼', '阿法替尼', '达可替尼',
            '克唑替尼', '塞瑞替尼', '阿来替尼', '劳拉替尼', '恩曲替尼',
            '伊布替尼', '泽布替尼', '奥布替尼',
            '索托拉西布', '达拉非尼', '曲美替尼',
            '奥拉帕利', '尼拉帕利', '卢卡帕利',
            '艾伏尼布', '恩西地平', '维莫德吉', '格拉吉布',
            '鲁索替尼', '芦可替尼', '依维莫司', '西罗莫司',
            '哌柏西利', '阿贝西利', '瑞博西利', '瑞波西利',
            '索拉非尼', '舒尼替尼', '帕唑帕尼', '仑伐替尼', '瑞戈非尼',
            '阿昔替尼', '卡博替尼',
            '伊马替尼', '尼洛替尼', '达沙替尼', '博舒替尼', '普纳替尼',
            '阿伐替尼', '瑞派替尼',
            '纳武利尤单抗', '帕博利珠单抗',
            '阿替利珠单抗', '度伐利尤单抗', '阿维鲁单抗',
            '伊匹木单抗', '曲美木单抗',
            '曲妥珠单抗', '帕妥珠单抗', '恩美曲妥珠单抗', '德曲妥珠单抗',
            '戈沙妥珠单抗',
            '他莫昔芬', '氟维司群', '阿那曲唑', '来曲唑', '依西美坦',
            '阿比特龙', '恩扎卢胺', '阿帕鲁胺', '达罗他胺',
            '维奈克拉', '维奈妥拉',
            '硼替佐米', '卡非佐米', '伊沙佐米',
            '来那度胺', '泊马度胺', '塞利尼索', '替莫唑胺',
            '利妥昔单抗', '奥法妥木单抗', '奥瑞珠单抗', '奥妥珠单抗',
            '达雷妥尤单抗', '伊沙妥昔单抗',
            '维布妥昔单抗', '本妥昔单抗',
            '贝伐珠单抗', '西妥昔单抗', '帕尼单抗', '雷莫西尤单抗',
            '吉瑞替尼',
            '阿基仑赛', '替沙仑赛', '瑞基奥仑赛',
            '拉罗替尼',
        ])

        # 部分适应症FDA获批/审查中的国产创新药
        self.partial_fda = set([
            '特瑞普利单抗', '信迪利单抗', '替雷利珠单抗',
            '卡瑞利珠单抗', '舒格利单抗', '斯鲁利单抗',
            '赛沃替尼', '吡咯替尼', '阿美替尼', '伏美替尼',
            '佐妥昔单抗', '戈沙妥珠单抗',
        ])

    def enrich_approval_numbers(self, df, cde_df):
        """补充批准文号"""
        print("\n[步骤1] 补充批准文号...")

        # 构建CDE药物名称到受理号的映射
        name_to_acceptance = {}
        for _, cde_row in cde_df.iterrows():
            cname = str(cde_row.get('drug_name') or '').strip()
            acc = str(cde_row.get('acceptance_number') or cde_row.get('application_number') or '').strip()
            app_num = str(cde_row.get('application_number') or '').strip()
            final_acc = acc if acc not in ['', 'None', 'NULL', 'nan', 'NaN', '无'] else (
                app_num if app_num not in ['', 'None', 'NULL', 'nan', 'NaN', '无'] else ''
            )
            if cname and final_acc:
                name_to_acceptance[cname] = final_acc
                name_to_acceptance[cname.replace(' ', '')] = final_acc
                # 简化名称匹配
                short = re.sub(r'[（(][^）)]*[）)]', '', cname).strip()
                if short != cname:
                    name_to_acceptance[short] = final_acc

        updated = 0
        for idx, row in df.iterrows():
            current = str(row.get('approval_number') or '').strip()
            if current in ['', 'None', 'NULL', 'nan', 'NaN', '无']:
                drug_name = str(row.get('drug_name_cn') or '').strip()
                matched = None

                # 精确匹配
                if drug_name in name_to_acceptance:
                    matched = name_to_acceptance[drug_name]
                else:
                    # 模糊匹配
                    for cde_name, acc in name_to_acceptance.items():
                        clean_cde = re.sub(r'[（(][^）)]*[）)]', '', cde_name).strip()
                        clean_drug = re.sub(r'[（(][^）)]*[）)]', '', drug_name).strip()
                        if clean_cde in clean_drug or clean_drug in clean_cde:
                            if len(clean_cde) > 2:
                                matched = acc
                                break

                if matched:
                    df.at[idx, 'approval_number'] = matched
                    updated += 1

        print(f"  成功补充: {updated} 条批准文号")
        return df

    def enrich_biomarkers(self, df):
        """补充分子靶点、生物标志物和伴随诊断"""
        print("\n[步骤2] 补充分子靶点和生物标志物...")

        target_updated = 0
        gene_updated = 0
        cd_updated = 0

        for idx, row in df.iterrows():
            drug_name = str(row.get('drug_name_cn') or '').strip()
            indication = str(row.get('indication') or '').strip()
            mechanism = str(row.get('mechanism_of_action') or '').strip()
            cur_target = str(row.get('molecular_target') or '').strip()
            cur_gene = str(row.get('gene_marker') or '').strip()
            cur_cd = str(row.get('companion_diagnosis') or '').strip()

            found_targets = []
            found_biomarkers = []
            found_cd = []

            # 1. 通过药物名称精确匹配
            for drug_key, target in self.drug_target_map.items():
                if drug_key in drug_name:
                    found_targets.append(target)
                    break

            # 2. 通过文本中的靶点关键词
            all_text = ' '.join([drug_name, indication, mechanism]).lower()
            for target_key, biomarkers in self.biomarker_map.items():
                if target_key.lower() in all_text:
                    if target_key not in ';'.join(found_targets):
                        found_targets.append(target_key)
                    found_biomarkers.extend(biomarkers[:2])
                    if target_key in self.cd_test_map:
                        found_cd.extend(self.cd_test_map[target_key][:2])

            # 3. 从适应症中提取特定生物标志物模式
            biomarker_patterns = {
                'PD-L1阳性 (TPS/CPS)': ['PD-L1阳性', 'PD-L1 TPS', 'PD-L1 CPS',
                                        'PD-L1表达', 'PD-L1≥1%'],
                'MSI-H（微卫星高度不稳定）': ['MSI-H', '微卫星高度不稳定', '微卫星不稳定'],
                'dMMR（错配修复缺陷）': ['dMMR', '错配修复缺陷', 'MMR缺陷'],
                'TMB-H（肿瘤突变负荷高）': ['TMB-H', 'TMB高', '肿瘤突变负荷'],
                'HER2阳性': ['HER2阳性', 'HER2 3+', 'HER2扩增', 'HER2过表达', 'HER2低表达'],
                'BRCA突变': ['BRCA突变', 'BRCA阳性', 'gBRCA', 'sBRCA'],
                'HRD阳性（同源重组缺陷）': ['HRD阳性', '同源重组修复缺陷', 'HRD'],
                'EGFR突变': ['EGFR突变', 'EGFR 19缺失', 'EGFR L858R', 'EGFR T790M',
                           'EGFR exon 19', 'EGFR exon 20'],
                'ALK融合/重排': ['ALK阳性', 'ALK融合', 'ALK重排'],
                'ROS1融合/重排': ['ROS1阳性', 'ROS1融合', 'ROS1重排'],
                'NTRK融合': ['NTRK融合', 'TRK融合', 'TRK阳性', 'NTRK1', 'NTRK2', 'NTRK3'],
                'BRAF V600E突变': ['BRAF V600E', 'BRAF V600', 'BRAF突变'],
                'KRAS G12C突变': ['KRAS G12C', 'KRAS G12D', 'KRAS突变'],
                'MET exon 14跳变': ['MET exon 14', 'MET 14跳变', 'MET扩增'],
                'RET融合/重排': ['RET融合', 'RET阳性', 'RET重排'],
                'FGFR融合/突变': ['FGFR融合', 'FGFR突变', 'FGFR2', 'FGFR3'],
                'FLT3-ITD/TKD突变': ['FLT3-ITD', 'FLT3 TKD', 'FLT3突变'],
                'IDH1 R132H突变': ['IDH1突变', 'IDH1 R132H', 'IDH2 R140Q'],
                'JAK2 V617F突变': ['JAK2 V617F', 'JAK2突变'],
                'Claudin18.2阳性': ['Claudin18.2', 'CLDN18.2', 'Claudin 18.2'],
                'DLL3阳性': ['DLL3阳性', 'DLL3表达', 'DLL3'],
                'PSMA阳性': ['PSMA阳性', 'PSMA', '前列腺特异性膜抗原'],
                'FRα阳性': ['FRα阳性', '叶酸受体α'],
                'TROP2阳性': ['TROP2阳性', 'TROP2'],
                'AR-V7阳性': ['AR-V7', '去势抵抗性前列腺癌', 'mCRPC'],
                'CD20阳性': ['CD20阳性', 'CD20表达', 'B细胞淋巴瘤'],
                'CD30阳性': ['CD30阳性', 'CD30表达'],
                'BCMA阳性': ['BCMA阳性', 'BCMA表达', 'B细胞成熟抗原'],
                'KIT突变（D816V等）': ['KIT突变', 'CD117阳性', 'KIT D816V'],
                'RB阳性/HR阳性': ['HR阳性', '激素受体阳性', 'ER阳性', 'RB阳性'],
            }

            for bm, patterns in biomarker_patterns.items():
                for p in patterns:
                    if p.lower() in ' '.join([indication, mechanism, drug_name]).lower():
                        if bm not in found_biomarkers:
                            found_biomarkers.append(bm)
                        break

            # 更新DataFrame - 仅在原数据为空或非常短时补充
            if found_targets and (not cur_target or cur_target in ['', 'None', 'NULL', 'nan', 'NaN', '无']):
                df.at[idx, 'molecular_target'] = '; '.join(list(dict.fromkeys(found_targets))[:5])
                target_updated += 1

            if found_biomarkers and (not cur_gene or cur_gene in ['', 'None', 'NULL', 'nan', 'NaN', '无']):
                df.at[idx, 'gene_marker'] = '; '.join(list(dict.fromkeys(found_biomarkers))[:8])
                gene_updated += 1

            if found_cd and (not cur_cd or cur_cd in ['', 'None', 'NULL', 'nan', 'NaN', '无']):
                df.at[idx, 'companion_diagnosis'] = '; '.join(list(dict.fromkeys(found_cd))[:3])
                cd_updated += 1

        print(f"  靶点补充: {target_updated} 条")
        print(f"  生物标志物补充: {gene_updated} 条")
        print(f"  伴随诊断检测补充: {cd_updated} 条")
        return df

    def categorize_indications(self, df):
        """根据适应症自动分类肿瘤类型"""
        print("\n[步骤3] 自动分类适应症...")

        df['主要肿瘤类型'] = ''
        df['适应症分类'] = ''

        for idx, row in df.iterrows():
            drug_name = str(row.get('drug_name_cn') or '').strip()
            indication = str(row.get('indication') or '').strip()
            mechanism = str(row.get('mechanism_of_action') or '').strip()
            target = str(row.get('molecular_target') or '').strip()

            all_text = ' '.join([drug_name, indication, mechanism, target]).lower()

            matched_categories = []
            for category, keywords in self.indication_categories.items():
                for kw in keywords:
                    if kw.lower() in all_text:
                        matched_categories.append(category)
                        break

            # 通过靶点推断适应症
            if not matched_categories:
                target_upper = target.upper()
                if 'EGFR' in target_upper or 'ALK' in target_upper or 'ROS1' in target_upper or 'KRAS' in target_upper:
                    matched_categories.append('非小细胞肺癌（NSCLC）')
                if 'HER2' in target_upper or 'HR阳性' in target or 'ER阳性' in target:
                    matched_categories.append('乳腺癌')
                if 'PD-1' in target_upper or 'PD-L1' in target_upper or 'CTLA-4' in target_upper:
                    matched_categories.append('泛肿瘤/多种实体瘤')
                if 'BTK' in target_upper or 'CD20' in target_upper or 'CD19' in target_upper:
                    matched_categories.append('淋巴瘤')
                    matched_categories.append('白血病')
                if 'BCMA' in target_upper or 'CD38' in target_upper or 'SLAMF7' in target.upper():
                    matched_categories.append('骨髓瘤')
                if 'PSMA' in target_upper or '去势抵抗性' in target:
                    matched_categories.append('前列腺癌')
                if 'CLAUDIN' in target.upper() or 'CLDN' in target_upper:
                    matched_categories.append('胃癌')
                if 'FGFR' in target_upper:
                    matched_categories.append('尿路上皮癌')
                    matched_categories.append('肝癌')
                if 'PARP' in target_upper or 'BRCA' in target_upper:
                    matched_categories.append('卵巢癌')
                    matched_categories.append('乳腺癌')
                if 'JAK' in target_upper or 'FLT3' in target_upper or 'IDH' in target_upper:
                    matched_categories.append('白血病')
                    matched_categories.append('骨髓增生异常综合征')
                if 'KIT' in target_upper or 'PDGFR' in target_upper:
                    matched_categories.append('软组织肉瘤')
                    matched_categories.append('白血病')

            if matched_categories:
                df.at[idx, '主要肿瘤类型'] = matched_categories[0]
                df.at[idx, '适应症分类'] = '; '.join(list(dict.fromkeys(matched_categories))[:5])
            else:
                df.at[idx, '主要肿瘤类型'] = '泛肿瘤/多种实体瘤'
                df.at[idx, '适应症分类'] = '泛肿瘤/多种实体瘤'

        cat_stats = df['主要肿瘤类型'].value_counts()
        print(f"  分类统计（前10类）:")
        for cat, cnt in cat_stats.head(10).items():
            print(f"    - {cat}: {cnt} 条")

        return df

    def add_international_comparison(self, df):
        """添加FDA/EMA批准情况的国际对比"""
        print("\n[步骤4] 添加国际对比数据...")

        df['FDA批准情况'] = ''
        df['EMA批准情况'] = ''
        df['国际可及性评估'] = ''
        df['国际批准状态总结'] = ''

        fda_count = 0
        ema_count = 0
        cn_only_count = 0

        for idx, row in df.iterrows():
            drug_name = str(row.get('drug_name_cn') or '').strip()

            # 简化名称用于匹配
            simple_name = re.sub(r'[（(][^）)]*[）)]', '', drug_name).strip()
            match_names = [drug_name, simple_name]

            # FDA批准判定
            is_fda = False
            fda_note = ''
            for dn in match_names:
                if any(name in dn for name in self.fda_approved):
                    is_fda = True
                    break

            if not is_fda:
                for dn in match_names:
                    if any(name in dn for name in self.partial_fda):
                        fda_note = '部分适应症FDA获批/审查中'
                        break

            # EMA批准判定
            is_ema = False
            for dn in match_names:
                if any(name in dn for name in self.ema_approved):
                    is_ema = True
                    break

            # 更新数据
            if is_fda:
                df.at[idx, 'FDA批准情况'] = 'FDA已批准'
                fda_count += 1
            elif fda_note:
                df.at[idx, 'FDA批准情况'] = fda_note
            else:
                df.at[idx, 'FDA批准情况'] = '未获FDA批准（中国/亚洲市场）'

            if is_ema:
                df.at[idx, 'EMA批准情况'] = 'EMA已批准'
                ema_count += 1
            else:
                df.at[idx, 'EMA批准情况'] = '未获EMA批准'

            # 国际可及性评估
            if is_fda and is_ema:
                df.at[idx, '国际可及性评估'] = '全球可及（FDA+EMA双批准）'
                df.at[idx, '国际批准状态总结'] = '国际主流市场均已批准，全球患者可及'
            elif is_fda or is_ema:
                df.at[idx, '国际可及性评估'] = '部分国际可及（FDA或EMA单批准）'
                df.at[idx, '国际批准状态总结'] = '已获部分国际监管机构批准，患者可及性中等'
            else:
                df.at[idx, '国际可及性评估'] = '仅中国/有限国际可及'
                df.at[idx, '国际批准状态总结'] = '主要在中国或有限国家/地区批准，国际可及性较低'
                cn_only_count += 1

        print(f"  FDA已批准: {fda_count} 条")
        print(f"  EMA已批准: {ema_count} 条")
        print(f"  仅中国/有限国际可及: {cn_only_count} 条")
        return df

    def finalize_enrichment(self, df):
        """最终整理 - 补充剂型、给药途径等"""
        print("\n[步骤5] 最终整理数据...")

        for idx, row in df.iterrows():
            name = str(row.get('drug_name_cn') or '').strip()
            cur_dosage = str(row.get('dosage_form') or '').strip()
            cur_route = str(row.get('route_of_administration') or '').strip()

            if cur_dosage in ['', 'None', 'NULL', 'nan', 'NaN', '无']:
                if '注射液' in name or '注射用' in name or '[177Lu]' in name:
                    df.at[idx, 'dosage_form'] = '注射剂/静脉输注'
                    df.at[idx, 'route_of_administration'] = '静脉输注/皮下注射'
                elif '片' in name or '胶囊' in name:
                    df.at[idx, 'dosage_form'] = '片剂/胶囊'
                    df.at[idx, 'route_of_administration'] = '口服'
                else:
                    df.at[idx, 'dosage_form'] = '固体制剂'
                    df.at[idx, 'route_of_administration'] = '口服/注射'

            # 统一空值处理
            for col in ['indication', 'mechanism_of_action']:
                val = str(row.get(col) or '').strip()
                if val in ['', 'None', 'NULL', 'nan', 'NaN', '无']:
                    df.at[idx, col] = '详见药品说明书'

        # 批准日期格式
        if 'approval_date' in df.columns:
            df['批准年份'] = df['approval_date'].apply(
                lambda x: str(x)[:4] if pd.notna(x) and str(x).strip() not in ['', 'None', 'nan'] else ''
            )

        print("  数据整理完成")
        return df

    def run_full_enrichment(self, df, cde_df):
        """运行完整的数据增强流程"""
        print("=" * 70)
        print("NMPA抗肿瘤药物数据增强流程")
        print("=" * 70)
        print(f"输入数据: {len(df)} 条记录")

        df = self.enrich_approval_numbers(df, cde_df)
        df = self.enrich_biomarkers(df)
        df = self.categorize_indications(df)
        df = self.add_international_comparison(df)
        df = self.finalize_enrichment(df)

        print("\n" + "=" * 70)
        print("增强完成！")
        print("=" * 70)
        return df


# ============================
# 第三部分：生成Excel报告
# ============================

def generate_excel_report(df, output_path):
    """生成多sheet的Excel报告"""
    print(f"\n[导出] 生成Excel报告: {output_path}")

    # 列选择和重命名
    export_cols = [
        'drug_name_cn', 'brand_name_cn', 'generic_name_cn',
        'approval_number', 'approval_date', '批准年份',
        'dosage_form', 'route_of_administration',
        'indication', 'mechanism_of_action',
        'molecular_target', 'gene_marker', 'companion_diagnosis',
        '主要肿瘤类型', '适应症分类',
        'FDA批准情况', 'EMA批准情况', '国际可及性评估', '国际批准状态总结',
        'applicant', 'clinical_trial_data', 'detail_url',
    ]
    available_cols = [c for c in export_cols if c in df.columns]
    report_df = df[available_cols].copy()

    col_names = {
        'drug_name_cn': '药品名称',
        'brand_name_cn': '商品名',
        'generic_name_cn': '通用名',
        'approval_number': '批准文号/受理号',
        'approval_date': '批准日期',
        '批准年份': '批准年份',
        'dosage_form': '剂型',
        'route_of_administration': '给药途径',
        'indication': '适应症',
        'mechanism_of_action': '作用机制',
        'molecular_target': '分子靶点',
        'gene_marker': '生物标志物/基因突变',
        'companion_diagnosis': '伴随诊断检测方法',
        '主要肿瘤类型': '主要肿瘤类型',
        '适应症分类': '适应症分类（多分类）',
        'FDA批准情况': 'FDA批准情况',
        'EMA批准情况': 'EMA批准情况',
        '国际可及性评估': '国际可及性',
        '国际批准状态总结': '国际批准状态说明',
        'applicant': '申请/生产企业',
        'clinical_trial_data': '临床试验信息',
        'detail_url': '详细信息来源',
    }
    report_df = report_df.rename(columns=col_names)
    report_df = report_df.sort_values('批准日期', ascending=False, na_position='last')

    with pd.ExcelWriter(output_path, engine='openpyxl') as writer:
        # 1. 总表 - 完整药物列表
        report_df.to_excel(writer, sheet_name='完整药物列表', index=False)
        print(f"  - Sheet: 完整药物列表 ({len(report_df)} 条)")

        # 2. 数据质量和覆盖统计
        stats_data = []
        stats_data.append(['总药物数（筛选后）', len(report_df)])

        for ch_col, stat_name in [
            ('分子靶点', '有分子靶点信息'),
            ('生物标志物/基因突变', '有生物标志物信息'),
            ('伴随诊断检测方法', '有伴随诊断信息'),
            ('批准文号/受理号', '有批准文号信息'),
        ]:
            if ch_col in report_df.columns:
                cnt = report_df[ch_col].apply(
                    lambda x: pd.notna(x) and str(x).strip() not in ['', 'None', 'NULL', 'nan', 'NaN', '无']
                ).sum()
                stats_data.append([stat_name, f'{cnt} ({cnt/len(report_df)*100:.1f}%)'])

        # FDA/EMA统计
        if 'FDA批准情况' in report_df.columns:
            fda_total = (report_df['FDA批准情况'] == 'FDA已批准').sum()
            stats_data.append(['FDA已批准', f'{fda_total} ({fda_total/len(report_df)*100:.1f}%)'])
        if 'EMA批准情况' in report_df.columns:
            ema_total = (report_df['EMA批准情况'] == 'EMA已批准').sum()
            stats_data.append(['EMA已批准', f'{ema_total} ({ema_total/len(report_df)*100:.1f}%)'])

        stats_df = pd.DataFrame(stats_data, columns=['统计项', '数值'])
        stats_df.to_excel(writer, sheet_name='数据质量统计', index=False)
        print(f"  - Sheet: 数据质量统计")

        # 3. 按年份分布
        if '批准年份' in report_df.columns:
            year_counts = report_df.groupby('批准年份').size().reset_index(name='批准药物数')
            year_counts = year_counts[year_counts['批准年份'].str.len() > 0].sort_values('批准年份', ascending=False)
            year_counts.to_excel(writer, sheet_name='按年份统计', index=False)
            print(f"  - Sheet: 按年份统计 ({len(year_counts)}年)")

        # 4. 按肿瘤类型分类（每个分类单独sheet）
        if '主要肿瘤类型' in report_df.columns:
            tumor_cats = report_df['主要肿瘤类型'].value_counts()
            for tumor_type in tumor_cats.index:
                sub_df = report_df[report_df['主要肿瘤类型'] == tumor_type]
                if len(sub_df) >= 1:
                    # 限制sheet名称长度（Excel限制31字符）
                    sheet_name = tumor_type[:28].replace('/', '_').replace('\\', '_')
                    if len(sub_df) >= 2 or tumor_type in ['非小细胞肺癌（NSCLC）', '乳腺癌', '肝癌',
                                                          '淋巴瘤', '白血病', '结直肠癌',
                                                          '泛肿瘤/多种实体瘤', '骨髓瘤', '前列腺癌']:
                        sub_df.to_excel(writer, sheet_name=sheet_name, index=False)
                        print(f"  - Sheet: {sheet_name} ({len(sub_df)}条)")

        # 5. 生物标志物专题报告
        if '生物标志物/基因突变' in report_df.columns:
            bio_df = report_df[report_df['生物标志物/基因突变'].apply(
                lambda x: pd.notna(x) and str(x).strip() not in ['', 'None', 'NULL', 'nan', 'NaN', '无']
            )]
            if len(bio_df) > 0:
                bio_df.to_excel(writer, sheet_name='生物标志物专题', index=False)
                print(f"  - Sheet: 生物标志物专题 ({len(bio_df)}条)")

        # 6. 伴随诊断专题
        if '伴随诊断检测方法' in report_df.columns:
            cd_df = report_df[report_df['伴随诊断检测方法'].apply(
                lambda x: pd.notna(x) and str(x).strip() not in ['', 'None', 'NULL', 'nan', 'NaN', '无']
            )]
            if len(cd_df) > 0:
                cd_df.to_excel(writer, sheet_name='伴随诊断专题', index=False)
                print(f"  - Sheet: 伴随诊断专题 ({len(cd_df)}条)")

        # 7. 国际对比分析
        intl_cols = [c for c in ['药品名称', '商品名', '适应症', '分子靶点',
                                  'FDA批准情况', 'EMA批准情况', '国际可及性',
                                  '国际可及性评估', '国际批准状态说明']
                     if c in report_df.columns]
        if intl_cols:
            intl_df = report_df[intl_cols].copy()
            intl_df.to_excel(writer, sheet_name='国际对比分析', index=False)
            print(f"  - Sheet: 国际对比分析 ({len(intl_df)}条)")

        # 8. 2024-2026年最新批准（近年新药）
        if '批准年份' in report_df.columns:
            recent_df = report_df[report_df['批准年份'].isin(['2024', '2025', '2026'])]
            if len(recent_df) > 0:
                recent_df.to_excel(writer, sheet_name='2024-2026最新批准', index=False)
                print(f"  - Sheet: 2024-2026最新批准 ({len(recent_df)}条)")

    print(f"\n✓ 报告生成完成！共 {len(report_df)} 条药物记录")
    return output_path


# ============================
# 第四部分：主程序
# ============================

def main():
    """主函数"""
    print("=" * 80)
    print("NMPA抗肿瘤药物完整增强报告系统")
    print("=" * 80)

    conn = sqlite3.connect(db_path)

    # 1. 读取NMPA药物数据
    print("\n[数据读取] 从数据库读取NMPA药物...")
    df_raw = pd.read_sql(
        "SELECT * FROM approved_drugs WHERE regulatory_agency = 'NMPA'",
        conn
    )
    print(f"  原始NMPA药物: {len(df_raw)} 条")

    # 2. 筛选抗肿瘤药物
    print("\n[筛选] 智能筛选抗肿瘤药物...")
    anticancer_mask = df_raw.apply(is_anticancer_drug, axis=1)
    df_anticancer = df_raw[anticancer_mask].copy().reset_index(drop=True)
    excluded_df = df_raw[~anticancer_mask].copy().reset_index(drop=True)
    print(f"  筛选出抗肿瘤药物: {len(df_anticancer)} 条")
    print(f"  排除非抗肿瘤药物: {len(excluded_df)} 条")

    if len(excluded_df) > 0:
        print("  被排除药物示例:")
        for _, r in excluded_df.head(10).iterrows():
            print(f"    - {r.get('drug_name_cn', '')} | {r.get('approval_date', '')}")

    # 3. 读取CDE特殊药品数据用于补充批准文号
    print("\n[数据补充] 读取CDE特殊药品数据...")
    try:
        cde_df = pd.read_sql("SELECT * FROM cde_special_drugs", conn)
        print(f"  CDE特殊药品: {len(cde_df)} 条")
    except Exception as e:
        print(f"  警告: 无法读取CDE表 ({e})")
        cde_df = pd.DataFrame()

    # 4. 运行增强系统
    enhancer = DrugDataEnhancer()
    enhanced_df = enhancer.run_full_enrichment(df_anticancer, cde_df)

    # 5. 保存到数据库
    print("\n[保存] 写入数据库...")
    try:
        enhanced_df.to_sql('enhanced_anticancer_drugs_v2', conn,
                           if_exists='replace', index=False)
        print("  ✓ 已保存到 enhanced_anticancer_drugs_v2 表")
    except Exception as e:
        print(f"  警告: 保存到数据库失败: {e}")

    # 6. 生成Excel报告
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    output_path = os.path.join(
        os.path.dirname(os.path.abspath(__file__)),
        f'NMPA抗肿瘤药物完整增强报告_{timestamp}.xlsx'
    )
    generate_excel_report(enhanced_df, output_path)

    # 7. 显示最终统计
    print("\n" + "=" * 80)
    print("最终统计摘要")
    print("=" * 80)

    print(f"\n[总体统计]")
    print(f"  总NMPA抗肿瘤药物: {len(enhanced_df)} 条")
    if '批准年份' in enhanced_df.columns:
        for yr in ['2026', '2025', '2024', '2023', '2022']:
            cnt = len(enhanced_df[enhanced_df['批准年份'] == yr])
            if cnt > 0:
                print(f"  - {yr}年: {cnt} 条")

    if '主要肿瘤类型' in enhanced_df.columns:
        print(f"\n[肿瘤类型分布（Top 10）]")
        top_cats = enhanced_df['主要肿瘤类型'].value_counts().head(10)
        for cat, cnt in top_cats.items():
            print(f"  - {cat}: {cnt} 条 ({cnt/len(enhanced_df)*100:.1f}%)")

    if 'FDA批准情况' in enhanced_df.columns:
        print(f"\n[国际批准状态]")
        fda_ok = (enhanced_df['FDA批准情况'] == 'FDA已批准').sum()
        ema_ok = (enhanced_df['EMA批准情况'] == 'EMA已批准').sum()
        partial = enhanced_df['FDA批准情况'].str.contains('部分|审查中').sum()
        only_cn = len(enhanced_df) - fda_ok - partial
        print(f"  FDA已批准: {fda_ok} 条 ({fda_ok/len(enhanced_df)*100:.1f}%)")
        print(f"  EMA已批准: {ema_ok} 条 ({ema_ok/len(enhanced_df)*100:.1f}%)")
        print(f"  部分FDA获批/审查中: {partial} 条")
        print(f"  未获国际批准（仅中国/亚洲市场）: {only_cn} 条")

    conn.close()

    print(f"\n\n✓ 报告文件: {output_path}")
    print(f"  文件大小约: {os.path.getsize(output_path)/1024:.0f} KB")
    return output_path


if __name__ == '__main__':
    output = main()
    print(f"\n最终输出文件:")
    print(f"  {output}")
