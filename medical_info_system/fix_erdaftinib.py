#!/usr/bin/env python3
"""
完善ERDAFITINIB的记录
"""
import sqlite3
import os

db_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'data', 'medical_info.db')

conn = sqlite3.connect(db_path)
conn.row_factory = sqlite3.Row
cur = conn.cursor()

print("=" * 100)
print("完善ERDAFITINIB的记录")
print("=" * 100)

# 首先查看当前状态
cur.execute("""
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

records = cur.fetchall()

print(f"\n找到 {len(records)} 条记录")
print("\n当前记录:")
for i, rec in enumerate(records):
    print(f"  {i+1}. ID {rec['id']}")
    print(f"     英文名: {rec['drug_name_en']}")
    print(f"     通用名: {rec['generic_name_en']}")
    print(f"     中文名: {rec['drug_name_cn']}")
    print(f"     批准日期: {rec['approval_date']}")

# 更新记录
print("\n\n更新记录...")

# 更新ERDAFITINIB的中文名称和日期
cur.execute("""
    UPDATE approved_drugs
    SET drug_name_cn = '厄达替尼',
        approval_date = '20190412'
    WHERE regulatory_agency = 'FDA'
      AND (
          drug_name_en LIKE '%ERDAFITINIB%' OR
          generic_name_en LIKE '%ERDAFITINIB%'
      )
""")

# 更新BALVERSA的中文名称和日期
cur.execute("""
    UPDATE approved_drugs
    SET drug_name_cn = '厄达替尼',
        approval_date = '20190412',
        generic_name_en = 'ERDAFITINIB'
    WHERE regulatory_agency = 'FDA'
      AND drug_name_en LIKE '%BALVERSA%'
""")

conn.commit()

# 再次验证
print("\n\n验证更新后的记录...")
cur.execute("""
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

updated = cur.fetchall()

print(f"\n更新后有 {len(updated)} 条记录")
for i, rec in enumerate(updated):
    print(f"\n  {i+1}. ID {rec['id']}")
    print(f"     英文名: {rec['drug_name_en']}")
    print(f"     通用名: {rec['generic_name_en']}")
    print(f"     中文名: {rec['drug_name_cn']}")
    print(f"     批准日期: {rec['approval_date']}")
    print(f"     适应症: { (rec['indication'] or 'N/A')[:100] }...")

conn.close()

print("\n\n✅ ERDAFITINIB信息完善完成!")
