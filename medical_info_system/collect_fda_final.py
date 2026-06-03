#!/usr/bin/env python3
"""
系统性FDA抗肿瘤药物采集脚本 - 最终版
从1990年至今全面采集FDA批准的抗肿瘤靶向药物和免疫药物
"""

import os
import sys
import time
import logging
import requests
from datetime import datetime
from typing import Dict, List, Optional

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


def create_systematic_fda_collector():
    """创建系统性FDA采集器实例"""
    config_path = os.path.join(current_dir, 'config', 'config.yaml')
    db_path = os.path.join(current_dir, 'data', 'medical_info.db')

    config_manager = create_config_manager(config_path)
    db_manager = init_database(db_path)
    translation_service = TranslationService(config_manager.get_translation_config())
    request_manager = RequestManager(config_manager.get_proxy_config())

    return FDADrugCollector(
        db_manager, config_manager, translation_service, request_manager
    )


def test_api():
    """测试API"""
    url = 'https://api.fda.gov/drug/drugsfda.json'
    params = {'search': 'pd-1', 'limit': 1}
    r = requests.get(url, params=params, timeout=30)
    print(f"API测试: {r.status_code}, 总数: {r.json().get('meta', {}).get('results', {}).get('total', 0) if r.status_code == 200 else 'N/A'}")
    return r.status_code == 200


def collect_fda_anticancer_drugs():
    """
    全面系统性采集FDA批准的抗肿瘤药物

    FDA drugsfda API限制：
    - 某些通用关键词（如 nsclc, melanoma, lymphoma 等）无法搜索
    - 工作关键词：pd-1, pd-l1, ctla-4, lag-3, kinase inhibitor, monoclonal antibody,
      breast cancer, colorectal cancer, prostate cancer, cancer, imatinib等
    """

    print("=" * 100)
    print("开始系统性FDA抗肿瘤药物采集")
    print("=" * 100)

    start_time = datetime.now()

    if not test_api():
        print("API测试失败，退出")
        return None

    collector = create_systematic_fda_collector()

    total_collected = 0
    total_added = 0
    total_duplicates = 0

    # FDA drugsfda API可工作的搜索关键词
    # 分成不同类别确保召回率
    search_periods = [
        {
            'name': '2020-2025',
            'start_date': '20200101',
            'end_date': '20251231',
            # 工作关键词按类别
            'keywords': [
                # 免疫检查点 - 高召回
                'pd-1', 'pd-l1', 'ctla-4', 'lag-3',
                # 靶点/机制
                'kinase inhibitor', 'monoclonal antibody',
                # 具体药物名称
                'imatinib', 'pembrolizumab', 'nivolumab', 'atezolizumab',
                'durvalumab', 'cemiplimab', 'ipilimumab', 'tremelimumab',
                # 癌症类型（能工作的）
                'breast cancer', 'colorectal cancer', 'prostate cancer', 'cancer'
            ]
        },
        {
            'name': '2010-2020',
            'start_date': '20100101',
            'end_date': '20191231',
            'keywords': [
                'pd-1', 'pd-l1', 'ctla-4', 'lag-3',
                'kinase inhibitor', 'monoclonal antibody',
                'imatinib', 'pembrolizumab', 'nivolumab', 'atezolizumab',
                'trastuzumab', 'rituximab', 'bevacizumab', 'cetuximab',
                'erlotinib', 'gefitinib', 'osimertinib', 'crizotinib',
                'breast cancer', 'colorectal cancer', 'prostate cancer', 'cancer'
            ]
        },
        {
            'name': '2000-2010',
            'start_date': '20000101',
            'end_date': '20091231',
            'keywords': [
                'kinase inhibitor', 'monoclonal antibody',
                'imatinib', 'trastuzumab', 'rituximab', 'bevacizumab', 'cetuximab',
                'erlotinib', 'gefitinib', 'sorafenib', 'sunitinib',
                'breast cancer', 'colorectal cancer', 'prostate cancer', 'cancer'
            ]
        },
        {
            'name': '1990-2000',
            'start_date': '19900101',
            'end_date': '19991231',
            'keywords': [
                'monoclonal antibody', 'rituximab', 'trastuzumab',
                'interferon', 'interleukin',
                'breast cancer', 'colorectal cancer', 'prostate cancer', 'cancer'
            ]
        },
    ]

    # 重要靶向药物名称列表（不分年代，用于补充采集）
    important_drugs = [
        # BCR-ABL
        'imatinib', 'dasatinib', 'nilotinib', 'bosutinib', 'ponatinib',
        # EGFR
        'erlotinib', 'gefitinib', 'afatinib', 'osimertinib', 'neratinib',
        # ALK
        'crizotinib', 'ceritinib', 'alectinib', 'brigatinib', 'lorlatinib',
        # BRAF/MEK
        'vemurafenib', 'dabrafenib', 'encorafenib',
        'trametinib', 'cobimetinib', 'binimetinib',
        # PD-1/PD-L1
        'pembrolizumab', 'nivolumab', 'atezolizumab', 'durvalumab', 'cemiplimab', 'avelumab',
        'ipilimumab', 'tremelimumab',
        # CD20/CD30/CD38
        'rituximab', 'obinutuzumab', 'ofatumumab', 'obinutuzumab',
        'brentuximab vedotin',
        # HER2
        'trastuzumab', 'pertuzumab', 'ado-trastuzumab emtansine', 'trastuzumab deruxtecan',
        # VEGF
        'bevacizumab', 'ramucirumab', 'ziv-aflibercept',
        # EGFR (other)
        'cetuximab', 'panitumumab', 'necitumumab',
        # PARP
        'olaparib', 'niraparib', 'rucaparib', 'talazoparib',
        # BTK
        'ibrutinib', 'acalabrutinib', 'zanubrutinib',
        # PI3K
        'idelalisib', 'duvelisib', 'copanlisib',
        # CDK4/6
        'palbociclib', 'ribociclib', 'abemaciclib',
        # Multi-target TKIs
        'sunitinib', 'sorafenib', 'pazopanib', 'axitinib', 'lenvatinib', 'cabozantinib',
        # mTOR
        'everolimus', 'temsirolimus',
        # Other
        'regorafenib', 'ruxolitinib',
        'midostaurin', 'gilteritinib',
        'venetoclax', 'enasidenib', 'ivosidenib',
        'larotrectinib', 'entrectinib',
        'selpercatinib', 'pralsetinib',
        'capmatinib', 'tepotinib',
        'erdafitinib', 'pemigatinib', 'infigratinib', 'futibatinib',
        # ADC
        'brentuximab vedotin', 'polatuzumab vedotin', 'enfortumab vedotin',
        'trastuzumab deruxtecan', 'sacituzumab govitecan',
        # 双特异性抗体
        'blinatumomab', 'tagraxofusp'
    ]

    # 分时期采集
    for period in search_periods:
        print(f"\n{'=' * 80}")
        print(f"采集时期: {period['name']}")
        print(f"日期范围: {period['start_date']} - {period['end_date']}")
        print("=" * 80)

        period_collected = 0
        skip = 0
        batch_size = 100
        max_records = 500

        while period_collected < max_records:
            try:
                # 构建查询 - 使用OR连接关键词，AND添加日期范围
                keywords_query = ' OR '.join(period['keywords'])
                date_query = f'submissions.submission_status_date:[{period["start_date"]} TO {period["end_date"]}]'
                full_query = f'{keywords_query} AND {date_query}'

                params = {
                    'search': full_query,
                    'skip': skip,
                    'limit': batch_size
                }

                print(f"  批次: skip={skip}, limit={batch_size}")

                response = requests.get(
                    'https://api.fda.gov/drug/drugsfda.json',
                    params=params,
                    timeout=60
                )

                if response.status_code != 200:
                    print(f"  API错误: {response.status_code} - {response.text[:100]}")
                    break

                data = response.json()
                results = data.get('results', [])

                if not results:
                    print(f"  该批次无更多数据")
                    break

                # 解析数据
                batch_drugs = collector.parse_drug_data(data)

                if not batch_drugs:
                    print(f"  该批次无有效抗肿瘤药物")
                    skip += batch_size
                    period_collected += batch_size
                    time.sleep(0.3)
                    continue

                # 处理每条药物
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
                    except Exception as e:
                        logger.warning(f"处理药物失败: {e}")

                print(f"  本批次处理: {len(batch_drugs)} 条药物记录")
                period_collected += len(batch_drugs)

                time.sleep(0.3)
                skip += batch_size

            except Exception as e:
                logger.error(f"采集批次失败: {e}")
                print(f"  错误: {e}")
                break

    # 补充采集：使用重要药物名称
    print(f"\n{'=' * 80}")
    print("补充采集: 重要靶向药物名称直接搜索")
    print("=" * 80)

    # 分批处理药物名称
    batch_size = 20
    for i in range(0, len(important_drugs), batch_size):
        batch = important_drugs[i:i+batch_size]
        query = ' OR '.join(batch)

        try:
            params = {
                'search': query,
                'skip': 0,
                'limit': 100
            }

            print(f"  药物批次 {i//batch_size + 1}: {len(batch)} 个")

            response = requests.get(
                'https://api.fda.gov/drug/drugsfda.json',
                params=params,
                timeout=60
            )

            if response.status_code == 200:
                data = response.json()
                if 'results' in data and data['results']:
                    batch_drugs = collector.parse_drug_data(data)
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
                        except Exception as e:
                            logger.warning(f"处理药物失败: {e}")

                    print(f"    处理: {len(batch_drugs)} 条")

            time.sleep(0.3)

        except Exception as e:
            logger.error(f"补充采集失败: {e}")

    end_time = datetime.now()
    duration = (end_time - start_time).total_seconds()

    print(f"\n{'=' * 100}")
    print("采集完成！")
    print(f"总耗时: {duration:.1f} 秒 ({duration/60:.1f} 分钟)")
    print(f"总采集记录: {total_collected}")
    print(f"新增记录: {total_added}")
    print(f"重复记录: {total_duplicates}")
    print("=" * 100)

    # 验证结果
    db_path = os.path.join(current_dir, 'data', 'medical_info.db')
    db_manager = init_database(db_path)

    fda_drugs = db_manager.execute_query(
        "SELECT COUNT(*) as count FROM approved_drugs WHERE regulatory_agency = 'FDA'"
    )
    fda_count = fda_drugs[0]['count'] if fda_drugs else 0

    distinct_drugs = db_manager.execute_query(
        "SELECT COUNT(DISTINCT drug_name_en) FROM approved_drugs WHERE regulatory_agency = 'FDA'"
    )
    distinct_count = distinct_drugs[0]['COUNT(DISTINCT drug_name_en)'] if distinct_drugs else 0

    print(f"\n数据库中FDA药物记录总数: {fda_count}")
    print(f"数据库中FDA不同药物数: {distinct_count}")

    # 日期分布
    date_dist = db_manager.execute_query(
        """
        SELECT substr(approval_date, 1, 4) as year, COUNT(*) as count
        FROM approved_drugs
        WHERE regulatory_agency = 'FDA' AND approval_date IS NOT NULL
        GROUP BY substr(approval_date, 1, 4)
        ORDER BY year DESC
        """
    )

    print(f"\nFDA药物年份分布:")
    for row in date_dist:
        print(f"  {row['year']}年: {row['count']} 条")

    return {
        'total_collected': total_collected,
        'total_added': total_added,
        'total_duplicates': total_duplicates,
        'duration': duration,
        'fda_count': fda_count,
        'distinct_drugs': distinct_count
    }


if __name__ == "__main__":
    try:
        result = collect_fda_anticancer_drugs()
        if result:
            print("\n系统性采集成功完成！")
        else:
            print("\n系统性采集失败！")
    except Exception as e:
        logger.error(f"采集失败: {e}")
        import traceback
        traceback.print_exc()
