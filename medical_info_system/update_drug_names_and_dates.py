#!/usr/bin/env python3
"""
完善FDA药物的中文名称和批准日期数据
"""
import sqlite3
import os

db_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'data', 'medical_info.db')

# 药物中英文映射表（品牌名和通用名）
DRUG_NAME_MAPPING = {
    # 免疫检查点抑制剂
    'KEYTRUDA': '帕博利珠单抗',
    'PEMBROLIZUMAB': '帕博利珠单抗',
    'OPDIVO': '纳武利尤单抗',
    'NIVOLUMAB': '纳武利尤单抗',
    'TECENTRIQ': '阿替利珠单抗',
    'ATEZOLIZUMAB': '阿替利珠单抗',
    'IMFINZI': '度伐利尤单抗',
    'DURVALUMAB': '度伐利尤单抗',
    'LIBTAYO': '西米普利单抗',
    'CEMIPLIMAB': '西米普利单抗',
    'YERVOY': '伊匹木单抗',
    'IPILIMUMAB': '伊匹木单抗',
    'IMJUDO': '曲美木单抗',
    'TREMELIMUMAB': '曲美木单抗',
    
    # HER2
    'HERCEPTIN': '曲妥珠单抗',
    'TRASTUZUMAB': '曲妥珠单抗',
    'PERJETA': '帕妥珠单抗',
    'PERTUZUMAB': '帕妥珠单抗',
    'KADCYLA': '恩美曲妥珠单抗',
    'ADO-TRASTUZUMAB EMTANSINE': '恩美曲妥珠单抗',
    'ENHERTU': '德曲妥珠单抗',
    'TRASTUZUMAB DERUXTECAN': '德曲妥珠单抗',
    
    # EGFR
    'TAGRISSO': '奥希替尼',
    'OSIMERTINIB': '奥希替尼',
    'TARCEVA': '厄洛替尼',
    'ERLOTINIB': '厄洛替尼',
    'IRESSA': '吉非替尼',
    'GEFITINIB': '吉非替尼',
    'GILOTRIF': '阿法替尼',
    'AFATINIB': '阿法替尼',
    
    # ALK/ROS1
    'XALKORI': '克唑替尼',
    'CRIZOTINIB': '克唑替尼',
    'ZYKADIA': '塞瑞替尼',
    'CERITINIB': '塞瑞替尼',
    'ALECENSA': '阿来替尼',
    'ALECTINIB': '阿来替尼',
    'ALUNBRIG': '布格替尼',
    'BRIGATINIB': '布格替尼',
    'LORBRENA': '劳拉替尼',
    'LORLATINIB': '劳拉替尼',
    
    # RET
    'RETEVMO': '塞尔帕替尼',
    'SELPERCATINIB': '塞尔帕替尼',
    'GAVRETO': '普拉替尼',
    'PRALSETINIB': '普拉替尼',
    
    # MET
    'TABRECTA': '卡马替尼',
    'CAPMATINIB': '卡马替尼',
    'TEPMETKO': '特泊替尼',
    'TEPOTINIB': '特泊替尼',
    
    # FGFR
    'BALVERSA': '厄达替尼',
    'ERDAFITINIB': '厄达替尼',
    'PEMAZYRE': '培米替尼',
    'PEMIGATINIB': '培米替尼',
    'TRUSELTIQ': '英菲替尼',
    'INFIGRATINIB': '英菲替尼',
    
    # BRAF/MEK
    'ZELBORAF': '维莫非尼',
    'VEMURAFENIB': '维莫非尼',
    'TAFINLAR': '达拉非尼',
    'DABRAFENIB': '达拉非尼',
    'BRAFTOVI': '恩考芬尼',
    'ENCORAFENIB': '恩考芬尼',
    'MEKINIST': '曲美替尼',
    'TRAMETINIB': '曲美替尼',
    'COTELLIC': '考比替尼',
    'COBIMETINIB': '考比替尼',
    'MEKTOVI': '比美替尼',
    'BINIMETINIB': '比美替尼',
    
    # VEGF/R
    'AVASTIN': '贝伐珠单抗',
    'BEVACIZUMAB': '贝伐珠单抗',
    'CYRAMZA': '雷莫西尤单抗',
    'RAMUCIRUMAB': '雷莫西尤单抗',
    'SUTENT': '舒尼替尼',
    'SUNITINIB': '舒尼替尼',
    'NEXAVAR': '索拉非尼',
    'SORAFENIB': '索拉非尼',
    'VOTRIENT': '帕唑帕尼',
    'PAZOPANIB': '帕唑帕尼',
    'INLYTA': '阿昔替尼',
    'AXITINIB': '阿昔替尼',
    'LENVIMA': '仑伐替尼',
    'LENVATINIB': '仑伐替尼',
    'COMETRIQ': '卡博替尼',
    'CABOMETYX': '卡博替尼',
    'CABOZANTINIB': '卡博替尼',
    'STIVARGA': '瑞戈非尼',
    'REGORAFENIB': '瑞戈非尼',
    
    # BCR-ABL
    'GLEEVEC': '伊马替尼',
    'IMATINIB': '伊马替尼',
    'SPRYCEL': '达沙替尼',
    'DASATINIB': '达沙替尼',
    'TASIGNA': '尼洛替尼',
    'NILOTINIB': '尼洛替尼',
    'BOSULIF': '博舒替尼',
    'BOSUTINIB': '博舒替尼',
    'ICLUSIG': '普纳替尼',
    'PONATINIB': '普纳替尼',
    'QINLOCK': '瑞普替尼',
    'RIPRETINIB': '瑞普替尼',
    
    # KIT
    'AYVAKIT': '阿伐替尼',
    'AVAPRITINIB': '阿伐替尼',
    
    # BTK
    'IMBRUVICA': '伊布替尼',
    'IBRUTINIB': '伊布替尼',
    'CALQUENCE': '阿卡替尼',
    'ACALABRUTINIB': '阿卡替尼',
    'BRUKINSA': '泽布替尼',
    'ZANUBRUTINIB': '泽布替尼',
    
    # PI3K
    'ZYDELIG': '伊德利西',
    'IDELALISIB': '伊德利西',
    'COPIKTRA': '杜韦利西布',
    'DUVELISIB': '杜韦利西布',
    'ALIQOPA': '库潘尼西',
    'COPANLISIB': '库潘尼西',
    'PIQRAY': '阿培利司',
    'ALPELISIB': '阿培利司',
    
    # PARP
    'LYNPARZA': '奥拉帕利',
    'OLAPARIB': '奥拉帕利',
    'ZEJULA': '尼拉帕利',
    'NIRAPARIB': '尼拉帕利',
    'RUBRACA': '芦卡帕利',
    'RUCAPARIB': '芦卡帕利',
    'TALZENNA': '他拉唑帕利',
    'TALAZOPARIB': '他拉唑帕利',
    
    # CDK4/6
    'IBRANCE': '哌柏西利',
    'PALBOCICLIB': '哌柏西利',
    'KISQALI': '瑞波西利',
    'RIBOCICLIB': '瑞波西利',
    'VERZENIO': '阿贝西利',
    'ABEMACICLIB': '阿贝西利',
    
    # mTOR
    'AFINITOR': '依维莫司',
    'EVEROLIMUS': '依维莫司',
    'TORISEL': '替西罗莫司',
    'TEMSIROLIMUS': '替西罗莫司',
    
    # FLT3
    'RYDAPT': '米哚妥林',
    'MIDOSTAURIN': '米哚妥林',
    'XOSPATA': '吉瑞替尼',
    'GILTERITINIB': '吉瑞替尼',
    'VANFLYTA': '奎扎替尼',
    'QUIZARTINIB': '奎扎替尼',
    
    # IDH
    'IDHIFA': '恩西地平',
    'ENASIDENIB': '恩西地平',
    'TIBSOVO': '艾伏尼布',
    'IVOSIDENIB': '艾伏尼布',
    
    # BCL-2
    'VENCLEXTA': '维奈克拉',
    'VENETOCLAX': '维奈克拉',
    
    # NTRK
    'VITRAKVI': '拉罗替尼',
    'LAROTRECTINIB': '拉罗替尼',
    'ROZLYTREK': '恩曲替尼',
    'ENTRECTINIB': '恩曲替尼',
    
    # JAK
    'JAKAFI': '鲁索替尼',
    'RUXOLITINIB': '鲁索替尼',
    'INREBIC': '菲卓替尼',
    'FEDRATINIB': '菲卓替尼',
    'OPZELURA': '鲁索替尼',
    
    # CD20
    'RITUXAN': '利妥昔单抗',
    'RITUXIMAB': '利妥昔单抗',
    'GAZYVA': '奥妥珠单抗',
    'OBINUTUZUMAB': '奥妥珠单抗',
    'ARZERRA': '奥法妥木单抗',
    'OFATUMUMAB': '奥法妥木单抗',
    
    # CD30
    'ADCETRIS': '维布妥昔单抗',
    'BRENTUXIMAB VEDOTIN': '维布妥昔单抗',
    
    # ADC
    'POLIVY': '泊洛妥珠单抗',
    'POLATUZUMAB VEDOTIN': '泊洛妥珠单抗',
    'PADCEV': '恩诺妥珠单抗',
    'ENFORTUMAB VEDOTIN': '恩诺妥珠单抗',
    'BLENREP': '贝兰妥珠单抗',
    'BELANTAMAB MAFODOTIN': '贝兰妥珠单抗',
    'LONCASTUXIMAB TESIRINE': '朗妥昔单抗',
    
    # 蛋白酶体抑制剂
    'VELCADE': '硼替佐米',
    'BORTEZOMIB': '硼替佐米',
    'KYPROLIS': '卡非佐米',
    'CARFILZOMIB': '卡非佐米',
    'NINLARO': '伊沙佐米',
    'IXAZOMIB': '伊沙佐米',
    
    # HDAC
    'ZOLINZA': '伏立诺他',
    'VORINOSTAT': '伏立诺他',
    'ISTODAX': '罗米地辛',
    'ROMIDEPSIN': '罗米地辛',
    'FARYDAK': '帕比司他',
    'PANOBINOSTAT': '帕比司他',
    
    # 免疫调节剂
    'REVLIMID': '来那度胺',
    'LENALIDOMIDE': '来那度胺',
    'POMALYST': '泊马度胺',
    'POMALIDOMIDE': '泊马度胺',
    'THALOMID': '沙利度胺',
    'THALIDOMIDE': '沙利度胺',
    
    # 其他
    'BLINCYTO': '贝林妥欧单抗',
    'BLINATUMOMAB': '贝林妥欧单抗',
    'MOZOBIL': '普乐沙福',
    'PLERIXAFOR': '普乐沙福',
}

# 已知药物批准日期
KNOWN_DRUG_DATES = {
    # EGFR
    'OSIMERTINIB': [
        ('20151113', ['T790M']),
        ('20180418', ['FIRST-LINE', '一线']),
        ('20201218', ['ADJUVANT', '术后辅助']),
        ('20240926', ['STAGE III', 'III期', 'UNRESECTABLE', '不可切除']),
    ],
    'AFATINIB': [
        ('20130712', ['NSCLC']),
        ('20180119', ['SQUAMOUS']),
    ],
    'ERLOTINIB': [
        ('20041118', ['NSCLC']),
        ('20130514', ['FIRST-LINE', 'EGFR']),
    ],
    'GEFITINIB': [
        ('20030505', ['NSCLC']),
    ],
    
    # ALK
    'CRIZOTINIB': [
        ('20110826', ['ALK', 'NSCLC']),
        ('20160311', ['ROS1']),
    ],
    'CERITINIB': [
        ('20140429', ['ALK']),
        ('20170526', ['FIRST-LINE']),
    ],
    'ALECTINIB': [
        ('20151211', ['ALK', 'CRIZOTINIB PROGRESSED']),
        ('20171106', ['FIRST-LINE']),
    ],
    'BRIGATINIB': [
        ('20170428', ['ALK', 'CRIZOTINIB PROGRESSED']),
        ('20200522', ['FIRST-LINE']),
    ],
    'LORLATINIB': [
        ('20181102', ['ALK', 'PROGRESSED']),
        ('20210303', ['FIRST-LINE']),
    ],
    
    # RET
    'SELPERCATINIB': [
        ('20200508', ['RET FUSION', 'NSCLC', 'THYROID CANCER']),
        ('20240529', ['SOLID TUMOR']),
        ('20240927', ['RADIOACTIVE IODINE']),
    ],
    'PRALSETINIB': [
        ('20200904', ['RET FUSION', 'NSCLC', 'THYROID CANCER']),
    ],
    
    # MET
    'CAPMATINIB': [
        ('20200506', ['MET EXON 14', 'NSCLC']),
    ],
    'TEPOTINIB': [
        ('20210203', ['MET EXON 14', 'NSCLC']),
    ],
    
    # FGFR
    'ERDAFITINIB': [
        ('20190412', ['FGFR3/FGFR2', 'BLADDER CANCER']),
    ],
    'PEMIGATINIB': [
        ('20200417', ['FGFR2', 'CHOLANGIOCARCINOMA']),
    ],
    'INFIGRATINIB': [
        ('20210528', ['FGFR2', 'CHOLANGIOCARCINOMA']),
    ],
    
    # BRAF/MEK
    'VEMURAFENIB': [
        ('20110817', ['BRAF V600E', 'MELANOMA']),
    ],
    'DABRAFENIB': [
        ('20130529', ['BRAF V600E', 'MELANOMA']),
        ('20170622', ['THYROID CANCER']),
    ],
    'ENCORAFENIB': [
        ('20180627', ['BRAF V600E', 'MELANOMA']),
        ('20200408', ['COLORECTAL CANCER']),
    ],
    'TRAMETINIB': [
        ('20130529', ['BRAF V600E/K', 'MELANOMA']),
        ('20180504', ['THYROID CANCER']),
    ],
    'COBIMETINIB': [
        ('20151110', ['BRAF V600E/K', 'MELANOMA']),
    ],
    'BINIMETINIB': [
        ('20180627', ['BRAF V600E/K', 'MELANOMA']),
    ],
    
    # VEGF/R
    'SUNITINIB': [
        ('20060126', ['GIST', 'KIT']),
        ('20060126', ['RCC', 'RENAL CELL CARCINOMA']),
        ('20111116', ['PANC NET', 'Pancreatic neuroendocrine']),
        ('20171214', ['ADJUVANT RCC']),
    ],
    'SORAFENIB': [
        ('20051220', ['RCC']),
        ('20071119', ['HCC', 'Hepatocellular']),
        ('20130228', ['DTC', 'differentiated thyroid']),
    ],
    'PAZOPANIB': [
        ('20091019', ['RCC']),
        ('20120426', ['SOFT TISSUE SARCOMA']),
    ],
    'AXITINIB': [
        ('20120127', ['RCC', 'second-line']),
        ('20190419', ['RCC', 'first-line in combination']),
    ],
    'LENVATINIB': [
        ('20150213', ['DTC', 'differentiated thyroid']),
        ('20160513', ['RCC']),
        ('20180816', ['HCC']),
        ('20210811', ['ENDOMETRIAL']),
    ],
    'CABOZANTINIB': [
        ('20121129', ['MTC', 'medullary thyroid']),
        ('20160425', ['RCC']),
        ('20190114', ['HCC']),
        ('20210917', ['RCC', 'first-line']),
    ],
    'REGORAFENIB': [
        ('20120927', ['COLORECTAL CANCER']),
        ('20130225', ['GIST']),
        ('20170427', ['HCC']),
    ],
    
    # BCR-ABL
    'IMATINIB': [
        ('20010510', ['CML', 'chronic myeloid leukemia']),
        ('20020201', ['GIST', 'KIT']),
        ('20111220', ['CML', 'pediatric']),
    ],
    'DASATINIB': [
        ('20060628', ['CML', 'PH+ ALL']),
        ('20101028', ['CML', 'pediatric']),
    ],
    'NILOTINIB': [
        ('20071029', ['CML']),
        ('20180322', ['CML', 'pediatric']),
    ],
    'BOSUTINIB': [
        ('20120904', ['CML']),
        ('20170322', ['CML', 'first-line']),
    ],
    'PONATINIB': [
        ('20121214', ['CML', 'T315I']),
        ('20161109', ['CML', 'ALL']),
    ],
    'RIPRETINIB': [
        ('20200515', ['GIST', 'advanced']),
    ],
    
    # KIT
    'AVAPRITINIB': [
        ('20200110', ['GIST', 'PDGFRA exon 18']),
        ('20210621', ['SM', 'AdvSM']),
        ('20220611', ['ISM', 'indolent systemic mastocytosis']),
    ],
    
    # BTK
    'IBRUTINIB': [
        ('20131113', ['MCL', 'mantle cell lymphoma']),
        ('20140212', ['CLL', '17p deletion']),
        ('20140728', ['CLL']),
        ('20150129', ['WM', 'Waldenström']),
        ('20160304', ['CLL', 'first-line']),
        ('20170802', ['GVHD']),
        ('20190128', ['CLL/SLL']),
        ('20231201', ['CLL/SLL']),
    ],
    'ACALABRUTINIB': [
        ('20171031', ['MCL']),
        ('20191121', ['CLL/SLL']),
        ('20210723', ['CLL/SLL']),
    ],
    'ZANUBRUTINIB': [
        ('20191114', ['MCL', 'CLL/SLL']),
        ('20210831', ['WM']),
        ('20220901', ['CLL/SLL']),
        ('20230119', ['MGUS']),
    ],
    
    # CDK4/6
    'PALBOCICLIB': [
        ('20150203', ['HR+', 'HER2-', 'BREAST CANCER']),
        ('20170331', ['first-line']),
        ('20230914', ['ADJUVANT']),
    ],
    'RIBOCICLIB': [
        ('20170313', ['HR+', 'HER2-', 'BREAST CANCER']),
        ('20180718', ['first-line']),
        ('20210727', ['ADJUVANT']),
    ],
    'ABEMACICLIB': [
        ('20170928', ['HR+', 'HER2-', 'BREAST CANCER']),
        ('20200313', ['ADJUVANT']),
    ],
    
    # PI3K
    'IDELALISIB': [
        ('20140723', ['CLL', 'FL', 'SLL']),
    ],
    'DUVELISIB': [
        ('20180924', ['FL', 'SLL', 'CLL']),
    ],
    'COPANLISIB': [
        ('20170914', ['FL', 'SLL']),
    ],
    'ALPELISIB': [
        ('20190524', ['HR+', 'HER2-', 'PIK3CA', 'BREAST CANCER']),
    ],
    
    # PARP
    'OLAPARIB': [
        ('20141219', ['BRCA', 'OVARIAN CANCER']),
        ('20181219', ['BRCA', 'HER2-', 'BREAST CANCER']),
        ('20200508', ['BRCA', 'METASTATIC', 'PROSTATE CANCER']),
        ('20220311', ['BRCA', 'ADJUVANT', 'EARLY', 'BREAST CANCER']),
    ],
    'NIRAPARIB': [
        ('20170327', ['OVARIAN CANCER']),
        ('20191023', ['OVARIAN CANCER', 'ADJUVANT']),
    ],
    'RUCAPARIB': [
        ('20161219', ['BRCA', 'OVARIAN CANCER']),
        ('20180406', ['OVARIAN CANCER', 'ADJUVANT']),
    ],
    'TALAZOPARIB': [
        ('20181016', ['BRCA', 'HER2-', 'BREAST CANCER']),
    ],
    
    # mTOR
    'EVEROLIMUS': [
        ('20090330', ['RCC']),
        ('20101101', ['PANC NET', 'pancreatic neuroendocrine']),
        ('20110505', ['TSC-AML', 'tuberous sclerosis']),
        ('20120720', ['HER2-', 'HR+', 'BREAST CANCER']),
        ('20160226', ['GI NET', 'gastrointestinal neuroendocrine']),
        ('20180410', ['TSC-SEGA', 'subependymal giant cell astrocytoma']),
        ('20200428', ['NF1-PN', 'neurofibromatosis']),
        ('20220812', ['TUBEROUS SCLEROSIS']),
    ],
    'TEMSIROLIMUS': [
        ('20070530', ['RCC']),
    ],
    
    # FLT3
    'MIDOSTAURIN': [
        ('20170428', ['FLT3', 'AML', 'MDS']),
        ('20170620', ['MCL', 'mast cell leukemia']),
    ],
    'GILTERITINIB': [
        ('20181128', ['FLT3', 'AML']),
        ('20231115', ['FLT3', 'AML']),
    ],
    'QUIZARTINIB': [
        ('20230720', ['FLT3-ITD', 'AML']),
    ],
    
    # IDH
    'ENASIDENIB': [
        ('20170801', ['IDH2', 'AML']),
    ],
    'IVOSIDENIB': [
        ('20180720', ['IDH1', 'AML']),
        ('20210825', ['IDH1', 'CHOLANGIOCARCINOMA']),
    ],
    
    # BCL-2
    'VENETOCLAX': [
        ('20160411', ['CLL', '17p deletion']),
        ('20180608', ['CLL', 'first-line']),
        ('20181121', ['AML', 'in combination']),
        ('20201016', ['CLL', 'ADJUVANT']),
        ('20220322', ['AML', 'first-line']),
        ('20231127', ['AML', 'pediatric']),
    ],
    
    # NTRK
    'LAROTRECTINIB': [
        ('20181126', ['NTRK', 'SOLID TUMOR']),
        ('20221123', ['NTRK', 'SOLID TUMOR', 'pediatric']),
    ],
    'ENTRECTINIB': [
        ('20190815', ['NTRK', 'ROS1', 'NSCLC']),
        ('20220608', ['NTRK', 'SOLID TUMOR', 'pediatric']),
    ],
    
    # JAK
    'RUXOLITINIB': [
        ('20111116', ['MF', 'myelofibrosis']),
        ('20141204', ['PV', 'polycythemia vera']),
        ('20190924', ['GVHD', 'steroid-refractory']),
        ('20210922', ['GVHD', 'acute']),
        ('20220718', ['GVHD', 'chronic']),
        ('20240927', ['AGVHD', 'acute graft-versus-host']),
    ],
    'FEDRATINIB': [
        ('20190816', ['MF', 'myelofibrosis']),
    ],
    
    # CD20
    'RITUXIMAB': [
        ('19971126', ['NHL', 'non-Hodgkin lymphoma']),
        ('20060210', ['CLL', 'chronic lymphocytic leukemia']),
        ('20110419', ['RA', 'rheumatoid arthritis']),
        ('20180607', ['Pemphigus vulgaris']),
        ('20201015', ['MCL', 'in combination']),
    ],
    'OBINUTUZUMAB': [
        ('20131101', ['CLL', 'chronic lymphocytic leukemia']),
        ('20160210', ['FL', 'follicular lymphoma']),
    ],
    'OFATUMOMAB': [
        ('20091026', ['CLL', 'chronic lymphocytic leukemia']),
        ('20160830', ['CLL', 'extended indication']),
    ],
    
    # 蛋白酶体抑制剂
    'BORTEZOMIB': [
        ('20030513', ['MM', 'multiple myeloma']),
        ('20080620', ['MCL', 'mantle cell lymphoma']),
        ('20120809', ['MM', 'first-line']),
    ],
    'CARFILZOMIB': [
        ('20120720', ['MM', 'multiple myeloma', 'refractory']),
        ('20150724', ['MM', 'first-line']),
        ('20200820', ['MM', 'in combination']),
    ],
    'IXAZOMIB': [
        ('20151120', ['MM', 'multiple myeloma']),
        ('20210301', ['MM', 'in combination']),
    ],
    
    # HDAC
    'VORINOSTAT': [
        ('20061006', ['CTCL', 'cutaneous T-cell lymphoma']),
    ],
    'ROMIDEPSIN': [
        ('20091105', ['CTCL']),
        ('20110616', ['PTCL', 'peripheral T-cell lymphoma']),
    ],
    'PANOBINOSTAT': [
        ('20150223', ['MM', 'multiple myeloma']),
    ],
    
    # 免疫调节剂
    'LENALIDOMIDE': [
        ('20051227', ['MM', 'multiple myeloma']),
        ('20060628', ['MDS', 'myelodysplastic syndrome']),
        ('20130605', ['MCL', 'mantle cell lymphoma']),
        ('20150218', ['MM', 'first-line']),
        ('20170222', ['MCL', 'second-line']),
        ('20190507', ['FL', 'follicular lymphoma']),
        ('20220324', ['MCL', 'in combination']),
    ],
    'POMALIDOMIDE': [
        ('20130208', ['MM', 'multiple myeloma', 'refractory']),
        ('20200514', ['AIDS-related KS', 'Kaposi sarcoma']),
    ],
    'THALIDOMIDE': [
        ('19980716', ['ENL', 'erythema nodosum leprosum']),
        ('20060525', ['MM', 'multiple myeloma', 'first-line']),
    ],
    
    # 其他
    'BLINATUMOMAB': [
        ('20141203', ['ALL', 'B-cell acute lymphoblastic leukemia']),
        ('20170711', ['ALL', 'minimal residual disease']),
        ('20180329', ['ALL', 'first-line']),
        ('20220111', ['ALL', 'pediatric']),
    ],
    'PLERIXAFOR': [
        ('20081215', ['HSC mobilization', 'stem cell transplant']),
        ('20180125', ['HSC mobilization', 'pediatric']),
    ],
}

def update_drug_names_and_dates():
    print("=" * 100)
    print("完善FDA药物的中文名称和批准日期")
    print("=" * 100)
    
    conn = sqlite3.connect(db_path)
    cur = conn.cursor()
    
    updated_names = 0
    updated_dates = 0
    
    # 获取所有需要更新的药物
    cur.execute("""
        SELECT 
            id,
            drug_name_en,
            generic_name_en,
            drug_name_cn,
            approval_date,
            indication
        FROM approved_drugs
        WHERE regulatory_agency = 'FDA'
        ORDER BY id
    """)
    
    all_drugs = cur.fetchall()
    
    for drug in all_drugs:
        drug_id = drug[0]
        drug_name_en = drug[1] or ''
        generic_name_en = drug[2] or ''
        current_cn = drug[3]
        current_date = drug[4]
        indication = drug[5] or ''
        
        # 查找中文名称
        new_cn = None
        
        # 先检查品牌名
        for key in DRUG_NAME_MAPPING:
            if key.upper() in drug_name_en.upper():
                new_cn = DRUG_NAME_MAPPING[key]
                break
        
        # 再检查通用名
        if not new_cn:
            for key in DRUG_NAME_MAPPING:
                if key.upper() in generic_name_en.upper():
                    new_cn = DRUG_NAME_MAPPING[key]
                    break
        
        # 更新中文名称
        if new_cn and new_cn != current_cn:
            cur.execute("""
                UPDATE approved_drugs
                SET drug_name_cn = ?
                WHERE id = ?
            """, (new_cn, drug_id))
            updated_names += 1
        
        # 查找并更新批准日期
        if not current_date or current_date == '':
            matched_date = None
            
            for key in KNOWN_DRUG_DATES:
                if key.upper() in drug_name_en.upper() or key.upper() in generic_name_en.upper():
                    date_entries = KNOWN_DRUG_DATES[key]
                    
                    for date_str, keywords in date_entries:
                        # 检查适应症匹配
                        if not keywords:
                            # 如果没有关键词限制，直接用第一个日期
                            matched_date = date_str
                            break
                        else:
                            # 检查关键词是否匹配
                            matched = True
                            for k in keywords:
                                if k.lower() not in indication.lower():
                                    matched = False
                                    break
                            if matched:
                                matched_date = date_str
                                break
                    
                    if matched_date:
                        break
            
            if matched_date:
                cur.execute("""
                    UPDATE approved_drugs
                    SET approval_date = ?
                    WHERE id = ?
                """, (matched_date, drug_id))
                updated_dates += 1
                print(f"  更新ID {drug_id} ({drug_name_en}) - 日期: {matched_date}")
    
    conn.commit()
    conn.close()
    
    print("\n" + "=" * 100)
    print(f"更新完成！")
    print(f"  更新中文名称: {updated_names} 条")
    print(f"  更新批准日期: {updated_dates} 条")
    print("=" * 100)


if __name__ == "__main__":
    update_drug_names_and_dates()
