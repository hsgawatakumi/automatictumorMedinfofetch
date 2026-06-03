#!/usr/bin/env python3
"""列出数据库中所有FDA抗肿瘤药物"""
import sqlite3
import os

db_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'data', 'medical_info.db')
conn = sqlite3.connect(db_path)
conn.row_factory = sqlite3.Row
cur = conn.cursor()

# 获取所有FDA药物（按药物名分组）
cur.execute("""
    SELECT DISTINCT drug_name_en, generic_name_en, MIN(approval_date) as earliest_approval
    FROM approved_drugs
    WHERE regulatory_agency = 'FDA' AND drug_name_en IS NOT NULL
    GROUP BY drug_name_en
    ORDER BY earliest_approval DESC
""")

print("=" * 100)
print("数据库中FDA抗肿瘤药物列表")
print("=" * 100)

drugs = cur.fetchall()
print(f"\n总计: {len(drugs)} 种不同药物\n")

for i, drug in enumerate(drugs, 1):
    print(f"{i:2d}. {drug['drug_name_en']:30s} | {drug['generic_name_en'][:40] if drug['generic_name_en'] else 'N/A':40s} | 首次获批: {drug['earliest_approval']}")

# 检查知名药物是否在列表中
known_drugs = [
    'pembrolizumab', 'nivolumab', 'atezolizumab', 'durvalumab', 'cemiplimab',
    'ipilimumab', 'trastuzumab', 'rituximab', 'imatinib', 'osimertinib',
    'erlotinib', 'gefitinib', 'afatinib', 'crizotinib', 'ceritinib',
    'bevacizumab', 'cetuximab', 'panitumumab', 'olaparib', 'niraparib',
    'ibrutinib', 'palbociclib', 'sunitinib', 'sorafenib', 'lenvatinib'
]

print("\n" + "=" * 100)
print("检查知名药物是否收录:")
print("=" * 100)

drug_names_lower = [d['drug_name_en'].lower() for d in drugs]
for known in known_drugs:
    found = any(known.lower() in name for name in drug_names_lower)
    status = "✓ 已收录" if found else "✗ 未收录"
    print(f"  {known:20s}: {status}")

conn.close()
