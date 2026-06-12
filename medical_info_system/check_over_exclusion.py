#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""检查被过度排除的抗肿瘤药物"""
import csv

with open('data/cde_all_drugs_optimized.csv', encoding='utf-8-sig') as f:
    reader = csv.DictReader(f)
    all_rows = list(reader)

print("=== 被判定为非抗肿瘤的药物中，实际可能是抗肿瘤药物的检查 ===")
print("(检查是否包含明确的基因靶点+癌症相关词)\n")

# 这些药名中包含的靶点词是强癌症信号
strong_cancer_signals = [
    '非小细胞肺癌', 'NSCLC', '小细胞肺癌', 'SCLC',
    '肝细胞癌', 'HCC',
    '黑色素瘤',
    '结直肠癌', 'CRC',
    'KRAS G12C', 'BRAF V600', 'EGFR 20',
    'CLDN18.2', 'CLDN18',
    '胶质瘤', '胶质母细胞瘤', 'GBM',
    '胃肠道间质瘤', 'GIST',
    '神经内分泌', 'NET',
    '肾细胞癌', 'RCC',
    '前列腺癌', 'CRPC',
    '淋巴瘤', '白血病', '骨髓瘤',
    '间皮瘤', '骨肉瘤',
    '胰腺癌', '胆道癌', '胆管癌',
    '食管癌', '胃癌', '乳腺癌',
    '卵巢癌', '宫颈癌', '子宫内膜癌',
    '头颈癌', '鼻咽癌', '甲状腺癌',
    '实体瘤', '恶性肿瘤',
    '晚期非小细胞', '晚期肝细胞', '晚期肾细胞',
    '转移性非小细胞', '转移性结直肠',
]

count = 0
for row in all_rows:
    if str(row['是否抗肿瘤']).strip().lower() not in ['true', 'yes', '1', '是']:
        combined = (row['药物名称'] + ' ' + row['拟定适应症']).lower()
        for signal in strong_cancer_signals:
            if signal.lower() in combined:
                count += 1
                print(f"  [{row['名单类型']}] {row['药物名称']}")
                print(f"    匹配: {signal}")
                print(f"    适应症: {row['拟定适应症'][:120]}")
                print()
                break

print(f"\n总计被过度排除的药物: {count} 条")

print("\n=== 检查JMKX001899片等特定药物 ===")
for row in all_rows:
    name = row['药物名称']
    for check in ['JMKX001899', 'JAB-21822', 'D-1553', 'Amivantamab']:
        if check.lower() in name.lower():
            print(f"  {name}")
            print(f"    是否抗肿瘤: {row['是否抗肿瘤']}")
            print(f"    适应症: {row['拟定适应症'][:200]}")
            print()
            break
