#!/usr/bin/env python3
"""
最后验证所有主要药物状态
"""
import sqlite3
import os

db_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'data', 'medical_info.db')
conn = sqlite3.connect(db_path)
conn.row_factory = sqlite3.Row
cur = conn.cursor()

print("=" * 100)
print("数据库最终完整性验证")
print("=" * 100)

# 主要抗肿瘤药物列表
important_drugs = [
    ('ERDAFITINIB', '厄达替尼'),
    ('EVEROLIMUS', '依维莫司'),
    ('DASATINIB', '达沙替尼'),
    ('SUNITINIB', '舒尼替尼'),
    ('PAZOPANIB', '帕唑帕尼'),
    ('AXITINIB', '阿昔替尼'),
    ('LENVATINIB', '仑伐替尼'),
    ('CABOZANTINIB', '卡博替尼'),
    ('PEMBROLIZUMAB', '帕博利珠单抗'),
    ('NIVOLUMAB', '纳武利尤单抗'),
    ('OSIMERTINIB', '奥希替尼'),
]

print("\n主要抗肿瘤药物状态验证:")
print("-" * 100)

all_ok = True
for name, expected_cn in important_drugs:
    cur.execute("""
        SELECT drug_name_en, drug_name_cn, approval_date
        FROM approved_drugs
        WHERE regulatory_agency = 'FDA'
          AND (
              drug_name_en LIKE ? OR
              generic_name_en LIKE ?
          )
        ORDER BY id DESC
        LIMIT 1
    """, (f'%{name}%', f'%{name}%'))
    result = cur.fetchone()
    
    if result:
        status = "✓" if (result[1] and result[1] != result[0]) else "⚠️"
        cn_name = result[1] if result[1] else "N/A"
        app_date = result[2] if result[2] else "N/A"
        
        print(f"  {status} {result[0]} / {cn_name} / {app_date}")
        
        if not result[1] or result[1] == result[0]:
            all_ok = False
    else:
        print(f"  ✗ {name} - 未找到")
        all_ok = False

# 基本统计
print("\n\n基本统计:")
print("-" * 100)
cur.execute("SELECT COUNT(*) FROM approved_drugs WHERE regulatory_agency = 'FDA'")
total_records = cur.fetchone()[0]

cur.execute("SELECT COUNT(DISTINCT drug_name_en) FROM approved_drugs WHERE regulatory_agency = 'FDA'")
distinct_drugs = cur.fetchone()[0]

cur.execute("""
    SELECT COUNT(*) FROM approved_drugs
    WHERE regulatory_agency = 'FDA'
      AND (
          drug_name_cn IS NULL OR drug_name_cn = '' OR drug_name_cn = drug_name_en
      )
""")
missing_cn = cur.fetchone()[0]

print(f"  FDA总记录数: {total_records}")
print(f"  不同药物数: {distinct_drugs}")
print(f"  中文名称缺失: {missing_cn}")

if all_ok and missing_cn == 0:
    print("\n✅ 数据库完整性完美!")
else:
    print("\n⚠️ 仍有一些需要完善的地方")

conn.close()
