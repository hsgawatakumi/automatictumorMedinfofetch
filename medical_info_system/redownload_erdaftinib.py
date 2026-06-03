#!/usr/bin/env python3
"""
重新采集ERDAFITINIB的正确信息
"""
import os
import sys
import requests

current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, current_dir)

from src.database import init_database
from src.utils.config_manager import create_config_manager
from src.utils.translator import TranslationService
from src.utils.http_client import RequestManager
from src.collectors.fda_collector import FDADrugCollector

db_path = os.path.join(current_dir, 'data', 'medical_info.db')


def redownload_erdaftinib():
    print("=" * 100)
    print("重新采集ERDAFITINIB的正确信息")
    print("=" * 100)
    
    # 创建采集器
    config = create_config_manager(os.path.join(current_dir, 'config', 'config.yaml'))
    db = init_database(db_path)
    translator = TranslationService(config.get_translation_config())
    http_mgr = RequestManager(config.get_proxy_config())
    collector = FDADrugCollector(db, config, translator, http_mgr)
    
    # 首先删除混乱的记录
    print("\n\n1. 删除混乱的记录...")
    db.execute_query("""
        DELETE FROM approved_drugs
        WHERE regulatory_agency = 'FDA'
          AND (
              id = 731 OR id = 890 OR
              drug_name_en LIKE '%ERDAFITINIB%' OR
              generic_name_en LIKE '%ERDAFITINIB%'
          )
    """)
    print(f"   已删除相关混乱记录")
    
    # 现在重新采集
    print("\n\n2. 重新采集ERDAFITINIB信息...")
    url = "https://api.fda.gov/drug/drugsfda.json"
    params = {
        "search": "BALVERSA OR ERDAFITINIB",
        "limit": 20
    }
    
    print(f"   请求URL: {url}")
    print(f"   搜索关键词: {params['search']}")
    
    response = requests.get(url, params=params, timeout=60)
    
    if response.status_code == 200:
        data = response.json()
        print(f"   获取到 {len(data.get('results', []))} 条结果")
        
        # 使用采集器处理数据
        drugs = collector.parse_drug_data(data)
        
        if drugs:
            print(f"   解析出 {len(drugs)} 条有效药物信息")
            
            for drug in drugs:
                try:
                    drug = collector.translate_drug_data(drug)
                    split_drugs = collector.split_by_indication(drug)
                    
                    for split_drug in split_drugs:
                        if collector.save_to_database(split_drug):
                            print(f"   ✓ 已保存: {split_drug.get('drug_name_en', 'N/A')}")
                        else:
                            print(f"   ℹ 已存在: {split_drug.get('drug_name_en', 'N/A')}")
                except Exception as e:
                    print(f"   ⚠️ 处理失败: {e}")
        else:
            print("   ❌ 没有解析出有效药物信息")
    else:
        print(f"   ❌ 请求失败: {response.status_code}")
    
    # 验证结果
    print("\n\n3. 验证采集结果...")
    results = db.execute_query("""
        SELECT *
        FROM approved_drugs
        WHERE regulatory_agency = 'FDA'
          AND (
              drug_name_en LIKE '%BALVERSA%' OR
              drug_name_en LIKE '%ERDAFITINIB%' OR
              generic_name_en LIKE '%ERDAFITINIB%'
          )
        ORDER BY id
    """)
    
    if results:
        print(f"   ✓ 成功采集到 {len(results)} 条ERDAFITINIB相关记录")
        for i, record in enumerate(results):
            print(f"     {i+1}. {record.get('drug_name_en', 'N/A')} / {record.get('drug_name_cn', 'N/A')} / {record.get('approval_date', 'N/A')}")
    else:
        print(f"   ❌ 没有找到任何ERDAFITINIB记录")


if __name__ == "__main__":
    redownload_erdaftinib()
