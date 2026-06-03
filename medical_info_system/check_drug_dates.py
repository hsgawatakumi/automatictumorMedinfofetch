#!/usr/bin/env python3
"""检查特定药物的适应症日期"""
import sqlite3
import os

db_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'data', 'medical_info.db')
conn = sqlite3.connect(db_path)
conn.row_factory = sqlite3.Row
cur = conn.cursor()

# 检查泰瑞沙 (Osimertinib)
print("=" * 100)
print("泰瑞沙 (OSIMERTINIB) 适应症及日期:")
print("=" * 100)
cur.execute("""
    SELECT id, drug_name_en, indication, approval_date
    FROM approved_drugs
    WHERE regulatory_agency = 'FDA'
      AND (drug_name_en LIKE '%OSIMERTINIB%' OR generic_name_en LIKE '%OSIMERTINIB%')
    ORDER BY approval_date
""")
for row in cur.fetchall():
    ind = row['indication'][:80] + '...' if row['indication'] and len(row['indication']) > 80 else (row['indication'] or 'N/A')
    print(f"  ID: {row['id']}, Date: {row['approval_date']}")
    print(f"    Indication: {ind}")

# 检查阿伐替尼 (Avapritinib)
print("\n" + "=" * 100)
print("阿伐替尼 (AVAPRITINIB) 适应症及日期:")
print("=" * 100)
cur.execute("""
    SELECT id, drug_name_en, indication, approval_date
    FROM approved_drugs
    WHERE regulatory_agency = 'FDA'
      AND (drug_name_en LIKE '%AVAPRITINIB%' OR generic_name_en LIKE '%AVAPRITINIB%')
    ORDER BY approval_date
""")
for row in cur.fetchall():
    ind = row['indication'][:80] + '...' if row['indication'] and len(row['indication']) > 80 else (row['indication'] or 'N/A')
    print(f"  ID: {row['id']}, Date: {row['approval_date']}")
    print(f"    Indication: {ind}")

# 检查塞普提尼 (Selpercatinib)
print("\n" + "=" * 100)
print("塞普提尼 (SELPERCATINIB) 适应症及日期:")
print("=" * 100)
cur.execute("""
    SELECT id, drug_name_en, indication, approval_date
    FROM approved_drugs
    WHERE regulatory_agency = 'FDA'
      AND (drug_name_en LIKE '%SELPERCATINIB%' OR generic_name_en LIKE '%SELPERCATINIB%')
    ORDER BY approval_date
""")
for row in cur.fetchall():
    ind = row['indication'][:80] + '...' if row['indication'] and len(row['indication']) > 80 else (row['indication'] or 'N/A')
    print(f"  ID: {row['id']}, Date: {row['approval_date']}")
    print(f"    Indication: {ind}")

conn.close()
