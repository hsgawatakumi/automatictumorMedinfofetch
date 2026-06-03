#!/usr/bin/env python3
"""
FDA抗肿瘤药物采集脚本 - 直接药物名称搜索版
通过已知的靶向药物和免疫药物名称直接搜索FDA数据库
"""

import os
import sys
import time
import logging
import requests
from datetime import datetime

# 添加项目路径
current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, current_dir)

from src.database import init_database
from src.utils.config_manager import create_config_manager
from src.utils.translator import TranslationService
from src.utils.http_client import RequestManager
from src.collectors.fda_collector import FDADrugCollector

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def create_collector():
    """创建采集器"""
    config_path = os.path.join(current_dir, 'config', 'config.yaml')
    db_path = os.path.join(current_dir, 'data', 'medical_info.db')

    config_manager = create_config_manager(config_path)
    db_manager = init_database(db_path)
    translation_service = TranslationService(config_manager.get_translation_config())
    request_manager = RequestManager(config_manager.get_proxy_config())

    return FDADrugCollector(
        db_manager, config_manager, translation_service, request_manager
    )


# 完整的抗肿瘤药物名称列表
ANTICANCER_DRUGS = [
    # 免疫检查点抑制剂 (PD-1/PD-L1/CTLA-4)
    'pembrolizumab', 'nivolumab', 'atezolizumab', 'durvalumab', 'cemiplimab', 'avelumab',
    'ipilimumab', 'tremelimumab',

    # BCR-ABL抑制剂
    'imatinib', 'dasatinib', 'nilotinib', 'bosutinib', 'ponatinib', 'bosutinib',

    # EGFR抑制剂
    'erlotinib', 'gefitinib', 'afatinib', 'osimertinib', 'neratinib', 'dacomitinib', 'mobocertinib',

    # ALK抑制剂
    'crizotinib', 'ceritinib', 'alectinib', 'brigatinib', 'lorlatinib', 'ensartinib',

    # BRAF/MEK抑制剂
    'vemurafenib', 'dabrafenib', 'encorafenib',
    'trametinib', 'cobimetinib', 'binimetinib', 'selumetinib', 'trametinib',

    # VEGF/VEGFR抑制剂
    'bevacizumab', 'ramucirumab', 'ziv-aflibercept', 'ponatinib',  # ponatinib也有VEGFR抑制

    # HER2抑制剂
    'trastuzumab', 'pertuzumab', 'ado-trastuzumab emtansine', 'trastuzumab deruxtecan', 'margetuximab',

    # EGFR (单克隆抗体)
    'cetuximab', 'panitumumab', 'necitumumab',

    # PARP抑制剂
    'olaparib', 'niraparib', 'rucaparib', 'talazoparib',

    # BTK抑制剂
    'ibrutinib', 'acalabrutinib', 'zanubrutinib',

    # PI3K抑制剂
    'idelalisib', 'duvelisib', 'copanlisib', 'alpelisib',

    # CDK4/6抑制剂
    'palbociclib', 'ribociclib', 'abemaciclib',

    # mTOR抑制剂
    'everolimus', 'temsirolimus',

    # 多靶点TKI
    'sunitinib', 'sorafenib', 'pazopanib', 'axitinib', 'lenvatinib', 'cabozantinib', 'regorafenib', 'nintedanib',

    # JAK抑制剂
    'ruxolitinib', 'fedratinib',

    # FLT3抑制剂
    'midostaurin', 'gilteritinib', 'quizartinib',

    # BCL-2抑制剂
    'venetoclax', 'navitoclax',

    # IDH抑制剂
    'enasidenib', 'ivosidenib',

    # NTRK抑制剂
    'larotrectinib', 'entrectinib',

    # RET抑制剂
    'selpercatinib', 'pralsetinib',

    # MET抑制剂
    'capmatinib', 'tepotinib', 'crizotinib',  # crizotinib也有MET抑制

    # FGFR抑制剂
    'erdafitinib', 'pemigatinib', 'infigratinib', 'futibatinib',

    # CD20单克隆抗体
    'rituximab', 'obinutuzumab', 'ofatumumab', 'rituximab',

    # CD30单克隆抗体
    'brentuximab vedotin',

    # CD38单克隆抗体
    'daratumumab', 'isatuximab',

    # 其他单克隆抗体
    'blinatumomab', 'tagraxofusp', 'mogamulizumab', 'olaratumab',

    # ADC (抗体药物偶联物)
    'brentuximab vedotin', 'polatuzumab vedotin', 'enfortumab vedotin',
    'trastuzumab deruxtecan', 'sacituzumab govitecan', 'belantamab mafodotin',
    'loncastuximab tesirine', 'moxetumomab pasudotox',

    # 免疫毒素
    'moxetumomab pasudotox',

    # 放射性药物
    'lutetium lu 177 dotatate', 'iobitux', 'radioimmunotherapy',

    # 蛋白酶体抑制剂
    'bortezomib', 'carfilzomib', 'ixazomib',

    # 组蛋白去乙酰化酶抑制剂
    'vorinostat', 'romidepsin', 'panobinostat',

    # 氨肽酶抑制剂
    'carfilzomib',

    # 抗代谢药
    'cladribine', 'fludarabine', 'pentostatin', 'methotrexate', 'pemetrexed',

    # 烷基化剂
    'cyclophosphamide', 'ifosfamide', 'temozolomide', 'dacarbazine', 'procarbazine',

    # 植物生物碱
    'vinblastine', 'vincristine', 'vinorelbine', 'etoposide', 'topotecan', 'irinotecan',

    # 抗肿瘤抗生素
    'doxorubicin', 'epirubicin', 'idarubicin', 'mitomycin', 'bleomycin',

    # 铂类
    'cisplatin', 'carboplatin', 'oxaliplatin',

    # 激素类
    'tamoxifen', 'anastrozole', 'letrozole', 'exemestane', 'fulvestrant',
    'bicalutamide', 'enzalutamide', 'apalutamide', 'abiraterone', 'degarelix',
    'leuprolide', 'goserelin', 'octreotide',

    # 分化诱导剂
    'tretinoin', 'arsenic trioxide',

    # 免疫调节剂
    'lenalidomide', 'pomalidomide', 'thalidomide',

    # 细胞凋亡诱导剂
    'obatoclax',

    # 靶向药物组合
    'pertuzumab', 'trastuzumab',  # HER2组合
]


def collect_by_drug_names():
    """通过药物名称列表采集FDA数据"""
    print("=" * 100)
    print("开始通过药物名称采集FDA抗肿瘤药物")
    print("=" * 100)

    start_time = datetime.now()

    collector = create_collector()

    # 去重
    unique_drugs = list(set(drug.lower() for drug in ANTICANCER_DRUGS))
    print(f"待采集药物数量: {len(unique_drugs)}")

    url = 'https://api.fda.gov/drug/drugsfda.json'

    total_collected = 0
    total_added = 0
    total_duplicates = 0
    drugs_found = []

    # 分批处理（每批10个药物名）
    batch_size = 10
    for i in range(0, len(unique_drugs), batch_size):
        batch = unique_drugs[i:i+batch_size]
        query = ' OR '.join(batch)

        try:
            params = {
                'search': query,
                'skip': 0,
                'limit': 100
            }

            print(f"\n批次 {i//batch_size + 1}: 搜索 {len(batch)} 个药物")

            response = requests.get(url, params=params, timeout=60)

            if response.status_code != 200:
                print(f"  API错误: {response.status_code}")
                continue

            data = response.json()
            results = data.get('results', [])

            if not results:
                print(f"  无数据")
                time.sleep(0.3)
                continue

            print(f"  获得 {len(results)} 条FDA记录")

            # 解析数据
            batch_drugs = collector.parse_drug_data(data)
            print(f"  识别出 {len(batch_drugs)} 条抗肿瘤药物")

            for drug in batch_drugs:
                try:
                    drug = collector.translate_drug_data(drug)
                    split_drugs = collector.split_by_indication(drug)

                    for split_drug in split_drugs:
                        success = collector.save_to_database(split_drug)
                        if success:
                            total_added += 1
                        else:
                            total_duplicates += 1
                        total_collected += 1

                    if drug.get('drug_name_en'):
                        drugs_found.append(drug['drug_name_en'])

                except Exception as e:
                    logger.warning(f"处理药物失败: {e}")

            time.sleep(0.3)

        except Exception as e:
            logger.error(f"批次采集失败: {e}")
            print(f"  错误: {e}")

    end_time = datetime.now()
    duration = (end_time - start_time).total_seconds()

    print(f"\n{'=' * 100}")
    print("采集完成！")
    print(f"总耗时: {duration:.1f} 秒")
    print(f"总采集记录: {total_collected}")
    print(f"新增记录: {total_added}")
    print(f"重复记录: {total_duplicates}")
    print(f"找到的药物: {len(set(drugs_found))} 种")
    print("=" * 100)

    # 验证结果
    db_path = os.path.join(current_dir, 'data', 'medical_info.db')
    db_manager = init_database(db_path)

    fda_count = db_manager.get_record_count('approved_drugs', "regulatory_agency = 'FDA'")

    distinct = db_manager.execute_query(
        "SELECT COUNT(DISTINCT drug_name_en) as cnt FROM approved_drugs WHERE regulatory_agency = 'FDA'"
    )
    distinct_count = distinct[0]['cnt'] if distinct else 0

    print(f"\n数据库中FDA药物记录总数: {fda_count}")
    print(f"数据库中FDA不同药物数: {distinct_count}")

    # 日期分布
    date_dist = db_manager.execute_query("""
        SELECT substr(approval_date, 1, 4) as year, COUNT(*) as cnt
        FROM approved_drugs
        WHERE regulatory_agency = 'FDA' AND approval_date IS NOT NULL
        GROUP BY substr(approval_date, 1, 4)
        ORDER BY year DESC
    """)

    print(f"\nFDA药物年份分布:")
    for row in date_dist:
        print(f"  {row['year']}年: {row['cnt']} 条")

    return {
        'total_collected': total_collected,
        'total_added': total_added,
        'duration': duration,
        'fda_count': fda_count,
        'distinct_count': distinct_count
    }


if __name__ == "__main__":
    try:
        result = collect_by_drug_names()
        print("\n采集完成！")
    except Exception as e:
        logger.error(f"采集失败: {e}")
        import traceback
        traceback.print_exc()
