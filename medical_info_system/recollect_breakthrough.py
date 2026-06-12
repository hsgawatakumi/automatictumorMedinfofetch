#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
修复突破性治疗数据 - 采集所有页面
注意：这需要较长时间运行（可能需要30-60分钟）
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
        logging.FileHandler('data/cde_recollection.log', encoding='utf-8'),
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
    if not indication or indication.strip() == "":
        return False
    indication_lower = indication.lower()
    for keyword in CANCER_KEYWORDS:
        if keyword.lower() in indication_lower:
            return True
    return False


def get_drug_indication(page: Page, list_type: str, row_idx: int) -> str:
    indication = ""

    try:
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
                
                let detailTable = null;
                if (listType === '优先审评') {
                    const tables = document.querySelectorAll('table');
                    for (let i = 0; i < tables.length; i++) {
                        const tableText = tables[i].innerText;
                        if (tableText.indexOf('优先审评公示详细信息') >= 0) {
                            detailTable = tables[i];
                            break;
                        }
                    }
                } else if (listType === '突破性治疗') {
                    const tables = document.querySelectorAll('table');
                    for (let i = 0; i < tables.length; i++) {
                        const tableText = tables[i].innerText;
                        if (tableText.indexOf('突破性治疗申请公示详细信息') >= 0) {
                            detailTable = tables[i];
                            break;
                        }
                    }
                }
                
                if (detailTable) {
                    const rows = detailTable.querySelectorAll('tr');
                    for (let i = 0; i < rows.length; i++) {
                        const rowText = rows[i].innerText;
                        if (rowText.indexOf('拟定适应症') >= 0 || rowText.indexOf('功能主治') >= 0 || rowText.indexOf('适应症') >= 0) {
                            const cells = rows[i].querySelectorAll('td, th');
                            for (let j = 0; j < cells.length; j++) {
                                const cellText = cells[j].innerText.trim();
                                if (cellText.indexOf('拟定适应症') < 0 && 
                                    cellText.indexOf('功能主治') < 0 && 
                                    cellText.indexOf('适应症') < 0 &&
                                    cellText.length > 5) {
                                    indication = cellText;
                                    break;
                                }
                            }
                            if (!indication && i + 1 < rows.length) {
                                const nextCells = rows[i + 1].querySelectorAll('td');
                                for (let j = 0; j < nextCells.length; j++) {
                                    const cellText = nextCells[j].innerText.trim();
                                    if (cellText.length > 5) {
                                        indication = cellText;
                                        break;
                                    }
                                }
                            }
                            if (indication) break;
                        }
                    }
                }
                
                if (!indication || indication === '理由及依据') {
                    const allText = document.body.innerText;
                    const indicationKeywords = ['拟定适应症', '功能主治', '适应症：', '适应症:', '拟用于'];
                    
                    for (const keyword of indicationKeywords) {
                        const idx = allText.indexOf(keyword);
                        if (idx >= 0) {
                            let text = allText.substring(idx + keyword.length);
                            const stopChars = ['\\n\\n', '\\n', '理由', '审评结论', '备注', '主要研究'];
                            let minIdx = text.length;
                            for (const char of stopChars) {
                                const charIdx = text.indexOf(char);
                                if (charIdx >= 0 && charIdx < minIdx) {
                                    minIdx = charIdx;
                                }
                            }
                            text = text.substring(0, minIdx).trim();
                            
                            if (text.length > 5 && text !== '理由及依据') {
                                indication = text;
                                break;
                            }
                        }
                    }
                }
                
                if (indication) {
                    const stopWords = ['理由及依据', '审评结论', '品种基本信息', '主要研究结果', '备注', '无'];
                    for (const word of stopWords) {
                        const idx = indication.indexOf(word);
                        if (idx > 0 && indication.length - idx < 100) {
                            indication = indication.substring(0, idx);
                        }
                    }
                    indication = indication.trim();
                    
                    if (indication.length > 500) {
                        indication = indication.substring(0, 500);
                    }
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


def collect_breakthrough_drugs(target_count=250):
    """采集突破性治疗药物数据"""
    drugs = []
    
    with sync_playwright() as p:
        logger.info("启动浏览器...")
        browser = p.chromium.launch(
            headless=False,
            slow_mo=300,
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
            
            logger.info("点击菜单...")
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
            
            page_num = 1
            total_collected = 0
            
            while total_collected < target_count:
                logger.info(f"第 {page_num} 页 (已收集 {total_collected}/{target_count})")
                
                # 获取表格数据 - 使用修复后的列索引
                tables_info = page.evaluate("""
                    () => {
                        const tables = document.querySelectorAll('table');
                        for (let i = 0; i < tables.length; i++) {
                            const rows = tables[i].querySelectorAll('tr');
                            if (rows.length > 5) {
                                const header = rows[0].innerText;
                                if (header.indexOf('序号') >= 0 && header.indexOf('药品名称') >= 0) {
                                    // 突破性治疗表格：序号,受理号,药品名称,注册申请人,申请日期,...
                                    const rowData = [];
                                    for (let j = 1; j < rows.length; j++) {
                                        const cells = rows[j].querySelectorAll('td');
                                        if (cells.length >= 5) {
                                            rowData.push({
                                                seq: cells[0]?.innerText?.trim() || '',
                                                acceptance: cells[1]?.innerText?.trim() || '',
                                                drugName: cells[2]?.innerText?.trim() || '',
                                                applicant: cells[3]?.innerText?.trim() || '',
                                                appDate: cells[4]?.innerText?.trim() || ''  // 申请日期在cells[4]
                                            });
                                        }
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
                    
                    for idx, item in enumerate(row_data):
                        if total_collected >= target_count:
                            break
                            
                        logger.info(f"采集 {idx + 1}/{len(row_data)}: {item['drugName']}")
                        
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
                        total_collected += 1
                        
                        time.sleep(1)
                
                # 翻页
                if total_collected < target_count:
                    clicked = page.evaluate("""
                        () => {
                            const links = document.querySelectorAll('a');
                            for (let link of links) {
                                if (link.textContent.trim() === '下一页') {
                                    link.click();
                                    return true;
                                }
                            }
                            return false;
                        }
                    """)
                    
                    if not clicked:
                        logger.info("没有更多页了")
                        break
                    
                    time.sleep(3)
                    page_num += 1
                else:
                    break
            
            logger.info(f"采集完成: {len(drugs)} 条")
            
        except Exception as e:
            logger.error(f"采集失败: {e}")
            import traceback
            traceback.print_exc()
        finally:
            browser.close()
    
    return drugs


def main():
    """主函数"""
    logger.info("开始重新采集突破性治疗数据...")
    logger.info("警告：这可能需要30-60分钟")
    
    # 采集突破性治疗数据
    breakthrough_drugs = collect_breakthrough_drugs(target_count=250)
    
    if breakthrough_drugs:
        # 读取优先审评数据
        priority_drugs = []
        if os.path.exists('data/cde_all_drugs_fixed.csv'):
            with open('data/cde_all_drugs_fixed.csv', 'r', encoding='utf-8-sig') as f:
                reader = csv.DictReader(f)
                for row in reader:
                    if row.get('名单类型') == '优先审评':
                        priority_drugs.append(row)
        
        logger.info(f"优先审评数据: {len(priority_drugs)} 条")
        logger.info(f"突破性治疗数据: {len(breakthrough_drugs)} 条")
        
        # 合并数据
        all_drugs = priority_drugs + breakthrough_drugs
        
        # 保存完整数据
        with open('data/cde_all_drugs_fixed_v2.csv', 'w', newline='', encoding='utf-8-sig') as f:
            writer = csv.DictWriter(f, fieldnames=[
                '名单类型', '序号', '药物名称', '受理号', '申请人',
                '申请日期', '拟定适应症', '是否抗肿瘤'
            ])
            writer.writeheader()
            writer.writerows(all_drugs)
        
        logger.info("完整数据已保存到: data/cde_all_drugs_fixed_v2.csv")
        
        # 筛选抗肿瘤药物
        anticancer_drugs = [d for d in all_drugs if d.get('是否抗肿瘤') == 'True']
        
        with open('data/cde_anticancer_drugs_fixed_v2.csv', 'w', newline='', encoding='utf-8-sig') as f:
            writer = csv.DictWriter(f, fieldnames=[
                '名单类型', '序号', '药物名称', '受理号', '申请人',
                '申请日期', '拟定适应症', '是否抗肿瘤'
            ])
            writer.writeheader()
            writer.writerows(anticancer_drugs)
        
        logger.info(f"抗肿瘤药物已保存: {len(anticancer_drugs)} 条")
        
        # 更新数据库
        from src.database import init_database
        db = init_database('data/medical_info.db')
        
        conn = db.connect()
        cursor = conn.cursor()
        cursor.execute("DELETE FROM cde_special_drugs")
        conn.commit()
        
        count = 0
        for drug in anticancer_drugs:
            record = {
                'cde_id': f"CDE-{drug['名单类型'][:2]}-{drug['序号']}",
                'drug_name': drug['药物名称'],
                'drug_type': drug['名单类型'],
                'indication': drug['拟定适应症'],
                'applicant': drug['申请人'],
                'application_date': drug['申请日期'],
                'acceptance_number': drug['受理号'],
                'approval_date': '',
                'status': '已纳入',
                'priority_type': drug['名单类型'] if drug['名单类型'] == '优先审评' else '',
                'breakthrough_type': drug['名单类型'] if drug['名单类型'] == '突破性治疗' else '',
                'trial_info': '',
                'molecular_target': '',
                'gene_marker': '',
                'reference_drug': '',
                'description': '',
                'detail_url': CDE_BASE_URL,
                'created_at': datetime.now().strftime('%Y-%m-%d'),
                'updated_at': datetime.now().strftime('%Y-%m-%d')
            }
            
            try:
                db.execute_insert('cde_special_drugs', record)
                count += 1
            except Exception as e:
                logger.error(f"插入失败: {drug['药物名称']} - {e}")
        
        logger.info(f"数据库更新完成: {count} 条记录")
        
        # 统计
        breakthrough_anticancer = sum(1 for d in anticancer_drugs if d.get('名单类型') == '突破性治疗')
        priority_anticancer = sum(1 for d in anticancer_drugs if d.get('名单类型') == '优先审评')
        
        logger.info(f"\n统计:")
        logger.info(f"  突破性治疗抗肿瘤: {breakthrough_anticancer} 条")
        logger.info(f"  优先审评抗肿瘤: {priority_anticancer} 条")
        logger.info(f"  总计: {len(anticancer_drugs)} 条")
        
        logger.info("\n完成！请重新导出Excel文件查看修复后的数据。")
    else:
        logger.error("采集失败")


if __name__ == '__main__':
    main()
