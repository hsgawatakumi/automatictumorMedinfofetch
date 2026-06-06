from src.database import DatabaseManager, init_database
import os

db_path = os.path.join('data', 'medical_info.db')
db = init_database(db_path)

# 查询最近的10条记录
results = db.execute_query('SELECT drug_name, indication, molecular_target, drug_type FROM cde_special_drugs ORDER BY updated_at DESC LIMIT 10')

print('数据库中最近的10条记录:')
print('=' * 80)
for i, row in enumerate(results, 1):
    print(f"{i}. {row['drug_name']}")
    print(f"   适应症: {row['indication']}")
    print(f"   类型: {row['drug_type']}")
    print()

# 统计
total = db.execute_query('SELECT COUNT(*) as count FROM cde_special_drugs')[0]['count']
breakthrough = db.execute_query('SELECT COUNT(*) as count FROM cde_special_drugs WHERE drug_type = "突破性治疗"')[0]['count']
priority = db.execute_query('SELECT COUNT(*) as count FROM cde_special_drugs WHERE drug_type = "优先审评"')[0]['count']

print(f"总计: {total} 条")
print(f"突破性治疗: {breakthrough} 条")
print(f"优先审评: {priority} 条")
