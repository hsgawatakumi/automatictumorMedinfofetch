"""
检查数据库结构
"""
import sqlite3
import os

db_path = 'medical_info.db'
print(f"数据库文件存在: {os.path.exists(db_path)}")
print(f"数据库文件大小: {os.path.getsize(db_path) if os.path.exists(db_path) else 0} bytes")

conn = sqlite3.connect('medical_info.db')
c = conn.cursor()

# 获取所有表
c.execute("SELECT name FROM sqlite_master WHERE type='table'")
tables = c.fetchall()
print(f"\n数据库表: {[t[0] for t in tables]}")

# 检查每个表的结构
for table in tables:
    table_name = table[0]
    c.execute(f"PRAGMA table_info({table_name})")
    columns = c.fetchall()
    print(f"\n表 {table_name} 的列:")
    for col in columns:
        print(f"  {col[1]}: {col[2]}")

    c.execute(f"SELECT COUNT(*) FROM {table_name}")
    count = c.fetchone()[0]
    print(f"  记录数: {count}")

conn.close()