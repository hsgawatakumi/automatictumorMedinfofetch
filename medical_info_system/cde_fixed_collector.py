#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
CDE 特殊品种完整数据采集脚本 - 修复版
基于实际页面分析，使用正确的双击事件和详情获取方法
"""

import os
import sys
import csv
import time
import logging
from datetime import datetime
from playwright.sync_api import sync_playwright, Page

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('data/cde_collection_fixed.log', encoding='utf-8'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# CDE 统一入口 URL
CDE_BASE_URL = "https://www.cde.org.cn/main/xxgk/listpage/2f78f372d351c6851af7431c7710a731"

# 扩展的抗肿瘤关键词
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


def print_progress_bar(iteration: int, total: int, prefix: str = '', suffix: str = ''):
    """打印进度条"""
    if total == 0:
        total = 1
    percent = ("{0:.1f}").format(100 * (iteration / float(total)))
    filled_length = 50
    bar = '█' * int(50 * iteration // total) + '-' * (50 - int(50 * iteration // total))
    print(f'\r{prefix} |{bar}| {percent}% {suffix}', end='')
    if iteration == total:
        print()


def collect_full_data():
    """采集完整数据"""
    all_drugs = []

    with sync_playwright() as p:
        # 启动浏览器
        logger.info("启动 Chromium 浏览器...")
        browser = p.chromium.launch(
            headless=False,
            slow_mo=300,
            args=['--disable-blink-features=AutomationControlled', '--no-sandbox']
        )

        # 创建上下文
        context = browser.new_context(
            viewport={'width': 1920, 'height': 1080},
            user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            locale='zh-CN',
            timezone_id='Asia/Shanghai'
        )

        page = context.new_page()

        # 采集突破性治疗公示
        logger.info("\n" + "=" * 70)
        logger.info("第一部分：采集纳入突破性治疗品种名单（前250条）")
        logger.info("=" * 70)
        breakthrough_drugs = collect_list(page, "突破性治疗公示", "纳入突破性治疗品种名单", "突破性治疗", target_count=250)
        all_drugs.extend(breakthrough_drugs)
        logger.info(f"突破性治疗采集完成: {len(breakthrough_drugs)} 条，其中抗肿瘤: {len([d for d in breakthrough_drugs if d['是否抗肿瘤']])} 条")

        time.sleep(3)

        # 采集优先审评公示
        logger.info("\n" + "=" * 70)
        logger.info("第二部分：采集纳入优先审评品种名单（前250条）")
        logger.info("=" * 70)
        priority_drugs = collect_list(page, "优先审评公示", "纳入优先审评品种名单", "优先审评", target_count=250)
        all_drugs.extend(priority_drugs)
        logger.info(f"优先审评采集完成: {len(priority_drugs)} 条，其中抗肿瘤: {len([d for d in priority_drugs if d['是否抗肿瘤']])} 条")

        browser.close()

    print("\n" + "=" * 70)
    print("✅ 所有目标采集工作已完成！")
    print(f"   总计采集: {len(all_drugs)} 条药物信息")
    cancer_drugs = [d for d in all_drugs if d['是否抗肿瘤']]
    print(f"   其中抗肿瘤药物: {len(cancer_drugs)} 条")
    print("=" * 70)

    return all_drugs


def collect_list(page: Page, menu_text: str, submenu_text: str, list_type: str, target_count: int):
    """采集单个列表的数据"""
    drugs = []

    # 导航到页面
    logger.info(f"导航到 CDE 页面...")
    page.goto(CDE_BASE_URL, wait_until="domcontentloaded", timeout=60000)
    time.sleep(5)

    # 点击对应菜单
    logger.info(f"点击菜单: {menu_text} -> {submenu_text}")
    try:
        # 使用 JS 查找并点击菜单项
        page.evaluate(f"""
            () => {{
                const menuItems = document.querySelectorAll('li');
                for (let item of menuItems) {{
                    if (item.textContent.trim() === '{menu_text}') {{
                        item.click();
                        break;
                    }}
                }}
            }}
        """)
        time.sleep(2)

        page.evaluate(f"""
            () => {{
                const menuItems = document.querySelectorAll('li');
                for (let item of menuItems) {{
                    if (item.textContent.trim() === '{submenu_text}') {{
                        item.click();
                        break;
                    }}
                }}
            }}
        """)
        time.sleep(3)
    except Exception as e:
        logger.warning(f"点击菜单失败: {e}，尝试继续...")

    # 采集多页
    page_num = 1
    total_collected = 0

    while total_collected < target_count:
        logger.info(f"  第 {page_num} 页 (已收集 {total_collected}/{target_count})")

        try:
            # 等待表格加载
            time.sleep(2)

            # 获取当前页数据
            page_drugs = extract_page_data(page, list_type, total_collected)
            drugs.extend(page_drugs)
            total_collected += len(page_drugs)

            # 更新进度条
            print_progress_bar(total_collected, target_count,
                              prefix=f'  采集{list_type}:',
                              suffix=f'({total_collected}/{target_count}) 第{page_num}页')

            logger.info(f"    本页采集: {len(page_drugs)} 条，总计: {total_collected} 条")

            # 翻页
            if total_collected < target_count:
                if not click_next_page(page):
                    logger.info("    没有更多页了，停止采集")
                    break
                time.sleep(3)
                page_num += 1
            else:
                logger.info("    已达到目标数量，停止采集")
                break

        except Exception as e:
            logger.error(f"    第 {page_num} 页采集失败: {e}")
            import traceback
            traceback.print_exc()
            break

    print_progress_bar(total_collected, target_count,
                      prefix=f'  采集{list_type}:',
                      suffix=f'({total_collected}/{target_count}) 完成!')

    return drugs


def extract_page_data(page: Page, list_type: str, start_num: int) -> list:
    """提取当前页的所有数据"""
    drugs = []

    try:
        # 使用 JS 获取所有数据行的信息 - 根据名单类型使用不同的列索引
        row_info = page.evaluate("""
            (listType) => {
                const tables = document.querySelectorAll('table');
                let dataTable = null;
                
                // 查找有数据的表格（行数 > 5）
                for (let i = 0; i < tables.length; i++) {
                    const rows = tables[i].querySelectorAll('tr');
                    if (rows.length > 5) {
                        const header = rows[0].innerText;
                        if (header.indexOf('序号') >= 0 && header.indexOf('药品名称') >= 0) {
                            // 判断是优先审评还是突破性治疗
                            const isPriority = header.indexOf('承办日期') >= 0;
                            
                            dataTable = { index: i, rows: [], listType: listType, isPriority: isPriority };
                            
                            for (let j = 1; j < rows.length; j++) {
                                const cells = rows[j].querySelectorAll('td');
                                if (cells.length >= 4) {
                                    const rowData = {
                                        index: j,
                                        seq: cells[0]?.innerText?.trim() || '',
                                        acceptance: cells[1]?.innerText?.trim() || '',
                                        drugName: cells[2]?.innerText?.trim() || '',
                                        applicant: cells[3]?.innerText?.trim() || '',
                                        ondblclick: rows[j].getAttribute('ondblclick') || ''
                                    };
                                    
                                    // 根据表格类型确定申请日期的列索引
                                    if (isPriority) {
                                        // 优先审评：序号,受理号,药品名称,注册申请人,承办日期,申请日期,...
                                        // 申请日期在 cells[5]
                                        if (cells.length >= 6) {
                                            rowData.appDate = cells[5]?.innerText?.trim() || '';
                                        }
                                    } else {
                                        // 突破性治疗：序号,受理号,药品名称,注册申请人,申请日期,...
                                        // 申请日期在 cells[4]
                                        if (cells.length >= 5) {
                                            rowData.appDate = cells[4]?.innerText?.trim() || '';
                                        }
                                    }
                                    
                                    dataTable.rows.push(rowData);
                                }
                            }
                            break;
                        }
                    }
                }
                return dataTable;
            }
        """, list_type)

        if not row_info or not row_info.get('rows'):
            logger.warning("    未找到数据表格")
            return []

        logger.info(f"    找到 {len(row_info['rows'])} 条数据")

        for idx, row_data in enumerate(row_info['rows']):
            try:
                seq = row_data.get('seq', '')
                acceptance = row_data.get('acceptance', '')
                drug_name = row_data.get('drugName', '')
                applicant = row_data.get('applicant', '')
                app_date = row_data.get('appDate', '')

                logger.info(f"    处理 {idx + 1}/{len(row_info['rows'])}: {drug_name}")

                # 获取详细适应症
                indication = get_drug_indication(page, list_type, idx + 1)

                # 判断是否抗肿瘤
                is_cancer = is_cancer_drug(indication)

                drug_info = {
                    '名单类型': list_type,
                    '序号': seq,
                    '药物名称': drug_name,
                    '受理号': acceptance,
                    '申请人': applicant,
                    '申请日期': app_date,
                    '拟定适应症': indication,
                    '是否抗肿瘤': is_cancer
                }

                drugs.append(drug_info)
                time.sleep(0.5)

            except Exception as e:
                logger.error(f"    提取第 {idx + 1} 条失败: {e}")
                continue

    except Exception as e:
        logger.error(f"提取页面数据失败: {e}")
        import traceback
        traceback.print_exc()

    return drugs


def get_drug_indication(page: Page, list_type: str, row_idx: int) -> str:
    """从弹窗中获取适应症"""
    indication = ""

    try:
        # 使用 JS 双击行并获取详情
        result = page.evaluate("""
            ([listType, rowIdx]) => {
                const tables = document.querySelectorAll('table');
                let dataTable = null;
                
                // 查找数据表格
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
                
                if (!dataTable) return { success: false, error: '未找到数据表格' };
                
                const rows = dataTable.table.querySelectorAll('tr');
                if (rowIdx >= rows.length) return { success: false, error: '行索引超出范围' };
                
                const targetRow = rows[rowIdx];
                
                // 触发双击事件
                const dblClickEvent = new MouseEvent('dblclick', {
                    view: window,
                    bubbles: true,
                    cancelable: true
                });
                targetRow.dispatchEvent(dblClickEvent);
                
                return { success: true };
            }
        """, [list_type, row_idx])

        # 等待弹窗加载
        time.sleep(3)

        # 提取详情内容 - 改进的逻辑
        detail = page.evaluate("""
            ([listType]) => {
                let indication = '';
                
                // 方法1: 根据名单类型查找对应的详情表格
                let detailTable = null;
                if (listType === '优先审评') {
                    // 优先审评详情表格
                    const tables = document.querySelectorAll('table');
                    for (let i = 0; i < tables.length; i++) {
                        const tableText = tables[i].innerText;
                        if (tableText.indexOf('优先审评公示详细信息') >= 0) {
                            detailTable = tables[i];
                            break;
                        }
                    }
                } else if (listType === '突破性治疗') {
                    // 突破性治疗详情表格
                    const tables = document.querySelectorAll('table');
                    for (let i = 0; i < tables.length; i++) {
                        const tableText = tables[i].innerText;
                        if (tableText.indexOf('突破性治疗申请公示详细信息') >= 0) {
                            detailTable = tables[i];
                            break;
                        }
                    }
                }
                
                // 从详情表格中提取适应症
                if (detailTable) {
                    const rows = detailTable.querySelectorAll('tr');
                    for (let i = 0; i < rows.length; i++) {
                        const rowText = rows[i].innerText;
                        // 查找包含"拟定适应症"或"功能主治"的行
                        if (rowText.indexOf('拟定适应症') >= 0 || rowText.indexOf('功能主治') >= 0 || rowText.indexOf('适应症') >= 0) {
                            const cells = rows[i].querySelectorAll('td, th');
                            for (let j = 0; j < cells.length; j++) {
                                const cellText = cells[j].innerText.trim();
                                // 跳过包含关键字的单元格
                                if (cellText.indexOf('拟定适应症') < 0 && 
                                    cellText.indexOf('功能主治') < 0 && 
                                    cellText.indexOf('适应症') < 0 &&
                                    cellText.length > 5) {
                                    indication = cellText;
                                    break;
                                }
                            }
                            // 如果当前行没找到，检查下一行
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
                
                // 方法2: 如果还没找到，从整个页面文本中查找
                if (!indication || indication === '理由及依据') {
                    const allText = document.body.innerText;
                    const indicationKeywords = ['拟定适应症', '功能主治', '适应症：', '适应症:', '拟用于'];
                    
                    for (const keyword of indicationKeywords) {
                        const idx = allText.indexOf(keyword);
                        if (idx >= 0) {
                            // 提取关键字后的内容
                            let text = allText.substring(idx + keyword.length);
                            // 清理到下一个常见分隔符
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
                
                // 清理最终的适应症文本
                if (indication) {
                    // 移除"理由及依据"等无用内容
                    const stopWords = ['理由及依据', '审评结论', '品种基本信息', '主要研究结果', '备注', '无'];
                    for (const word of stopWords) {
                        const idx = indication.indexOf(word);
                        if (idx > 0 && indication.length - idx < 100) {
                            indication = indication.substring(0, idx);
                        }
                    }
                    indication = indication.trim();
                    
                    // 截断到合理长度
                    if (indication.length > 500) {
                        indication = indication.substring(0, 500);
                    }
                }
                
                // 尝试关闭弹窗
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
        
        # 如果获取到的内容太短或没用，尝试记录但继续
        if not indication or len(indication) < 5 or indication == '理由及依据':
            logger.warning(f"获取到的适应症可能不正确: '{indication}'")
            
        time.sleep(0.5)

    except Exception as e:
        logger.error(f"获取弹窗详情失败: {e}")

    return indication


def click_next_page(page: Page) -> bool:
    """点击下一页"""
    try:
        # 使用 JS 查找并点击下一页
        result = page.evaluate("""
            () => {
                // 查找下一页链接
                const links = document.querySelectorAll('a');
                for (let link of links) {
                    if (link.textContent.trim() === '下一页') {
                        link.click();
                        return { success: true };
                    }
                }
                return { success: false };
            }
        """)

        return result.get('success', False)

    except Exception as e:
        logger.error(f"翻页失败: {e}")
        return False


def save_csv_and_update_db(drugs: list):
    """保存CSV并更新数据库"""
    if not drugs:
        logger.warning("没有数据可保存")
        return

    os.makedirs('data', exist_ok=True)

    # 保存全部数据
    all_csv_path = 'data/cde_all_drugs_fixed.csv'
    with open(all_csv_path, 'w', newline='', encoding='utf-8-sig') as f:
        writer = csv.DictWriter(f, fieldnames=[
            '名单类型', '序号', '药物名称', '受理号', '申请人',
            '申请日期', '拟定适应症', '是否抗肿瘤'
        ])
        writer.writeheader()
        writer.writerows(drugs)

    logger.info(f"全部数据已保存: {all_csv_path}")
    logger.info(f"总计: {len(drugs)} 条")

    # 筛选抗肿瘤药物
    cancer_drugs = [d for d in drugs if d['是否抗肿瘤']]
    logger.info(f"其中抗肿瘤药物: {len(cancer_drugs)} 条")

    # 保存抗肿瘤药物
    if cancer_drugs:
        cancer_csv_path = 'data/cde_anticancer_drugs_fixed.csv'
        with open(cancer_csv_path, 'w', newline='', encoding='utf-8-sig') as f:
            writer = csv.DictWriter(f, fieldnames=[
                '名单类型', '序号', '药物名称', '受理号', '申请人',
                '申请日期', '拟定适应症', '是否抗肿瘤'
            ])
            writer.writeheader()
            writer.writerows(cancer_drugs)

        logger.info(f"抗肿瘤药物已保存: {cancer_csv_path}")
        update_database(cancer_drugs)


def update_database(cancer_drugs: list):
    """更新数据库"""
    try:
        from src.database import init_database

        db_path = 'data/medical_info.db'
        db = init_database(db_path)

        # 清空表
        conn = db.connect()
        cursor = conn.cursor()
        cursor.execute("DELETE FROM cde_special_drugs")
        conn.commit()

        now = datetime.now().strftime('%Y-%m-%d')
        count = 0

        for drug in cancer_drugs:
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
                'created_at': now,
                'updated_at': now
            }

            try:
                db.execute_insert('cde_special_drugs', record)
                count += 1
            except Exception as e:
                logger.error(f"插入失败: {drug['药物名称']} - {e}")

        logger.info(f"\n数据库更新成功: {count} 条记录")

    except Exception as e:
        logger.error(f"数据库更新失败: {e}")
        import traceback
        traceback.print_exc()


def main():
    logger.info("=" * 70)
    logger.info("CDE 特殊品种完整数据采集程序 - 修复版")
    logger.info("=" * 70)

    try:
        all_drugs = collect_full_data()

        if all_drugs:
            save_csv_and_update_db(all_drugs)
        else:
            logger.warning("没有采集到任何数据")

    except KeyboardInterrupt:
        logger.info("\n用户中断采集")
    except Exception as e:
        logger.error(f"\n采集失败: {e}")
        import traceback
        traceback.print_exc()


if __name__ == '__main__':
    main()
