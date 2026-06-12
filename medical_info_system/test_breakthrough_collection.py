#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试突破性治疗数据采集 - 只采集前5条来验证修复是否有效
"""

import os
import sys
import csv
import time
import logging
from datetime import datetime
from playwright.sync_api import sync_playwright, Page

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('data/test_breakthrough.log', encoding='utf-8'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

CDE_BASE_URL = "https://www.cde.org.cn/main/xxgk/listpage/2f78f372d351c6851af7431c7710a731"

CANCER_KEYWORDS = [
    '癌', '肿瘤', '白血病', '淋巴瘤', '肉瘤', '骨髓瘤', '瘤',
    '肺癌', '非小细胞肺癌', 'NSCLC', 'SCLC', '小细胞肺癌',
    '乳腺癌', '肝癌', '胃癌', '结直肠癌', '胰腺癌', '食管癌', '胆管癌',
    '肾癌', '膀胱癌', '前列腺癌', '睾丸癌',
    '卵巢癌', '宫颈癌', '子宫内膜癌', '子宫癌',
    '黑色素瘤', '脑癌', '胶质瘤', '头颈癌', '鼻咽癌', '甲状腺癌',
    'B细胞恶性肿瘤', 'MM', 'CLL', 'CML', 'MDS',
    '尿路上皮癌', '肾盂癌', '输尿管癌',
    'EGFR', 'ALK', 'ROS1', 'RET', 'MET', 'HER2', 'ERBB2', 'PD-1', 'PD-L1',
    'BCMA', 'CD38', 'CD20', 'VEGFR', 'FGFR', 'NTRK', 'KRAS', 'BRAF', 'MEK',
    'CDK4', 'CDK6', 'PIK3CA', 'PTEN', 'BRCA',
    '单抗', '抗体', 'ADC', '免疫治疗', 'TKI', '抑制剂',
    '腺癌', '鳞癌', '神经内分泌瘤', '实体瘤', '转移性', '晚期',
    '间皮瘤', '皮肤癌', '骨肉瘤', '尤文肉瘤', '脂肪肉瘤',
    '胃肠道间质瘤', 'GIST', '壶腹癌', '十二指肠癌',
    '胆道癌', 'IDH1', 'IDH2'
]


def is_cancer_drug(indication: str) -> bool:
    """判断是否为抗肿瘤药物"""
    if not indication or indication.strip() == "":
        return False
    indication_lower = indication.lower()
    for keyword in CANCER_KEYWORDS:
        if keyword.lower() in indication_lower:
            return True
    return False


def get_drug_indication(page: Page, list_type: str, row_idx: int) -> str:
    """从弹窗中获取适应症 - 使用改进的逻辑"""
    indication = ""

    try:
        # 使用 JS 双击行并获取详情
        page.evaluate("""
            ([listType, rowIdx]) => {
                const tables = document.querySelectorAll('table');
                let dataTable = null;
                
                for (let i = 0; i < tables.length; i++) {
                    const rows = tables[i].querySelectorAll('tr');
                    if (rows.length > 5) {
                        const header = rows[0].innerText;
                        if (header.indexOf('序号') >= 0 && header.indexOf('药品名称') >= 0) {
                            dataTable = { table: tables[i], index: i };
                            break;
                        }
                    }
                }
                
                if (!dataTable) return { success: false };
                
                const rows = dataTable.table.querySelectorAll('tr');
                if (rowIdx >= rows.length) return { success: false };
                
                const targetRow = rows[rowIdx];
                const dblClickEvent = new MouseEvent('dblclick', {
                    view: window,
                    bubbles: true,
                    cancelable: true
                });
                targetRow.dispatchEvent(dblClickEvent);
                
                return { success: true };
            }
        """, [list_type, row_idx])

        time.sleep(3)

        detail = page.evaluate("""
            ([listType]) => {
                let indication = '';
                
                const allText = document.body.innerText;
                const indicationKeywords = ['拟定适应症', '功能主治', '适应症', '拟用于'];
                
                for (const keyword of indicationKeywords) {
                    const regex = new RegExp(keyword + '[\\\\s\\\\S]{0,1000}');
                    const match = allText.match(regex);
                    if (match) {
                        let text = match[0];
                        text = text.substring(keyword.length);
                        text = text.trim();
                        
                        const uselessPrefixes = ['：', ':', ' ', '\\\\n', '\\\\t'];
                        for (const prefix of uselessPrefixes) {
                            if (text.startsWith(prefix)) {
                                text = text.substring(prefix.length).trim();
                            }
                        }
                        
                        if (text.length > 5 && !['理由及依据', '无', ''].includes(text)) {
                            if (text.length > 500) {
                                text = text.substring(0, 500);
                            }
                            indication = text;
                            break;
                        }
                    }
                }
                
                if (!indication) {
                    const tables = document.querySelectorAll('table');
                    for (let i = 0; i < tables.length; i++) {
                        const tableText = tables[i].innerText;
                        if (tableText.indexOf('拟定适应症') >= 0 || tableText.indexOf('功能主治') >= 0) {
                            const rows = tables[i].querySelectorAll('tr');
                            for (let j = 0; j < rows.length; j++) {
                                const rowText = rows[j].innerText;
                                if (rowText.indexOf('拟定适应症') >= 0 || rowText.indexOf('功能主治') >= 0) {
                                    const cells = rows[j].querySelectorAll('td');
                                    for (let k = 0; k < cells.length; k++) {
                                        const cellText = cells[k].innerText.trim();
                                        if (cellText.indexOf('拟定适应症') < 0 && 
                                            cellText.indexOf('功能主治') < 0 && 
                                            cellText.length > 5) {
                                            indication = cellText;
                                            break;
                                        }
                                    }
                                    if (!indication && j + 1 < rows.length) {
                                        const nextCells = rows[j + 1].querySelectorAll('td');
                                        for (let k = 0; k < nextCells.length; k++) {
                                            const cellText = nextCells[k].innerText.trim();
                                            if (cellText.length > 5) {
                                                indication = cellText;
                                                break;
                                            }
                                        }
                                    }
                                }
                            }
                            if (indication) break;
                        }
                    }
                }
                
                if (indication) {
                    const stopWords = ['理由及依据', '审评结论', '品种基本信息', '主要研究结果', '备注'];
                    for (const word of stopWords) {
                        const idx = indication.indexOf(word);
                        if (idx > 0) {
                            indication = indication.substring(0, idx);
                        }
                    }
                    indication = indication.trim();
                }
                
                try {
                    if (typeof layer !== 'undefined' && layer.closeAll) {
                        layer.closeAll();
                    }
                } catch (e) {}
                
                return { success: true, indication: indication };
            }
        """, [list_type])

        if detail.get('success'):
            indication = detail.get('indication', '')
            
        time.sleep(0.5)

    except Exception as e:
        logger.error(f"获取弹窗详情失败: {e}")

    return indication


def test_collection():
    """测试采集突破性治疗的前5条数据"""
    drugs = []
    
    with sync_playwright() as p:
        logger.info("启动浏览器...")
        browser = p.chromium.launch(
            headless=False,
            slow_mo=500,
            args=['--disable-blink-features=AutomationControlled', '--no-sandbox']
        )
        
        context = browser.new_context(
            viewport={'width': 1920, 'height': 1080},
            user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            locale='zh-CN',
            timezone_id='Asia/Shanghai'
        )
        
        page = context.new_page()
        
        try:
            logger.info(f"访问: {CDE_BASE_URL}")
            page.goto(CDE_BASE_URL, wait_until="domcontentloaded", timeout=60000)
            time.sleep(5)
            
            logger.info("点击菜单: 突破性治疗公示 -> 纳入突破性治疗品种名单")
            
            page.evaluate("""
                () => {
                    const menuItems = document.querySelectorAll('li');
                    for (let item of menuItems) {
                        if (item.textContent.trim() === '突破性治疗公示') {
                            item.click();
                            break;
                        }
                    }
                }
            """)
            time.sleep(2)
            
            page.evaluate("""
                () => {
                    const menuItems = document.querySelectorAll('li');
                    for (let item of menuItems) {
                        if (item.textContent.trim() === '纳入突破性治疗品种名单') {
                            item.click();
                            break;
                        }
                    }
                }
            """)
            time.sleep(5)
            
            logger.info("获取表格数据...")
            tables_info = page.evaluate("""
                () => {
                    const tables = document.querySelectorAll('table');
                    for (let i = 0; i < tables.length; i++) {
                        const rows = tables[i].querySelectorAll('tr');
                        if (rows.length > 5) {
                            const header = rows[0].innerText;
                            if (header.indexOf('序号') >= 0 && header.indexOf('药品名称') >= 0) {
                                const rowData = [];
                                for (let j = 1; j < Math.min(6, rows.length); j++) {
                                    const cells = rows[j].querySelectorAll('td');
                                    rowData.push({
                                        seq: cells[0]?.innerText?.trim() || '',
                                        acceptance: cells[1]?.innerText?.trim() || '',
                                        drugName: cells[2]?.innerText?.trim() || '',
                                        applicant: cells[3]?.innerText?.trim() || '',
                                        appDate: cells[5]?.innerText?.trim() || ''
                                    });
                                }
                                return { found: true, data: rowData };
                            }
                        }
                    }
                    return { found: false };
                }
            """)
            
            if tables_info.get('found'):
                row_data = tables_info.get('data', [])
                logger.info(f"找到 {len(row_data)} 条数据，开始采集详情...")
                
                for idx, item in enumerate(row_data):
                    logger.info(f"正在采集第 {idx + 1} 条: {item.get('drugName')}")
                    
                    indication = get_drug_indication(page, "突破性治疗", idx + 1)
                    
                    is_cancer = is_cancer_drug(indication)
                    
                    drug_info = {
                        '名单类型': '突破性治疗',
                        '序号': item.get('seq'),
                        '药物名称': item.get('drugName'),
                        '受理号': item.get('acceptance'),
                        '申请人': item.get('applicant'),
                        '申请日期': item.get('appDate'),
                        '拟定适应症': indication,
                        '是否抗肿瘤': is_cancer
                    }
                    
                    drugs.append(drug_info)
                    logger.info(f"  适应症: {indication[:100] if indication else '未获取到'}")
                    logger.info(f"  是否抗肿瘤: {is_cancer}")
                    
                    time.sleep(2)
            
            # 保存测试结果
            os.makedirs('data', exist_ok=True)
            csv_path = 'data/test_breakthrough_results.csv'
            with open(csv_path, 'w', newline='', encoding='utf-8-sig') as f:
                writer = csv.DictWriter(f, fieldnames=[
                    '名单类型', '序号', '药物名称', '受理号', '申请人',
                    '申请日期', '拟定适应症', '是否抗肿瘤'
                ])
                writer.writeheader()
                writer.writerows(drugs)
            
            logger.info(f"测试结果已保存到: {csv_path}")
            logger.info(f"共采集 {len(drugs)} 条数据")
            
            cancer_count = sum(1 for d in drugs if d['是否抗肿瘤'])
            logger.info(f"其中抗肿瘤药物: {cancer_count} 条")
            
            for drug in drugs:
                logger.info(f"  {drug['药物名称']}: {drug['拟定适应症'][:80] if drug['拟定适应症'] else '无适应症'} -> {'是' if drug['是否抗肿瘤'] else '否'}")
            
        except Exception as e:
            logger.error(f"测试失败: {e}")
            import traceback
            traceback.print_exc()
        finally:
            browser.close()
    
    return drugs


if __name__ == '__main__':
    test_collection()

