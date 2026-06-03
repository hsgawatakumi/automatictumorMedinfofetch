#!/usr/bin/env python3
"""强化采集缺失的关键抗肿瘤药物"""
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

# 缺失的关键药物及其品牌名、通用名
CRITICAL_MISSING_DRUGS = {
    # BTK抑制剂
    'ibrutinib': ['imbruvica', 'ibrutinib'],
    'acalabrutinib': ['calquence', 'acalabrutinib'],
    'zanubrutinib': ['brukinsa', 'zanubrutinib'],
    
    # CDK4/6抑制剂
    'palbociclib': ['ibrance', 'palbociclib'],
    'ribociclib': ['kisqali', 'ribociclib'],
    'abemaciclib': ['verzenio', 'abemaciclib'],
    
    # 多靶点TKI
    'sunitinib': ['sutent', 'sunitinib'],
    'sorafenib': ['nexavar', 'sorafenib'],
    'pazopanib': ['votrient', 'pazopanib'],
    'axitinib': ['inlyta', 'axitinib'],
    'lenvatinib': ['lenvima', 'lenvatinib'],
    'cabozantinib': ['cometriq', 'cabozantinib', 'cabometyx'],
    'regorafenib': ['stivarga', 'regorafenib'],
    
    # mTOR抑制剂
    'everolimus': ['afinitor', 'everolimus'],
    'temsirolimus': ['torisel', 'temsirolimus'],
    
    # RET抑制剂
    'pralsetinib': ['gavreto', 'pralsetinib'],
    
    # MET抑制剂
    'tepotinib': ['tepmertko', 'tepotinib'],
    'capmatinib': ['tabrecta', 'capmatinib'],
    
    # FGFR抑制剂
    'erdafitinib': ['balversa', 'erdafitinib'],
    'pemigatinib': ['pemazyre', 'pemigatinib'],
    'infigratinib': ['truseltiq', 'infigratinib'],
    
    # FLT3抑制剂
    'midostaurin': ['rydapt', 'midostaurin'],
    'gilteritinib': ['xospata', 'gilteritinib'],
    'quizartinib': ['vanflyta', 'quizartinib'],
    
    # JAK抑制剂
    'ruxolitinib': ['jakafi', 'ruxolitinib'],
    'fedratinib': ['inrebic', 'fedratinib'],
    
    # PI3K抑制剂
    'idelalisib': ['zydelig', 'idelalisib'],
    'duvelisib': ['copiktra', 'duvelisib'],
    'copanlisib': ['aliqopa', 'copanlisib'],
    'alpelisib': ['piqray', 'alpelisib'],
    
    # IDH抑制剂
    'enasidenib': ['idhifa', 'enasidenib'],
    'ivosidenib': ['tibsovo', 'ivosidenib'],
    
    # BCL-2
    'venetoclax': ['venclexta', 'venetoclax'],
    'navitoclax': ['navitoclax'],
    
    # 蛋白酶体抑制剂
    'bortezomib': ['velcade', 'bortezomib'],
    'carfilzomib': ['kyprolis', 'carfilzomib'],
    'ixazomib': ['ninlaro', 'ixazomib'],
    
    # HDAC
    'vorinostat': ['zolinza', 'vorinostat'],
    'romidepsin': ['istodax', 'romidepsin'],
    'panobinostat': ['farydak', 'panobinostat'],
    
    # 免疫调节剂
    'lenalidomide': ['revlimid', 'lenalidomide'],
    'pomalidomide': ['pomalyst', 'pomalidomide'],
    'thalidomide': ['thalomid', 'thalidomide'],
}


def create_collector():
    config_path = os.path.join(current_dir, 'config', 'config.yaml')
    db_path = os.path.join(current_dir, 'data', 'medical_info.db')
    config_manager = create_config_manager(config_path)
    db_manager = init_database(db_path)
    translation_service = TranslationService(config_manager.get_translation_config())
    request_manager = RequestManager(config_manager.get_proxy_config())
    return FDADrugCollector(db_manager, config_manager, translation_service, request_manager)


def main():
    print("=" * 100)
    print("强化采集缺失的关键抗肿瘤药物")
    print(f"待采集: {len(CRITICAL_MISSING_DRUGS)} 类药物")
    print("=" * 100)

    collector = create_collector()
    url = 'https://api.fda.gov/drug/drugsfda.json'

    total_added = 0
    drugs_found = 0

    # 逐个药物采集，确保覆盖面
    for generic_name, name_list in CRITICAL_MISSING_DRUGS.items():
        print(f"\n{'=' * 100}")
        print(f"搜索药物: {generic_name}")
        print(f"可能名称: {', '.join(name_list)}")
        print('=' * 100)

        found_for_drug = False

        # 尝试每个可能的名称
        for search_term in name_list:
            try:
                params = {
                    'search': search_term,
                    'skip': 0,
                    'limit': 100
                }

                print(f"  搜索: {search_term}")
                response = requests.get(url, params=params, timeout=60)

                if response.status_code != 200:
                    print(f"  API错误: {response.status_code}")
                    continue

                data = response.json()
                results = data.get('results', [])

                if not results:
                    print(f"  无数据")
                    continue

                print(f"  获得 {len(results)} 条FDA记录")

                # 解析并保存数据
                drug_entries = collector.parse_drug_data(data)
                print(f"  识别出 {len(drug_entries)} 条抗肿瘤药物")

                for drug in drug_entries:
                    try:
                        drug = collector.translate_drug_data(drug)
                        split_drugs = collector.split_by_indication(drug)
                        for split_drug in split_drugs:
                            if collector.save_to_database(split_drug):
                                total_added += 1
                                found_for_drug = True
                    except Exception as e:
                        logger.warning(f"处理失败: {e}")

                if found_for_drug:
                    drugs_found += 1
                    break

            except Exception as e:
                logger.error(f"搜索 {search_term} 失败: {e}")
                continue

            time.sleep(0.3)

        if not found_for_drug:
            print(f"⚠️ {generic_name} 未找到任何数据")

    print(f"\n{'=' * 100}")
    print(f"强化采集完成！")
    print(f"新增记录: {total_added}")
    print(f"新增药物类型: {drugs_found}")
    print("=" * 100)


if __name__ == "__main__":
    main()
