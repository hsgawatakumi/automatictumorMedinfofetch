#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""验证并更新CDE特殊品种数据"""

import csv
import os
import sys
import logging

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# 读取CSV
csv_path = 'data/cde_all_drugs_fixed_v3.csv'
logger.info(f"读取 {csv_path}...")

priority_anticancer = 0
breakthrough_anticancer = 0
priority_total = 0
breakthrough_total = 0

with open(csv_path, 'r', encoding='utf-8-sig') as f:
    reader = csv.DictReader(f)
    for row in reader:
        drug_type = row.get('名单类型', '')
        is_cancer_val = row.get('是否抗肿瘤', 'False')
        
        # 处理布尔值和字符串
        if isinstance(is_cancer_val, bool):
            is_cancer = is_cancer_val
        else:
            is_cancer = str(is_cancer_val).strip().lower() in ['true', 'yes', '1', '是']
        
        if drug_type == '优先审评':
            priority_total += 1
            if is_cancer:
                priority_anticancer += 1
        elif drug_type == '突破性治疗':
            breakthrough_total += 1
            if is_cancer:
                breakthrough_anticancer += 1

logger.info(f"\n数据统计:")
logger.info(f"  优先审评总数: {priority_total} 条，抗肿瘤: {priority_anticancer} 条")
logger.info(f"  突破性治疗总数: {breakthrough_total} 条，抗肿瘤: {breakthrough_anticancer} 条")
logger.info(f"  总计: {priority_total + breakthrough_total} 条，抗肿瘤: {priority_anticancer + breakthrough_anticancer} 条")

# 更新数据库
logger.info(f"\n更新数据库...")
from src.database import init_database
db = init_database('data/medical_info.db')
conn = db.connect()
cursor = conn.cursor()
cursor.execute("DELETE FROM cde_special_drugs")
conn.commit()

count = 0
with open(csv_path, 'r', encoding='utf-8-sig') as f:
    reader = csv.DictReader(f)
    for row in reader:
        is_cancer_val = row.get('是否抗肿瘤', 'False')
        if isinstance(is_cancer_val, bool):
            is_cancer = is_cancer_val
        else:
            is_cancer = str(is_cancer_val).strip().lower() in ['true', 'yes', '1', '是']
        
        if not is_cancer:
            continue
        
        record = {
            'cde_id': f"CDE-{row['名单类型'][:2]}-{row['序号']}",
            'drug_name': row['药物名称'],
            'drug_type': row['名单类型'],
            'indication': row['拟定适应症'],
            'applicant': row['申请人'],
            'application_date': row['申请日期'],
            'acceptance_number': row['受理号'],
            'approval_date': '',
            'status': '已纳入',
            'priority_type': row['名单类型'] if row['名单类型'] == '优先审评' else '',
            'breakthrough_type': row['名单类型'] if row['名单类型'] == '突破性治疗' else '',
            'trial_info': '',
            'molecular_target': '',
            'gene_marker': '',
            'reference_drug': '',
            'description': '',
            'detail_url': '',
            'created_at': '2026-06-12',
            'updated_at': '2026-06-12'
        }
        try:
            db.execute_insert('cde_special_drugs', record)
            count += 1
        except Exception as e:
            logger.error(f"插入失败: {row['药物名称']} - {e}")

logger.info(f"数据库更新完成: {count} 条记录")
conn.close()

# 重新统计
logger.info(f"\n数据库统计:")
from src.database import init_database
db = init_database('data/medical_info.db')
rows = db.execute_query('SELECT drug_type, COUNT(*) as cnt FROM cde_special_drugs GROUP BY drug_type')
for row in rows:
    logger.info(f"  {row['drug_type']}: {row['cnt']} 条")

logger.info(f"\n完成！请在Streamlit中重新导出Excel文件。")