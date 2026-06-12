#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""验证用户提到的药物的筛选结果"""
import csv

with open('data/cde_all_drugs_optimized.csv', encoding='utf-8-sig') as f:
    reader = csv.DictReader(f)
    all_rows = list(reader)

print("=== 用户特别提到的药物验证 ===\n")

check_keywords = ['尼卡利单抗', '氯法齐明', 'Aficamten', '来法莫林', 'HMPL-523',
                   'KJ103', 'JMKX001899', 'JAB-21822', 'D-1553', 'Amivantamab']

for row in all_rows:
    name = row['药物名称']
    for kw in check_keywords:
        if kw.lower() in name.lower():
            print(f'{name}')
            print(f'  名单类型: {row["名单类型"]}')
            print(f'  是否抗肿瘤: {row["是否抗肿瘤"]}')
            print(f'  分子靶点: {row.get("molecular_target", "")}')
            print(f'  基因标志物: {row.get("gene_marker", "")}')
            print(f'  英文药名: {row.get("drug_name_en", "")}')
            print(f'  适应症: {row["拟定适应症"][:120]}')
            print()
            break

print("\n=== 统计摘要 ===")
priority_cancer = sum(1 for r in all_rows if r['名单类型'] == '优先审评' and r['是否抗肿瘤'] == 'True')
breakthrough_cancer = sum(1 for r in all_rows if r['名单类型'] == '突破性治疗' and r['是否抗肿瘤'] == 'True')
print(f'优先审评抗肿瘤: {priority_cancer}')
print(f'突破性治疗抗肿瘤: {breakthrough_cancer}')
print(f'总计: {priority_cancer + breakthrough_cancer}')
