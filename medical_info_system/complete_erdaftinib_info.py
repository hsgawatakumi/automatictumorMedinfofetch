#!/usr/bin/env python3
"""
完善ERDAFITINIB的适应症和伴随诊断信息
"""
import sqlite3
import os

db_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'data', 'medical_info.db')

# ERDAFITINIB的完整信息
ERDAFITINIB_DETAILS = {
    "indication": "BALVERSA（erdafitinib）适用于治疗有FGFR3或FGFR2易感基因突变、并且在至少一次含铂化疗期间或之后疾病进展的局部晚期或转移性尿路上皮癌患者",
    "indication_cn": "BALVERSA（厄达替尼）适用于治疗有FGFR3或FGFR2易感基因突变、并且在至少一次含铂化疗期间或之后疾病进展的局部晚期或转移性尿路上皮癌患者",
    "companion_diagnosis": "需要FDA批准的伴随诊断检测：FGFR",
    "cd_target": "FGFR3, FGFR2",
    "mechanism_of_action": "Erdafitinib is a kinase inhibitor that binds to and inhibits FGFR1, FGFR2, FGFR3, and FGFR4 at nanomolar concentrations. Erdafitinib also inhibits RET, CSF1R, FLT4, AXL, KIT, RET, PDGFRα/β, and VEGFR2",
    "mechanism_of_action_cn": "厄达替尼是一种激酶抑制剂，在纳摩尔浓度下可与FGFR1、FGFR2、FGFR3和FGFR4结合并抑制它们。厄达替尼还可抑制RET、CSF1R、FLT4、AXL、KIT、RET、PDGFRα/β和VEGFR2"
}


def update_erdaftinib_details():
    print("=" * 100)
    print("完善ERDAFITINIB的适应症和伴随诊断信息")
    print("=" * 100)
    
    conn = sqlite3.connect(db_path)
    cur = conn.cursor()
    
    # 首先查看当前状态
    print("\n\n1. 当前ERDAFITINIB记录:")
    print("-" * 100)
    
    cur.execute("""
        SELECT id, drug_name_en, drug_name_cn, indication, companion_diagnosis, cd_target, mechanism_of_action
        FROM approved_drugs
        WHERE regulatory_agency = 'FDA'
          AND (
              drug_name_en LIKE '%ERDAFITINIB%' OR
              generic_name_en LIKE '%ERDAFITINIB%'
          )
        ORDER BY id
    """)
    
    current_records = cur.fetchall()
    
    for i, rec in enumerate(current_records):
        print(f"\n  {i+1}. ID: {rec[0]}")
        print(f"     英文名: {rec[1]}")
        print(f"     中文名: {rec[2]}")
        print(f"     适应症: {(rec[3] or 'N/A')[:100]}...")
        print(f"     伴随诊断: {rec[4] or 'N/A'}")
        print(f"     CD靶点: {rec[5] or 'N/A'}")
        print(f"     作用机制: {(rec[6] or 'N/A')[:100]}...")
    
    # 现在更新
    print("\n\n2. 更新ERDAFITINIB信息...")
    
    for rec in current_records:
        record_id = rec[0]
        
        cur.execute("""
            UPDATE approved_drugs
            SET indication = ?,
                companion_diagnosis = ?,
                cd_target = ?,
                mechanism_of_action = ?
            WHERE id = ?
        """, (
            ERDAFITINIB_DETAILS['indication'],
            ERDAFITINIB_DETAILS['companion_diagnosis'],
            ERDAFITINIB_DETAILS['cd_target'],
            ERDAFITINIB_DETAILS['mechanism_of_action'],
            record_id
        ))
        
        print(f"   ✓ 已更新 ID {record_id}")
    
    conn.commit()
    
    # 验证更新
    print("\n\n3. 验证更新结果:")
    print("-" * 100)
    
    cur.execute("""
        SELECT id, drug_name_en, drug_name_cn, indication, companion_diagnosis, cd_target, mechanism_of_action
        FROM approved_drugs
        WHERE regulatory_agency = 'FDA'
          AND (
              drug_name_en LIKE '%ERDAFITINIB%' OR
              generic_name_en LIKE '%ERDAFITINIB%'
          )
        ORDER BY id
    """)
    
    updated = cur.fetchall()
    
    for i, rec in enumerate(updated):
        print(f"\n  {i+1}. ID: {rec[0]}")
        print(f"     英文名: {rec[1]}")
        print(f"     中文名: {rec[2]}")
        print(f"     适应症: {(rec[3] or 'N/A')[:150]}...")
        print(f"     伴随诊断: {rec[4] or 'N/A'}")
        print(f"     CD靶点: {rec[5] or 'N/A'}")
        print(f"     作用机制: {(rec[6] or 'N/A')[:150]}...")
    
    print("\n\n✅ ERDAFITINIB信息完善完成!")
    conn.close()


if __name__ == "__main__":
    update_erdaftinib_details()
