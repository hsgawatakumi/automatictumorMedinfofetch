#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""检查用户提到的被误判的药物"""
import csv

with open('data/cde_all_drugs_fixed_v3.csv', encoding='utf-8-sig') as f:
    reader = csv.DictReader(f)
    all_rows = list(reader)

print("=== 检查被误判的药物 ===")
keywords = ['尼卡利单抗', '氯法齐明', 'Aficamten', '来法莫林', 'HMPL-523', 'KJ103']
for row in all_rows:
    name = row['药物名称']
    for kw in keywords:
        if kw.lower() in name.lower():
            print(f'[{kw}] 药物: {name}')
            print(f'  适应症: {row["拟定适应症"][:300]}')
            print(f'  是否抗肿瘤: {row["是否抗肿瘤"]}')
            print(f'  名单类型: {row["名单类型"]}')
            print()
            break

print("\n=== 检查当前筛选出的非抗肿瘤药物（误判）===")
non_cancer_check = [
    '高血压', '糖尿病', '类风湿', '关节炎', '感染', '抗菌', '抗病毒',
    'HIV', '乙肝', '结核', '哮喘', 'COPD', '慢性阻塞', '心脏病', '心力衰竭',
    '心血管', '皮肤病', '过敏', '哮喘', '贫血', '凝血', '癫痫', '偏头痛',
    '阿尔茨海默', '帕金森', '青光眼', '白内障', '肝炎', '肺炎', '胃病',
    '肠道', '消化', '寄生虫', '真菌', '细菌', '病毒'
]
count = 0
for row in all_rows:
    if str(row['是否抗肿瘤']).strip().lower() in ['true', 'yes', '1', '是']:
        indication = row['拟定适应症'].lower()
        name = row['药物名称'].lower()
        for nc in non_cancer_check:
            if nc in name or nc in indication:
                count += 1
                if count <= 20:
                    print(f'  {row["药物名称"]} - {row["拟定适应症"][:150]}')
                break

print(f"\n总计疑似误判的抗肿瘤药物: {count} 条")

print("\n=== 检查药物名称中英文化情况 ===")
for row in all_rows[:20]:
    name = row['药物名称']
    if any(ord(c) > 127 for c in name) and any(ord(c) <= 127 and c.isalpha() for c in name):
        print(f'  中英混合: {name}')
