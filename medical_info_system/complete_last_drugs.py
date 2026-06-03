#!/usr/bin/env python3
"""
补充最后几个未翻译药物
"""
import sqlite3
import os

db_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'data', 'medical_info.db')

# 最后几个药物的中文翻译
LAST_DRUG_NAMES = {
    'ROZLYTREK': '恩曲替尼',
    'TEMSIROLIMUS': '替西罗莫司',
    'TIVDAK': '替尔妥昔单抗',
    'TORISEL': '替西罗莫司',
    'VECTIBIX': '帕尼单抗',
    'VITRAKVI': '拉罗替尼',
    'ZALTRAP': '阿柏西普',
}


def complete_last_translations():
    print("=" * 100)
    print("补充最后几个未翻译药物的中文名称")
    print("=" * 100)
    
    conn = sqlite3.connect(db_path)
    cur = conn.cursor()
    
    # 更新最后几个药物
    updated = 0
    for key, value in LAST_DRUG_NAMES.items():
        cur.execute("""
            UPDATE approved_drugs
            SET drug_name_cn = ?
            WHERE regulatory_agency = 'FDA'
              AND (drug_name_en LIKE ? OR generic_name_en LIKE ?)
        """, (value, f'%{key}%', f'%{key}%'))
        
        updated += cur.rowcount
        if cur.rowcount > 0:
            print(f"  更新 {key} → {value} ({cur.rowcount}条)")
    
    conn.commit()
    
    print(f"\n更新完成! 总共更新了 {updated} 条记录")
    
    # 最终验证
    cur.execute("""
        SELECT COUNT(*) FROM approved_drugs
        WHERE regulatory_agency = 'FDA'
          AND (drug_name_cn IS NULL OR drug_name_cn = '' OR drug_name_cn = drug_name_en)
    """)
    remaining = cur.fetchone()[0]
    
    print(f"\n最终剩余未翻译药物数: {remaining}")
    
    if remaining == 0:
        print("✅ 所有药物中文翻译完成!")
    else:
        print(f"⚠️ 仍有 {remaining} 条未翻译")
    
    conn.close()


if __name__ == "__main__":
    complete_last_translations()
