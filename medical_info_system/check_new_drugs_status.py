#!/usr/bin/env python3
"""
检查FDA新增药物的中文名称、批准日期、适应症缺失情况
"""
import sqlite3
import os

db_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'data', 'medical_info.db')
conn = sqlite3.connect(db_path)
conn.row_factory = sqlite3.Row
cur = conn.cursor()

print("=" * 100)
print("检查新增FDA药物的数据完整性问题")
print("=" * 100)

# 1. 获取所有FDA药物，检查哪些有缺失
print("\n1. 检查FDA药物的基本信息缺失情况")
print("-" * 100)
cur.execute("""
    SELECT 
        id,
        drug_name_en,
        generic_name_en,
        drug_name_cn,
        approval_date,
        indication,
        data_collection_time
    FROM approved_drugs
    WHERE regulatory_agency = 'FDA'
    ORDER BY id DESC
""")

drugs = cur.fetchall()

print(f"\n总FDA药物数: {len(drugs)}")

missing_fields = {
    'drug_name_cn': 0,
    'approval_date': 0,
    'indication': 0
}

for drug in drugs:
    if not drug['drug_name_cn'] or drug['drug_name_cn'] == '':
        missing_fields['drug_name_cn'] += 1
    if not drug['approval_date'] or drug['approval_date'] == '':
        missing_fields['approval_date'] += 1
    if not drug['indication'] or drug['indication'] == '':
        missing_fields['indication'] += 1

print(f"  中文名称缺失: {missing_fields['drug_name_cn']} ({100*missing_fields['drug_name_cn']/len(drugs):.1f}%)")
print(f"  批准日期缺失: {missing_fields['approval_date']} ({100*missing_fields['approval_date']/len(drugs):.1f}%)")
print(f"  适应症缺失: {missing_fields['indication']} ({100*missing_fields['indication']/len(drugs):.1f}%)")

# 2. 列出最近新增的20条药物，查看它们的状态
print("\n\n2. 最近新增的20条FDA药物信息")
print("-" * 100)

cur.execute("""
    SELECT 
        id,
        drug_name_en,
        generic_name_en,
        drug_name_cn,
        approval_date,
        data_collection_time
    FROM approved_drugs
    WHERE regulatory_agency = 'FDA'
    ORDER BY id DESC
    LIMIT 20
""")

recent_drugs = cur.fetchall()

for drug in recent_drugs:
    drug_name_cn = drug['drug_name_cn'] or '(缺失)'
    approval_date = drug['approval_date'] or '(缺失)'
    print(f"  ID: {drug['id']}")
    print(f"    英文名: {drug['drug_name_en']}")
    print(f"    通用名: {drug['generic_name_en'] or '(无)'}")
    print(f"    中文名: {drug_name_cn}")
    print(f"    批准日期: {approval_date}")
    print()

# 3. 列出有缺失的代表性药物
print("\n3. 有数据缺失的代表性药物 (前30条)")
print("-" * 100)
cur.execute("""
    SELECT 
        id,
        drug_name_en,
        generic_name_en,
        drug_name_cn,
        approval_date,
        indication
    FROM approved_drugs
    WHERE regulatory_agency = 'FDA'
      AND (
          drug_name_cn IS NULL OR drug_name_cn = '' OR
          approval_date IS NULL OR approval_date = ''
      )
    ORDER BY id DESC
    LIMIT 30
""")

missing_drugs = cur.fetchall()

for drug in missing_drugs:
    missing_info = []
    if not drug['drug_name_cn']:
        missing_info.append('中文名缺失')
    if not drug['approval_date']:
        missing_info.append('批准日期缺失')
    
    print(f"  ID: {drug['id']}, 英文名: {drug['drug_name_en']}")
    print(f"    问题: {', '.join(missing_info)}")
    print()

conn.close()
