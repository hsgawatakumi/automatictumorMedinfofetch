#!/usr/bin/env python3
"""
直接查询数据库，查看真实的字段内容
"""
import sqlite3
import os

db_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'data', 'medical_info.db')
conn = sqlite3.connect(db_path)
cur = conn.cursor()

print("=" * 100)
print("直接查询ERDAFITINIB的数据库信息")
print("=" * 100)

# 查询字段列名
cur.execute("PRAGMA table_info(approved_drugs)")
columns = [desc[1] for desc in cur.fetchall()]
print(f"\n数据库字段: {columns}")

# 查询ID在895和896的记录
cur.execute("""
    SELECT *
    FROM approved_drugs
    WHERE id IN (895, 896)
    ORDER BY id
""")

records = cur.fetchall()

print(f"\n找到 {len(records)} 条记录\n")

for i, record in enumerate(records):
    print(f"  {i+1}. ID: {record[0]}")
    for j, value in enumerate(record):
        col_name = columns[j]
        if value and str(value).strip():
            print(f"     {col_name:30s}: {str(value)[:80]}")

conn.close()
