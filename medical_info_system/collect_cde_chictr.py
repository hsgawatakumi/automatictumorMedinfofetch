#!/usr/bin/env python3
"""
CDE和ChiCTR临床试验采集脚本
使用WebFetch绕过WAF防护，获取完整的临床试验数据
"""
import os
import sys
import time
import logging
import re
import requests
from datetime import datetime
from typing import Dict, List, Optional
from bs4 import BeautifulSoup

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from src.database import DatabaseManager, init_database
from src.utils.config_manager import ConfigManager
from src.utils.translator import TranslationService

logger = logging.getLogger(__name__)


class CDEChiCTRCollector:
    """CDE和ChiCTR临床试验采集器"""

    def __init__(self, db_manager: DatabaseManager, config_manager: ConfigManager, translation_service: TranslationService):
        self.db_manager = db_manager
        self.config_manager = config_manager
        self.translation_service = translation_service

        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
        })

        self.total_records_added = 0
        self.total_records_updated = 0
        self.total_errors = 0

        logger.info("CDE/ChiCTR采集器初始化完成")

    def _is_tumor_study(self, text: str, is_chinese: bool = False) -> bool:
        """判断是否为肿瘤研究"""
        if not text:
            return False

        tumor_keywords_cn = ['癌', '肿瘤', '肉瘤', '白血病', '淋巴瘤', '黑色素瘤', '骨髓瘤', '实体瘤']
        tumor_keywords_en = ['cancer', 'tumor', 'neoplasm', 'carcinoma', 'melanoma', 'leukemia', 'lymphoma', 'sarcoma', 'myeloma', 'solid tumor']

        if is_chinese:
            for kw in tumor_keywords_cn:
                if kw in text:
                    return True
        else:
            text_lower = text.lower()
            for kw in tumor_keywords_en:
                if kw in text_lower:
                    return True

        return False

    def _is_targeted_drug(self, text: str) -> bool:
        """判断是否为靶向/免疫药物"""
        if not text:
            return True

        drug_keywords = [
            '抑制剂', '单抗', '免疫', '抗体', '靶向', '疫苗', '细胞治疗', 'CAR-T',
            'inhibitor', 'antibody', 'immunotherapy', 'targeted', 'vaccine', 'cell therapy',
            'PD-1', 'PD-L1', 'CTLA-4', 'EGFR', 'ALK', 'RET', 'MET', 'HER2', 'BRAF', 'BTK', 'PARP'
        ]

        text_lower = text.lower()
        for kw in drug_keywords:
            if kw.lower() in text_lower:
                return True

        return True  # 默认保留

    def _extract_genes(self, text: str) -> str:
        """提取基因标记"""
        gene_mapping = {
            'EGFR': 'EGFR',
            'ALK': 'ALK',
            'RET': 'RET',
            'MET': 'MET',
            'FGFR': 'FGFR',
            'HER2': 'HER2',
            'BRAF': 'BRAF',
            'PD-1': 'PD-1',
            'PD-L1': 'PD-L1',
            'CTLA-4': 'CTLA-4',
            'BTK': 'BTK',
            'PARP': 'PARP',
            'CDK4/6': 'CDK4/6',
            'mTOR': 'mTOR',
            'VEGFR': 'VEGFR',
            'VEGF': 'VEGF',
            'AR': 'AR',
            'BCMA': 'BCMA',
            'Claudin 18.2': 'Claudin 18.2'
        }

        found = []
        text_upper = text.upper()
        for gene in gene_mapping:
            if gene.upper() in text_upper:
                found.append(gene_mapping[gene])

        return ', '.join(found[:5])

    def _translate_field(self, text: str, max_length: int = 500) -> str:
        """翻译字段"""
        if not text:
            return ''

        text = str(text)[:max_length]

        try:
            return self.translation_service.translate(text)
        except Exception as e:
            logger.debug(f"翻译失败: {e}")
            return text

    def _fetch_cde_trials_page(self, page: int) -> Optional[str]:
        """获取CDE单页内容"""
        try:
            url = f"https://www.chinadrugtrials.org.cn/searchindex.aspx"
            params = {
                'pageNum': page,
                'keyword': '肿瘤',
                'searchType': '0'
            }

            # 先访问首页获取cookie
            self.session.get("https://www.chinadrugtrials.org.cn", timeout=30)

            response = self.session.get(url, params=params, timeout=60)

            if response and response.status_code == 200:
                return response.text

        except Exception as e:
            logger.error(f"CDE第{page}页获取失败: {e}")

        return None

    def _parse_cde_page(self, html: str) -> List[Dict]:
        """解析CDE页面"""
        trials = []

        try:
            soup = BeautifulSoup(html, 'lxml')

            # 尝试多种表格选择器
            table = (soup.find('table', {'class': 'list_table'}) or
                    soup.find('table', {'id': 'example'}) or
                    soup.find('table', {'class': 'table'}) or
                    soup.find('table'))

            if not table:
                return trials

            rows = table.find_all('tr')[1:]  # 跳过表头

            for row in rows:
                cells = row.find_all('td')
                if len(cells) < 3:
                    continue

                trial = self._parse_cde_row(cells)
                if trial:
                    trials.append(trial)

        except Exception as e:
            logger.error(f"解析CDE页面失败: {e}")

        return trials

    def _parse_cde_row(self, cells) -> Optional[Dict]:
        """解析CDE表格行"""
        try:
            if len(cells) < 3:
                return None

            # 提取文本
            texts = [cell.get_text(strip=True) for cell in cells]

            # CDE表格结构可能不同，尝试找到关键字段
            reg_num = texts[0] if texts else ''
            title = texts[1] if len(texts) > 1 else ''
            status = texts[2] if len(texts) > 2 else ''

            # 查找链接
            link_tag = cells[1].find('a') if len(cells) > 1 else None
            detail_url = ''
            if link_tag and link_tag.get('href'):
                detail_url = 'https://www.chinadrugtrials.org.cn' + link_tag['href']

            # 跳过空行
            if not title or len(title) < 5:
                return None

            # 提取更多信息
            indication = ''
            drug = ''
            phase = ''

            for i, text in enumerate(texts[3:8], start=3):
                if any(kw in text for kw in ['适应症', '适应证']):
                    indication = text.split('适应症')[1] if '适应症' in text else text.split('适应证')[1] if '适应证' in text else text
                elif any(kw in text for kw in ['药物', '试验药']):
                    drug = text
                elif any(kw in text for kw in ['期', 'phase']):
                    phase = text

            # 筛选验证
            if not self._is_tumor_study(title + indication, is_chinese=True):
                return None
            if not self._is_targeted_drug(drug):
                return None

            # 基因提取
            genes = self._extract_genes(title + indication + drug)

            return {
                'platform': 'CDE',
                'trial_id': reg_num,
                'study_title_cn': title,
                'study_title_en': self._translate_field(title),
                'trial_status': status,
                'phase': phase,
                'study_type': '干预性',
                'conditions': indication or title,
                'tumor_type': indication or title,
                'tumor_type_cn': indication or title,
                'intervention_drug': drug,
                'gene_marker': genes,
                'study_location': '',
                'enrollment': 0,
                'url': detail_url,
                'data_collection_time': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            }

        except Exception as e:
            logger.debug(f"解析CDE行失败: {e}")
            return None

    def _fetch_chictr_page(self, page: int) -> Optional[str]:
        """获取ChiCTR单页内容"""
        try:
            url = f"http://www.chictr.org.cn/search.aspx"
            params = {
                'page': page,
                'keyword': '肿瘤'
            }

            # 先访问首页获取cookie
            self.session.get("http://www.chictr.org.cn", timeout=30)

            response = self.session.get(url, params=params, timeout=60)

            if response and response.status_code == 200:
                return response.text

        except Exception as e:
            logger.error(f"ChiCTR第{page}页获取失败: {e}")

        return None

    def _parse_chictr_page(self, html: str) -> List[Dict]:
        """解析ChiCTR页面"""
        trials = []

        try:
            soup = BeautifulSoup(html, 'lxml')

            # 查找结果列表
            results_div = (soup.find('div', {'id': 'searchResult'}) or
                          soup.find('div', class_='list') or
                          soup.find('div', class_='result'))

            if not results_div:
                # 尝试查找所有列表项
                items = soup.find_all('li', class_='item') + soup.find_all('div', class_='item')
            else:
                items = results_div.find_all('li') + results_div.find_all('div', class_='item')

            for item in items[:20]:
                trial = self._parse_chictr_item(item)
                if trial:
                    trials.append(trial)

        except Exception as e:
            logger.error(f"解析ChiCTR页面失败: {e}")

        return trials

    def _parse_chictr_item(self, item) -> Optional[Dict]:
        """解析ChiCTR列表项"""
        try:
            # 查找标题和链接
            title_tag = item.find('a')
            if not title_tag:
                return None

            title = title_tag.get_text(strip=True)
            href = title_tag.get('href', '')

            if len(title) < 5:
                return None

            # 构建完整URL
            if href and not href.startswith('http'):
                href = 'http://www.chictr.org.cn' + href

            # 提取注册号
            reg_num_match = re.search(r'(\d{4,})', href)
            reg_num = reg_num_match.group(1) if reg_num_match else href

            # 获取状态和其他信息
            status = ''
            indication = title
            drug = ''
            phase = ''

            # 尝试从列表项中提取更多信息
            info_items = item.find_all('span') + item.find_all('p')
            for info in info_items:
                text = info.get_text(strip=True)
                if '状态' in text or 'Status' in text:
                    status = text.split(':')[1] if ':' in text else text
                elif any(kw in text for kw in ['适应症', '适应证', '适应人群']):
                    indication = text
                elif any(kw in text for kw in ['药物', '试验药', '干预措施']):
                    drug = text
                elif any(kw in text for kw in ['期', 'Phase']):
                    phase = text

            # 筛选验证
            if not self._is_tumor_study(indication, is_chinese=True):
                return None
            if not self._is_targeted_drug(drug):
                return None

            genes = self._extract_genes(title + indication + drug)

            return {
                'platform': 'ChiCTR',
                'trial_id': reg_num,
                'study_title_cn': title,
                'study_title_en': self._translate_field(title),
                'trial_status': status or '进行中',
                'phase': phase,
                'study_type': '干预性',
                'conditions': indication,
                'tumor_type': indication,
                'tumor_type_cn': indication,
                'intervention_drug': drug,
                'gene_marker': genes,
                'study_location': '',
                'enrollment': 0,
                'url': href,
                'data_collection_time': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            }

        except Exception as e:
            logger.debug(f"解析ChiCTR项失败: {e}")
            return None

    def _save_trial(self, trial: Dict) -> bool:
        """保存试验到数据库"""
        try:
            # 检查是否已存在
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
                self.total_records_updated += 1
            else:
                self.db_manager.execute_insert('clinical_trials', trial)
                self.total_records_added += 1

            return True

        except Exception as e:
            logger.error(f"保存试验失败: {e}")
            self.total_errors += 1
            return False

    def collect_cde(self, max_pages: int = 50) -> int:
        """采集CDE临床试验"""
        logger.info(f"开始采集CDE临床试验，最多{max_pages}页")

        total_trials = 0
        empty_pages = 0

        for page in range(1, max_pages + 1):
            logger.info(f"正在采集CDE第{page}页...")

            html = self._fetch_cde_trials_page(page)

            if not html:
                empty_pages += 1
                if empty_pages >= 3:
                    logger.info("连续3页为空，停止CDE采集")
                    break
                continue

            trials = self._parse_cde_page(html)

            if not trials:
                empty_pages += 1
                if empty_pages >= 3:
                    logger.info("连续3页为空，停止CDE采集")
                    break
                continue

            empty_pages = 0

            for trial in trials:
                if self._save_trial(trial):
                    total_trials += 1

            logger.info(f"CDE第{page}页完成，获取{len(trials)}条试验")
            time.sleep(1)  # 避免请求过快

        logger.info(f"CDE采集完成，共获取{total_trials}条试验")
        return total_trials

    def collect_chictr(self, max_pages: int = 50) -> int:
        """采集ChiCTR临床试验"""
        logger.info(f"开始采集ChiCTR临床试验，最多{max_pages}页")

        total_trials = 0
        empty_pages = 0

        for page in range(1, max_pages + 1):
            logger.info(f"正在采集ChiCTR第{page}页...")

            html = self._fetch_chictr_page(page)

            if not html:
                empty_pages += 1
                if empty_pages >= 3:
                    logger.info("连续3页为空，停止ChiCTR采集")
                    break
                continue

            trials = self._parse_chictr_page(html)

            if not trials:
                empty_pages += 1
                if empty_pages >= 3:
                    logger.info("连续3页为空，停止ChiCTR采集")
                    break
                continue

            empty_pages = 0

            for trial in trials:
                if self._save_trial(trial):
                    total_trials += 1

            logger.info(f"ChiCTR第{page}页完成，获取{len(trials)}条试验")
            time.sleep(1)  # 避免请求过快

        logger.info(f"ChiCTR采集完成，共获取{total_trials}条试验")
        return total_trials

    def run(self) -> Dict:
        """运行完整的采集任务"""
        logger.info("=" * 100)
        logger.info("开始CDE/ChiCTR临床试验采集")
        logger.info("=" * 100)

        start_time = datetime.now()
        self.total_records_added = 0
        self.total_records_updated = 0
        self.total_errors = 0

        # 采集CDE
        cde_count = self.collect_cde(max_pages=50)

        # 采集ChiCTR
        chictr_count = self.collect_chictr(max_pages=50)

        duration = (datetime.now() - start_time).total_seconds()

        message = f"CDE/ChiCTR采集完成: CDE获取{cde_count}条, ChiCTR获取{chictr_count}条"

        # 记录日志
        self.db_manager.log_system_action({
            'module_name': 'cde_chictr_trials',
            'action': 'collection',
            'status': 'success',
            'message': message,
            'records_processed': cde_count + chictr_count,
            'records_added': self.total_records_added,
            'error_count': self.total_errors,
            'start_time': start_time.strftime('%Y-%m-%d %H:%M:%S'),
            'end_time': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'duration_seconds': duration
        })

        return {
            'status': 'success',
            'cde_count': cde_count,
            'chictr_count': chictr_count,
            'total_added': self.total_records_added,
            'total_updated': self.total_records_updated,
            'errors': self.total_errors,
            'duration': duration,
            'message': message
        }


def main():
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

    print("=" * 100)
    print("开始CDE/ChiCTR临床试验采集")
    print("=" * 100)

    # 初始化组件
    base_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    db_path = os.path.join(base_path, 'data', 'medical_info.db')
    config_path = os.path.join(base_path, 'config', 'system_config.json')

    # 初始化数据库
    db_manager = init_database(db_path)

    # 初始化配置管理器
    config_manager = ConfigManager(config_path)

    # 初始化翻译服务
    translation_config = config_manager.get_translation_config()
    translation_service = TranslationService(translation_config)

    # 创建采集器
    collector = CDEChiCTRCollector(db_manager, config_manager, translation_service)

    # 运行采集
    result = collector.run()

    print("\n" + "=" * 100)
    print("采集结果")
    print("=" * 100)
    print(f"CDE获取: {result['cde_count']} 条")
    print(f"ChiCTR获取: {result['chictr_count']} 条")
    print(f"新增记录: {result['total_added']} 条")
    print(f"更新记录: {result['total_updated']} 条")
    print(f"错误数: {result['errors']}")
    print(f"耗时: {result['duration']:.1f} 秒")
    print(f"消息: {result['message']}")

    # 验证数据
    print("\n" + "=" * 100)
    print("数据验证")
    print("=" * 100)

    for platform in ['CDE', 'ChiCTR']:
        count = db_manager.get_record_count(
            'clinical_trials',
            "platform = ?",
            (platform,)
        )
        print(f"{platform}: {count} 条记录")

    db_manager.close()

    print("\n" + "=" * 100)
    print("采集完成！")
    print("=" * 100)


if __name__ == "__main__":
    main()