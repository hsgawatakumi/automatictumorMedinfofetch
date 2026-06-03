#!/usr/bin/env python3
"""检查数据库中现有的药物数据"""

import os
import sys

# 添加项目路径
current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, current_dir)

from src.database import init_database
from src.utils.config_manager import create_config_manager


def check_database():
    print("=" * 80)
    print("检查医学信息收集系统数据库")
    print("=" * 80)
    
    # 获取数据库路径
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
    
    print(f"\n数据库路径: {db_path}")
    
    # 初始化数据库
    db_manager = init_database(db_path)
    
    # 检查数据统计
    print("\n" + "=" * 80)
    print("数据统计")
    print("=" * 80)
    
    tables = [
        ('approved_drugs', '已批准药物'),
        ('nda_drugs', 'NDA申请'),
        ('cde_special_drugs', 'CDE特殊品种'),
        ('academic_papers', '学术文献'),
        ('clinical_trials', '临床试验'),
    ]
    
    for table, name in tables:
        try:
            count = db_manager.get_record_count(table)
            print(f"{name}: {count} 条记录")
        except Exception as e:
            print(f"{name}: 无法查询 - {e}")
    
    # 检查已批准药物详情
    print("\n" + "=" * 80)
    print("已批准药物详情 (前20条)")
    print("=" * 80)
    
    try:
        drugs = db_manager.execute_query(
            "SELECT * FROM approved_drugs ORDER BY approval_date DESC LIMIT 20"
        )
        
        if drugs:
            for drug in drugs:
                print(f"\nID: {drug.get('id')}")
                print(f"  监管机构: {drug.get('regulatory_agency')}")
                print(f"  商品名: {drug.get('drug_name_en')} ({drug.get('drug_name_cn')})")
                print(f"  通用名: {drug.get('generic_name_en')} ({drug.get('generic_name_cn')})")
                print(f"  批准日期: {drug.get('approval_date')}")
                print(f"  适应症: {drug.get('indication', '')[:80]}...")
        else:
            print("数据库中没有已批准药物数据")
    except Exception as e:
        print(f"查询已批准药物失败: {e}")
    
    # 专门检查奥希替尼
    print("\n" + "=" * 80)
    print("检查奥希替尼 (TAGRISSO)")
    print("=" * 80)
    
    try:
        osimertinib_drugs = db_manager.execute_query(
            """
            SELECT * FROM approved_drugs 
            WHERE generic_name_en LIKE '%osimertinib%' 
               OR drug_name_en LIKE '%tagrisso%'
            ORDER BY approval_date
            """
        )
        
        if osimertinib_drugs:
            print(f"\n找到 {len(osimertinib_drugs)} 条奥希替尼相关记录:")
            for drug in osimertinib_drugs:
                print(f"\nID: {drug.get('id')}")
                print(f"  商品名: {drug.get('drug_name_en')}")
                print(f"  通用名: {drug.get('generic_name_en')}")
                print(f"  批准日期: {drug.get('approval_date')}")
                print(f"  适应症: {drug.get('indication', '')}")
        else:
            print("数据库中没有找到奥希替尼相关数据")
    except Exception as e:
        print(f"查询奥希替尼失败: {e}")
    
    print("\n" + "=" * 80)
    print("检查完成")
    print("=" * 80)


if __name__ == "__main__":
    check_database()
