#!/usr/bin/env python3
"""
测试适应症-日期匹配功能的简单脚本
特别是验证奥希替尼的改进效果
"""

import sys
import os

# 添加项目路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from src.collectors.fda_collector import FDADrugCollector


def test_osimertinib_known_dates():
    """测试奥希替尼的已知适应症日期获取"""
    print("=" * 60)
    print("测试1: 检查奥希替尼已知日期功能")
    print("=" * 60)
    
    # 模拟初始化
    # 创建临时对象（不实际初始化整个系统）
    class MockDB:
        pass
    
    class MockConfig:
        def get(self, *args, **kwargs):
            return None
    
    class MockTranslator:
        def translate(self, *args, **kwargs):
            return ""
    
    collector = FDADrugCollector(MockDB(), MockConfig(), MockTranslator(), None)
    
    # 测试已知药物日期获取
    history = collector._get_known_drug_approval_dates("TAGRISSO", "OSIMERTINIB")
    
    print(f"\n获取到 {len(history)} 条奥希替尼的批准日期:")
    for item in history:
        print(f"  - {item['approval_date']}: {item['indication']} (来源: {item['source']})")
    
    return history


def test_intelligent_matching():
    """测试智能匹配算法"""
    print("\n" + "=" * 60)
    print("测试2: 检查智能适应症-日期匹配算法")
    print("=" * 60)
    
    class MockDB:
        pass
    
    class MockConfig:
        def get(self, *args, **kwargs):
            return None
    
    class MockTranslator:
        def translate(self, *args, **kwargs):
            return ""
    
    collector = FDADrugCollector(MockDB(), MockConfig(), MockTranslator(), None)
    
    # 模拟数据
    test_drugs = [
        {
            "indication": "TAGRISSO is indicated for the treatment of EGFR exon 19 deletion or exon 21 L858R mutation-positive metastatic non-small cell lung cancer (NSCLC)",
            "approval_date": "20180418"
        },
        {
            "indication": "TAGRISSO is indicated for the adjuvant treatment of EGFR exon 19 deletion or exon 21 L858R mutation-positive non-small cell lung cancer (NSCLC)",
            "approval_date": "20180418"
        },
        {
            "indication": "TAGRISSO is indicated for the treatment of EGFR exon 20 insertion mutation-positive metastatic non-small cell lung cancer (NSCLC)",
            "approval_date": "20180418"
        }
    ]
    
    test_history = [
        {'approval_date': '20151113', 'indication': 'EGFR exon 19 del/exon 21 L858R+ metastatic NSCLC'},
        {'approval_date': '20180418', 'indication': 'EGFR exon 19 del/exon 21 L858R+ metastatic NSCLC (first-line)'},
        {'approval_date': '20201218', 'indication': 'EGFR exon 19 del/exon 21 L858R+ NSCLC (adjuvant)'},
        {'approval_date': '20240523', 'indication': 'EGFR exon 20 insertion+ metastatic NSCLC'}
    ]
    
    matched = collector._intelligent_match_indication_dates(test_drugs, test_history, "20180418")
    
    print("\n智能匹配结果:")
    for i, drug in enumerate(matched):
        print(f"  适应症{i+1}:")
        print(f"    日期: {drug['approval_date']}")
        print(f"    原始: {drug['indication'][:100]}...")
        print()
    
    return matched


if __name__ == "__main__":
    try:
        print("\n🧪 测试FDA适应症-日期匹配功能\n")
        test_osimertinib_known_dates()
        test_intelligent_matching()
        print("\n✅ 测试完成！")
    except Exception as e:
        print(f"\n❌ 测试出错: {e}")
        import traceback
        traceback.print_exc()
