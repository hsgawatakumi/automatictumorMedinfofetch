#!/usr/bin/env python3
"""
修复CDE特殊品种表问题
删除旧表，重新创建
"""
import os
import sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from src.database import init_database

def main():
    db_path = os.path.join(os.path.dirname(__file__), 'data', 'medical_info.db')
    print(f"连接数据库: {db_path}")
    
    db_manager = init_database(db_path)
    
    # 尝试删除旧的cde_special_drugs表（如果存在）
    try:
        db_manager.conn.execute("DROP TABLE IF EXISTS cde_special_drugs")
        db_manager.conn.commit()
        print("已删除旧的cde_special_drugs表")
    except Exception as e:
        print(f"删除表时出错（可能表不存在）: {e}")
    
    # 重新创建所有表（包括正确的索引）
    print("重新初始化所有表...")
    db_manager.init_tables()
    
    print("修复完成！")
    db_manager.close()

if __name__ == "__main__":
    main()
