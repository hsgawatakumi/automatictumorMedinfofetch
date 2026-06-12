#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
修复数据库更新脚本 - 正确处理突破性治疗数据
"""

import os
import sys
import csv
import logging
from datetime import datetime

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

CDE_BASE_URL = "https://www.cde.org.cn/main/xxgk/listpage/2f78f372d351c6851af7431c7710a731"


def update_database():
    """从修复后的CSV更新数据库"""
    from src.database import init_database
    
    db_path = 'data/medical_info.db'
    db = init_database(db_path)
    
    # 清空表
    conn = db.connect()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM cde_special_drugs")
    conn.commit()
    
    count = 0
    priority_count = 0
    breakthrough_count = 0
    
    # 读取修复后的CSV
    csv_file = 'data/cde_all_drugs_fixed_v2.csv'
    
    if not os.path.exists(csv_file):
        logger.error(f"文件不存在: {csv_file}")
        return
    
    with open(csv_file, 'r', encoding='utf-8-sig') as f:
        reader = csv.DictReader(f)
        for row in reader:
            # 只处理标记为抗肿瘤的药物
            is_cancer = row.get('是否抗肿瘤', '').strip()
            
            # 接受多种可能的True值
            if is_cancer not in ['True', 'true', 'TRUE', '是', '1']:
                continue
            
            drug_type = row.get('名单类型', '')
            
            record = {
                'cde_id': f"CDE-{drug_type[:2]}-{row.get('序号', '')}",
                'drug_name': row.get('药物名称', ''),
                'drug_type': drug_type,
                'indication': row.get('拟定适应症', ''),
                'applicant': row.get('申请人', ''),
                'application_date': row.get('申请日期', ''),
                'acceptance_number': row.get('受理号', ''),
                'approval_date': '',
                'status': '已纳入',
                'priority_type': drug_type if drug_type == '优先审评' else '',
                'breakthrough_type': drug_type if drug_type == '突破性治疗' else '',
                'trial_info': '',
                'molecular_target': '',
                'gene_marker': '',
                'reference_drug': '',
                'description': '',
                'detail_url': CDE_BASE_URL,
                'created_at': datetime.now().strftime('%Y-%m-%d'),
                'updated_at': datetime.now().strftime('%Y-%m-%d')
            }
            
            try:
                db.execute_insert('cde_special_drugs', record)
                count += 1
                
                if drug_type == '突破性治疗':
                    breakthrough_count += 1
                elif drug_type == '优先审评':
                    priority_count += 1
                    
            except Exception as e:
                logger.error(f"插入失败: {row.get('药物名称')} - {e}")
    
    logger.info(f"数据库更新完成: {count} 条记录")
    logger.info(f"  优先审评抗肿瘤: {priority_count} 条")
    logger.info(f"  突破性治疗抗肿瘤: {breakthrough_count} 条")
    
    return count, priority_count, breakthrough_count


def verify_csv_data():
    """验证CSV数据"""
    csv_file = 'data/cde_all_drugs_fixed_v2.csv'
    
    total = 0
    priority_total = 0
    breakthrough_total = 0
    priority_anticancer = 0
    breakthrough_anticancer = 0
    
    with open(csv_file, 'r', encoding='utf-8-sig') as f:
        reader = csv.DictReader(f)
        for row in reader:
            total += 1
            drug_type = row.get('名单类型', '')
            is_cancer = row.get('是否抗肿瘤', '').strip()
            
            if drug_type == '优先审评':
                priority_total += 1
                if is_cancer in ['True', 'true', 'TRUE', '是', '1']:
                    priority_anticancer += 1
            elif drug_type == '突破性治疗':
                breakthrough_total += 1
                if is_cancer in ['True', 'true', 'TRUE', '是', '1']:
                    breakthrough_anticancer += 1
    
    logger.info(f"\nCSV数据统计:")
    logger.info(f"  总记录数: {total}")
    logger.info(f"  优先审评总数: {priority_total}, 其中抗肿瘤: {priority_anticancer}")
    logger.info(f"  突破性治疗总数: {breakthrough_total}, 其中抗肿瘤: {breakthrough_anticancer}")
    
    return total, priority_total, breakthrough_total, priority_anticancer, breakthrough_anticancer


if __name__ == '__main__':
    # 先验证CSV数据
    total, priority_total, breakthrough_total, priority_anticancer, breakthrough_anticancer = verify_csv_data()
    
    # 更新数据库
    logger.info("\n开始更新数据库...")
    count, db_priority, db_breakthrough = update_database()
    
    logger.info("\n完成！")
