"""
CDE特殊药物采集脚本 - 处理相同URL不同路径的情况
纳入优先审评品种名单、纳入突破性治疗品种名单
"""

import os
import sys
import csv
import time
import logging
from datetime import datetime
from playwright.sync_api import sync_playwright
from playwright_stealth import stealth

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# CDE URLs - 两个名单使用相同的基础URL
CDE_BASE_URL = "https://www.cde.org.cn/main/xxgk/listpage/b40868b5e21c038a6aa8b4319d21b07d"

# 扩展的抗肿瘤关键词列表
CANCER_KEYWORDS = [
    # 常见肿瘤名称
    '癌', '肿瘤', '白血病', '淋巴瘤', '肉瘤', '骨髓瘤', '瘤',
    # 肺癌
    '肺癌', '非小细胞肺癌', '小细胞肺癌', 'NSCLC', 'SCLC',
    # 乳腺癌
    '乳腺癌', '乳腺',
    # 消化系统肿瘤
    '肝癌', '胃癌', '结直肠癌', '直肠癌', '结肠癌', '食管癌', '胰腺癌', '胆管癌',
    # 泌尿系统肿瘤
    '肾癌', '膀胱癌', '前列腺癌', '睾丸癌',
    # 妇科肿瘤
    '卵巢癌', '宫颈癌', '子宫内膜癌', '子宫癌',
    # 其他肿瘤
    '黑色素瘤', '脑癌', '胶质瘤', '头颈癌', '甲状腺癌', '胸腺瘤',
    # 血液肿瘤
    '多发性骨髓瘤', 'MM', 'CLL', 'CML',
    # 靶向药相关
    'EGFR', 'ALK', 'ROS1', 'RET', 'MET', 'HER2', 'VEGF', 'PD-1', 'PD-L1', 'BTK',
    'BCMA', 'CD38', 'CD20', 'VEGFR', 'FGFR', 'NTRK', 'KRAS', 'BRAF', 'MEK', 'ERK',
    # 生物制剂
    '单抗', '抗体', 'ADC', '免疫治疗',
    # 其他关键词
    '腺癌', '鳞癌', '神经内分泌瘤', '实体瘤', '转移性', '晚期',
    # 新增关键词
    '间皮瘤', '鼻咽癌', '皮肤癌', '骨肉瘤', '尤文肉瘤', '脂肪肉瘤',
    '平滑肌肉瘤', '胃肠道间质瘤', 'GIST', '壶腹癌', '十二指肠癌'
]

def is_cancer_indication(indication: str) -> bool:
    """判断适应症是否为抗肿瘤相关"""
    if not indication:
        return False
    
    indication_upper = indication.upper()
    for keyword in CANCER_KEYWORDS:
        if keyword.upper() in indication_upper or keyword in indication:
            return True
    
    return False

def collect_with_playwright():
    """使用Playwright采集数据"""
    all_drugs = []
    
    with sync_playwright() as p:
        # 启动Chromium浏览器
        print("启动浏览器...")
        browser = p.chromium.launch(headless=False)
        
        # 创建上下文
        context = browser.new_context(
            viewport={'width': 1920, 'height': 1080},
            user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            locale='zh-CN',
            timezone_id='Asia/Shanghai'
        )
        
        # 创建页面
        page = context.new_page()
        
        print("=" * 70)
        print("开始采集CDE官网药物信息")
        print("=" * 70)
        
        # 采集优先审评品种名单
        print("\n[1/2] 采集纳入优先审评品种名单...")
        print("导航到：信息公开 >> 优先审评公示")
        priority_drugs = collect_list_by_navigation(page, CDE_BASE_URL, "优先审评公示", "优先审评")
        all_drugs.extend(priority_drugs)
        print(f"优先审评品种: {len(priority_drugs)} 条")
        
        time.sleep(3)  # 页面间休息
        
        # 采集突破性治疗品种名单
        print("\n[2/2] 采集纳入突破性治疗品种名单...")
        print("导航到：信息公开 >> 突破性治疗公示")
        breakthrough_drugs = collect_list_by_navigation(page, CDE_BASE_URL, "突破性治疗公示", "突破性治疗")
        all_drugs.extend(breakthrough_drugs)
        print(f"突破性治疗品种: {len(breakthrough_drugs)} 条")
        
        # 关闭浏览器
        browser.close()
    
    return all_drugs

def collect_list_by_navigation(page, url, nav_text, list_type):
    """通过导航到特定tab来采集列表"""
    drugs = []
    
    try:
        print(f"访问基础URL: {url}")
        page.goto(url, wait_until="networkidle", timeout=60000)
        time.sleep(3)  # 等待页面完全加载
        
        # 查找并点击对应的导航tab
        # 尝试多种选择器
        selectors = [
            f'a:has-text("{nav_text}")',
            f'li:has-text("{nav_text}")',
            f'span:has-text("{nav_text}")',
            f'text="{nav_text}"'
        ]
        
        nav_found = False
        for selector in selectors:
            try:
                elements = page.query_selector_all(selector)
                for elem in elements:
                    try:
                        elem_text = elem.inner_text()
                        if nav_text in elem_text:
                            print(f"  找到导航: {elem_text}")
                            elem.click()
                            time.sleep(2)  # 等待内容加载
                            nav_found = True
                            break
                    except:
                        continue
                if nav_found:
                    break
            except Exception as e:
                continue
        
        if not nav_found:
            # 尝试通过JavaScript查找并点击
            print(f"  尝试通过JavaScript导航到 {nav_text}...")
            js_code = f"""
            // 查找包含指定文本的元素并点击
            function findAndClick(text) {{
                const elements = document.querySelectorAll('*');
                for (let elem of elements) {{
                    if (elem.childNodes.length === 1 && elem.textContent.trim() === text) {{
                        elem.click();
                        return true;
                    }}
                }}
                return false;
            }}
            findAndClick('{nav_text}');
            """
            page.evaluate(js_code)
            time.sleep(2)
        
        # 等待表格加载
        page.wait_for_selector("table", timeout=10000)
        time.sleep(2)
        
        # 尝试翻页
        for page_num in range(1, 11):  # 第1-10页
            print(f"  处理第 {page_num}/10 页...")
            
            # 提取当前页药物
            page_drugs = extract_drugs(page, list_type)
            drugs.extend(page_drugs)
            
            # 点击下一页
            if page_num < 10:
                try:
                    # 尝试多种下一页按钮选择器
                    next_selectors = [
                        'button:has-text("下一页")',
                        '.ant-pagination-next:not([disabled])',
                        'button.ant-pagination-item-link',
                        '[aria-label="下一页"]'
                    ]
                    
                    next_found = False
                    for next_selector in next_selectors:
                        try:
                            next_button = page.query_selector(next_selector)
                            if next_button and not next_button.is_disabled():
                                next_button.click()
                                time.sleep(2)
                                next_found = True
                                break
                        except:
                            continue
                    
                    if not next_found:
                        print(f"    无法找到下一页按钮，停止")
                        break
                        
                except Exception as e:
                    print(f"    点击下一页失败: {e}")
                    break
        
    except Exception as e:
        print(f"采集失败: {e}")
        logger.error(f"采集{list_type}失败: {e}")
    
    return drugs

def extract_drugs(page, list_type):
    """提取当前页的药物信息"""
    drugs = []
    
    try:
        # 等待表格加载
        page.wait_for_selector("table tbody", timeout=5000)
        time.sleep(1)
        
        # 获取所有行
        rows = page.query_selector_all("table tbody tr")
        print(f"    找到 {len(rows)} 行数据")
        
        for row in rows:
            try:
                # 获取单元格数据
                cells = row.query_selector_all("td")
                if len(cells) >= 5:
                    drug_name = cells[1].inner_text().strip()
                    
                    # 获取药物详情
                    indication = get_drug_indication(page, cells[1])
                    
                    # 判断是否为抗肿瘤药物
                    is_cancer = is_cancer_indication(indication)
                    
                    drug_info = {
                        '名单类型': list_type,
                        '序号': cells[0].inner_text().strip(),
                        '药物名称': drug_name,
                        '受理号': cells[2].inner_text().strip(),
                        '申请人': cells[3].inner_text().strip(),
                        '申请日期': cells[4].inner_text().strip(),
                        '拟定适应症': indication,
                        '是否抗肿瘤': '是' if is_cancer else '否'
                    }
                    
                    drugs.append(drug_info)
                    if is_cancer:
                        print(f"      ✓ {drug_name} - 抗肿瘤")
                    
                    time.sleep(0.5)  # 操作间隔
                    
            except Exception as e:
                print(f"    提取失败: {e}")
                continue
        
    except Exception as e:
        print(f"提取失败: {e}")
    
    return drugs

def get_drug_indication(page, cell):
    """获取药物拟定适应症"""
    indication = ""
    
    try:
        # 点击药物名称
        link = cell.query_selector("a")
        if link:
            link.click()
            time.sleep(1)
            
            # 查找弹窗
            try:
                modal = page.wait_for_selector(".ant-modal, .modal, [role='dialog']", timeout=3000)
                if modal:
                    modal_text = modal.inner_text()
                    
                    # 提取拟定适应症
                    lines = modal_text.split('\n')
                    for i, line in enumerate(lines):
                        if '拟定适应症' in line or '功能主治' in line:
                            if i + 1 < len(lines):
                                indication = lines[i + 1].strip()
                                break
                    
                    # 关闭弹窗
                    close_selectors = [
                        "button[class*='close']",
                        ".ant-modal-close",
                        "[aria-label='Close']"
                    ]
                    
                    closed = False
                    for close_selector in close_selectors:
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
                    
                    time.sleep(0.5)
                    
            except Exception as e:
                print(f"    弹窗处理失败: {e}")
                try:
                    page.keyboard.press("Escape")
                except:
                    pass
        
    except Exception as e:
        print(f"    获取详情失败: {e}")
        try:
            page.keyboard.press("Escape")
        except:
            pass
    
    return indication

def save_to_csv(drugs, filename):
    """保存为CSV文件"""
    if not drugs:
        print("没有数据可保存")
        return []
    
    filepath = os.path.join(os.path.dirname(__file__), 'data', filename)
    
    # 确保目录存在
    os.makedirs(os.path.dirname(filepath), exist_ok=True)
    
    with open(filepath, 'w', newline='', encoding='utf-8-sig') as f:
        writer = csv.DictWriter(f, fieldnames=[
            '名单类型', '序号', '药物名称', '受理号', '申请人', 
            '申请日期', '拟定适应症', '是否抗肿瘤'
        ])
        writer.writeheader()
        writer.writerows(drugs)
    
    print(f"\n数据已保存到: {filepath}")
    
    # 统计
    cancer_drugs = [d for d in drugs if d.get('是否抗肿瘤') == '是']
    print(f"总计: {len(drugs)} 条")
    print(f"其中抗肿瘤药物: {len(cancer_drugs)} 条")
    
    return cancer_drugs

def update_database(drugs):
    """更新数据库"""
    try:
        from src.database import DatabaseManager, init_database
        
        # 初始化数据库
        db_path = os.path.join(os.path.dirname(__file__), 'data', 'medical_info.db')
        db_manager = init_database(db_path)
        
        # 清空旧数据
        conn = db_manager.connect()
        cursor = conn.cursor()
        cursor.execute("DELETE FROM cde_special_drugs")
        conn.commit()
        
        # 插入新数据
        now = datetime.now().strftime('%Y-%m-%d')
        count = 0
        
        for drug in drugs:
            if drug.get('是否抗肿瘤') == '是':
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
                    'priority_type': drug['名单类型'] if '优先' in drug['名单类型'] else '',
                    'breakthrough_type': drug['名单类型'] if '突破' in drug['名单类型'] else '',
                    'trial_info': '',
                    'molecular_target': '',
                    'gene_marker': '',
                    'reference_drug': '',
                    'description': '',
                    'detail_url': 'https://www.cde.org.cn',
                    'created_at': now,
                    'updated_at': now
                }
                
                try:
                    db_manager.execute_insert('cde_special_drugs', record)
                    count += 1
                except Exception as e:
                    print(f"插入失败: {drug['药物名称']} - {e}")
        
        print(f"\n数据库更新完成: {count} 条记录")
        return count
        
    except Exception as e:
        print(f"数据库更新失败: {e}")
        logger.error(f"数据库更新失败: {e}")
        return 0

def main():
    """主函数"""
    print("=" * 70)
    print("CDE官网抗肿瘤药物自动化采集程序")
    print("(相同URL，不同路径导航)")
    print("=" * 70)
    
    try:
        # 采集数据
        all_drugs = collect_with_playwright()
        
        if all_drugs:
            # 保存为CSV
            save_to_csv(all_drugs, 'cde_all_drugs.csv')
            
            # 筛选抗肿瘤药物
            cancer_drugs = [d for d in all_drugs if d.get('是否抗肿瘤') == '是']
            
            if cancer_drugs:
                save_to_csv(cancer_drugs, 'cde_anticancer_drugs.csv')
                
                # 更新数据库
                update_database(cancer_drugs)
        
        print("\n" + "=" * 70)
        print("采集完成！")
        print("=" * 70)
        
    except KeyboardInterrupt:
        print("\n用户中断")
    except Exception as e:
        print(f"\n错误: {e}")
        import traceback
        traceback.print_exc()
        logger.error(f"主函数错误: {e}")

if __name__ == '__main__':
    main()
