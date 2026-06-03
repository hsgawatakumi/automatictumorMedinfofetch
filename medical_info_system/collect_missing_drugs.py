#!/usr/bin/env python3
"""
补充采集缺失的FDA抗肿瘤药物
"""
import os
import sys
import time
import logging
import requests
from datetime import datetime

current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, current_dir)

from src.database import init_database
from src.utils.config_manager import create_config_manager
from src.utils.translator import TranslationService
from src.utils.http_client import RequestManager
from src.collectors.fda_collector import FDADrugCollector

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# 缺失的药物列表
MISSING_DRUGS = [
    # PD-1/PD-L1
    'avelumab', 'dostarlimab',
    # CTLA-4 (已收录部分)
    # HER2 (部分已收录)
    'neratinib', 'margetuximab',
    # EGFR (部分已收录)
    'dacomitinib', 'mobocertinib',
    # VEGF (部分已收录)
    'ziv-aflibercept',
    # PARP
    'olaparib', 'niraparib', 'rucaparib', 'talazoparib',
    # BTK
    'ibrutinib', 'acalabrutinib', 'zanubrutinib',
    # CDK4/6
    'palbociclib', 'ribociclib', 'abemaciclib',
    # mTOR
    'everolimus', 'temsirolimus',
    # Multi-target TKIs
    'sunitinib', 'sorafenib', 'pazopanib', 'axitinib', 'lenvatinib', 'cabozantinib',
    # NTRK
    'larotrectinib', 'entrectinib',
    # RET
    'pralsetinib',
    # MET
    'tepotinib',
    # FGFR (部分已收录)
    'erdafitinib', 'pemigatinib', 'infigratinib',
    # ADC
    'polatuzumab vedotin', 'enfortumab vedotin',
    'sacituzumab govitecan', 'belantamab mafodotin',
    'loncastuximab tesirine',
    # 蛋白酶体抑制剂
    'bortezomib', 'carfilzomib', 'ixazomib',
    # HDAC抑制剂
    'vorinostat', 'romidepsin', 'panobinostat',
    # 免疫调节剂
    'lenalidomide', 'pomalidomide', 'thalidomide',
    # BCL-2
    'venetoclax',
    # FLT3 (部分已收录)
    'quizartinib',
    # JAK (部分已收录)
    'fedratinib',
    # PI3K (部分已收录)
    'idelalisib', 'duvelisib', 'copanlisib', 'alpelisib',
    # IDH
    'enasidenib', 'ivosidenib',
    # 其他
    'plitidepsin', 'abiraterone', 'enzalutamide', 'apalutamide', 'degarelix',
    'leuprolide', 'octreotide', 'tamoxifen', 'fulvestrant',
]


def create_collector():
    config_path = os.path.join(current_dir, 'config', 'config.yaml')
    db_path = os.path.join(current_dir, 'data', 'medical_info.db')
    config_manager = create_config_manager(config_path)
    db_manager = init_database(db_path)
    translation_service = TranslationService(config_manager.get_translation_config())
    request_manager = RequestManager(config_manager.get_proxy_config())
    return FDADrugCollector(db_manager, config_manager, translation_service, request_manager)


def main():
    print("=" * 80)
    print("补充采集缺失的FDA抗肿瘤药物")
    print("=" * 80)

    collector = create_collector()
    url = 'https://api.fda.gov/drug/drugsfda.json'

    total_added = 0
    total_found = 0

    # 分批处理
    batch_size = 10
    for i in range(0, len(MISSING_DRUGS), batch_size):
        batch = MISSING_DRUGS[i:i+batch_size]
        query = ' OR '.join(batch)

        print(f"\n批次 {i//batch_size + 1}: 搜索 {len(batch)} 个药物")

        try:
            params = {'search': query, 'skip': 0, 'limit': 100}
            response = requests.get(url, params=params, timeout=60)

            if response.status_code != 200:
                print(f"  API错误: {response.status_code}")
                time.sleep(1)
                continue

            data = response.json()
            results = data.get('results', [])

            if not results:
                print(f"  无数据")
                time.sleep(0.5)
                continue

            print(f"  获得 {len(results)} 条FDA记录")

            drugs = collector.parse_drug_data(data)
            print(f"  识别出 {len(drugs)} 条抗肿瘤药物")

            for drug in drugs:
                try:
                    drug = collector.translate_drug_data(drug)
                    split_drugs = collector.split_by_indication(drug)
                    for split_drug in split_drugs:
                        if collector.save_to_database(split_drug):
                            total_added += 1
                        total_found += 1
                except Exception as e:
                    logger.warning(f"处理失败: {e}")

            time.sleep(0.5)

        except Exception as e:
            logger.error(f"批次失败: {e}")

    print(f"\n{'=' * 80}")
    print(f"补充采集完成！")
    print(f"新增记录: {total_added}")
    print(f"处理记录: {total_found}")
    print("=" * 80)

    # 检查最终状态
    db_path = os.path.join(current_dir, 'data', 'medical_info.db')
    db_manager = init_database(db_path)
    fda_count = db_manager.get_record_count('approved_drugs', "regulatory_agency = 'FDA'")
    print(f"\n数据库中FDA药物记录总数: {fda_count}")


if __name__ == "__main__":
    main()
