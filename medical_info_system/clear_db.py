from src.database import DatabaseManager, init_database
import os

db_path = os.path.join('data', 'medical_info.db')
db = init_database(db_path)

# 清空表
conn = db.connect()
cursor = conn.cursor()
cursor.execute("DELETE FROM cde_special_drugs")
conn.commit()
deleted_count = cursor.rowcount
print(f"已清空数据库: {deleted_count} 条记录")
