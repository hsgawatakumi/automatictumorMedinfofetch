#!/usr/bin/env python3
"""
验证数据库中的基因标记
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from src.database import init_database


def main():
    print("=" * 80)
    print("数据库基因标记验证")
    print("=" * 80)
    
    base_path = os.path.dirname(os.path.abspath(__file__))
    db_path = os.path.join(base_path, 'data', 'medical_info.db')
    
    db_manager = init_database(db_path)
    
    # 查询一些记录查看基因标记
    print("\n查询CDE记录（最近10条）:")
    cde_trials = db_manager.execute_query(
        "SELECT trial_id, trial_status, gene_marker, study_title_cn FROM clinical_trials "
        "WHERE platform = ? ORDER BY id DESC LIMIT 10",
        ('CDE',)
    )
    
    for t in cde_trials:
        print(f"\n- {t['trial_id']}: {t['trial_status']}")
        print(f"  基因: {t['gene_marker'] or '无'}")
        print(f"  标题: {t['study_title_cn'][:60]}...")
    
    print("\n" + "=" * 80)
    print("查询ChiCTR记录（最近10条）:")
    chictr_trials = db_manager.execute_query(
        "SELECT trial_id, trial_status, gene_marker, study_title_cn FROM clinical_trials "
        "WHERE platform = ? ORDER BY id DESC LIMIT 10",
        ('ChiCTR',)
    )
    
    for t in chictr_trials:
        print(f"\n- {t['trial_id']}: {t['trial_status']}")
        print(f"  基因: {t['gene_marker'] or '无'}")
        print(f"  标题: {t['study_title_cn'][:60]}...")
    
    print("\n" + "=" * 80)
    print("查询ClinicalTrials.gov记录（最近10条）:")
    ctgov_trials = db_manager.execute_query(
        "SELECT trial_id, trial_status, gene_marker, study_title_cn FROM clinical_trials "
        "WHERE platform = ? ORDER BY id DESC LIMIT 10",
        ('ClinicalTrials.gov',)
    )
    
    for t in ctgov_trials:
        print(f"\n- {t['trial_id']}: {t['trial_status']}")
        print(f"  基因: {t['gene_marker'] or '无'}")
        title = t['study_title_cn'] or '无中文标题'
        print(f"  标题: {title[:60]}...")
    
    print("\n" + "=" * 80)
    print("统计信息:")
    print("=" * 80)
    
    platforms = ['ClinicalTrials.gov', 'CDE', 'ChiCTR']
    total_with_genes = 0
    
    for platform in platforms:
        count = db_manager.get_record_count('clinical_trials', "platform = ?", (platform,))
        count_with_genes = db_manager.get_record_count(
            'clinical_trials', 
            "platform = ? AND gene_marker IS NOT NULL AND gene_marker != ''",
            (platform,)
        )
        total_with_genes += count_with_genes
        print(f"{platform}: {count} 条, 其中 {count_with_genes} 条有基因标记 ({count_with_genes/count*100:.1f}%)")
    
    print(f"\n总计: 有基因标记的记录共 {total_with_genes} 条")
    
    db_manager.close()
    print("=" * 80)


if __name__ == "__main__":
    main()
