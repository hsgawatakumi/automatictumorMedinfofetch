#!/usr/bin/env python3
"""
最终验证FDA药物数据完整性
"""
import sqlite3
import os

db_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'data', 'medical_info.db')
conn = sqlite3.connect(db_path)
conn.row_factory = sqlite3.Row
cur = conn.cursor()

print("=" * 100)
print("最终验证FDA药物数据完整性")
print("=" * 100)

# 1. 基本统计
cur.execute("SELECT COUNT(*) FROM approved_drugs WHERE regulatory_agency = 'FDA'")
total_fda = cur.fetchone()[0]
print(f"\nFDA药物总记录数: {total_fda}")

# 检查缺失
cur.execute("SELECT COUNT(*) FROM approved_drugs WHERE regulatory_agency = 'FDA' AND (drug_name_cn IS NULL OR drug_name_cn = '')")
missing_cn = cur.fetchone()[0]
cur.execute("SELECT COUNT(*) FROM approved_drugs WHERE regulatory_agency = 'FDA' AND (approval_date IS NULL OR approval_date = '')")
missing_date = cur.fetchone()[0]

print(f"\n缺失情况:")
print(f"  中文名称缺失: {missing_cn} ({100*missing_cn/total_fda:.1f}%)")
print(f"  批准日期缺失: {missing_date} ({100*missing_date/total_fda:.1f}%)")

# 2. 显示一些最近更新的药物
print("\n" + "=" * 100)
print("最近更新的药物 (前30条):")
print("=" * 100)

cur.execute("""
    SELECT 
        id,
        drug_name_en,
        drug_name_cn,
        approval_date,
        substr(indication, 1, 50) AS indication_preview
    FROM approved_drugs
    WHERE regulatory_agency = 'FDA'
    ORDER BY id DESC
    LIMIT 30
""")

drugs = cur.fetchall()

for drug in drugs:
    id = drug[0]
    name_en = drug[1]
    name_cn = drug[2] or '-'
    date = drug[3] or '-'
    indication = drug[4] or '-'
    
    print(f"  ID {id}")
    print(f"    英文名: {name_en}")
    print(f"    中文名: {name_cn}")
    print(f"    批准日期: {date}")
    print(f"    适应症: {indication}...")
    print()

# 3. 显示有代表性的药物列表
print("\n" + "=" * 100)
print("代表性药物列表 (包含主要类别):")
print("=" * 100)

drug_categories = [
    ("PD-1/PD-L1", ['KEYTRUDA', 'OPDIVO', 'TECENTRIQ', 'IMFINZI', 'LIBTAYO']),
    ("BTK抑制剂", ['IMBRUVICA', 'CALQUENCE', 'BRUKINSA']),
    ("CDK4/6抑制剂", ['IBRANCE', 'KISQALI', 'VERZENIO']),
    ("PARP抑制剂", ['LYNPARZA', 'ZEJULA', 'RUBRACA', 'TALZENNA']),
    ("EGFR/ALK/ROS1", ['TAGRISSO', 'XALKORI', 'ALECENSA', 'LORBRENA']),
]

for category, names in drug_categories:
    print(f"\n{category}:")
    for name in names:
        cur.execute("""
            SELECT drug_name_en, drug_name_cn, approval_date, COUNT(*) AS count
            FROM approved_drugs
            WHERE regulatory_agency = 'FDA'
              AND (drug_name_en LIKE ? OR generic_name_en LIKE ?)
        """, (f'%{name}%', f'%{name}%'))
        
        result = cur.fetchone()
        if result and result[0]:
            print(f"  {result[0]} / {result[1] or 'N/A'} ({result[2] or 'N/A'}) - {result[3]}条")
        else:
            print(f"  {name}: ❌ 未找到")

print("\n" + "=" * 100)
print("验证完成!")
print("=" * 100)

conn.close()
