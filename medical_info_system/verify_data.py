"""
验证NMPA药物数据质量
"""
import sqlite3

db_path = 'data/medical_info.db'
conn = sqlite3.connect(db_path)
cursor = conn.cursor()

print("=" * 60)
print("  NMPA药物数据质量验证")
print("=" * 60)

# 1. 统计信息
cursor.execute('SELECT COUNT(*) FROM approved_drugs WHERE regulatory_agency = "NMPA"')
total = cursor.fetchone()[0]

cursor.execute('SELECT COUNT(*) FROM approved_drugs WHERE regulatory_agency = "NMPA" AND indication IS NOT NULL AND indication != ""')
with_indication = cursor.fetchone()[0]

cursor.execute('SELECT COUNT(*) FROM approved_drugs WHERE regulatory_agency = "NMPA" AND mechanism_of_action IS NOT NULL AND mechanism_of_action != ""')
with_mechanism = cursor.fetchone()[0]

cursor.execute('SELECT COUNT(*) FROM approved_drugs WHERE regulatory_agency = "NMPA" AND gene_marker IS NOT NULL AND gene_marker != ""')
with_biomarker = cursor.fetchone()[0]

print(f"\n[统计信息]")
print(f"NMPA药物总数: {total}")
print(f"有适应症信息: {with_indication} ({with_indication/total*100:.1f}%)")
print(f"有作用机制信息: {with_mechanism} ({with_mechanism/total*100:.1f}%)")
print(f"有生物标志物信息: {with_biomarker} ({with_biomarker/total*100:.1f}%)")

# 2. 显示一些记录的样本
cursor.execute('''
    SELECT drug_name_cn, application_number, indication, mechanism_of_action, gene_marker
    FROM approved_drugs
    WHERE regulatory_agency = "NMPA" AND indication IS NOT NULL AND indication != ""
    LIMIT 10
''')

print(f"\n[样例数据 - 10条]")
for i, (name, app_no, indication, mechanism, biomarker) in enumerate(cursor.fetchall(), 1):
    print(f"\n{i}. {name} ({app_no})")
    if indication:
        print(f"   适应症: {indication[:80]}..." if len(indication) > 80 else f"   适应症: {indication}")
    if mechanism:
        print(f"   机制: {mechanism[:60]}..." if len(mechanism) > 60 else f"   机制: {mechanism}")
    if biomarker:
        print(f"   生物标志物: {biomarker[:60]}..." if len(biomarker) > 60 else f"   生物标志物: {biomarker}")

# 3. 显示缺失适应症的药物
cursor.execute('''
    SELECT drug_name_cn, application_number
    FROM approved_drugs
    WHERE regulatory_agency = "NMPA" AND (indication IS NULL OR indication = "")
    LIMIT 20
''')

print(f"\n[缺失适应症的药物 - 前20条]")
for i, (name, app_no) in enumerate(cursor.fetchall(), 1):
    print(f"  {i}. {name} ({app_no})")

conn.close()
print("\n" + "=" * 60)
