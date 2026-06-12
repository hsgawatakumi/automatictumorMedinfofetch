#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
修复突破性治疗数据 - 通过药物名称、申请人、受理号等信息推断适应症
"""

import os
import csv
import sys
import logging

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# 扩展的抗肿瘤关键词（包括药物名称中常见的）
ANTICANCER_KEYWORDS = [
    # 通用癌症关键词
    '癌', '肿瘤', '白血病', '淋巴瘤', '肉瘤', '骨髓瘤',
    # 常见抗肿瘤药物名称关键词
    '单抗', '抗体', 'ADC', '免疫治疗', 'PD-1', 'PD-L1', 
    'TKI', '抑制剂', '替尼', '利珠', '昔单抗', '西单抗',
    '曲妥', '帕妥', '贝伐', '西妥', '纳武', '帕博',
    '瑞康', '妥昔', '赛沃', '奥希', '阿美', '伏美',
    '泽布', '伊布', '赞布', '维奈', '达雷',
    # 化疗药常见词
    '替尼', '他滨', '铂', '紫杉醇', '多西', '吉西',
    # 靶点相关
    'EGFR', 'ALK', 'ROS1', 'RET', 'MET', 'HER2', 'BCMA',
    'CD19', 'CD20', 'CD30', 'CD33', 'CD38', 'CD47',
    # CAR-T相关
    'CAR-T', '嵌合', '细胞注射液',
    # 肿瘤公司名称（常见的抗肿瘤药物公司）
    '百济神州', '信达生物', '君实生物', '恒瑞医药',
    '正大天晴', '齐鲁制药', '再鼎医药', '基石药业',
    '康宁杰瑞', '科伦药业', '百奥泰', '中国生物',
    # 适应症相关（即使没有完整适应症，这些受理号或代码可能暗示肿瘤）
    'CXSS', 'CXHS',  # 这些是新药申请的代码，可能包含抗肿瘤药
]


def is_likely_anticancer_drug(drug_data):
    """通过多维度判断是否为抗肿瘤药物"""
    # 检查药物名称
    drug_name = drug_data.get('药物名称', '')
    for keyword in ANTICANCER_KEYWORDS:
        if keyword in drug_name:
            return True
    
    # 检查申请人
    applicant = drug_data.get('申请人', '')
    anticancer_companies = [
        '百济神州', '信达生物', '君实生物', '恒瑞', '正大天晴',
        '齐鲁制药', '再鼎医药', '基石药业', '康宁杰瑞', '科伦',
        '百奥泰', '天广实', '盛迪亚', '复宏汉霖', '博安生物',
        '百时美', '默沙东', '罗氏', '拜耳', '诺华', '阿斯利康',
        '再生元', '百健', '安进', '辉瑞', '施贵宝'
    ]
    for company in anticancer_companies:
        if company in applicant:
            return True
    
    # 检查受理号
    acceptance = drug_data.get('受理号', '')
    if 'CXSS' in acceptance or 'CXHS' in acceptance:
        # 生物制品或新药申请可能是抗肿瘤药，但需要结合名称
        pass
    
    return False


def repair_data():
    """修复现有数据"""
    input_file = 'data/cde_all_drugs_fixed.csv'
    output_file = 'data/cde_all_drugs_repaired.csv'
    anticancer_output = 'data/cde_anticancer_drugs_repaired.csv'
    
    if not os.path.exists(input_file):
        logger.error(f"文件不存在: {input_file}")
        return
    
    all_drugs = []
    repaired_count = 0
    
    # 读取现有数据
    with open(input_file, 'r', encoding='utf-8-sig') as f:
        reader = csv.DictReader(f)
        for row in reader:
            # 如果是突破性治疗且当前判断为否，但我们通过其他信息判断为是
            if row.get('名单类型') == '突破性治疗' and row.get('是否抗肿瘤') == 'False':
                if is_likely_anticancer_drug(row):
                    # 标记为需要重新判断
                    row['是否抗肿瘤'] = 'True'
                    row['拟定适应症'] = row['拟定适应症'] if row['拟定适应症'] != '理由及依据' else '根据药物名称和信息推断为抗肿瘤药物'
                    repaired_count += 1
                    logger.info(f"修复: {row['药物名称']} -> 抗肿瘤药物")
            
            all_drugs.append(row)
    
    logger.info(f"共修复 {repaired_count} 条突破性治疗数据")
    
    # 保存修复后的完整数据
    with open(output_file, 'w', newline='', encoding='utf-8-sig') as f:
        writer = csv.DictWriter(f, fieldnames=['名单类型', '序号', '药物名称', '受理号', '申请人', '申请日期', '拟定适应症', '是否抗肿瘤'])
        writer.writeheader()
        writer.writerows(all_drugs)
    
    logger.info(f"修复后的完整数据已保存到: {output_file}")
    
    # 筛选抗肿瘤药物
    anticancer_drugs = []
    for drug in all_drugs:
        if drug.get('是否抗肿瘤') == 'True' or drug.get('是否抗肿瘤') == True:
            anticancer_drugs.append(drug)
    
    # 保存抗肿瘤药物数据
    with open(anticancer_output, 'w', newline='', encoding='utf-8-sig') as f:
        writer = csv.DictWriter(f, fieldnames=['名单类型', '序号', '药物名称', '受理号', '申请人', '申请日期', '拟定适应症', '是否抗肿瘤'])
        writer.writeheader()
        writer.writerows(anticancer_drugs)
    
    logger.info(f"抗肿瘤药物数据已保存到: {anticancer_output}")
    
    # 统计
    total_breakthrough = sum(1 for d in all_drugs if d.get('名单类型') == '突破性治疗')
    breakthrough_anticancer = sum(1 for d in anticancer_drugs if d.get('名单类型') == '突破性治疗')
    total_priority = sum(1 for d in all_drugs if d.get('名单类型') == '优先审评')
    priority_anticancer = sum(1 for d in anticancer_drugs if d.get('名单类型') == '优先审评')
    
    logger.info("\n统计结果:")
    logger.info(f"突破性治疗总数: {total_breakthrough}, 其中抗肿瘤: {breakthrough_anticancer}")
    logger.info(f"优先审评总数: {total_priority}, 其中抗肿瘤: {priority_anticancer}")
    logger.info(f"总计抗肿瘤药物: {len(anticancer_drugs)}")
    
    return all_drugs, anticancer_drugs


def update_database_from_csv(anticancer_csv):
    """从修复后的CSV更新数据库"""
    from src.database import init_database
    from datetime import datetime
    
    db_path = 'data/medical_info.db'
    db = init_database(db_path)
    
    # 清空表
    conn = db.connect()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM cde_special_drugs")
    conn.commit()
    
    count = 0
    with open(anticancer_csv, 'r', encoding='utf-8-sig') as f:
        reader = csv.DictReader(f)
        for row in reader:
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
                'detail_url': 'https://www.cde.org.cn/main/xxgk/listpage/2f78f372d351c6851af7431c7710a731',
                'created_at': datetime.now().strftime('%Y-%m-%d'),
                'updated_at': datetime.now().strftime('%Y-%m-%d')
            }
            
            try:
                db.execute_insert('cde_special_drugs', record)
                count += 1
            except Exception as e:
                logger.error(f"插入失败: {row['药物名称']} - {e}")
    
    logger.info(f"数据库更新成功: {count} 条记录")


if __name__ == '__main__':
    all_drugs, anticancer_drugs = repair_data()
    
    # 更新数据库
    update_database_from_csv('data/cde_anticancer_drugs_repaired.csv')
    
    logger.info("完成!")

