#!/usr/bin/env python3
"""快速检查FDA药物数量"""
import sqlite3
import os

db_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'data', 'medical_info.db')
conn = sqlite3.connect(db_path)
cur = conn.cursor()

cur.execute("SELECT COUNT(*) FROM approved_drugs WHERE regulatory_agency = 'FDA'")
count = cur.fetchone()[0]
print(f"当前FDA药物记录数: {count}")

cur.execute("SELECT COUNT(DISTINCT drug_name_en) FROM approved_drugs WHERE regulatory_agency = 'FDA'")
distinct = cur.fetchone()[0]
print(f"不同药物数: {distinct}")

conn.close()
