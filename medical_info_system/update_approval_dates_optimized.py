#!/usr/bin/env python3
"""
优化版FDA药物批准日期更新脚本
"""
import sqlite3
import os

db_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'data', 'medical_info.db')

# 药物及其批准日期（先给一个主要的批准日期）
DRUG_PRIMARY_APPROVAL_DATE = {
    # EGFR
    'OSIMERTINIB': '20151113',
    'AFATINIB': '20130712',
    'ERLOTINIB': '20041118',
    'GEFITINIB': '20030505',
    
    # ALK
    'CRIZOTINIB': '20110826',
    'CERITINIB': '20140429',
    'ALECTINIB': '20151211',
    'BRIGATINIB': '20170428',
    'LORLATINIB': '20181102',
    
    # RET
    'SELPERCATINIB': '20200508',
    'PRALSETINIB': '20200904',
    
    # MET
    'CAPMATINIB': '20200506',
    'TEPOTINIB': '20210203',
    
    # FGFR
    'ERDAFITINIB': '20190412',
    'PEMIGATINIB': '20200417',
    'INFIGRATINIB': '20210528',
    
    # BRAF/MEK
    'VEMURAFENIB': '20110817',
    'DABRAFENIB': '20130529',
    'ENCORAFENIB': '20180627',
    'TRAMETINIB': '20130529',
    'COBIMETINIB': '20151110',
    'BINIMETINIB': '20180627',
    
    # VEGF/R
    'SUNITINIB': '20060126',
    'SORAFENIB': '20051220',
    'PAZOPANIB': '20091019',
    'AXITINIB': '20120127',
    'LENVATINIB': '20150213',
    'CABOZANTINIB': '20121129',
    'REGORAFENIB': '20120927',
    
    # BCR-ABL
    'IMATINIB': '20010510',
    'DASATINIB': '20060628',
    'NILOTINIB': '20071029',
    'BOSUTINIB': '20120904',
    'PONATINIB': '20121214',
    'RIPRETINIB': '20200515',
    
    # KIT
    'AVAPRITINIB': '20200110',
    
    # BTK
    'IBRUTINIB': '20131113',
    'ACALABRUTINIB': '20171031',
    'ZANUBRUTINIB': '20191114',
    
    # PI3K
    'IDELALISIB': '20140723',
    'DUVELISIB': '20180924',
    'COPANLISIB': '20170914',
    'ALPELISIB': '20190524',
    
    # PARP
    'OLAPARIB': '20141219',
    'NIRAPARIB': '20170327',
    'RUCAPARIB': '20161219',
    'TALAZOPARIB': '20181016',
    
    # CDK4/6
    'PALBOCICLIB': '20150203',
    'RIBOCICLIB': '20170313',
    'ABEMACICLIB': '20170928',
    
    # mTOR
    'EVEROLIMUS': '20090330',
    'TEMSIROLIMUS': '20070530',
    
    # FLT3
    'MIDOSTAURIN': '20170428',
    'GILTERITINIB': '20181128',
    'QUIZARTINIB': '20230720',
    
    # IDH
    'ENASIDENIB': '20170801',
    'IVOSIDENIB': '20180720',
    
    # BCL-2
    'VENETOCLAX': '20160411',
    
    # NTRK
    'LAROTRECTINIB': '20181126',
    'ENTRECTINIB': '20190815',
    
    # JAK
    'RUXOLITINIB': '20111116',
    'FEDRATINIB': '20190816',
    
    # CD20
    'RITUXIMAB': '19971126',
    'OBINUTUZUMAB': '20131101',
    'OFATUMOMAB': '20091026',
    
    # 蛋白酶体抑制剂
    'BORTEZOMIB': '20030513',
    'CARFILZOMIB': '20120720',
    'IXAZOMIB': '20151120',
    
    # HDAC
    'VORINOSTAT': '20061006',
    'ROMIDEPSIN': '20091105',
    'PANOBINOSTAT': '20150223',
    
    # 免疫调节剂
    'LENALIDOMIDE': '20051227',
    'POMALIDOMIDE': '20130208',
    'THALIDOMIDE': '19980716',
    
    # 其他
    'BLINATUMOMAB': '20141203',
    'PLERIXAFOR': '20081215',
}


def update_approval_dates_optimized():
    print("=" * 100)
    print("优化版FDA药物批准日期更新")
    print("=" * 100)
    
    conn = sqlite3.connect(db_path)
    cur = conn.cursor()
    
    updated = 0
    
    # 获取所有FDA药物
    cur.execute("""
        SELECT id, drug_name_en, generic_name_en, approval_date
        FROM approved_drugs
        WHERE regulatory_agency = 'FDA'
    """)
    
    drugs = cur.fetchall()
    
    print(f"\n检查 {len(drugs)} 条FDA药物记录...")
    
    for drug in drugs:
        drug_id = drug[0]
        drug_name_en = drug[1] or ''
        generic_name_en = drug[2] or ''
        current_date = drug[3]
        
        if current_date and current_date != '':
            continue
        
        # 查找匹配的药物
        matched_date = None
        
        for key in DRUG_PRIMARY_APPROVAL_DATE:
            if (key in drug_name_en.upper()) or (key in generic_name_en.upper()):
                matched_date = DRUG_PRIMARY_APPROVAL_DATE[key]
                break
        
        if matched_date:
            cur.execute("""
                UPDATE approved_drugs
                SET approval_date = ?
                WHERE id = ?
            """, (matched_date, drug_id))
            updated += 1
            print(f"  更新ID {drug_id} ({drug_name_en}) - 日期: {matched_date}")
    
    conn.commit()
    conn.close()
    
    print("\n" + "=" * 100)
    print(f"日期更新完成！")
    print(f"  更新批准日期: {updated} 条")
    print("=" * 100)


if __name__ == "__main__":
    update_approval_dates_optimized()
