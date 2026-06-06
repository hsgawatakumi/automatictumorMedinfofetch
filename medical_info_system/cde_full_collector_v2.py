#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
CDE完整数据采集脚本 - 改进版v2
修复JavaScript错误、改进弹窗提取、增强抗肿瘤识别
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
        logging.FileHandler('data/cde_collection_v2.log', encoding='utf-8'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# CDE URL
CDE_BASE_URL = "https://www.cde.org.cn/main/xxgk/listpage/b40868b5e21c038a6aa8b4319d21b07d"

# 扩展的抗肿瘤关键词
CANCER_KEYWORDS = [
    # 肿瘤类型
    '癌', '肿瘤', '白血病', '淋巴瘤', '肉瘤', '骨髓瘤', '瘤',
    '肺癌', '非小细胞肺癌', 'NSCLC', 'SCLC', '小细胞肺癌',
    '乳腺癌', '肝癌', '胃癌', '结直肠癌', '胰腺癌', '食管癌', '胆管癌',
    '肾癌', '膀胱癌', '前列腺癌', '睾丸癌',
    '卵巢癌', '宫颈癌', '子宫内膜癌', '子宫癌',
    '黑色素瘤', '脑癌', '胶质瘤', '头颈癌', '鼻咽癌', '甲状腺癌',
    'B细胞恶性肿瘤', 'MM', 'CLL', 'CML', 'MDS',
    '尿路上皮癌', '膀胱癌', '肾盂癌', '输尿管癌',
    # 靶点
    'EGFR', 'ALK', 'ROS1', 'RET', 'MET', 'HER2', 'ERBB2', 'PD-1', 'PD-L1',
    'BCMA', 'CD38', 'CD20', 'VEGFR', 'FGFR', 'NTRK', 'KRAS', 'BRAF', 'MEK',
    'CDK4', 'CDK6', 'PIK3CA', 'PTEN', 'BRCA',
    # 药物类型
    '单抗', '抗体', 'ADC', '免疫治疗', 'TKI', '抑制剂',
    # 其他关键词
    '腺癌', '鳞癌', '神经内分泌瘤', '实体瘤', '转移性', '晚期',
    '间皮瘤', '皮肤癌', '骨肉瘤', '尤文肉瘤', '脂肪肉瘤',
    '胃肠道间质瘤', 'GIST', '壶腹癌', '十二指肠癌'
]

def is_cancer_drug(indication: str) -> bool:
    if not indication or indication.strip() == "":
        # 如果没有适应症，根据药物名称判断
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
        logger.info("启动Chromium浏览器...")
        browser = p.chromium.launch(
            headless=False,  # 有头模式
            slow_mo=200,     # 放慢操作
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
        logger.info("\n" + "="*70)
        logger.info("第一部分：采集突破性治疗公示（200条）")
        logger.info("="*70)
        breakthrough_drugs = collect_single_tab(page, "突破性治疗公示", "突破性治疗", target_count=200)
        all_drugs.extend(breakthrough_drugs)
        logger.info(f"突破性治疗采集完成: {len(breakthrough_drugs)} 条")
        
        time.sleep(3)
        
        # 采集优先审评公示
        logger.info("\n" + "="*70)
        logger.info("第二部分：采集优先审评公示（200条）")
        logger.info("="*70)
        priority_drugs = collect_single_tab(page, "优先审评公示", "优先审评", target_count=200)
        all_drugs.extend(priority_drugs)
        logger.info(f"优先审评采集完成: {len(priority_drugs)} 条")
        
        browser.close()
    
    print("\n" + "="*70)
    print("✅ 所有目标采集工作已完成！")
    print(f"   总计采集: {len(all_drugs)} 条药物信息")
    cancer_drugs = [d for d in all_drugs if d['是否抗肿瘤']]
    print(f"   其中抗肿瘤药物: {len(cancer_drugs)} 条")
    print("="*70)
    
    return all_drugs

def collect_single_tab(page: Page, tab_text: str, list_type: str, target_count: int):
    """采集单个tab的数据"""
    drugs = []
    
    # 导航到页面
    logger.info(f"导航到: {CDE_BASE_URL}")
    page.goto(CDE_BASE_URL, wait_until="domcontentloaded", timeout=60000)
    time.sleep(5)  # 等待JS执行
    
    # 点击对应tab
    logger.info(f"点击tab: {tab_text}")
    
    # 多次尝试点击
    for attempt in range(3):
        try:
            # 方法1：使用Playwright选择器
            try:
                link = page.locator(f'text="{tab_text}"').first
                if link.is_visible():
                    link.click()
                    time.sleep(3)
                    logger.info(f"  使用Playwright locators成功点击")
                    break
            except:
                pass
            
            # 方法2：使用JavaScript点击
            try:
                js_code = f"""
                function findAndClick() {{
                    var elements = document.querySelectorAll('*');
                    for (var i = 0; i < elements.length; i++) {{
                        var elem = elements[i];
                        if (elem.textContent.trim() === '{tab_text}' && elem.offsetParent !== null) {{
                            elem.click();
                            return true;
                        }}
                    }}
                    return false;
                }}
                findAndClick();
                """
                result = page.evaluate(js_code)
                if result:
                    time.sleep(3)
                    logger.info(f"  使用JavaScript成功点击")
                    break
            except Exception as e:
                logger.error(f"  JavaScript点击失败: {e}")
                
        except Exception as e:
            logger.error(f"  点击tab尝试 {attempt+1} 失败: {e}")
        
        if attempt < 2:
            time.sleep(2)
    
    # 采集多页
    page_num = 1
    total_collected = 0
    
    while total_collected < target_count:
        logger.info(f"  第 {page_num} 页 (已收集 {total_collected}/{target_count})")
        
        try:
            # 等待表格
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
            break
    
    print_progress_bar(total_collected, target_count, 
                      prefix=f'  采集{list_type}:',
                      suffix=f'({total_collected}/{target_count}) 完成!')
    
    return drugs

def extract_page_data(page: Page, list_type: str, start_num: int) -> list:
    """提取当前页的所有数据"""
    drugs = []
    
    try:
        rows = page.query_selector_all("table tbody tr")
        logger.info(f"    找到 {len(rows)} 行")
        
        for i, row in enumerate(rows):
            try:
                cells = row.query_selector_all("td")
                if len(cells) < 5:
                    continue
                
                # 列顺序: 序号(0) | 受理号(1) | 药物名称(2) | 申请人(3) | 申请日期(4)
                seq = cells[0].inner_text().strip()
                acceptance = cells[1].inner_text().strip()
                drug_name = cells[2].inner_text().strip()
                applicant = cells[3].inner_text().strip()
                app_date = cells[4].inner_text().strip()
                
                # 获取详细适应症
                indication = get_drug_indication_from_modal(page, cells[2])
                
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
                
                if (i + 1) % 10 == 0:
                    logger.info(f"      处理 {i+1}/{len(rows)}: {drug_name}")
                
                time.sleep(0.5)
                
            except Exception as e:
                logger.error(f"    提取第 {i+1} 行失败: {e}")
                continue
    
    except Exception as e:
        logger.error(f"提取页面数据失败: {e}")
    
    return drugs

def get_drug_indication_from_modal(page: Page, drug_name_cell) -> str:
    """从弹窗中获取适应症"""
    indication = ""
    
    try:
        # 点击药物名称链接
        link = drug_name_cell.query_selector("a")
        if link:
            link.click()
            time.sleep(1.5)
            
            # 查找弹窗
            modal = None
            for selector in ['.ant-modal-content', '.modal-content', '[role="dialog"]']:
                try:
                    modal = page.query_selector(selector)
                    if modal and modal.is_visible():
                        break
                except:
                    continue
            
            if modal:
                # 获取弹窗文本
                modal_text = modal.inner_text()
                
                # 查找拟定适应症
                lines = modal_text.split('\n')
                for i, line in enumerate(lines):
                    line = line.strip()
                    if '拟定适应症' in line or '功能主治' in line:
                        # 找后续行作为适应症内容
                        if i + 1 < len(lines):
                            indication_parts = []
                            for j in range(i + 1, len(lines)):
                                next_line = lines[j].strip()
                                # 跳过标题类内容
                                if any(kw in next_line for kw in ['受理号', '申请人', '申请日期', '拟定适应症', '功能主治']):
                                    break
                                if next_line:
                                    indication_parts.append(next_line)
                            indication = ' '.join(indication_parts)
                            break
                
                # 关闭弹窗
                try:
                    close_btn = modal.query_selector('.ant-modal-close, button.close, [aria-label="close"]')
                    if close_btn:
                        close_btn.click()
                    else:
                        page.keyboard.press("Escape")
                except:
                    page.keyboard.press("Escape")
                
                time.sleep(0.5)
        
    except Exception as e:
        logger.error(f"获取弹窗详情失败: {e}")
        try:
            page.keyboard.press("Escape")
            time.sleep(0.3)
        except:
            pass
    
    return indication

def click_next_page(page: Page) -> bool:
    """点击下一页"""
    try:
        # 尝试多种选择器
        selectors = [
            'button:text-is("下一页")',
            'button:has-text("下一页")',
            '.ant-pagination-next:not([disabled])'
        ]
        
        for selector in selectors:
            try:
                btn = page.query_selector(selector)
                if btn and not btn.is_disabled():
                    btn.click()
                    return True
            except:
                continue
        
        # 尝试直接点击页码
        try:
            current_page = 1
            active = page.query_selector('.ant-pagination-item-active')
            if active:
                current_page = int(active.inner_text())
            
            next_page_btn = page.query_selector(f'.ant-pagination-item:text("{current_page + 1}")')
            if next_page_btn:
                next_page_btn.click()
                return True
        except:
            pass
        
        return False
    
    except Exception as e:
        logger.error(f"翻页失败: {e}")
        return False

def save_csv_and_update_db(drugs: list):
    """保存CSV并更新数据库"""
    if not drugs:
        logger.warning("没有数据可保存")
        return
    
    # 保存全部数据
    all_csv_path = 'data/cde_all_drugs_v2.csv'
    os.makedirs(os.path.dirname(all_csv_path), exist_ok=True)
    
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
        cancer_csv_path = 'data/cde_anticancer_drugs_v2.csv'
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
        from src.database import DatabaseManager, init_database
        
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

def main():
    logger.info("="*70)
    logger.info("CDE特殊品种完整数据采集程序 v2")
    logger.info("="*70)
    
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
