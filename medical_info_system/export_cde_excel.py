#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""从数据库直接导出cde_special_drugs Excel，包含优先审评和突破性治疗两个sheet"""

import os
import sys
import sqlite3
import logging
from datetime import datetime
import pandas as pd

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

db_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'data', 'medical_info.db')
output_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'data')
timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
output_file = os.path.join(output_dir, f'cde_special_drugs_{timestamp}.xlsx')

logger.info(f"读取数据库: {db_path}")

# 读取数据
conn = sqlite3.connect(db_path)

# 读取所有cde_special_drugs数据
df = pd.read_sql_query(
    "SELECT * FROM cde_special_drugs ORDER BY drug_type, id",
    conn
)
conn.close()

logger.info(f"总记录数: {len(df)}")

# 检查可用列
logger.info(f"数据库列: {list(df.columns)}")

# 选择并重命名导出列（中英文双语列名）
column_mapping = {
    'drug_name': '药物名称',
    'drug_name_en': '英文药名',
    'drug_type': '名单类型',
    'acceptance_number': '受理号',
    'applicant': '申请人',
    'indication': '适应症',
    'molecular_target': '分子靶点',
    'gene_marker': '基因标志物',
    'mechanism_of_action': '作用机制',
    'target_gene': '靶基因',
    'application_date': '申请日期',
    'approval_date': '批准日期',
    'status': '状态',
}

# 检查实际可用的列
available_columns = []
for db_col, _ in column_mapping.items():
    if db_col in df.columns:
        available_columns.append(db_col)

logger.info(f"导出列数: {len(available_columns)}")

# 分别筛选优先审评和突破性治疗
priority_df = df[df['drug_type'].str.contains('优先', na=False)].copy()
breakthrough_df = df[df['drug_type'].str.contains('突破性', na=False)].copy()

logger.info(f"优先审评: {len(priority_df)} 条")
logger.info(f"突破性治疗: {len(breakthrough_df)} 条")

# 重命名列
priority_df_export = priority_df[available_columns].rename(
    columns={k: v for k, v in column_mapping.items() if k in available_columns}
)
breakthrough_df_export = breakthrough_df[available_columns].rename(
    columns={k: v for k, v in column_mapping.items() if k in available_columns}
)

# 导出Excel
os.makedirs(output_dir, exist_ok=True)

with pd.ExcelWriter(output_file, engine='openpyxl') as writer:
    if len(priority_df_export) > 0:
        priority_df_export.to_excel(writer, sheet_name='优先审评', index=False)
    if len(breakthrough_df_export) > 0:
        breakthrough_df_export.to_excel(writer, sheet_name='突破性治疗', index=False)

logger.info(f"\n导出成功！文件: {output_file}")
logger.info(f"优先审评: {len(priority_df_export)} 条")
logger.info(f"突破性治疗: {len(breakthrough_df_export)} 条")

# 输出预览
print(f"\n=== 优先审评Sheet预览（前5条）===")
print(priority_df_export.head(5).to_string())
print(f"\n=== 突破性治疗Sheet预览（前5条）===")
print(breakthrough_df_export.head(5).to_string())

print(f"\n=== 统计信息 ===")
print(f"分子靶点已填写: {sum(df['molecular_target'].notna() & (df['molecular_target'] != ''))} / {len(df)}")
print(f"基因标志物已填写: {sum(df['gene_marker'].notna() & (df['gene_marker'] != ''))} / {len(df)}")
print(f"英文药名已填写: {sum(df['drug_name_en'].notna() & (df['drug_name_en'] != ''))} / {len(df)}")
