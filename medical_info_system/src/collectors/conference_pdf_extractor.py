"""
肿瘤学术年会摘要PDF提取模块
从用户上传的会议摘要PDF中提取抗肿瘤药物及基因标志物研究信息
支持文字版PDF和图片扫描版PDF（OCR）
"""

import os
import sys
import re
import logging
import hashlib
from datetime import datetime
from typing import Dict, List, Optional, Tuple

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

logger = logging.getLogger(__name__)

# 尝试导入PDF处理库
try:
    import fitz  # PyMuPDF
    PYMUPDF_AVAILABLE = True
except ImportError:
    PYMUPDF_AVAILABLE = False
    logger.warning("PyMuPDF未安装，文字版PDF提取功能受限")

try:
    import pdfplumber
    PDFPLUMBER_AVAILABLE = True
except ImportError:
    PDFPLUMBER_AVAILABLE = False
    logger.warning("pdfplumber未安装")

try:
    from PIL import Image
    import pytesseract
    OCR_AVAILABLE = True
except ImportError:
    OCR_AVAILABLE = False
    logger.warning("pytesseract或Pillow未安装，图片版PDF OCR功能受限")


class ConferencePDFExtractor:
    """会议摘要PDF提取器"""

    def __init__(self, config_manager=None):
        """
        初始化PDF提取器

        Args:
            config_manager: 配置管理器
        """
        self.config_manager = config_manager

        # 抗肿瘤药物关键词
        self.anti_tumor_drug_keywords = [
            '单抗', '单克隆抗体', '替尼', '替尼类', '激酶抑制剂',
            '帕博利珠单抗', '纳武利尤单抗', '卡瑞利珠单抗', '信迪利单抗',
            '特瑞普利单抗', '替雷利珠单抗', '阿替利珠单抗', '度伐利尤单抗',
            '西妥昔单抗', '尼妥珠单抗', '曲妥珠单抗', '帕妥珠单抗',
            '贝伐珠单抗', '雷莫芦单抗', '恩美曲妥珠单抗', '德曲妥珠单抗',
            '伊匹木单抗', '度伐利尤单抗', '阿替利珠单抗', '阿维单抗',
            '奥希替尼', '吉非替尼', '厄洛替尼', '埃克替尼', '阿法替尼',
            '达克替尼', '奈拉替尼', '拉帕替尼', '吡咯替尼', '图卡替尼',
            '舒尼替尼', '索拉非尼', '仑伐替尼', '帕唑帕尼', '阿帕替尼',
            '安罗替尼', '尼达尼布', '伊维莫司', '依维莫司', '坦西莫司',
            '维莫非尼', '达拉非尼', 'encorafenib', 'binimetinib', 'cobimetinib',
            'trametinib', 'selumetinib', '曲美替尼', '比美替尼', '考比替尼',
            '克唑替尼', '色瑞替尼', '阿来替尼', '布加替尼', '劳拉替尼',
            '恩沙替尼', '伊鲁替尼', '阿卡替尼', '泽布替尼', '奥布替尼',
            '吉列替尼', '普纳替尼', 'ponatinib', 'bosutinib', 'dasatinib',
            'nilotinib', '伊马替尼', '达沙替尼', '尼洛替尼', '氟马替尼',
            '利妥昔单抗', '托珠单抗', '西达本胺', '贝林司他', '伏立诺他',
            '帕比司他', '罗米地辛', '羟基脲', '伊沙匹隆', '艾日布林',
            '多柔比星', '表柔比星', '吡柔比星', '丝裂霉素', '平阳霉素',
            '培美曲塞', '吉西他滨', '多西他赛', '紫杉醇', '白蛋白紫杉醇',
            '脂质体紫杉醇', '伊立替康', '拓扑替康', '羟喜树碱', '依托泊苷',
            '替莫唑胺', '达卡巴嗪', '替吉奥', '卡培他滨', '替加氟', '氟尿嘧啶',
            '雷替曲塞', '长春瑞滨', '长春碱', '长春新碱', '长春地辛',
            '顺铂', '卡铂', '奥沙利铂', '奈达铂', '洛铂', '环磷酰胺',
            '异环磷酰胺', '美司钠', '氮芥', '苯丁酸氮芥', '甲氨蝶呤',
            '氟尿嘧啶', '阿糖胞苷', '吉西他滨', '克拉屈滨', '氟达拉滨',
            '来那度胺', '沙利度胺', '泊马度胺', '硼替佐米', '卡非佐米',
            '伊沙佐米', '达雷妥尤单抗', 'isatuximab', 'elotuzumab',
            'belantamab', 'magrolimab', 'tafasitamab',
            'CAR-T', 'TCR-T', 'NK细胞', 'CIK细胞', 'DC细胞',
            'PD-1', 'PD-L1', 'CTLA-4', 'LAG-3', 'TIM-3', 'TIGIT',
            'PARP抑制剂', 'BRCA', 'MSI', 'dMMR', 'TMB', 'NTRK',
            'ROS1', 'ALK', 'EGFR', 'HER2', 'VEGF', 'VEGFR',
            'FGFR', 'MET', 'RET', 'KIT', 'PDGFRA', 'BRAF',
            'KRAS', 'NRAS', 'HRAS', 'PIK3CA', 'PTEN', 'AKT',
            'mTOR', 'MEK', 'ERK', 'RAF', 'SRC', 'ABL',
            'ADC', '抗体偶联药物', '裸抗', '双抗', '双特异性抗体',
            '免疫检查点', '免疫治疗', '靶向治疗', '化疗', '内分泌治疗',
            'olaparib', 'niraparib', 'rucaparib', 'talazoparib', 'veliparib',
            'pemigatinib', 'infigratinib', 'derazantinib', 'erdafitinib',
            'ivosidenib', 'enasidenib', 'ivosidenib', 'ivos',
            'venetoclax', 'venclexta', 'navitoclax',
        ]

        # 基因标志物关键词
        self.gene_marker_keywords = [
            'EGFR', 'ALK', 'ROS1', 'RET', 'MET', 'BRAF', 'KRAS', 'NRAS',
            'HER2', 'ERBB2', 'ERBB3', 'ERBB4', 'VEGF', 'VEGFR', 'FGFR',
            'PD-1', 'PD-L1', 'PD-L2', 'CTLA-4', 'LAG-3', 'TIM-3', 'TIGIT',
            'BRCA1', 'BRCA2', 'PARP', 'MSI', 'dMMR', 'pMMR', 'TMB',
            'NTRK', 'NTRK1', 'NTRK2', 'NTRK3', 'TPM3-NTRK1', 'LMNA-NTRK1',
            'EML4-ALK', 'ALK-EML4', 'ROS1-CD74', 'ROS1-SLC34A2',
            'BRAF-V600E', 'BRAF-V600K', 'BRAF-V600', 'KRAS-G12C', 'KRAS-G12D',
            'KRAS-G12V', 'KRAS-G12', 'KRAS-G13', 'NRAS-Q61',
            'PIK3CA', 'PIK3CA-E545K', 'PIK3CA-H1047R', 'PIK3CA-E542',
            'PTEN', 'AKT1', 'AKT2', 'AKT3', 'mTOR', 'MTOR',
            'ABL1', 'BCR-ABL', 't(9;22)', 'Philadelphia',
            'MYC', 'MYCN', 'MYCL', 'BCL2', 'BCL6', 'MCL1',
            'CD20', 'CD19', 'CD22', 'CD30', 'CD33', 'CD38', 'CD123',
            'BCMA', 'GPRC5D', 'FCRL5', 'SLAMF7',
            'KRAS', 'HRAS', 'NRAS', 'MRAS', 'RRAS', 'RRAS2',
            'RAF1', 'ARAF', 'BRAF', 'KRA', 'NF1', 'NF2',
            'PTCH1', 'SMO', 'SUFU', 'GLI1', 'GLI2', 'SHH',
            'TP53', 'RB1', 'MDM2', 'MDM4', 'CDK4', 'CDK6',
            'ATM', 'ATR', 'CHEK1', 'CHEK2', 'RAD51', 'BRCA',
            'MLH1', 'MSH2', 'MSH6', 'PMS2', 'EPCAM',
            'CDKN2A', 'CDKN2B', 'CDKN1A', 'CDKN1B',
            'APC', 'CTNNB1', 'AXIN1', 'AXIN2', 'AMER1',
            'NOTCH1', 'NOTCH2', 'NOTCH3', 'NOTCH4',
            'JAK1', 'JAK2', 'JAK3', 'STAT3', 'STAT5',
            'FLT3', 'FLT3-ITD', 'FLT3-D835', 'KIT', 'PDGFRA', 'PDGFRB',
            'CSF3R', 'CSF1R', 'KDR', 'FLT1', 'FLT4',
            'IDH1', 'IDH2', 'IDH1-R132', 'IDH2-R140', 'IDH2-R172',
            'DNMT3A', 'DNMT3B', 'DNMT1', 'TET2', 'ASXL1', 'EZH2',
            'ARID1A', 'ARID1B', 'SMARCA4', 'SMARCB1', 'SMARCC1',
            'MED12', 'Cyclin D', 'CCND1', 'CCND2', 'CCND3', 'CDK4', 'CDK6',
            'CDK2', 'CDK1', 'CDK7', 'CDK9', 'CDK12',
            'ER', 'ER+', 'ER-', 'PR', 'PR+', 'PR-', 'HER2', 'HER2+', 'HER2-',
            'AR', 'AR+', 'PSA', 'PSMA',
            'V600E', 'V600K', 'V600', 'G12C', 'G12D', 'G12V', 'G13D',
            'E542K', 'E545K', 'H1047R', 'H1047', 'E545', 'E542',
            'R132H', 'R132', 'R140Q', 'R172K', 'R172',
            'L858R', '19-del', 'T790M', 'C797S',
            'ITD', 'D835', 'F691', 'G691',
            'MSI-H', 'dMMR', 'TMB-H', 'BRAF突变', 'KRAS突变', 'NRAS突变',
            'EGFR突变', 'ALK融合', 'ROS1融合', 'MET扩增', 'MET突变',
            'HER2突变', 'HER2扩增', 'FGFR融合', 'FGFR突变', 'FGFR扩增',
            'NTRK融合', 'NTRK重排', 'BRCA突变', 'HRD', 'LOH',
            'PD-L1表达', 'PD-1表达', 'CD8+T细胞', 'TIL',
        ]

        # 会议类型识别
        self.conference_patterns = {
            'ASCO': r'ASCO|American Society of Clinical Oncology',
            'ESMO': r'ESMO|European Society for Medical Oncology',
            'AACR': r'AACR|American Association for Cancer Research',
            'CSCO': r'CSCO|Chinese Society of Clinical Oncology',
            'WCLC': r'WCLC|World Conference on Lung Cancer',
            'ASH': r'ASH|American Society of Hematology',
            'SGO': r'SGO|Society of Gynecologic Oncology',
            'ESMO Asia': r'ESMO Asia',
        }

        logger.info("ConferencePDFExtractor初始化完成")

    def extract_text_from_pdf(self, pdf_path: str) -> str:
        """
        从文字版PDF提取文本

        Args:
            pdf_path: PDF文件路径

        Returns:
            提取的文本
        """
        if not os.path.exists(pdf_path):
            logger.error(f"PDF文件不存在: {pdf_path}")
            return ""

        text = ""

        # 方法1: PyMuPDF
        if PYMUPDF_AVAILABLE:
            try:
                doc = fitz.open(pdf_path)
                for page_num in range(len(doc)):
                    page = doc[page_num]
                    text += page.get_text()
                    text += "\n--- Page Break ---\n"
                doc.close()
                logger.info(f"PyMuPDF提取成功: {len(text)} 字符")
                return text
            except Exception as e:
                logger.warning(f"PyMuPDF提取失败: {e}")

        # 方法2: pdfplumber
        if PDFPLUMBER_AVAILABLE:
            try:
                with pdfplumber.open(pdf_path) as pdf:
                    for page in pdf.pages:
                        page_text = page.extract_text()
                        if page_text:
                            text += page_text
                            text += "\n--- Page Break ---\n"
                logger.info(f"pdfplumber提取成功: {len(text)} 字符")
                return text
            except Exception as e:
                logger.warning(f"pdfplumber提取失败: {e}")

        logger.warning("没有可用的PDF文字提取库")
        return text

    def extract_text_from_pdf_images(self, pdf_path: str, dpi: int = 300) -> str:
        """
        从图片版PDF提取文本（OCR）

        Args:
            pdf_path: PDF文件路径
            dpi: OCR分辨率

        Returns:
            提取的文本
        """
        if not OCR_AVAILABLE:
            logger.error("OCR库不可用")
            return ""

        if not os.path.exists(pdf_path):
            logger.error(f"PDF文件不存在: {pdf_path}")
            return ""

        text = ""

        try:
            doc = fitz.open(pdf_path)
            for page_num in range(len(doc)):
                page = doc[page_num]
                # 将页面渲染为图像
                pix = page.get_pixmap(dpi=dpi)
                img_data = pix.tobytes("png")
                img = Image.open(io.BytesIO(img_data))

                # OCR
                page_text = pytesseract.image_to_string(img, lang='chi_sim+eng')
                text += page_text
                text += "\n--- Page Break ---\n"

                logger.info(f"第 {page_num + 1} 页OCR完成")

            doc.close()
            logger.info(f"图片PDF OCR提取成功: {len(text)} 字符")

        except Exception as e:
            logger.error(f"图片PDF OCR失败: {e}")

        return text

    def extract_text_auto(self, pdf_path: str) -> str:
        """
        自动选择方式提取文本（先尝试文字版，失败则用OCR）

        Args:
            pdf_path: PDF文件路径

        Returns:
            提取的文本
        """
        # 先尝试文字提取
        text = self.extract_text_from_pdf(pdf_path)

        # 如果提取的文本太少，尝试OCR
        if len(text.strip()) < 500:
            logger.info("文字提取内容过少，尝试图片OCR...")
            text = self.extract_text_from_pdf_images(pdf_path)

        return text

    def identify_conference(self, text: str) -> str:
        """
        识别会议类型

        Args:
            text: PDF文本

        Returns:
            会议名称
        """
        for conf_name, pattern in self.conference_patterns.items():
            if re.search(pattern, text, re.IGNORECASE):
                return conf_name
        return "Unknown"

    def extract_abstracts(self, text: str) -> List[Dict]:
        """
        从文本中提取摘要块

        Args:
            text: PDF文本

        Returns:
            摘要列表
        """
        abstracts = []

        lines = text.split('\n')
        current_abstract = None
        current_lines = []

        abstract_pattern = re.compile(
            r'^\s*(?:Abstract\s*)?(?:#)?\s*(\d{3,6})',
            re.IGNORECASE
        )

        for line in lines:
            match = abstract_pattern.match(line)
            if match:
                if current_abstract and current_lines:
                    abstract_text = '\n'.join(current_lines).strip()
                    if len(abstract_text) > 50:
                        abstracts.append({
                            'number': current_abstract,
                            'text': abstract_text[:3000],
                            'raw_text': abstract_text,
                        })

                current_abstract = match.group(1)
                current_lines = [line]
            elif current_abstract:
                current_lines.append(line)

        if current_abstract and current_lines:
            abstract_text = '\n'.join(current_lines).strip()
            if len(abstract_text) > 50:
                abstracts.append({
                    'number': current_abstract,
                    'text': abstract_text[:3000],
                    'raw_text': abstract_text,
                })

        if len(abstracts) < 2:
            lba_pattern = re.compile(r'^\s*(?:LBA\s*(\d+))', re.IGNORECASE)
            current_lba = None
            lba_lines = []

            for line in lines:
                match = lba_pattern.match(line)
                if match:
                    if current_lba and lba_lines:
                        abstract_text = '\n'.join(lba_lines).strip()
                        if len(abstract_text) > 50:
                            abstracts.append({
                                'number': f'LBA{current_lba}',
                                'text': abstract_text[:3000],
                                'raw_text': abstract_text,
                            })
                    current_lba = match.group(1)
                    lba_lines = [line]
                elif current_lba:
                    lba_lines.append(line)

            if current_lba and lba_lines:
                abstract_text = '\n'.join(lba_lines).strip()
                if len(abstract_text) > 50:
                    abstracts.append({
                        'number': f'LBA{current_lba}',
                        'text': abstract_text[:3000],
                        'raw_text': abstract_text,
                    })

        if len(abstracts) < 2:
            num_pattern = re.compile(r'^\s*#\s*(\d{3,6})\s')
            current_num = None
            num_lines = []

            for line in lines:
                match = num_pattern.match(line)
                if match and len(match.group(1)) >= 3:
                    if current_num and num_lines:
                        abstract_text = '\n'.join(num_lines).strip()
                        if len(abstract_text) > 50:
                            abstracts.append({
                                'number': current_num,
                                'text': abstract_text[:3000],
                                'raw_text': abstract_text,
                            })
                    current_num = match.group(1)
                    num_lines = [line]
                elif current_num:
                    num_lines.append(line)

            if current_num and num_lines:
                abstract_text = '\n'.join(num_lines).strip()
                if len(abstract_text) > 50:
                    abstracts.append({
                        'number': current_num,
                        'text': abstract_text[:3000],
                        'raw_text': abstract_text,
                    })

        if len(abstracts) < 3:
            paragraphs = re.split(r'\n\s*\n', text)
            for para in paragraphs:
                para = para.strip()
                if len(para) > 100 and any(
                    kw.lower() in para.lower()
                    for kw in ['patient', 'tumor', 'cancer', 'trial', 'phase', 'ORR', 'PFS', 'OS']
                ):
                    abstracts.append({
                        'number': str(len(abstracts) + 1),
                        'text': para[:3000],
                        'raw_text': para,
                    })

        seen = set()
        unique_abstracts = []
        for ab in abstracts:
            key = str(ab['number']) + ab['text'][:30]
            if key not in seen:
                seen.add(key)
                unique_abstracts.append(ab)

        logger.info(f"提取到 {len(unique_abstracts)} 个摘要")
        return unique_abstracts

    def extract_drug_info(self, abstract_text: str) -> List[str]:
        """
        从摘要中提取抗肿瘤药物

        Args:
            abstract_text: 摘要文本

        Returns:
            药物列表
        """
        found_drugs = []

        for keyword in self.anti_tumor_drug_keywords:
            if keyword.lower() in abstract_text.lower():
                if keyword not in found_drugs:
                    found_drugs.append(keyword)

        # 英文药物名匹配
        english_drug_pattern = r'(?:pembrolizumab|nivolumab|camrelizumab|sintilimab|toripalimab|tislelizumab|atezolizumab|durvalumab|cetuximab|nimotuzumab|trastuzumab|pertuzumab|bevacizumab|ramucirumab|trastuzumab deruxtecan|ipilimumab|osimertinib|gefitinib|erlotinib|icotinib|afatinib|dacomitinib|neratinib|lapatinib|pyrotinib|tucatinib|sunitinib|sorafenib|lenvatinib|pazopanib|apatinib|anlotinib|nintedanib|everolimus|temsirolimus|vemurafenib|dabrafenib|encorafenib|binimetinib|cobimetinib|trametinib|selumetinib|crizotinib|ceritinib|alectinib|brigatinib|lorlatinib|ensartinib|ibrutinib|acalabrutinib|zanubrutinib|duvelisib|parinib|crizotinib|lorlatinib|olaparib|niraparib|rucaparib|talazoparib|veliparib|pemigatinib|infigratinib|erdafitinib|ivosidenib|enasidenib|venetoclax|isatuximab|elotuzumab|belantamab|magrolimab|tafasitamab|daratumumab|idecabtagene|vicleucel|axi-cel|tisa-cel|liso-cel|axi-cel| plano-cel)\b'
        english_matches = re.findall(english_drug_pattern, abstract_text, re.IGNORECASE)
        for drug in english_matches:
            if drug.lower() not in [d.lower() for d in found_drugs]:
                found_drugs.append(drug.capitalize())

        return found_drugs

    def extract_gene_markers(self, abstract_text: str) -> List[str]:
        """
        从摘要中提取基因标志物

        Args:
            abstract_text: 摘要文本

        Returns:
            基因标志物列表
        """
        found_markers = []

        for keyword in self.gene_marker_keywords:
            if keyword.upper() in abstract_text.upper():
                if keyword not in found_markers:
                    found_markers.append(keyword)

        return found_markers

    def extract_study_info(self, abstract_text: str) -> Dict:
        """
        提取研究信息

        Args:
            abstract_text: 摘要文本

        Returns:
            研究信息字典
        """
        info = {
            'phase': '',
            'study_type': '',
            'sample_size': '',
            'efficacy': {},
            'safety': {},
        }

        # 试验分期
        phase_patterns = [
            r'(?:phase|Ph\.?|ph\.?)\s*(I{1,3}|II{1,2}|III{1,2}|IV|1|2|3|4)\b',
            r'(?:Phase|Ph\.?|ph\.?)\s*(I{1,3}|II{1,2}|III{1,2}|IV)\b',
        ]
        for pattern in phase_patterns:
            match = re.search(pattern, abstract_text, re.IGNORECASE)
            if match:
                info['phase'] = match.group(0)
                break

        # 样本量
        size_patterns = [
            r'(\d+)\s*(?:patients?|pts?|subjects?|participants?|cases?|样本|患者)',
            r'N\s*[=≈]\s*(\d+)',
            r'enrollment\s*[=:]\s*(\d+)',
        ]
        for pattern in size_patterns:
            match = re.search(pattern, abstract_text, re.IGNORECASE)
            if match:
                info['sample_size'] = match.group(1)
                break

        # 疗效数据
        efficacy_patterns = [
            (r'ORR\s*[=:]\s*(\d+(?:\.\d+)?)\s*%?', 'ORR'),
            (r'DCR\s*[=:]\s*(\d+(?:\.\d+)?)\s*%?', 'DCR'),
            (r'PFS\s*[=:]\s*(\d+(?:\.\d+)?)\s*(?:months|m|月)', 'PFS'),
            (r'OS\s*[=:]\s*(\d+(?:\.\d+)?)\s*(?:months|m|月|years|y|年)', 'OS'),
            (r'C?R\s*[=:]\s*(\d+(?:\.\d+)?)\s*%?', 'CR'),
            (r'PR\s*[=:]\s*(\d+(?:\.\d+)?)\s*%?', 'PR'),
            (r'SD\s*[=:]\s*(\d+(?:\.\d+)?)\s*%?', 'SD'),
        ]
        for pattern, metric in efficacy_patterns:
            match = re.search(pattern, abstract_text, re.IGNORECASE)
            if match:
                info['efficacy'][metric] = match.group(1)

        return info

    def process_abstract(self, abstract: Dict, conference: str) -> Optional[Dict]:
        """
        处理单个摘要

        Args:
            abstract: 摘要数据
            conference: 会议名称

        Returns:
            处理后的数据
        """
        text = abstract.get('text', '')

        drugs = self.extract_drug_info(text)
        genes = self.extract_gene_markers(text)
        study_info = self.extract_study_info(text)

        # 如果没有找到药物和基因，跳过
        if not drugs and not genes:
            return None

        return {
            'conference_name': conference,
            'conference_year': datetime.now().year,
            'abstract_number': abstract.get('number', ''),
            'title_en': '',
            'title_cn': '',
            'authors': '',
            'presentation_type': '',
            'session_name': '',
            'tumor_type': '',
            'tumor_type_cn': '',
            'target_gene': ', '.join(genes[:5]),
            'drug_name': ', '.join(drugs[:5]),
            'study_phase': study_info.get('phase', ''),
            'key_findings_en': '',
            'key_findings_cn': '',
            'efficacy_data': str(study_info.get('efficacy', {})),
            'sample_size': study_info.get('sample_size', ''),
            'url': '',
            'data_collection_time': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'source_file': abstract.get('source_file', ''),
            'source': 'PDF_Extraction'
        }

    def process_pdf_file(self, pdf_path: str, conference: str = None) -> List[Dict]:
        """
        处理单个PDF文件

        Args:
            pdf_path: PDF文件路径
            conference: 会议名称（可选，自动识别）

        Returns:
            提取的数据列表
        """
        logger.info(f"处理PDF文件: {pdf_path}")

        # 提取文本
        text = self.extract_text_auto(pdf_path)

        if not text or len(text.strip()) < 100:
            logger.warning(f"PDF文本提取失败或内容过少: {pdf_path}")
            return []

        # 识别会议
        if not conference:
            conference = self.identify_conference(text)
            logger.info(f"识别会议: {conference}")

        # 提取摘要
        abstracts = self.extract_abstracts(text)

        if not abstracts:
            logger.warning("未提取到摘要，尝试整页处理...")
            abstracts = [{'number': '1', 'text': text, 'source_file': os.path.basename(pdf_path)}]

        # 处理每个摘要
        results = []
        for abstract in abstracts:
            abstract['source_file'] = os.path.basename(pdf_path)
            processed = self.process_abstract(abstract, conference)
            if processed:
                results.append(processed)

        logger.info(f"从 {pdf_path} 提取到 {len(results)} 条有效记录")
        return results

    def save_to_database(self, db_manager, data_list: List[Dict]) -> Dict:
        """
        保存数据到数据库

        Args:
            db_manager: 数据库管理器
            data_list: 数据列表

        Returns:
            统计信息
        """
        stats = {'processed': 0, 'added': 0, 'updated': 0, 'errors': 0}

        for data in data_list:
            try:
                stats['processed'] += 1

                existing = db_manager.execute_query(
                    "SELECT id FROM conference_abstracts WHERE conference_name = ? AND conference_year = ? AND abstract_number = ?",
                    (data.get('conference_name'), data.get('conference_year'), data.get('abstract_number'))
                )

                if existing:
                    db_manager.execute_update(
                        'conference_abstracts',
                        data,
                        'conference_name = ? AND conference_year = ? AND abstract_number = ?',
                        (data.get('conference_name'), data.get('conference_year'), data.get('abstract_number'))
                    )
                    stats['updated'] += 1
                else:
                    db_manager.execute_insert('conference_abstracts', data)
                    stats['added'] += 1

            except Exception as e:
                logger.error(f"保存失败: {e}")
                stats['errors'] += 1

        return stats


# 辅助模块
import io


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)

    extractor = ConferencePDFExtractor()

    test_pdf = "test_abstracts.pdf"
    if os.path.exists(test_pdf):
        results = extractor.process_pdf_file(test_pdf)
        print(f"提取结果: {len(results)} 条")
        for r in results[:5]:
            print(f"  - {r.get('drug_name', 'N/A')} | {r.get('target_gene', 'N/A')}")
