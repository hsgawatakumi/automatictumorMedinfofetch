#!/usr/bin/env python3
"""检查并补充采集缺失的FDA抗肿瘤药物"""
import sqlite3
import os
import requests
import time

db_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'data', 'medical_info.db')
conn = sqlite3.connect(db_path)
conn.row_factory = sqlite3.Row
cur = conn.cursor()

# 获取已收录的药物名称
cur.execute("""
    SELECT DISTINCT LOWER(drug_name_en) as name
    FROM approved_drugs
    WHERE regulatory_agency = 'FDA' AND drug_name_en IS NOT NULL
""")
existing = set(row['name'] for row in cur.fetchall())
print(f"已收录药物数量: {len(existing)}")

# 已知抗肿瘤药物映射 (品牌名 -> 通用名)
KNOWN_DRUGS = {
    # PD-1/PD-L1 抑制剂
    'keytruda': 'pembrolizumab',
    'opdivo': 'nivolumab',
    'tecentriq': 'atezolizumab',
    'imfinzi': 'durvalumab',
    'libtayo': 'cemiplimab',
    'bavencio': 'avelumab',
    'jemperli': 'dostarlimab',

    # CTLA-4 抑制剂
    'yervoy': 'ipilimumab',
    'imjudo': 'tremelimumab',

    # CD20 单克隆抗体
    'rituxan': 'rituximab',
    'gazyva': 'obinutuzumab',
    'arzerra': 'ofatumumab',
    'tres爱美': 'rituximab',

    # HER2 抑制剂
    'herceptin': 'trastuzumab',
    'perjeta': 'pertuzumab',
    'kadcyla': 'ado-trastuzumab emtansine',
    'enhertu': 'trastuzumab deruxtecan',

    # EGFR 抑制剂
    'tarceva': 'erlotinib',
    'iressa': 'gefitinib',
    'gilotrif': 'afatinib',
    'tagrisso': 'osimertinib',
    'nerlynx': 'neratinib',
    'vizimpro': 'dacomitinib',

    # VEGF 抑制剂
    'avastin': 'bevacizumab',
    'cyramza': 'ramucirumab',

    # BCR-ABL 抑制剂
    'gleevec': 'imatinib',
    'sprycel': 'dasatinib',
    'tasigna': 'nilotinib',
    'bosulif': 'bosutinib',
    'iclusig': 'ponatinib',

    # ALK 抑制剂
    'xalkori': 'crizotinib',
    'zykadia': 'ceritinib',
    'alecensa': 'alectinib',
    'alunbrig': 'brigatinib',
    'lorbrena': 'lorlatinib',

    # BRAF/MEK 抑制剂
    'zelboraf': 'vemurafenib',
    'tafinlar': 'dabrafenib',
    'braftovi': 'encorafenib',
    'mekinist': 'trametinib',
    'cotellic': 'cobimetinib',
    'mektovi': 'binimetinib',

    # PARP 抑制剂
    'lynparza': 'olaparib',
    'zejula': 'niraparib',
    'rubraca': 'rucaparib',
    'talzenna': 'talazoparib',

    # BTK 抑制剂
    'imbruvica': 'ibrutinib',
    'calquence': 'acalabrutinib',
    'brukinsa': 'zanubrutinib',

    # CDK4/6 抑制剂
    'ibrance': 'palbociclib',
    'kisqali': 'ribociclib',
    'verzenio': 'abemaciclib',

    # mTOR 抑制剂
    'afinitor': 'everolimus',
    'torisel': 'temsirolimus',

    # 多靶点TKI
    'sutent': 'sunitinib',
    'nexavar': 'sorafenib',
    'votrient': 'pazopanib',
    'inlyta': 'axitinib',
    'lenvima': 'lenvatinib',
    'cometriq': 'cabozantinib',
    'stivarga': 'regorafenib',

    # NTRK 抑制剂
    'vitrakvi': 'larotrectinib',
    'rozlytrek': 'entrectinib',

    # RET 抑制剂
    'retevmo': 'selpercatinib',
    'gavreto': 'pralsetinib',

    # FGFR 抑制剂
    'balversa': 'erdafitinib',
    'pemazyre': 'pemigatinib',
    'truseltiq': 'infigratinib',
    'lytgobi': 'futibatinib',

    # 其他靶向药
    'tepotinib': 'tepotinib',
    'capmatinib': 'capmatinib',
    'erdafitinib': 'erdafitinib',

    # ADC
    'polivy': 'polatuzumab vedotin',
    'padcev': 'enfortumab vedotin',
    'adcetryis': 'brentuximab vedotin',
    'kadcyla': 'ado-trastuzumab emtansine',
    'enhertu': 'trastuzumab deruxtecan',
    'trodelvy': 'sacituzumab govitecan',
    'blenrep': 'belantamab mafodotin',

    # 蛋白酶体抑制剂
    'velcade': 'bortezomib',
    'kyprolis': 'carfilzomib',
    'ninlaro': 'ixazomib',

    # 组蛋白去乙酰化酶抑制剂
    'zolinza': 'vorinostat',
    'istodax': 'romidepsin',
    'farydak': 'panobinostat',

    # 免疫调节剂
    'revlimid': 'lenalidomide',
    'pomalyst': 'pomalidomide',
    'thalomid': 'thalidomide',

    # BCL-2 抑制剂
    'venclexta': 'venetoclax',

    # FLT3 抑制剂
    'ridafin': 'midostaurin',
    'xospata': 'gilteritinib',

    # JAK 抑制剂
    'jakafi': 'ruxolitinib',
    'inhbec': 'fedratinib',

    # PI3K 抑制剂
    'zydelig': 'idelalisib',
    'copiktra': 'duvelisib',
    'aliqopa': 'copanlisib',
    'piqray': 'alpelisib',
}

# 检查缺失的药物
print("\n检查已知抗肿瘤药物收录情况:")
missing = []
for brand, generic in KNOWN_DRUGS.items():
    if brand not in existing and generic not in existing:
        missing.append((brand, generic))

print(f"缺失药物数量: {len(missing)}")
for brand, generic in missing[:20]:
    print(f"  {brand} ({generic})")

conn.close()

# 返回缺失列表供后续处理
print(f"\n需要补充采集的药物总数: {len(missing)}")
