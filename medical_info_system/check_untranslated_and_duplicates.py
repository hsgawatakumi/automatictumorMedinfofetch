#!/usr/bin/env python3
"""
检查未翻译药物和重复行情况
"""
import sqlite3
import os

db_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'data', 'medical_info.db')
conn = sqlite3.connect(db_path)
conn.row_factory = sqlite3.Row
cur = conn.cursor()

print("=" * 100)
print("检查未翻译药物和重复行")
print("=" * 100)

# 1. 查找未正确翻译的药物（中文名称等于英文名称）
print("\n1. 检查未正确翻译的药物:")
print("-" * 100)

cur.execute("""
    SELECT DISTINCT drug_name_en, drug_name_cn
    FROM approved_drugs
    WHERE regulatory_agency = 'FDA'
      AND drug_name_en IS NOT NULL
      AND drug_name_en != ''
    ORDER BY drug_name_en
""")

drugs = cur.fetchall()

untranslated = []
for drug in drugs:
    name_en = drug[0]
    name_cn = drug[1] or ''
    
    if name_cn.upper() == name_en.upper() or name_cn == '' or name_cn is None:
        untranslated.append(drug)

print(f"  可能未翻译药物数: {len(untranslated)}")
print(f"\n  未翻译药物列表 (前30条):")
for i, drug in enumerate(untranslated[:30]):
    print(f"    - {drug[0]} / {drug[1] or 'N/A'}")


# 2. 查找重复记录
print("\n\n2. 检查重复记录:")
print("-" * 100)

# 查找可能的重复（基于药物名和适应症的重复
cur.execute("""
    SELECT drug_name_en, generic_name_en, drug_name_cn, indication, COUNT(*) as count
    FROM approved_drugs
    WHERE regulatory_agency = 'FDA'
    GROUP BY drug_name_en, generic_name_en, drug_name_cn, indication
    HAVING COUNT(*) > 1
    ORDER BY count DESC
    LIMIT 30
""")

duplicates = cur.fetchall()
print(f"\n找到 {len(duplicates)} 组重复记录")
print("\n  重复最严重的前30组:")
for dup in duplicates:
    name_en = dup[0] or ''
    gen_en = dup[1] or ''
    name_cn = dup[2] or ''
    ind = dup[3] or ''
    count = dup[4]
    print(f"    {name_en} / {gen_en} - 适应症: {ind[:60]}... - 重复: {count}次")


# 3. 查看数据库基本统计
print("\n\n3. 数据库基本统计:")
print("-" * 100)
cur.execute("SELECT COUNT(*) FROM approved_drugs WHERE regulatory_agency = 'FDA'")
count_fda = cur.fetchone()[0]

cur.execute("SELECT COUNT(DISTINCT drug_name_en) FROM approved_drugs WHERE regulatory_agency = 'FDA'")
count_drugs = cur.fetchone()[0]

print(f"FDA总记录数: {count_fda}")
print(f"FDA不同药物数: {count_drugs}")

conn.close()
