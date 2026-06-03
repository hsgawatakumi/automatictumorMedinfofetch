#!/usr/bin/env python3
"""
最终全面验证数据库中的ERDAFITINIB和其他药物
"""
import sqlite3
import os

db_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'data', 'medical_info.db')
conn = sqlite3.connect(db_path)
conn.row_factory = sqlite3.Row
cur = conn.cursor()

print("=" * 100)
print("最终验证ERDAFITINIB全面检查")
print("=" * 100)

cur.execute("""
    SELECT *
    FROM approved_drugs
    WHERE regulatory_agency = 'FDA'
      AND (
          drug_name_en LIKE '%ERDAFITINIB%' OR
          generic_name_en LIKE '%ERDAFITINIB%' OR
          drug_name_en LIKE '%BALVERSA%'
      )
    ORDER BY id
""")

drugs = cur.fetchall()

print(f"\n找到 {len(drugs)} 条相关记录")

for i, rec in enumerate(drugs):
    print(f"\n  {i+1}. ID {rec['id']}")
    print("-" * 80)
    print(f"     英文名: {rec['drug_name_en']}")
    print(f"     通用名: {rec['generic_name_en'] or 'N/A'}")
    print(f"     中文名: {rec['drug_name_cn'] or 'N/A'}")
    print(f"     批准日期: {rec['approval_date'] or 'N/A'}")
    print(f"     适应症: {(rec['indication'] or 'N/A')[:200]}...")
    print(f"     伴随诊断: {rec['companion_diagnosis'] or 'N/A'}")
    print(f"     靶点: {rec['cd_target'] or 'N/A'}")
    print(f"     作用机制: {(rec['mechanism_of_action'] or 'N/A')[:200]}...")

print("\n\n" + "=" * 100)
print("✅ 验证完成!")
print("=" * 100)
conn.close()
