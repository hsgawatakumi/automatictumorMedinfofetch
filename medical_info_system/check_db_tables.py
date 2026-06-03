#!/usr/bin/env python3
"""
检查数据库表结构
"""
import os
import sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from src.database import DatabaseManager

db_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'data', 'medical_info.db')
db_manager = DatabaseManager(db_path)

print("=" * 100)
print("数据库表列表")
print("=" * 100)

# 获取所有表名
tables = db_manager.execute_query("SELECT name FROM sqlite_master WHERE type='table'")

for i, table in enumerate(tables):
    table_name = table['name']
    print(f"\n{i+1}. {table_name}")
    
    # 获取表结构
    columns = db_manager.execute_query(f"PRAGMA table_info({table_name})")
    print("-" * 80)
    
    for col in columns:
        print(f"  {col['cid']. {col['name']} - {col['type']}")

print("\n" + "=" * 100)

# 检查已有的数据量
print("\n数据统计")
print("-" * 80)

for table in tables:
    table_name = table['name']
    count = db_manager.execute_query(f"SELECT COUNT(*) as cnt FROM {table_name}")
    print(f"{table_name}: {count[0]['cnt']} 条记录")

db_manager.close()
