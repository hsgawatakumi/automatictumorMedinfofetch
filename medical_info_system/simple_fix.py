#!/usr/bin/env python3
"""
简单修复：直接删除旧表，创建新表，不调用init_database
"""
import os
import sys
import sqlite3
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from src.database import DatabaseManager

def main():
    db_path = os.path.join(os.path.dirname(__file__), 'data', 'medical_info.db')
    print(f"连接数据库: {db_path}")
    
    # 直接连接SQL连接，不调用init_database
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # 删除旧的cde_special_drugs表（如果存在）
    print("删除旧的cde_special_drugs表...")
    cursor.execute("DROP TABLE IF EXISTS cde_special_drugs")
    
    # 创建新的cde_special_drugs表
    print("创建新的cde_special_drugs表...")
    cursor.execute("""
    CREATE TABLE cde_special_drugs (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        cde_id TEXT,
        drug_name TEXT,
        drug_name_en TEXT,
        drug_type TEXT,
        indication TEXT,
        applicant TEXT,
        application_date TEXT,
        approval_date TEXT,
        status TEXT,
        priority_type TEXT,
        breakthrough_type TEXT,
        trial_info TEXT,
        molecular_target TEXT,
        gene_marker TEXT,
        reference_drug TEXT,
        description TEXT,
        detail_url TEXT,
        created_at TEXT,
        updated_at TEXT
    )
    """)
    
    # 创建索引
    print("创建索引...")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_cde_special_type ON cde_special_drugs(drug_type)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_cde_special_date ON cde_special_drugs(application_date)")
    
    conn.commit()
    conn.close()
    
    print("修复完成！")
    
    # 现在重新运行采集器添加数据
    print("\n现在运行采集器添加数据...")
    import subprocess
    subprocess.run([sys.executable, "collect_cde_special_drugs.py"], cwd=os.path.dirname(__file__))

if __name__ == "__main__":
    main()
