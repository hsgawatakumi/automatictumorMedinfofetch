#!/usr/bin/env python3
"""补充采集缺失的关键抗肿瘤药物"""
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

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# 仍缺失的药物
STILL_MISSING = [
    # BTK抑制剂
    'ibrutinib', 'acalabrutinib', 'zanubrutinib',
    # CDK4/6抑制剂
    'palbociclib', 'ribociclib', 'abemaciclib',
    # 多靶点TKI
    'sunitinib', 'sorafenib', 'pazopanib', 'axitinib', 'lenvatinib', 'cabozantinib', 'regorafenib',
    # mTOR抑制剂
    'everolimus', 'temsirolimus',
    # RET抑制剂
    'pralsetinib',
    # MET抑制剂
    'tepotinib',
    # FGFR抑制剂
    'erdafitinib', 'pemigatinib', 'infigratinib',
    # FLT3抑制剂
    'quizartinib', 'gilteritinib',
    # JAK抑制剂
    'fedratinib',
    # PI3K抑制剂
    'idelalisib', 'duvelisib', 'copanlisib', 'alpelisib',
    # IDH抑制剂
    'enasidenib', 'ivosidenib',
    # BCL-2
    'venetoclax',
    # 蛋白酶体抑制剂
    'bortezomib', 'carfilzomib', 'ixazomib',
    # HDAC
    'vorinostat', 'romidepsin', 'panobinostat',
    # 免疫调节剂
    'lenalidomide', 'pomalidomide',
    # 其他
    'midostaurin', 'ruxolitinib',
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
    print("补充采集缺失的关键抗肿瘤药物")
    print(f"待采集: {len(STILL_MISSING)} 个药物")
    print("=" * 80)

    collector = create_collector()
    url = 'https://api.fda.gov/drug/drugsfda.json'

    total_added = 0

    # 分批处理
    batch_size = 10
    for i in range(0, len(STILL_MISSING), batch_size):
        batch = STILL_MISSING[i:i+batch_size]
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
            else:
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
                    except Exception as e:
                        logger.warning(f"处理失败: {e}")

            time.sleep(0.5)

        except Exception as e:
            logger.error(f"批次失败: {e}")

    print(f"\n{'=' * 80}")
    print(f"补充采集完成！新增记录: {total_added}")
    print("=" * 80)


if __name__ == "__main__":
    main()
