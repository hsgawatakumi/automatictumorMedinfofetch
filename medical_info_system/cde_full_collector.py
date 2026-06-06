#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
CDE完整数据采集脚本 - 带进度条版本
支持突破性治疗公示和优先审评公示两个页面
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
        logging.FileHandler('data/cde_collection.log', encoding='utf-8'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# CDE URL
CDE_BASE_URL = "https://www.cde.org.cn/main/xxgk/listpage/b40868b5e21c038a6aa8b4319d21b07d"

# 抗肿瘤关键词
CANCER_KEYWORDS = [
    '癌', '肿瘤', '白血病', '淋巴瘤', '肉瘤', '骨髓瘤', '瘤',
    '肺癌', '非小细胞肺癌', 'NSCLC', 'SCLC', '小细胞肺癌',
    '乳腺癌', '肝癌', '胃癌', '结直肠癌', '胰腺癌', '食管癌', '胆管癌',
    '肾癌', '膀胱癌', '前列腺癌', '睾丸癌',
    '卵巢癌', '宫颈癌', '子宫内膜癌', '子宫癌',
    '黑色素瘤', '脑癌', '胶质瘤', '头颈癌', '鼻咽癌', '甲状腺癌',
    'B细胞恶性肿瘤', 'MM', 'CLL', 'CML', 'MDS',
    'EGFR', 'ALK', 'ROS1', 'RET', 'MET', 'HER2', 'PD-1', 'PD-L1',
    'BCMA', 'CD38', 'CD20', 'VEGFR', 'FGFR', 'NTRK', 'KRAS', 'BRAF',
    '单抗', '抗体', 'ADC', '免疫治疗',
    '腺癌', '鳞癌', '神经内分泌瘤', '实体瘤', '转移性', '晚期',
    '间皮瘤', '皮肤癌', '骨肉瘤', '尤文肉瘤', '脂肪肉瘤',
    '胃肠道间质瘤', 'GIST', '壶腹癌', '十二指肠癌', '尿路上皮癌'
]

def is_cancer_drug(indication: str) -> bool:
    if not indication:
        return False
    indication_lower = indication.lower()
    for keyword in CANCER_KEYWORDS:
        if keyword.lower() in indication_lower:
            return True
    return False

def print_progress_bar(iteration: int, total: int, prefix: str = '', 
                      suffix: str = '', length: int = 50, fill: str = '█'):
    """打印进度条"""
    percent = ("{0:.1f}").format(100 * (iteration / float(total)))
    filled_length = int(length * iteration // total)
    bar = fill * filled_length + '-' * (length - filled_length)
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
            headless=False,  # 有头模式，方便观察
            slow_mo=150,     # 稍微放慢操作
            args=[
                '--disable-blink-features=AutomationControlled',
                '--no-sandbox'
            ]
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
        
        time.sleep(3)  # 休息
        
        # 采集优先审评公示
        logger.info("\n" + "="*70)
        logger.info("第二部分：采集优先审评公示（200条）")
        logger.info("="*70)
        priority_drugs = collect_single_tab(page, "优先审评公示", "优先审评", target_count=200)
        all_drugs.extend(priority_drugs)
        logger.info(f"优先审评采集完成: {len(priority_drugs)} 条")
        
        browser.close()
    
    # 完成提示
    print("\n" + "="*70)
    print("✅ 所有目标采集工作已完成！")
    print(f"   总计采集: {len(all_drugs)} 条药物信息")
    print("="*70)
    
    return all_drugs

def collect_single_tab(page: Page, tab_text: str, list_type: str, target_count: int):
    """采集单个tab的数据"""
    drugs = []
    
    # 导航到页面
    logger.info(f"导航到: {CDE_BASE_URL}")
    page.goto(CDE_BASE_URL, wait_until="domcontentloaded", timeout=60000)
    time.sleep(4)  # 等待JS执行
    
    # 点击对应tab
    logger.info(f"点击tab: {tab_text}")
    success = click_tab(page, tab_text)
    if not success:
        logger.error(f"无法找到并点击tab: {tab_text}")
        return drugs
    
    time.sleep(3)
    
    # 采集多页直到达到目标数量
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
            logger.info(f"    本页采集: {len(page_drugs)} 条，总计: {total_collected} 条")
            
            # 更新进度条
            print_progress_bar(total_collected, target_count, 
                              prefix=f'  采集{list_type}:',
                              suffix=f'({total_collected}/{target_count}) 第{page_num}页')
            
            # 检查是否还需要翻页
            if total_collected < target_count:
                if not click_next_page(page):
                    logger.info("    没有更多页了，停止采集")
                    break
                time.sleep(2.5)
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

def click_tab(page: Page, tab_text: str) -> bool:
    """点击指定的tab"""
    try:
        # 多种方式查找
        selectors = [
            f'text="{tab_text}"',
            f'a:text("{tab_text}")',
            f'span:text("{tab_text}")',
            f'li:text("{tab_text}")'
        ]
        
        for selector in selectors:
            try:
                elem = page.query_selector(selector)
                if elem:
                    elem.click()
                    time.sleep(2)
                    return True
            except:
                continue
        
        # 尝试通过JS查找
        js_result = page.evaluate(f'''
        function clickTab(text) {{
            const allElements = document.querySelectorAll('*');
            for (let elem of allElements) {{
                if (elem.textContent.trim() === text) {{
                    elem.click();
                    return true;
                }}
            }}
            return false;
        }}
        clickTab('{tab_text}');
        ''')
        
        return js_result if js_result is not None else False
        
    except Exception as e:
        logger.error(f"点击tab失败: {e}")
        return False

def extract_page_data(page: Page, list_type: str, start_num: int) -> list:
    """提取当前页的所有数据"""
    drugs = []
    
    try:
        # 获取所有行
        rows = page.query_selector_all("table tbody tr")
        logger.info(f"    找到 {len(rows)} 行")
        
        for i, row in enumerate(rows):
            try:
                cells = row.query_selector_all("td")
                if len(cells) < 5:
                    continue
                
                # 从表格中提取基本信息 - 注意列顺序
                # 实际列顺序: 序号(0) | 药物名称(1) | 受理号(2) | 申请人(3) | 申请日期(4)
                seq = cells[0].inner_text().strip() if len(cells) > 0 else ""
                acceptance = cells[1].inner_text().strip() if len(cells) > 1 else ""  # 这是受理号
                drug_name = cells[2].inner_text().strip() if len(cells) > 2 else ""   # 这是药物名称!
                applicant = cells[3].inner_text().strip() if len(cells) > 3 else ""  # 这是申请人
                app_date = cells[4].inner_text().strip() if len(cells) > 4 else ""   # 这是申请日期
                
                # 获取详细适应症
                indication = get_drug_indication_from_modal(page, cells[2])  # 点击药物名称单元格
                
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
                
                # 输出进度
                if (i + 1) % 5 == 0:
                    logger.info(f"      处理 {i+1}/{len(rows)}: {drug_name}")
                
                time.sleep(0.8)  # 操作间隔
                
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
            time.sleep(1.2)
            
            # 查找弹窗
            modal_selectors = [
                '.ant-modal',
                '.modal',
                '[role="dialog"]'
            ]
            
            modal = None
            for selector in modal_selectors:
                try:
                    modal = page.query_selector(selector)
                    if modal:
                        break
                except:
                    continue
            
            if modal:
                # 获取弹窗全部文本
                modal_text = modal.inner_text()
                
                # 查找适应症
                if '拟定适应症' in modal_text or '功能主治' in modal_text:
                    lines = modal_text.split('\n')
                    for i, line in enumerate(lines):
                        line = line.strip()
                        if '拟定适应症' in line or '功能主治' in line:
                            # 找后面的内容（可能分多行）
                            if i + 1 < len(lines):
                                j = i + 1
                                while j < len(lines):
                                    content = lines[j].strip()
                                    if content and not any(kw in lines[j] for kw in ['药品名称', '受理号', '申请人', '申请日期', '拟定适应症', '功能主治']):
                                        if indication:
                                            indication += " "
                                        indication += content
                                    else:
                                        break
                                    j += 1
                            break
                
                # 关闭弹窗
                close_buttons = [
                    '.ant-modal-close',
                    'button[aria-label="Close"]',
                    'button:text("×")',
                    'button:text("关闭")'
                ]
                
                closed = False
                for close_selector in close_buttons:
                    try:
                        close_btn = modal.query_selector(close_selector)
                        if close_btn:
                            close_btn.click()
                            closed = True
                            break
                    except:
                        continue
                
                if not closed:
                    page.keyboard.press("Escape")
                
                time.sleep(0.6)
        
    except Exception as e:
        logger.error(f"获取弹窗详情失败: {e}")
        try:
            page.keyboard.press("Escape")
            time.sleep(0.5)
        except:
            pass
    
    return indication

def click_next_page(page: Page) -> bool:
    """点击下一页"""
    try:
        selectors = [
            'button:text("下一页")',
            '.ant-pagination-next:not([disabled]) button',
            '[aria-label="Next Page"]'
        ]
        
        for selector in selectors:
            try:
                btn = page.query_selector(selector)
                if btn and not btn.is_disabled():
                    btn.click()
                    return True
            except:
                continue
        
        # 尝试通过页面索引
        try:
            current_page = get_current_page(page)
            next_page_selector = f'.ant-pagination-item:text("{current_page + 1}")'
            next_btn = page.query_selector(next_page_selector)
            if next_btn:
                next_btn.click()
                return True
        except:
            pass
        
        return False
    
    except Exception as e:
        logger.error(f"点击下一页失败: {e}")
        return False

def get_current_page(page: Page) -> int:
    """获取当前页码"""
    try:
        active = page.query_selector('.ant-pagination-item-active')
        if active:
            return int(active.inner_text())
    except:
        pass
    return 1

def save_csv_and_update_db(drugs: list):
    """保存CSV并更新数据库"""
    if not drugs:
        logger.warning("没有数据可保存")
        return
    
    # 保存全部数据
    all_csv_path = 'data/cde_all_drugs.csv'
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
    cancer_csv_path = 'data/cde_anticancer_drugs.csv'
    with open(cancer_csv_path, 'w', newline='', encoding='utf-8-sig') as f:
        writer = csv.DictWriter(f, fieldnames=[
            '名单类型', '序号', '药物名称', '受理号', '申请人',
            '申请日期', '拟定适应症', '是否抗肿瘤'
        ])
        writer.writeheader()
        writer.writerows(cancer_drugs)
    
    logger.info(f"抗肿瘤药物已保存: {cancer_csv_path}")
    
    # 更新数据库
    if cancer_drugs:
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
        import traceback
        traceback.print_exc()

def main():
    logger.info("="*70)
    logger.info("CDE特殊品种完整数据采集程序")
    logger.info("="*70)
    
    try:
        # 采集数据
        all_drugs = collect_full_data()
        
        # 保存并更新
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
