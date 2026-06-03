#!/usr/bin/env python3
"""
完善未翻译药物和去除重复记录
"""
import sqlite3
import os

db_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'data', 'medical_info.db')

# 补充完整的药物中英文映射
ADDITIONAL_DRUG_NAMES = {
    # 品牌名
    'AFINITOR': '依维莫司',
    'AFINITOR DISPERZ': '依维莫司',
    'AHZANTIVE': '阿伐替尼',
    'AXITINIB': '阿昔替尼',
    'BALVERSA': '厄达替尼',
    'CABOMETYX': '卡博替尼',
    'CABOZANTINIB': '卡博替尼',
    'COMETRIQ': '卡博替尼',
    'DATROWAY': '帕博利珠单抗',
    'ELZONRIS': '塔格拉吉',
    'EMRELIS': '奥珠单抗',
    'ERBITUX': '西妥昔单抗',
    'ERDAFITINIB': '厄达替尼',
    'EVEROLIMUS': '依维莫司',
    'EYLEA': '阿柏西普',
    'EYLEA HD': '阿柏西普',
    'GAVRETO': '普拉替尼',
    'IBTROZI': '他瑞替尼',
    'IDHIFA': '恩西地平',
    'INLYTA': '阿昔替尼',
    'JAKAFI': '鲁索替尼',
    'JAKAFI XR': '鲁索替尼',
    'LENVATINIB': '仑伐替尼',
    'LENVIMA': '仑伐替尼',
    'NEXAVAR': '索拉非尼',
    'OPZELURA': '鲁索替尼',
    'PAVBLU': '帕博利珠单抗',
    'PAZOPANIB HYDROCHLORIDE': '帕唑帕尼',
    'PEMAZYRE': '培米替尼',
    'PORTRAZZA': '耐昔妥珠单抗',
    
    # 通用名
    'ERDAFITINIB': '厄达替尼',
    'EVEROLIMUS': '依维莫司',
    'AXITINIB': '阿昔替尼',
    'LENVATINIB': '仑伐替尼',
    'CABOZANTINIB': '卡博替尼',
    'PAZOPANIB': '帕唑帕尼',
    'SORAFENIB': '索拉非尼',
    'SUNITINIB': '舒尼替尼',
    'DASATINIB': '达沙替尼',
    'NILOTINIB': '尼洛替尼',
    'BOSUTINIB': '博舒替尼',
    'PONATINIB': '普纳替尼',
    'IDELALISIB': '伊德利西',
    'DUVELISIB': '杜韦利西布',
    'COPANLISIB': '库潘尼西',
    'ALPELISIB': '阿培利司',
    'ENASIDENIB': '恩西地平',
    'IVOSIDENIB': '艾伏尼布',
    'VENETOCLAX': '维奈克拉',
    'MIDOSTAURIN': '米哚妥林',
    'GILTERITINIB': '吉瑞替尼',
    'QUIZARTINIB': '奎扎替尼',
    'FEDRATINIB': '菲卓替尼',
    'VORINOSTAT': '伏立诺他',
    'ROMIDEPSIN': '罗米地辛',
    'PANOBINOSTAT': '帕比司他',
    'BORTEZOMIB': '硼替佐米',
    'CARFILZOMIB': '卡非佐米',
    'IXAZOMIB': '伊沙佐米',
    'LENALIDOMIDE': '来那度胺',
    'POMALIDOMIDE': '泊马度胺',
    'THALIDOMIDE': '沙利度胺',
    'PLERIXAFOR': '普乐沙福',
    'RUXOLITINIB': '鲁索替尼',
    'TALETRECTINIB': '他瑞替尼',
    'PRALSETINIB': '普拉替尼',
    'CAPMATINIB': '卡马替尼',
    'TEPOTINIB': '特泊替尼',
    'PEMIGATINIB': '培米替尼',
    'INFIGRATINIB': '英菲替尼',
    'CABOZANTINIB': '卡博替尼',
    'REGORAFENIB': '瑞戈非尼',
}


def clean_and_update_data():
    print("=" * 100)
    print("完善未翻译药物和去除重复记录")
    print("=" * 100)
    
    conn = sqlite3.connect(db_path)
    cur = conn.cursor()
    
    # 1. 补充未翻译的中文名称
    print("\n\n" + "-" * 100)
    print("1. 补充未翻译的中文名称...")
    print("-" * 100)
    
    cur.execute("""
        SELECT id, drug_name_en, generic_name_en, drug_name_cn
        FROM approved_drugs
        WHERE regulatory_agency = 'FDA'
    """)
    
    all_drugs = cur.fetchall()
    
    updated_names = 0
    for drug in all_drugs:
        id = drug[0]
        name_en = drug[1] or ''
        generic_en = drug[2] or ''
        current_cn = drug[3] or ''
        
        new_cn = None
        
        # 查找匹配的中文名称
        for key in ADDITIONAL_DRUG_NAMES:
            if key.upper() in name_en.upper() or key.upper() in generic_en.upper():
                new_cn = ADDITIONAL_DRUG_NAMES[key]
                break
        
        if new_cn and (new_cn.upper() != current_cn.upper() or current_cn == ''):
            cur.execute("""
                UPDATE approved_drugs
                SET drug_name_cn = ?
                WHERE id = ?
            """, (new_cn, id))
            updated_names += 1
            print(f"  ID {id}: {name_en} → {new_cn}")
    
    print(f"\n完成！更新中文名称: {updated_names} 条")
    
    # 2. 去除重复记录
    print("\n\n" + "-" * 100)
    print("2. 去除重复记录...")
    print("-" * 100)
    
    # 查找重复的记录（基于drug_name_en, generic_name_en, indication）
    cur.execute("""
        SELECT MIN(id) AS id_to_keep, drug_name_en, generic_name_en, drug_name_cn, indication,
               COUNT(*) AS total_count
        FROM approved_drugs
        WHERE regulatory_agency = 'FDA'
        GROUP BY drug_name_en, generic_name_en, drug_name_cn, indication
        HAVING COUNT(*) > 1
    """)
    
    duplicates = cur.fetchall()
    print(f"\n找到 {len(duplicates)} 组重复记录")
    
    removed_count = 0
    for dup in duplicates:
        keep_id = dup[0]
        name_en = dup[1]
        generic_en = dup[2]
        name_cn = dup[3]
        indication = dup[4]
        count = dup[5]
        
        # 保留最小的id，删除其他的
        cur.execute("""
            DELETE FROM approved_drugs
            WHERE regulatory_agency = 'FDA'
              AND drug_name_en = ?
              AND generic_name_en = ?
              AND drug_name_cn = ?
              AND indication = ?
              AND id != ?
        """, (name_en, generic_en, name_cn, indication, keep_id))
        
        removed = cur.rowcount
        removed_count += removed
        
        if removed > 0:
            print(f"  保留ID {keep_id}, 删除 {removed}条重复记录: {name_en}")
    
    conn.commit()
    
    # 统计结果
    cur.execute("SELECT COUNT(*) FROM approved_drugs WHERE regulatory_agency = 'FDA'")
    new_count = cur.fetchone()[0]
    cur.execute("SELECT COUNT(DISTINCT drug_name_en) FROM approved_drugs WHERE regulatory_agency = 'FDA'")
    new_drugs = cur.fetchone()[0]
    
    print(f"\n" + "=" * 100)
    print(f"处理完成!")
    print(f"  更新中文名称: {updated_names} 条")
    print(f"  删除重复记录: {removed_count} 条")
    print(f"  现在FDA总记录数: {new_count}")
    print(f"  现在FDA不同药物数: {new_drugs}")
    print("=" * 100)
    
    conn.close()


if __name__ == "__main__":
    clean_and_update_data()
