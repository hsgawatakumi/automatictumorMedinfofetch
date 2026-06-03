#!/usr/bin/env python3
"""
检查ERDAFITINIB的当前状态
"""
import sqlite3
import os

db_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'data', 'medical_info.db')
conn = sqlite3.connect(db_path)
conn.row_factory = sqlite3.Row
cur = conn.cursor()

print("=" * 100)
print("检查ERDAFITINIB的数据库信息")
print("=" * 100)

# 查询所有与ERDAFITINIB相关的记录
cur.execute("""
    SELECT *
    FROM approved_drugs
    WHERE regulatory_agency = 'FDA'
      AND (
          drug_name_en LIKE '%ERDAFITINIB%' OR
          drug_name_en LIKE '%BALVERSA%' OR
          generic_name_en LIKE '%ERDAFITINIB%'
      )
    ORDER BY id
""")

drugs = cur.fetchall()

print(f"\n找到 {len(drugs)} 条ERDAFITINIB相关记录\n")

if len(drugs) > 0:
    for i, drug in enumerate(drugs):
        print(f"  {i+1}. ID: {drug[0]}")
        print(f"     英文名: {drug[1]}")
        print(f"     通用名: {drug[2] or 'N/A'}")
        print(f"     中文名: {drug[3] or 'N/A'}")
        print(f"     批准日期: {drug[4] or 'N/A'}")
        print(f"     适应症: {(drug[10] or 'N/A')[:100]}...")
        print()
else:
    print("  ❌ 没有找到任何ERDAFITINIB相关记录")

conn.close()
