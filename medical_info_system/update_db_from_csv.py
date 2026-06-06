"""
将CSV数据更新到数据库cde_special_drugs表
"""
import os
import sys
import csv
import sqlite3
from datetime import datetime

# 数据库路径
DB_PATH = r"e:\TRAE progect\自动化医学信息收集系统\medical_info_system\data\medical_info.db"
CSV_PATH = r"e:\TRAE progect\自动化医学信息收集系统\medical_info_system\cde_anticancer_drugs.csv"

def update_db_from_csv():
    """从CSV文件读取数据并更新到数据库"""
    print("="*60)
    print("开始更新数据库")
    print("="*60)
    
    # 检查CSV文件是否存在
    if not os.path.exists(CSV_PATH):
        print(f"错误: CSV文件不存在 {CSV_PATH}")
        return False
    
    # 检查数据库是否存在
    if not os.path.exists(DB_PATH):
        print(f"错误: 数据库不存在 {DB_PATH}")
        return False
    
    # 连接数据库
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # 读取CSV文件
    with open(CSV_PATH, 'r', encoding='utf-8-sig') as f:
        reader = csv.DictReader(f)
        rows = list(reader)
    
    print(f"\n从CSV文件读取了 {len(rows)} 条记录")
    
    # 更新数据库
    updated_count = 0
    error_count = 0
    
    for row in rows:
        try:
            # 确定药物类型
            program_type = row['program_type']
            if '突破性' in program_type:
                drug_type = '突破性治疗'
            elif '优先审评' in program_type:
                drug_type = '优先审评'
            else:
                drug_type = program_type
            
            # 检查记录是否已存在
            cursor.execute(
                "SELECT id FROM cde_special_drugs WHERE drug_name = ? AND applicant = ?",
                (row['drug_name_cn'], row['applicant'])
            )
            existing = cursor.fetchone()
            
            if existing:
                # 更新现有记录
                cursor.execute("""
                    UPDATE cde_special_drugs SET
                        drug_name = ?,
                        applicant = ?,
                        indication = ?,
                        application_date = ?,
                        status = ?,
                        priority_type = ?,
                        breakthrough_type = ?,
                        detail_url = ?,
                        updated_at = ?
                    WHERE drug_name = ? AND applicant = ?
                """, (
                    row['drug_name_cn'],
                    row['applicant'],
                    row['indication'],
                    row['inclusion_date'],
                    '审评中',
                    '优先审评' if '优先' in drug_type else '',
                    '突破性治疗' if '突破性' in drug_type else '',
                    row['detail_url'],
                    datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                    row['drug_name_cn'],
                    row['applicant']
                ))
            else:
                # 插入新记录
                cursor.execute("""
                    INSERT INTO cde_special_drugs (
                        drug_name, applicant, indication, application_date,
                        status, priority_type, breakthrough_type, detail_url,
                        created_at, updated_at
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    row['drug_name_cn'],
                    row['applicant'],
                    row['indication'],
                    row['inclusion_date'],
                    '审评中',
                    '优先审评' if '优先' in drug_type else '',
                    '突破性治疗' if '突破性' in drug_type else '',
                    row['detail_url'],
                    datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                    datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                ))
            
            updated_count += 1
            
        except Exception as e:
            print(f"更新记录失败: {row.get('drug_name_cn', 'Unknown')} - {e}")
            error_count += 1
    
    # 提交更改
    conn.commit()
    
    # 验证更新结果
    cursor.execute("SELECT COUNT(*) FROM cde_special_drugs")
    total_count = cursor.fetchone()[0]
    
    print(f"\n数据库更新完成:")
    print(f"  - 成功更新: {updated_count} 条")
    print(f"  - 更新失败: {error_count} 条")
    print(f"  - cde_special_drugs 表中总计: {total_count} 条记录")
    
    # 显示一些示例数据
    print("\n数据库中最近的10条记录:")
    cursor.execute("""
        SELECT drug_name, applicant, indication, status, priority_type
        FROM cde_special_drugs
        ORDER BY id DESC
        LIMIT 10
    """)
    rows = cursor.fetchall()
    for row in rows:
        print(f"  {row[0]} - {row[1]} - {row[2]} [{row[3]}] [优先:{row[4]}]")
    
    # 关闭数据库连接
    conn.close()
    
    print("\n" + "="*60)
    print("数据库更新验证完成")
    print("="*60)
    
    return True

if __name__ == "__main__":
    success = update_db_from_csv()
    sys.exit(0 if success else 1)
