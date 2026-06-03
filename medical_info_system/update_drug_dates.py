#!/usr/bin/env python3
"""更新数据库中药物的批准日期，特别是重要药物的不同适应症日期"""

import os
import sys

# 添加项目路径
current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, current_dir)

from src.database import init_database
from src.utils.config_manager import create_config_manager


# 已知药物的准确适应症-日期对应关系
KNOWN_DRUG_DATES = {
    'osimertinib': [
        {
            'date': '20151113',
            'indication_keywords': ['T790M'],
            'priority': 1,
            'description': 'EGFR T790M mutation-positive NSCLC, post-TKI progression'
        },
        {
            'date': '20180418',
            'indication_keywords': ['first-line', '1L'],
            'priority': 2,
            'description': 'First-line EGFR exon 19/exon 21+ NSCLC'
        },
        {
            'date': '20201218',
            'indication_keywords': ['adjuvant', 'resection', 'surgery'],
            'priority': 3,
            'description': 'Adjuvant treatment post-resection'
        },
        {
            'date': '20240523',
            'indication_keywords': ['exon 20', 'insertion'],
            'priority': 4,
            'description': 'EGFR exon 20 insertion+ NSCLC'
        },
    ],
    # 可以添加更多药物
    'pembrolizumab': [
        {'date': '20140904', 'indication_keywords': ['melanoma'], 'description': 'Melanoma'},
        {'date': '20161024', 'indication_keywords': ['first-line', 'nsclc', 'combination'], 'description': 'First-line NSCLC combination'},
    ],
}


def update_drug_dates():
    print("=" * 80)
    print("更新药物批准日期")
    print("=" * 80)
    
    # 初始化
    config_path = os.path.join(
        os.path.dirname(os.path.abspath(__file__)),
        'config',
        'config.yaml'
    )
    config_manager = create_config_manager(config_path)
    db_path = os.path.join(
        os.path.dirname(os.path.abspath(__file__)),
        'data',
        'medical_info.db'
    )
    db_manager = init_database(db_path)
    
    updated_count = 0
    
    # 遍历每个已知药物
    for drug_key, date_entries in KNOWN_DRUG_DATES.items():
        print(f"\n处理药物: {drug_key}")
        print("-" * 80)
        
        # 查询该药物的所有记录
        drugs = db_manager.execute_query(
            """
            SELECT * FROM approved_drugs 
            WHERE LOWER(generic_name_en) LIKE ? 
               OR LOWER(drug_name_en) LIKE ?
            ORDER BY id
            """,
            (f'%{drug_key}%', f'%{drug_key}%')
        )
        
        if not drugs:
            print(f"  未找到 {drug_key} 的记录")
            continue
        
        print(f"  找到 {len(drugs)} 条记录")
        
        # 为每条记录匹配最合适的日期
        for drug in drugs:
            drug_id = drug['id']
            indication = drug.get('indication', '').lower()
            current_date = drug.get('approval_date')
            new_date = None
            matched_desc = ''
            best_match_priority = 999  # 数值越小优先级越高
            
            # 尝试匹配关键字（按优先级）
            for entry in date_entries:
                entry_date = entry['date']
                keywords = entry['indication_keywords']
                entry_priority = entry.get('priority', 999)
                
                # 检查是否有任何关键字匹配
                matched = False
                for kw in keywords:
                    if kw.lower() in indication:
                        matched = True
                        break
                
                if matched and entry_priority < best_match_priority:
                    # 找到更高优先级的匹配
                    new_date = entry_date
                    matched_desc = entry['description']
                    best_match_priority = entry_priority
            
            # 如果没有匹配，保持日期不变
            if not new_date:
                print(f"  ID {drug_id}: 保持原有日期 {current_date} (未匹配到特定适应症)")
                continue
            
            if new_date != current_date:
                # 更新日期
                db_manager.execute_update(
                    'approved_drugs',
                    {'approval_date': new_date},
                    "id = ?",
                    (drug_id,)
                )
                updated_count += 1
                print(f"  ID {drug_id}: 更新日期 {current_date} -> {new_date} ({matched_desc})")
            else:
                print(f"  ID {drug_id}: 日期已是 {new_date}，无需更新 ({matched_desc})")
    
    print("\n" + "=" * 80)
    print(f"更新完成！共更新 {updated_count} 条记录")
    print("=" * 80)
    
    # 验证结果
    print("\n" + "=" * 80)
    print("验证更新结果")
    print("=" * 80)
    
    # 重新查询奥希替尼
    osimertinib_drugs = db_manager.execute_query(
        """
        SELECT * FROM approved_drugs 
        WHERE LOWER(generic_name_en) LIKE '%osimertinib%' 
           OR LOWER(drug_name_en) LIKE '%tagrisso%'
        ORDER BY approval_date
        """
    )
    
    if osimertinib_drugs:
        print(f"\n奥希替尼记录 ({len(osimertinib_drugs)} 条):")
        for drug in osimertinib_drugs:
            print(f"\n  ID: {drug['id']}")
            print(f"  日期: {drug['approval_date']}")
            print(f"  适应症: {drug['indication'][:100]}...")


if __name__ == "__main__":
    update_drug_dates()
