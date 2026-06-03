#!/usr/bin/env python3
"""
最终验证数据库状态
"""
import sqlite3
import os

db_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'data', 'medical_info.db')
conn = sqlite3.connect(db_path)
conn.row_factory = sqlite3.Row
cur = conn.cursor()

print("=" * 100)
print("最终数据库验证结果")
print("=" * 100)

# 1. 基本统计
cur.execute("SELECT COUNT(*) FROM approved_drugs WHERE regulatory_agency = 'FDA'")
total_fda = cur.fetchone()[0]

cur.execute("SELECT COUNT(DISTINCT drug_name_en) FROM approved_drugs WHERE regulatory_agency = 'FDA'")
distinct_drugs = cur.fetchone()[0]

print(f"\nFDA总记录数: {total_fda}")
print(f"FDA不同药物数: {distinct_drugs}")


# 2. 检查是否还有未翻译的药物
print("\n2. 检查未翻译药物:")
print("-" * 100)

cur.execute("""
    SELECT DISTINCT drug_name_en, drug_name_cn
    FROM approved_drugs
    WHERE regulatory_agency = 'FDA'
      AND (drug_name_cn IS NULL OR drug_name_cn = '' OR drug_name_cn = drug_name_en)
    ORDER BY drug_name_en
""")

remaining_untranslated = cur.fetchall()

print(f"\n仍未翻译药物数: {len(remaining_untranslated)}")

if len(remaining_untranslated) > 0:
    print("\n仍未翻译药物:")
    for i, drug in enumerate(remaining_untranslated[:20]):
        print(f"  - {drug[0]} / {drug[1] or 'N/A'}")


# 3. 检查是否还有重复记录
print("\n\n3. 检查重复记录:")
print("-" * 100)

cur.execute("""
    SELECT drug_name_en, COUNT(*) AS count
    FROM (
        SELECT drug_name_en, generic_name_en, drug_name_cn, indication
        FROM approved_drugs
        WHERE regulatory_agency = 'FDA'
        GROUP BY drug_name_en, generic_name_en, drug_name_cn, indication
        HAVING COUNT(*) > 1
    )
    GROUP BY drug_name_en
""")

remaining_duplicates = cur.fetchall()

print(f"\n剩余重复组数: {len(remaining_duplicates)}")


# 4. 验证主要药物翻译和状态
print("\n\n4. 主要药物验证:")
print("-" * 100)

important_drugs = [
    'ERDAFITINIB', 'EVEROLIMUS', 'DASATINIB',
    'SUNITINIB', 'PAZOPANIB',
    'AXITINIB', 'LENVATINIB', 'CABOZANTINIB'
]

print("\n重要药物翻译检查:")
for name in important_drugs:
    cur.execute("""
        SELECT drug_name_en, drug_name_cn
        FROM approved_drugs
        WHERE regulatory_agency = 'FDA'
          AND (drug_name_en LIKE ? OR generic_name_en LIKE ?)
        LIMIT 1
    """, (f'%{name}%', f'%{name}%'))
    result = cur.fetchone()
    if result:
        print(f"  ✓ {result[0]} / {result[1] or 'N/A'}")
    else:
        print(f"  ✗ {name} - 未找到")


print("\n\n" + "=" * 100)
print("验证完成!")
print("=" * 100)

conn.close()
