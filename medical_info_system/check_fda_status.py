#!/usr/bin/env python3
"""检查FDA药物数据库状态"""

import sqlite3
import os

db_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'data', 'medical_info.db')

conn = sqlite3.connect(db_path)
cur = conn.cursor()

# 检查FDA药物数量
cur.execute("SELECT COUNT(*) FROM approved_drugs WHERE regulatory_agency = 'FDA'")
fda_count = cur.fetchone()[0]
print(f"FDA药物总记录数: {fda_count}")

# 检查不同药物数量
cur.execute("SELECT COUNT(DISTINCT drug_name_en) FROM approved_drugs WHERE regulatory_agency = 'FDA'")
fda_drugs = cur.fetchone()[0]
print(f"FDA不同药物数: {fda_drugs}")

# 检查日期分布
cur.execute("""
    SELECT substr(approval_date, 1, 4) as year, COUNT(*) as count
    FROM approved_drugs
    WHERE regulatory_agency = 'FDA' AND approval_date IS NOT NULL
    GROUP BY substr(approval_date, 1, 4)
    ORDER BY year DESC
""")
print("\n年份分布:")
for row in cur.fetchall():
    print(f"  {row[0]}: {row[1]}条")

# 检查最近采集的药物
cur.execute("""
    SELECT DISTINCT drug_name_en, approval_date, data_collection_time
    FROM approved_drugs
    WHERE regulatory_agency = 'FDA'
    ORDER BY data_collection_time DESC
    LIMIT 15
""")
print("\n最近采集的药物:")
for row in cur.fetchall():
    print(f"  {row[0]} | {row[1]} | {row[2]}")

# 按药物名统计适应症数量
cur.execute("""
    SELECT drug_name_en, COUNT(*) as indication_count
    FROM approved_drugs
    WHERE regulatory_agency = 'FDA' AND drug_name_en IS NOT NULL
    GROUP BY drug_name_en
    HAVING indication_count > 1
    ORDER BY indication_count DESC
    LIMIT 10
""")
print("\n多适应症药物:")
for row in cur.fetchall():
    print(f"  {row[0]}: {row[1]}个适应症")

conn.close()
