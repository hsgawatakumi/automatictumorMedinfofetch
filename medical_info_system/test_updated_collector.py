#!/usr/bin/env python3
"""测试更新后的临床试验收集器"""
import sys
import os
sys.path.insert(0, '.')
from src.collectors.clinical_trials_optimized import ClinicalTrialsOptimizedCollector
from src.database import init_database
from src.utils.config_manager import ConfigManager
from src.utils.translator import TranslationService
import logging

# 设置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# 初始化组件
config_path = 'config/config.yaml'
db_path = 'data/medical_info.db'
config_manager = ConfigManager(config_path)
db_manager = init_database(db_path)
translation_config = config_manager.get_translation_config()
translation_service = TranslationService(translation_config)

print('='*80)
print('开始运行更新后的临床试验收集器...')
print('='*80)

# 验证基因和肿瘤类型列表
genes = config_manager.get_target_genes()
tumor_types = config_manager.get_tumor_types()
print(f'目标基因数量: {len(genes)}')
print(f'肿瘤类型数量: {len(tumor_types)}')
print()

# 创建并运行收集器
collector = ClinicalTrialsOptimizedCollector(db_manager, config_manager, translation_service)

print('正在收集CDE数据...')
cde_trials = collector._fetch_cde_trials(max_pages=2)
print(f'CDE获取到 {len(cde_trials)} 条记录')
print()

print('正在收集ChiCTR数据...')
chictr_trials = collector._fetch_chictr_trials(max_pages=2)
print(f'ChiCTR获取到 {len(chictr_trials)} 条记录')
print()

# 验证CDE的基因标记
print('='*80)
print('验证CDE基因标记:')
print('='*80)
for i, trial in enumerate(cde_trials[:5]):
    print(f'{i+1}. {trial["trial_id"]}: {trial["study_title_cn"][:50]}...')
    print(f'   基因标记: {trial["gene_marker"] or "无"}')
print()

# 验证ChiCTR的基因标记
print('='*80)
print('验证ChiCTR基因标记:')
print('='*80)
for i, trial in enumerate(chictr_trials[:5]):
    print(f'{i+1}. {trial["trial_id"]}: {trial["study_title_cn"][:50]}...')
    print(f'   基因标记: {trial["gene_marker"] or "无"}')
print()

# 保存数据
print('='*80)
print('正在保存数据到数据库...')
print('='*80)
for trial in cde_trials:
    collector._save_trial(trial)
for trial in chictr_trials:
    collector._save_trial(trial)

print(f'总共处理: {collector.total_records_processed}')
print(f'新增记录: {collector.total_records_added}')
print(f'错误数量: {collector.total_errors}')

db_manager.close()

print()
print('='*80)
print('收集和验证完成！')
print('='*80)
