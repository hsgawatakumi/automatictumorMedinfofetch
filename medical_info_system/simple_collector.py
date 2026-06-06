"""
简化版CDE特殊药物采集脚本
使用Playwright + playwright-stealth方案采集CDE官网的抗肿瘤药物信息
"""

import os
import sys
import csv
import time
import logging
from datetime import datetime
from playwright.sync_api import sync_playwright
from playwright_stealth import Stealth

# 创建Stealth实例
stealth = Stealth()

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# CDE URLs - 使用正确的URL
BREAKTHROUGH_URL = "https://www.cde.org.cn/main/xxgk/listpage/9f9c74c73e0f7f8a0d38327fb2570e9f"
PRIORITY_URL = "https://www.cde.org.cn/main/xxgk/listpage/4b5255eb0a84820cef4ca3e8b6bbe20c"

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
    '多发性骨髓瘤', 'MM', 'CLL', 'CML', 'B细胞恶性肿瘤',
    # 靶向药相关
    'EGFR', 'ALK', 'ROS1', 'RET', 'MET', 'HER2', 'VEGF', 'PD-1', 'PD-L1', 'BTK',
    'BCMA', 'CD38', 'CD20', 'VEGFR', 'FGFR', 'NTRK', 'KRAS', 'BRAF', 'MEK', 'ERK',
    # 生物制剂
    '单抗', '抗体', 'ADC', '免疫治疗',
    # 其他关键词
    '腺癌', '鳞癌', '神经内分泌瘤', '实体瘤', '转移性', '晚期',
    # 新增关键词
    '间皮瘤', '鼻咽癌', '皮肤癌', '骨肉瘤', '尤文肉瘤', '脂肪肉瘤',
    '平滑肌肉瘤', '胃肠道间质瘤', 'GIST', '壶腹癌', '十二指肠癌',
    # 淋巴瘤/白血病亚型
    '套细胞淋巴瘤', '边缘区淋巴瘤', '滤泡性淋巴瘤', '弥漫大B细胞淋巴瘤',
    '慢性淋巴细胞白血病', '急性髓系白血病', '急性淋巴细胞白血病',
    '骨髓增生异常综合征', 'MDS'
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
        headless = os.environ.get('HEADLESS', 'false').lower() == 'true'
        print(f"浏览器模式: {'无头模式' if headless else '可视化模式'}")
        browser = p.chromium.launch(headless=headless)
        
        # 创建上下文
        context = browser.new_context(
            viewport={'width': 1920, 'height': 1080},
            user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            locale='zh-CN',
            timezone_id='Asia/Shanghai'
        )
        
        # 应用Stealth配置
        stealth.apply_stealth_sync(context)
        
        # 创建页面
        page = context.new_page()
        
        print("=" * 70)
        print("开始采集CDE官网药物信息")
        print("=" * 70)
        
        # 采集突破性治疗名单
        print("\n[1/2] 采集突破性治疗品种名单...")
        breakthrough_drugs = collect_list(page, BREAKTHROUGH_URL, "突破性治疗")
        all_drugs.extend(breakthrough_drugs)
        print(f"突破性治疗品种: {len(breakthrough_drugs)} 条")
        
        time.sleep(3)  # 页面间休息
        
        # 采集优先审评名单
        print("\n[2/2] 采集优先审评品种名单...")
        priority_drugs = collect_list(page, PRIORITY_URL, "优先审评")
        all_drugs.extend(priority_drugs)
        print(f"优先审评品种: {len(priority_drugs)} 条")
        
        # 关闭浏览器
        browser.close()
    
    return all_drugs

def collect_list(page, url, list_type):
    """采集单个名单"""
    drugs = []
    
    try:
        print(f"访问: {url}")
        page.goto(url, wait_until="domcontentloaded", timeout=60000)
        time.sleep(5)  # 增加等待时间让JavaScript执行
        
        # 打印页面信息用于调试
        print(f"    页面标题: {page.title()}")
        print(f"    当前URL: {page.url}")
        
        # 打印页面内容前1000字符用于调试
        page_content = page.content()
        print(f"    页面内容长度: {len(page_content)} 字符")
        if len(page_content) < 2000:
            print(f"    页面内容: {page_content[:1000]}")
        else:
            print(f"    页面内容前1000字符: {page_content[:1000]}")
        
        # 尝试翻页
        for page_num in range(1, 11):  # 第1-10页
            print(f"  处理第 {page_num}/10 页...")
            
            # 提取当前页药物
            page_drugs = extract_drugs(page, list_type)
            drugs.extend(page_drugs)
            
            # 点击下一页
            if page_num < 10:
                try:
                    next_button = page.query_selector('button:has-text("下一页"), .ant-pagination-next:not([disabled])')
                    if next_button:
                        next_button.click()
                        time.sleep(2)  # 等待页面加载
                    else:
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
        # 等待一段时间让JavaScript执行
        print("    等待页面渲染...")
        time.sleep(8)  # 增加等待时间
        
        # 尝试查找包含数据的表格
        rows = []
        
        # 首先检查是否有 iframe
        iframes = page.query_selector_all("iframe")
        print(f"    页面中有 {len(iframes)} 个iframe")
        
        # 尝试多种可能的选择器
        selectors = [
            "table tbody tr",
            ".ant-table-tbody tr",
            "tr[class*='row']",
            "div[class*='list'] tr",
            ".layui-table tbody tr",
            "table.layui-table tbody tr"
        ]
        
        found_selector = None
        for selector in selectors:
            try:
                page.wait_for_selector(selector, timeout=5000)
                rows = page.query_selector_all(selector)
                if rows:
                    found_selector = selector
                    print(f"    使用选择器: {selector}, 找到 {len(rows)} 行")
                    break
            except Exception as e:
                continue
        
        if not rows:
            # 输出页面中存在的表格元素用于调试
            try:
                tables = page.query_selector_all("table")
                print(f"    页面中有 {len(tables)} 个表格")
                if tables:
                    for i, t in enumerate(tables[:3]):
                        rows_in_table = t.query_selector_all("tr")
                        print(f"    表格{i+1}有 {len(rows_in_table)} 行")
                        # 尝试获取表格的class
                        table_class = t.get_attribute("class")
                        print(f"    表格{i+1} class: {table_class}")
            except:
                pass
            return drugs
        
        for row in rows:
            try:
                # 获取单元格数据
                cells = row.query_selector_all("td")
                if len(cells) >= 5:
                    # 调试：打印列数和前几列内容
                    if len(drugs) < 2:
                        print(f"    [调试] 列数: {len(cells)}")
                        for idx, cell in enumerate(cells[:min(7, len(cells))]):
                            print(f"    [调试] 列{idx}: {cell.inner_text().strip()[:50]}")
                    
                    # 根据实际CDE网站表格结构，列顺序为：
                    # 序号(0) | 药物名称(1) | 受理号(2) | 申请人(3) | 申请日期(4) | 拟定适应症(5)
                    # 注意：实际数据显示拟定适应症在第5列，申请日期在第4列
                    seq_num = cells[0].inner_text().strip()
                    drug_name = cells[1].inner_text().strip()  # 药物名称
                    acceptance_num = cells[2].inner_text().strip()  # 受理号
                    applicant = cells[3].inner_text().strip()
                    app_date = cells[4].inner_text().strip()  # 申请日期
                    
                    # 获取药物详情（点击药物名称链接）
                    indication = get_drug_indication(page, cells[1])  # cells[1]是药物名称单元格
                    
                    # 如果没有从弹窗获取到适应症，尝试从表格直接获取
                    # 注意：CDE表格中拟定适应症可能在第5列或第6列
                    if not indication:
                        if len(cells) > 5:
                            potential_indication = cells[5].inner_text().strip()
                            # 如果第5列看起来像适应症（包含癌、瘤、肿瘤等关键词）
                            if any(k in potential_indication for k in ['癌', '瘤', '肿瘤', '适应症', '白血病', '淋巴瘤']):
                                indication = potential_indication
                                print(f"    [修正] 从第5列获取适应症: {indication[:30]}...")
                        if not indication and len(cells) > 6:
                            potential_indication = cells[6].inner_text().strip()
                            if any(k in potential_indication for k in ['癌', '瘤', '肿瘤', '适应症', '白血病', '淋巴瘤']):
                                indication = potential_indication
                    
                    # 判断是否为抗肿瘤药物
                    is_cancer = is_cancer_indication(indication)
                    
                    drug_info = {
                        '名单类型': list_type,
                        '序号': seq_num,
                        '药物名称': drug_name,
                        '受理号': acceptance_num,
                        '申请人': applicant,
                        '申请日期': app_date,
                        '拟定适应症': indication,
                        '是否抗肿瘤': '是' if is_cancer else '否'
                    }
                    
                    drugs.append(drug_info)
                    if is_cancer:
                        print(f"    ✓ {drug_name} - {indication[:30]}...")
                    
                    time.sleep(0.5)  # 操作间隔
                    
            except Exception as e:
                print(f"    提取失败: {e}")
                continue
        
    except Exception as e:
        print(f"提取失败: {e}")
    
    return drugs

def get_drug_indication(page, cell):
    """获取药物拟定适应症"""
    try:
        # 点击药物名称
        link = cell.query_selector("a")
        if link:
            link.click()
            time.sleep(1)
            
            # 查找弹窗
            modal = page.wait_for_selector(".ant-modal, .modal, [role='dialog']", timeout=3000)
            if modal:
                modal_text = modal.inner_text()
                
                # 提取拟定适应症
                indication = ""
                lines = modal_text.split('\n')
                for i, line in enumerate(lines):
                    if '拟定适应症' in line or '功能主治' in line:
                        if i + 1 < len(lines):
                            indication = lines[i + 1].strip()
                            break
                
                # 关闭弹窗
                close_btn = modal.query_selector("button[class*='close'], .ant-modal-close")
                if close_btn:
                    close_btn.click()
                else:
                    page.keyboard.press("Escape")
                
                time.sleep(0.5)
                return indication
        
    except Exception as e:
        print(f"获取详情失败: {e}")
        try:
            page.keyboard.press("Escape")
        except:
            pass
    
    return ""

def save_to_csv(drugs, filename):
    """保存为CSV文件"""
    if not drugs:
        print("没有数据可保存")
        return
    
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
    print("=" * 70)
    
    try:
        # 采集数据
        all_drugs = collect_with_playwright()
        
        if all_drugs:
            # 保存为CSV
            save_to_csv(all_drugs, 'cde_anticancer_drugs.csv')
            
            # 筛选抗肿瘤药物
            cancer_drugs = [d for d in all_drugs if d.get('是否抗肿瘤') == '是']
            
            if cancer_drugs:
                save_to_csv(cancer_drugs, 'cde_cancer_drugs_only.csv')
                
                # 更新数据库
                update_database(cancer_drugs)
        
        print("\n" + "=" * 70)
        print("采集完成！")
        print("=" * 70)
        
    except KeyboardInterrupt:
        print("\n用户中断")
    except Exception as e:
        print(f"\n错误: {e}")
        logger.error(f"主函数错误: {e}")

if __name__ == '__main__':
    main()
