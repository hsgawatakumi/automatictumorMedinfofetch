#!/usr/bin/env python3
"""
系统性FDA抗肿瘤药物采集脚本
从1990年至今全面采集FDA批准的抗肿瘤靶向药物和免疫药物
"""

import os
import sys
import time
import logging
import requests
from datetime import datetime
from typing import Dict, List, Optional

# 添加项目路径
current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, current_dir)

from src.database import init_database
from src.utils.config_manager import create_config_manager
from src.utils.translator import TranslationService
from src.utils.http_client import RequestManager
from src.collectors.fda_collector import FDADrugCollector

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def create_systematic_fda_collector():
    """创建系统性FDA采集器实例"""
    config_path = os.path.join(current_dir, 'config', 'config.yaml')
    db_path = os.path.join(current_dir, 'data', 'medical_info.db')
    
    config_manager = create_config_manager(config_path)
    db_manager = init_database(db_path)
    translation_service = TranslationService(config_manager.get_translation_config())
    request_manager = RequestManager(config_manager.get_proxy_config())
    
    return FDADrugCollector(
        db_manager, config_manager, translation_service, request_manager
    )


def collect_fda_anticancer_drugs_comprehensive():
    """
    全面系统性采集FDA批准的抗肿瘤药物
    
    采集策略：
    1. 分年代采集（1990-2000, 2000-2010, 2010-2020, 2020-2025）
    2. 使用多种关键词组合确保召回率
    3. 大幅增加采集数量
    4. 严格的去重和过滤
    """
    
    print("=" * 100)
    print("开始系统性FDA抗肿瘤药物采集")
    print("目标: 采集1990年至今所有FDA批准的抗肿瘤靶向药物和免疫药物")
    print("=" * 100)
    
    start_time = datetime.now()
    
    # 创建采集器
    collector = create_systematic_fda_collector()
    
    # 采集统计
    total_collected = 0
    total_added = 0
    total_duplicates = 0
    
    # 定义需要采集的年代和对应的关键词
    # 这样可以确保不同时期的药物都能被采集到
    collection_periods = [
        # 2020年至今 - 免疫治疗、靶向治疗爆发期
        {
            'name': '2020-2025',
            'start_date': '20200101',
            'end_date': '20251231',
            'keywords': [
                # 免疫检查点
                'pd-1', 'pd-l1', 'ctla-4', 'lag-3', 'checkpoint',
                # 抗体类
                'monoclonal antibody', 'adc', 'antibody-drug conjugate',
                # 激酶抑制剂
                'kinase inhibitor', 'egfr', 'alk', 'braf', 'mek', 'kras',
                'vegf', 'her2', 'cdk4', 'cdk6', 'parp', 'btk', 'pi3k',
                # 肿瘤类型
                'nsclc', 'melanoma', 'lymphoma', 'leukemia', 'myeloma',
                'breast cancer', 'colorectal cancer', 'prostate cancer'
            ]
        },
        # 2010-2020 - 靶向治疗快速发展期
        {
            'name': '2010-2020',
            'start_date': '20100101',
            'end_date': '20191231',
            'keywords': [
                'pd-1', 'pd-l1', 'ctla-4', 'checkpoint inhibitor',
                'monoclonal antibody', 'kinase inhibitor',
                'egfr inhibitor', 'alk inhibitor', 'braf inhibitor',
                'vegf inhibitor', 'her2', 'cdk inhibitor',
                'nsclc', 'melanoma', 'lymphoma', ' leukemia',
                'breast cancer', 'colorectal', 'renal cell',
                'carcinoma', 'sarcoma', 'multiple myeloma'
            ]
        },
        # 2000-2010 - 靶向治疗起步期
        {
            'name': '2000-2010',
            'start_date': '20000101',
            'end_date': '20091231',
            'keywords': [
                'monoclonal antibody', 'kinase inhibitor',
                'egfr', 'her2', 'vegf', 'bcr-abl',
                'chronic myelogenous leukemia', 'gastrointestinal stromal',
                'breast cancer', 'colorectal', 'nsclc', 'renal',
                'lymphoma', 'leukemia', 'imatinib', 'trastuzumab',
                'rituximab', 'bevacizumab', 'cetuximab'
            ]
        },
        # 1990-2000 - 早期靶向药物
        {
            'name': '1990-2000',
            'start_date': '19900101',
            'end_date': '19991231',
            'keywords': [
                'monoclonal antibody', 'rituximab', 'trastuzumab',
                'interferon', 'interleukin', 'antineoplastic',
                'leukemia', 'lymphoma', 'breast cancer',
                'colorectal', 'chronic myelogenous'
            ]
        },
    ]
    
    # 额外的重要靶向药物关键词（不分年代）
    important_keywords = [
        'imatinib', 'dasatinib', 'nilotinib', 'bosutinib', 'ponatinib',  # BCR-ABL
        'erlotinib', 'gefitinib', 'afatinib', 'osimertinib',  # EGFR
        'crizotinib', 'ceritinib', 'alectinib', 'brigatinib', 'lorlatinib',  # ALK
        'vemurafenib', 'dabrafenib', 'encorafenib',  # BRAF
        'trametinib', 'cobimetinib', 'binimetinib', 'mekinist',  # MEK
        'pembrolizumab', 'nivolumab', 'atezolizumab', 'durvalumab', 'cemiplimab',  # PD-1/PD-L1
        'ipilimumab', 'tremelimumab',  # CTLA-4
        'rituximab', 'obinutuzumab', 'ofatumumab',  # CD20
        'trastuzumab', 'pertuzumab', 'ado-trastuzumab', 'trastuzumab deruxtecan',  # HER2
        'bevacizumab', 'ramucirumab', 'ziv-aflibercept',  # VEGF
        'cetuximab', 'panitumumab', 'necitumumab',  # EGFR
        'ramucirumab',  # VEGFR2
        'blinatumomab', 'tagraxofusp',  # 双特异性抗体
        'brentuximab vedotin', 'polatuzumab vedotin', 'enfortumab vedotin',  # ADC
        'olaparib', 'niraparib', 'rucaparib', 'talazoparib',  # PARP
        'ibrutinib', 'acalabrutinib', 'zanubrutinib',  # BTK
        'idelalisib', 'duvelisib', 'copanlisib',  # PI3K
        'palbociclib', 'ribociclib', 'abemaciclib',  # CDK4/6
        'sunitinib', 'sorafenib', 'pazopanib', 'axitinib', 'lenvatinib', 'cabozantinib',  # 多靶点TKI
        'everolimus', 'temsirolimus',  # mTOR
        'vemurafenib',  # BRAF
        'regorafenib', 'tasocitinib',  # 多靶点
        'plerixafor', 'ruxolitinib',  # JAK
        'midostaurin', 'gilteritinib',  # FLT3
        'venetoclax', 'navitoclax',  # BCL-2
        'enasidenib', 'ivosidenib',  # IDH
        'larotrectinib', 'entrectinib',  # NTRK
        'selpercatinib', 'pralsetinib',  # RET
        'capmatinib', 'tepotinib',  # MET
        'erdafitinib',  # FGFR
        'pemigatinib', 'infigratinib', 'futibatinib',  # FGFR
        'sitravatinib',  # RTK
        'taletrectinib',  # NTRK
    ]
    
    # 采集每个年代
    for period in collection_periods:
        print(f"\n{'=' * 100}")
        print(f"采集时期: {period['name']}")
        print(f"日期范围: {period['start_date']} - {period['end_date']}")
        print(f"关键词数量: {len(period['keywords'])}")
        print("=" * 100)
        
        period_collected = 0
        
        # 分批采集（每批100条）
        skip = 0
        batch_size = 100
        max_records_per_period = 500  # 每个时期最多采集500条
        
        while period_collected < max_records_per_period:
            try:
                # 构建查询 - 注意FDA API字段需要完整路径
                query_parts = period['keywords'][:20]  # 限制关键词数量避免查询过长
                query = ' OR '.join(query_parts)
                # 使用完整的字段路径 submissions.submission_status_date
                query += f' AND submissions.submission_status_date:[{period["start_date"]} TO {period["end_date"]}]'
                
                # 发送API请求
                params = {
                    'search': query,
                    'skip': skip,
                    'limit': batch_size
                }
                
                print(f"  采集批次: skip={skip}, limit={batch_size}")
                
                response = requests.get(
                    'https://api.fda.gov/drug/drugsfda.json',
                    params=params,
                    timeout=60
                )
                
                if response.status_code != 200:
                    logger.error(f"API请求失败: {response.status_code}")
                    break
                
                data = response.json()
                
                if 'results' not in data or not data['results']:
                    print(f"  该批次无更多数据，停止采集")
                    break
                
                # 解析数据
                batch_drugs = collector.parse_drug_data(data)
                
                if not batch_drugs:
                    print(f"  该批次无有效抗肿瘤药物")
                    skip += batch_size
                    period_collected += batch_size
                    time.sleep(1)
                    continue
                
                # 处理每条药物
                for drug in batch_drugs:
                    try:
                        # 翻译
                        drug = collector.translate_drug_data(drug)
                        
                        # 按适应症拆分
                        split_drugs = collector.split_by_indication(drug)
                        
                        # 保存
                        for split_drug in split_drugs:
                            success = collector.save_to_database(split_drug)
                            if success:
                                total_added += 1
                            else:
                                total_duplicates += 1
                            
                            total_collected += 1
                        
                    except Exception as e:
                        logger.warning(f"处理药物失败: {e}")
                
                print(f"  本批次处理: {len(batch_drugs)} 条药物记录")
                period_collected += len(batch_drugs)
                
                # 添加延迟
                time.sleep(1)
                
                # 更新skip
                skip += batch_size
                
            except Exception as e:
                logger.error(f"采集批次失败: {e}")
                break
    
    # 额外采集：使用重要药物名称直接搜索（不分年代）
    print(f"\n{'=' * 100}")
    print("补充采集: 重要靶向药物名称直接搜索")
    print("=" * 100)
    
    batch_size = 10
    for i in range(0, len(important_keywords), batch_size):
        keyword_batch = important_keywords[i:i+batch_size]
        query = ' OR '.join(keyword_batch)
        
        try:
            params = {
                'search': query,
                'skip': 0,
                'limit': 100
            }
            
            print(f"  搜索关键词批次 {i//batch_size + 1}: {len(keyword_batch)} 个药物")
            
            response = requests.get(
                'https://api.fda.gov/drug/drugsfda.json',
                params=params,
                timeout=60
            )
            
            if response.status_code == 200:
                data = response.json()
                if 'results' in data and data['results']:
                    batch_drugs = collector.parse_drug_data(data)
                    for drug in batch_drugs:
                        try:
                            drug = collector.translate_drug_data(drug)
                            split_drugs = collector.split_by_indication(drug)
                            for split_drug in split_drugs:
                                success = collector.save_to_database(split_drug)
                                if success:
                                    total_added += 1
                                else:
                                    total_duplicates += 1
                                total_collected += 1
                        except Exception as e:
                            logger.warning(f"处理药物失败: {e}")
                    
                    print(f"    处理: {len(batch_drugs)} 条")
            
            time.sleep(1)
            
        except Exception as e:
            logger.error(f"补充采集失败: {e}")
    
    end_time = datetime.now()
    duration = (end_time - start_time).total_seconds()
    
    print(f"\n{'=' * 100}")
    print("采集完成！")
    print(f"总耗时: {duration:.1f} 秒 ({duration/60:.1f} 分钟)")
    print(f"总采集记录: {total_collected}")
    print(f"新增记录: {total_added}")
    print(f"重复记录: {total_duplicates}")
    print("=" * 100)
    
    # 验证采集结果
    print(f"\n{'=' * 100}")
    print("验证采集结果")
    print("=" * 100)
    
    db_path = os.path.join(current_dir, 'data', 'medical_info.db')
    db_manager = init_database(db_path)
    
    total_drugs = db_manager.get_record_count('approved_drugs')
    fda_drugs = db_manager.execute_query(
        "SELECT COUNT(*) as count FROM approved_drugs WHERE regulatory_agency = 'FDA'"
    )
    fda_count = fda_drugs[0]['count'] if fda_drugs else 0
    
    print(f"数据库中FDA药物总数: {fda_count}")
    print(f"数据库中总药物数: {total_drugs}")
    
    # 显示日期分布
    date_distribution = db_manager.execute_query(
        """
        SELECT 
            substr(approval_date, 1, 4) as year,
            COUNT(*) as count 
        FROM approved_drugs 
        WHERE regulatory_agency = 'FDA' 
          AND approval_date IS NOT NULL
        GROUP BY substr(approval_date, 1, 4)
        ORDER BY year DESC
        """
    )
    
    print(f"\nFDA药物年份分布:")
    for row in date_distribution[:15]:  # 显示前15年
        print(f"  {row['year']}年: {row['count']} 条")
    
    return {
        'total_collected': total_collected,
        'total_added': total_added,
        'total_duplicates': total_duplicates,
        'duration': duration,
        'fda_count': fda_count
    }


if __name__ == "__main__":
    try:
        result = collect_fda_anticancer_drugs_comprehensive()
        print("\n✅ 系统性采集成功完成！")
    except Exception as e:
        logger.error(f"采集失败: {e}")
        import traceback
        traceback.print_exc()
        print(f"\n❌ 采集失败: {e}")
