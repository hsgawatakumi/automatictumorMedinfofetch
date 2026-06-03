#!/usr/bin/env python3
"""最终验证FDA药物数据库完整性"""
import sqlite3
import os

db_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'data', 'medical_info.db')
conn = sqlite3.connect(db_path)
conn.row_factory = sqlite3.Row
cur = conn.cursor()

# 获取所有FDA药物（品牌名和通用名都显示）
cur.execute("""
    SELECT DISTINCT drug_name_en, generic_name_en,
           MIN(approval_date) as earliest_approval,
           COUNT(*) as indication_count
    FROM approved_drugs
    WHERE regulatory_agency = 'FDA' AND drug_name_en IS NOT NULL
    GROUP BY drug_name_en
    ORDER BY earliest_approval DESC
""")

drugs = cur.fetchall()

# 品牌名到通用名映射
BRAND_TO_GENERIC = {
    'keytruda': 'pembrolizumab',
    'opdivo': 'nivolumab',
    'tecentriq': 'atezolizumab',
    'imfinzi': 'durvalumab',
    'libtayo': 'cemiplimab',
    'bavencio': 'avelumab',
    'yervoy': 'ipilimumab',
    'imjudo': 'tremelimumab',
    'herceptin': 'trastuzumab',
    'avastin': 'bevacizumab',
    'rituxan': 'rituximab',
    'gleevec': 'imatinib',
    'tagrisso': 'osimertinib',
    'tarceva': 'erlotinib',
    'iressa': 'gefitinib',
    'gilotrif': 'afatinib',
    'xalkori': 'crizotinib',
    'zykadia': 'ceritinib',
    'alecensa': 'alectinib',
    'alunbrig': 'brigatinib',
    'lorbrena': 'lorlatinib',
    'zelboraf': 'vemurafenib',
    'tafinlar': 'dabrafenib',
    'braftovi': 'encorafenib',
    'mekinist': 'trametinib',
    'cotellic': 'cobimetinib',
    'mektovi': 'binimetinib',
    'lynparza': 'olaparib',
    'zejula': 'niraparib',
    'rubraca': 'rucaparib',
    'talzenna': 'talazoparib',
    'imbruvica': 'ibrutinib',
    'calquence': 'acalabrutinib',
    'brukinsa': 'zanubrutinib',
    'ibrance': 'palbociclib',
    'kisqali': 'ribociclib',
    'verzenio': 'abemaciclib',
    'sutent': 'sunitinib',
    'nexavar': 'sorafenib',
    'votrient': 'pazopanib',
    'inlyta': 'axitinib',
    'lenvima': 'lenvatinib',
    'cometriq': 'cabozantinib',
    'stivarga': 'regorafenib',
    'cyramza': 'ramucirumab',
    'erbitux': 'cetuximab',
    'vectibix': 'panitumumab',
    'portrazza': 'necitumumab',
    ' Kadcyla': 'ado-trastuzumab emtansine',
    'enhertu': 'trastuzumab deruxtecan',
    'perjeta': 'pertuzumab',
    'gazyva': 'obinutuzumab',
    'arzerra': 'ofatumumab',
    'blenrep': 'belantamab mafodotin',
    'polivy': 'polatuzumab vedotin',
    'padcev': 'enfortumab vedotin',
    'adcetris': 'brentuximab vedotin',
    'sprycel': 'dasatinib',
    'tasigna': 'nilotinib',
    'bosulif': 'bosutinib',
    'iclusig': 'ponatinib',
    'qinlock': 'ripretinib',
    'ayvakit': 'avapritinib',
    'retvm': 'selpercatinib',
    'retevmo': 'selpercatinib',
    'gavreto': 'pralsetinib',
    'piqray': 'alpelisib',
    'zeclenz': 'afatinib',
}

print("=" * 100)
print("FDA抗肿瘤药物数据库最终验证")
print("=" * 100)

print(f"\n总计收录: {len(drugs)} 种不同药物")

# 检查关键药物收录情况
key_drugs = [
    ('KEYTRUDA', 'pembrolizumab'),
    ('OPDIVO', 'nivolumab'),
    ('TECENTRIQ', 'atezolizumab'),
    ('IMFINZI', 'durvalumab'),
    ('LIBTAYO', 'cemiplimab'),
    ('YERVOY', 'ipilimumab'),
    ('IMJUDO', 'tremelimumab'),
    ('HERCEPTIN', 'trastuzumab'),
    ('AVASTIN', 'bevacizumab'),
    ('RITUXAN', 'rituximab'),
    ('GLEEVEC', 'imatinib'),
    ('TAGRISSO', 'osimertinib'),
    ('ERBITUX', 'cetuximab'),
    ('VECTIBIX', 'panitumumab'),
    ('CYRAMZA', 'ramucirumab'),
    ('LYNPARZA', 'olaparib'),
    ('ZEJULA', 'niraparib'),
    ('RUBRACA', 'rucaparib'),
    ('IMBRUVICA', 'ibrutinib'),
    ('CALQUENCE', 'acalabrutinib'),
    ('BRUKINSA', 'zanubrutinib'),
    ('IBRANCE', 'palbociclib'),
    ('KISQALI', 'ribociclib'),
    ('VERZENIO', 'abemaciclib'),
    ('SUTENT', 'sunitinib'),
    ('NEXAVAR', 'sorafenib'),
    ('LENVIMA', 'lenvatinib'),
    ('ADCETRIS', 'brentuximab vedotin'),
    ('POLIVY', 'polatuzumab vedotin'),
    ('PADCEV', 'enfortumab vedotin'),
    ('ENHERTU', 'trastuzumab deruxtecan'),
    ('BLINCYTO', 'blinatumomab'),
    ('BOSULIF', 'bosutinib'),
    ('TASIGNA', 'nilotinib'),
    ('ICLUSIG', 'ponatinib'),
    ('XALKORI', 'crizotinib'),
    ('ZYKADIA', 'ceritinib'),
    ('ALECENSA', 'alectinib'),
    ('ALUNBRIG', 'brigatinib'),
    ('LORBRENA', 'lorlatinib'),
    ('ZELBORAF', 'vemurafenib'),
    ('TAFINLAR', 'dabrafenib'),
    ('BRAFTOVI', 'encorafenib'),
    ('MEKINIST', 'trametinib'),
    ('COTELLIC', 'cobimetinib'),
    ('MEKTOVI', 'binimetinib'),
    ('GAZYVA', 'obinutuzumab'),
    ('PERJETA', 'pertuzumab'),
    ('KADCYLA', 'ado-trastuzumab emtansine'),
    ('QINLOCK', 'ripretinib'),
    ('AYVAKIT', 'avapritinib'),
    ('RETEVMO', 'selpercatinib'),
    ('GAVRETO', 'pralsetinib'),
]

drug_names_lower = [d['drug_name_en'].lower() for d in drugs]

print("\n关键抗肿瘤药物收录验证:")
found_count = 0
for brand, generic in key_drugs:
    if any(brand.lower() in name for name in drug_names_lower):
        print(f"  ✓ {brand:15s} ({generic})")
        found_count += 1
    else:
        print(f"  ✗ {brand:15s} ({generic}) - 未收录")

print(f"\n关键药物收录率: {found_count}/{len(key_drugs)} ({100*found_count/len(key_drugs):.1f}%)")

# 年份分布
cur.execute("""
    SELECT substr(approval_date, 1, 4) as year, COUNT(*) as cnt
    FROM approved_drugs
    WHERE regulatory_agency = 'FDA' AND approval_date IS NOT NULL AND approval_date != ''
    GROUP BY substr(approval_date, 1, 4)
    ORDER BY year DESC
""")

print("\n年份分布:")
for row in cur.fetchall():
    print(f"  {row['year']}年: {row['cnt']} 条")

# 总记录数
cur.execute("SELECT COUNT(*) FROM approved_drugs WHERE regulatory_agency = 'FDA'")
total_records = cur.fetchone()[0]
print(f"\nFDA药物总记录数: {total_records}")

conn.close()
