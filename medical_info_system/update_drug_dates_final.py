#!/usr/bin/env python3
"""更新数据库中药物的批准日期，基于真实FDA批准日期"""

import os
import sys

# 添加项目路径
current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, current_dir)

from src.database import init_database
from src.utils.config_manager import create_config_manager


# 真实FDA批准日期（基于FDA官方信息）
KNOWN_DRUG_DATES = {
    # 奥希替尼 TAGRISSO
    'osimertinib': [
        {
            'date': '20151113',
            'indication_keywords': ['T790M'],
            'priority': 1,
            'description': 'EGFR T790M mutation-positive NSCLC'
        },
        {
            'date': '20180418',
            'indication_keywords': ['first-line', '1L', 'exon 19', 'exon 21', 'L858R', '一线'],
            'priority': 2,
            'description': 'First-line EGFR+ metastatic NSCLC'
        },
        {
            'date': '20201218',
            'indication_keywords': ['adjuvant', 'resection', 'surgery', '术后辅助'],
            'priority': 3,
            'description': 'Adjuvant treatment post-resection'
        },
        {
            'date': '20240926',
            'indication_keywords': ['stage iii', 'iii期', 'unresectable', '不可切除', 'locally advanced', 'pacific', 'LAURA'],
            'priority': 4,
            'description': 'Stage III unresectable EGFR+ NSCLC (LAURA trial)'
        },
    ],
    
    # 阿伐替尼 AYVAKIT (Avapritinib)
    'avapritinib': [
        {
            'date': '20200110',
            'indication_keywords': ['GIST', 'gastrointestinal stromal', '胃肠道间质瘤', 'PDGFRA', 'D842V'],
            'priority': 1,
            'description': 'PDGFRA exon 18+ GIST'
        },
        {
            'date': '20210621',
            'indication_keywords': ['advanced systemic mastocytosis', 'AdvSM', 'ASM', 'SM-AHN', 'mast cell leukemia', 'MCL', '系统性肥大细胞增多症'],
            'priority': 2,
            'description': 'Advanced Systemic Mastocytosis (AdvSM)'
        },
        {
            'date': '20220611',
            'indication_keywords': ['indolent systemic mastocytosis', 'ISM', '惰性系统性肥大细胞增多症'],
            'priority': 3,
            'description': 'Indolent Systemic Mastocytosis (ISM)'
        },
    ],
    
    # 塞普提尼 RETEVMO (Selpercatinib)
    'selpercatinib': [
        {
            'date': '20200508',
            'indication_keywords': ['NSCLC', 'non-small cell lung', '非小细胞肺癌', 'RET fusion'],
            'priority': 1,
            'description': 'RET fusion+ NSCLC (First approval)'
        },
        {
            'date': '20200508',
            'indication_keywords': ['thyroid cancer', 'MTC', 'medullary thyroid', '甲状腺癌', '髓样'],
            'priority': 2,
            'description': 'RET mutation+ MTC and RET fusion+ thyroid cancer'
        },
        {
            'date': '20240529',
            'indication_keywords': ['solid tumor', '实体瘤', 'fusion-positive solid tumor'],
            'priority': 3,
            'description': 'RET fusion+ solid tumors (expanded approval)'
        },
        {
            'date': '20240927',
            'indication_keywords': ['radioactive iodine', 'RAI-refractory', '碘难治'],
            'priority': 4,
            'description': 'RET fusion+ thyroid cancer (regular approval)'
        },
    ],
}


def update_drug_dates():
    print("=" * 100)
    print("基于真实FDA批准日期更新药物数据")
    print("=" * 100)
    
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
        print("-" * 100)
        
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
    
    print("\n" + "=" * 100)
    print(f"更新完成！共更新 {updated_count} 条记录")
    print("=" * 100)
    
    # 验证结果
    print("\n" + "=" * 100)
    print("验证更新结果")
    print("=" * 100)
    
    # 重新查询所有相关药物
    for drug_key in KNOWN_DRUG_DATES.keys():
        drugs = db_manager.execute_query(
            """
            SELECT * FROM approved_drugs 
            WHERE LOWER(generic_name_en) LIKE ? 
               OR LOWER(drug_name_en) LIKE ?
            ORDER BY approval_date
            """,
            (f'%{drug_key}%', f'%{drug_key}%')
        )
        
        if drugs:
            print(f"\n{drug_key} ({len(drugs)} 条记录):")
            for drug in drugs:
                indication_preview = drug['indication'][:80] + "..." if len(drug['indication']) > 80 else drug['indication']
                print(f"  {drug['approval_date']}: {indication_preview}")


if __name__ == "__main__":
    update_drug_dates()
