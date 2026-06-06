"""
CDE特殊药物采集脚本 - 增强版
处理WAF和动态加载问题
"""

import os
import sys
import csv
import time
import logging
from datetime import datetime
from playwright.sync_api import sync_playwright

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# CDE URLs
CDE_BASE_URL = "https://www.cde.org.cn/main/xxgk/listpage/b40868b5e21c038a6aa8b4319d21b07d"

# 抗肿瘤关键词
CANCER_KEYWORDS = [
    '癌', '肿瘤', '白血病', '淋巴瘤', '肉瘤', '骨髓瘤', '瘤',
    '肺癌', '非小细胞肺癌', '小细胞肺癌', 'NSCLC', 'SCLC',
    '乳腺癌', '肝癌', '胃癌', '结直肠癌', '胰腺癌', '食管癌', '胆管癌',
    '肾癌', '膀胱癌', '前列腺癌', '卵巢癌', '宫颈癌', '子宫内膜癌',
    '黑色素瘤', '脑癌', '胶质瘤', '甲状腺癌',
    'EGFR', 'ALK', 'ROS1', 'RET', 'MET', 'HER2', 'PD-1', 'PD-L1',
    'BCMA', 'CD38', 'VEGFR', 'FGFR', 'NTRK', 'KRAS', 'BRAF',
    '单抗', '抗体', 'ADC', '免疫治疗',
    '腺癌', '鳞癌', '神经内分泌瘤', '实体瘤', '转移性', '晚期',
    # 血液肿瘤
    'B细胞恶性肿瘤', '多发性骨髓瘤', 'MM', 'CLL', 'CML',
    '套细胞淋巴瘤', '边缘区淋巴瘤', '滤泡性淋巴瘤', '弥漫大B细胞淋巴瘤',
    '慢性淋巴细胞白血病', '急性髓系白血病', '急性淋巴细胞白血病',
    '骨髓增生异常综合征', 'MDS',
    # 其他
    '鼻咽癌', '头颈癌', '皮肤癌', '胃肠道间质瘤', 'GIST'
]

def is_cancer_indication(indication: str) -> bool:
    if not indication:
        return False
    for keyword in CANCER_KEYWORDS:
        if keyword.lower() in indication.lower():
            return True
    return False

def collect_with_retry():
    """带重试机制的采集"""
    max_retries = 3
    
    for attempt in range(1, max_retries + 1):
        print(f"\n尝试 {attempt}/{max_retries}...")
        
        try:
            all_drugs = perform_collection()
            if all_drugs:
                return all_drugs
        except Exception as e:
            print(f"尝试 {attempt} 失败: {e}")
            if attempt < max_retries:
                print("等待 5 秒后重试...")
                time.sleep(5)
    
    return []

def perform_collection():
    """执行采集"""
    all_drugs = []
    
    with sync_playwright() as p:
        # 启动浏览器
        headless = os.environ.get('HEADLESS', 'false').lower() == 'true'
        print(f"浏览器模式: {'无头模式' if headless else '可视化模式'}")
        browser = p.chromium.launch(
            headless=headless,
            args=['--disable-blink-features=AutomationControlled']
        )
        
        # 创建上下文
        context = browser.new_context(
            viewport={'width': 1920, 'height': 1080},
            user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            locale='zh-CN',
            timezone_id='Asia/Shanghai',
            extra_http_headers={
                'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8'
            }
        )
        
        # 创建页面
        page = context.new_page()
        
        print("=" * 70)
        print("开始采集CDE官网药物信息")
        print("=" * 70)
        
        # 采集优先审评
        print("\n[1/2] 采集纳入优先审评品种名单...")
        try:
            priority_drugs = collect_single_list(page, CDE_BASE_URL, "优先审评公示", "优先审评")
            all_drugs.extend(priority_drugs)
            print(f"✓ 优先审评品种: {len(priority_drugs)} 条")
        except Exception as e:
            print(f"✗ 优先审评采集失败: {e}")
        
        time.sleep(3)
        
        # 采集突破性治疗
        print("\n[2/2] 采集纳入突破性治疗品种名单...")
        try:
            breakthrough_drugs = collect_single_list(page, CDE_BASE_URL, "突破性治疗公示", "突破性治疗")
            all_drugs.extend(breakthrough_drugs)
            print(f"✓ 突破性治疗品种: {len(breakthrough_drugs)} 条")
        except Exception as e:
            print(f"✗ 突破性治疗采集失败: {e}")
        
        browser.close()
    
    return all_drugs

def collect_single_list(page, url, nav_text, list_type):
    """采集单个列表"""
    drugs = []
    
    print(f"  访问: {url}")
    
    # 多次尝试加载页面
    for load_attempt in range(3):
        try:
            page.goto(url, wait_until="domcontentloaded", timeout=30000)
            time.sleep(3)  # 等待JS执行
            
            # 检查页面是否加载成功
            title = page.title()
            print(f"  页面标题: {title}")
            
            if "CDE" in title or "药品审评" in title:
                break
            else:
                print(f"  页面加载异常，尝试 {load_attempt + 1}/3")
                time.sleep(2)
                
        except Exception as e:
            print(f"  加载失败: {e}")
            if load_attempt < 2:
                time.sleep(3)
            else:
                raise
    
    # 导航到对应tab
    print(f"  导航到: {nav_text}")
    try:
        # 执行JavaScript查找并点击
        js_code = f'''
        function navigateToNav(text) {{
            // 方案1: 查找面包屑或导航链接
            const allLinks = document.querySelectorAll('a, span, li, div');
            for (let elem of allLinks) {{
                if (elem.textContent.trim() === text) {{
                    elem.click();
                    return true;
                }}
            }}
            
            // 方案2: 查找包含关键词的元素
            for (let elem of allLinks) {{
                if (elem.textContent.includes(text)) {{
                    elem.click();
                    return true;
                }}
            }}
            
            return false;
        }}
        navigateToNav('{nav_text}');
        '''
        page.evaluate(js_code)
        time.sleep(3)
    except Exception as e:
        print(f"  导航失败: {e}")
    
    # 等待并提取表格数据
    print(f"  提取{list_type}数据...")
    
    for page_num in range(1, 11):
        print(f"    第 {page_num}/10 页...")
        
        try:
            # 等待表格出现
            page.wait_for_selector("table", timeout=10000)
            time.sleep(1)
            
            # 提取当前页数据
            page_drugs = extract_table_data(page, list_type)
            drugs.extend(page_drugs)
            print(f"      提取 {len(page_drugs)} 条")
            
            # 翻页
            if page_num < 10:
                if not click_next_page(page):
                    print("      无法翻页，停止")
                    break
                time.sleep(2)
                
        except Exception as e:
            print(f"      提取失败: {e}")
            break
    
    return drugs

def extract_table_data(page, list_type):
    """提取表格数据"""
    drugs = []
    
    try:
        # 查找表格
        table = page.query_selector("table tbody")
        if not table:
            return drugs
        
        rows = table.query_selector_all("tr")
        
        for row in rows:
            try:
                cells = row.query_selector_all("td")
                if len(cells) >= 5:
                    # 调试：打印列数
                    if len(drugs) < 2:
                        print(f"    [调试] 列数: {len(cells)}")
                        for idx, cell in enumerate(cells[:min(7, len(cells))]):
                            print(f"    [调试] 列{idx}: {cell.inner_text().strip()[:50]}")
                    
                    # 根据实际CDE网站表格结构，列顺序为：
                    # 序号(0) | 药物名称(1) | 受理号(2) | 申请人(3) | 申请日期(4) | 拟定适应症(5)
                    drug_name = cells[1].inner_text().strip()
                    acceptance_num = cells[2].inner_text().strip()
                    applicant = cells[3].inner_text().strip()
                    app_date = cells[4].inner_text().strip()
                    
                    # 点击获取详情
                    indication = ""
                    try:
                        link = cells[1].query_selector("a")
                        if link:
                            link.click()
                            time.sleep(1)
                            
                            # 获取弹窗内容
                            modal = page.query_selector(".ant-modal, .modal, [role='dialog']")
                            if modal:
                                modal_text = modal.inner_text()
                                
                                # 提取适应症
                                lines = modal_text.split('\n')
                                for i, line in enumerate(lines):
                                    if '拟定适应症' in line or '功能主治' in line:
                                        if i + 1 < len(lines):
                                            indication = lines[i + 1].strip()
                                        break
                                
                                # 关闭弹窗
                                page.keyboard.press("Escape")
                                time.sleep(0.5)
                                
                    except Exception as e:
                        print(f"        获取详情失败: {e}")
                        try:
                            page.keyboard.press("Escape")
                        except:
                            pass
                    
                    # 如果没有从弹窗获取到适应症，尝试从表格直接获取
                    if not indication and len(cells) > 5:
                        potential_indication = cells[5].inner_text().strip()
                        if any(k in potential_indication for k in ['癌', '瘤', '肿瘤', '适应症', '白血病', '淋巴瘤']):
                            indication = potential_indication
                            print(f"    [修正] 从第5列获取适应症: {indication[:30]}...")
                    
                    is_cancer = is_cancer_indication(indication)
                    
                    drug_info = {
                        '名单类型': list_type,
                        '序号': cells[0].inner_text().strip(),
                        '药物名称': drug_name,
                        '受理号': acceptance_num,
                        '申请人': applicant,
                        '申请日期': app_date,
                        '拟定适应症': indication,
                        '是否抗肿瘤': '是' if is_cancer else '否'
                    }
                    
                    drugs.append(drug_info)
                    
                    if is_cancer:
                        print(f"        ✓ {drug_name}")
                    
                    time.sleep(0.5)
                    
            except Exception as e:
                continue
    
    except Exception as e:
        print(f"  表格提取失败: {e}")
    
    return drugs

def click_next_page(page):
    """点击下一页"""
    try:
        # 多种选择器
        selectors = [
            'button:has-text("下一页")',
            '.ant-pagination-next:not([disabled]) button',
            '[aria-label="Next"]',
            'button.ant-pagination-item-link'
        ]
        
        for selector in selectors:
            try:
                btn = page.query_selector(selector)
                if btn and not btn.is_disabled():
                    btn.click()
                    return True
            except:
                continue
        
        return False
        
    except Exception as e:
        print(f"  翻页失败: {e}")
        return False

def save_and_update(drugs):
    """保存和更新"""
    if not drugs:
        print("\n没有数据可保存")
        return
    
    # 保存全部数据
    filepath = os.path.join(os.path.dirname(__file__), 'data', 'cde_all_drugs.csv')
    os.makedirs(os.path.dirname(filepath), exist_ok=True)
    
    with open(filepath, 'w', newline='', encoding='utf-8-sig') as f:
        writer = csv.DictWriter(f, fieldnames=[
            '名单类型', '序号', '药物名称', '受理号', '申请人',
            '申请日期', '拟定适应症', '是否抗肿瘤'
        ])
        writer.writeheader()
        writer.writerows(drugs)
    
    print(f"\n数据已保存: {filepath}")
    
    # 筛选抗肿瘤
    cancer_drugs = [d for d in drugs if d.get('是否抗肿瘤') == '是']
    print(f"总计: {len(drugs)} 条")
    print(f"抗肿瘤药物: {len(cancer_drugs)} 条")
    
    # 更新数据库
    if cancer_drugs:
        save_cancer_drugs(cancer_drugs)

def save_cancer_drugs(drugs):
    """保存抗肿瘤药物到数据库"""
    try:
        from src.database import DatabaseManager, init_database
        
        db_path = os.path.join(os.path.dirname(__file__), 'data', 'medical_info.db')
        db_manager = init_database(db_path)
        
        conn = db_manager.connect()
        cursor = conn.cursor()
        cursor.execute("DELETE FROM cde_special_drugs")
        conn.commit()
        
        now = datetime.now().strftime('%Y-%m-%d')
        count = 0
        
        for drug in drugs:
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
                print(f"  插入失败: {drug['药物名称']} - {e}")
        
        print(f"\n数据库更新: {count} 条")
        
    except Exception as e:
        print(f"\n数据库更新失败: {e}")

def main():
    print("=" * 70)
    print("CDE官网抗肿瘤药物采集程序")
    print("=" * 70)
    
    try:
        all_drugs = collect_with_retry()
        
        if all_drugs:
            save_and_update(all_drugs)
        
        print("\n" + "=" * 70)
        print("采集完成!")
        print("=" * 70)
        
    except KeyboardInterrupt:
        print("\n用户中断")
    except Exception as e:
        print(f"\n错误: {e}")
        import traceback
        traceback.print_exc()

if __name__ == '__main__':
    main()
