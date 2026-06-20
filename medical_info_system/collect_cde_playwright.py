"""使用Playwright收集CDE网站的最新抗肿瘤药物数据"""
try:
    from playwright.sync_api import sync_playwright
except ImportError:
    print("⚠️ Playwright未安装，跳过网页收集")
    import sys
    sys.exit(0)

import sqlite3
import time
import os
import re
from datetime import datetime

db_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'data', 'medical_info.db')

# CDE上市药品信息页面
CDE_POSTMARKET_PAGE = "https://www.cde.org.cn/main/xxgk/postmarketpage"
CDE_PRIORITY_REVIEW = "https://www.cde.org.cn/main/xxgk/listpage/9f9c74c3cc1404a8951ac4f42883f91a"
CDE_BREAKTHROUGH = "https://www.cde.org.cn/main/xxgk/listpage/4b5255eb0a894a2aab7e289485bd4165"

print("=" * 80)
print("使用Playwright收集CDE最新药物数据")
print("=" * 80)

def save_drug_to_db(drug_data):
    """保存药物到数据库"""
    if not drug_data or not drug_data.get('drug_name'):
        return False

    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    drug_name = drug_data['drug_name'].strip()

    # 检查是否已存在
    existing = cursor.execute("""
        SELECT id FROM approved_drugs
        WHERE regulatory_agency = 'NMPA'
        AND (drug_name_cn = ? OR drug_name_cn LIKE '%' || ? || '%')
        LIMIT 1
    """, (drug_name, drug_name)).fetchone()

    if existing:
        conn.close()
        return False

    indication = drug_data.get('indication', '')
    applicant = drug_data.get('applicant', '')
    approval_date = drug_data.get('date', '')
    detail_url = drug_data.get('detail_url', '')

    # 剂型和给药途径
    dosage_form = None
    route_of_administration = None

    if '片' in drug_name or '胶囊' in drug_name or '颗粒' in drug_name:
        dosage_form = '口服'
        route_of_administration = '口服'
    elif '注射液' in drug_name or '注射用' in drug_name:
        dosage_form = '注射'
        route_of_administration = '静脉注射/静脉输注'

    # 靶点提取
    molecular_target = None
    gene_marker = None
    mechanism_parts = []

    if indication:
        target_keywords = ['EGFR', 'ALK', 'HER2', 'HER3', 'PD-1', 'PD-L1', 'PDL1',
                          'VEGF', 'VEGFR', 'BTK', 'PARP', 'KRAS', 'BRAF', 'NTRK', 'RET',
                          'CD19', 'CD20', 'CD22', 'CD30', 'CD33', 'CD38', 'CD138',
                          'CLDN18', 'Claudin', 'DLL3', 'PSMA', 'IDH1', 'IDH2', 'BCMA',
                          'TROP2', 'FGFR', 'MET', 'FLT3', 'mTOR', 'PI3K', 'AKT',
                          'MEK', 'AR', 'c-KIT', 'HER2阳性', 'EGFR 20']
        found = []
        for t in target_keywords:
            if t.lower() in indication.lower() or t in indication:
                found.append(t)
        if found:
            molecular_target = '; '.join(list(set(found)))
            mechanism_parts.append(f"靶点: {molecular_target}")

        gene_patterns = re.findall(r'([A-Z0-9]{2,15}(?:基因|突变|融合|扩增|阳性))', indication)
        if gene_patterns:
            gene_marker = '; '.join(gene_patterns[:5])
            mechanism_parts.append(f"生物标志物: {gene_marker}")

        mechanism_parts.append(f"适应症: {indication}")

    mechanism_of_action = '\n'.join(mechanism_parts) if mechanism_parts else None

    try:
        cursor.execute("""
            INSERT INTO approved_drugs (
                regulatory_agency, drug_name_cn, brand_name_cn,
                approval_number, approval_date, indication,
                dosage_form, route_of_administration, mechanism_of_action,
                molecular_target, gene_marker, companion_diagnosis,
                clinical_trial_data, detail_url, data_collection_time,
                created_at, updated_at, applicant
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            'NMPA', drug_name, None, None,
            approval_date, indication, dosage_form, route_of_administration,
            mechanism_of_action, molecular_target, gene_marker, None, None,
            detail_url, datetime.now().isoformat(), None, None, applicant
        ))
        conn.commit()
        result = True
    except Exception as e:
        result = False

    conn.close()
    return result

def collect_cde_with_playwright():
    collected = 0
    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            context = browser.new_context(
                user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                viewport={'width': 1280, 'height': 720}
            )
            page = context.new_page()

            # 访问优先审评页面
            urls_to_collect = [CDE_PRIORITY_REVIEW, CDE_BREAKTHROUGH]
            for url in urls_to_collect:
                try:
                    print(f"\n正在访问: {url}")
                    page.goto(url, timeout=30000)
                    time.sleep(5)

                    # 等待表格加载
                    try:
                        page.wait_for_selector('table', timeout=10000)
                    except:
                        print("  未找到表格，尝试提取文本...")

                    # 获取所有文本
                    content = page.inner_text('body')
                    print(f"  页面内容长度: {len(content)} 字符")

                    # 查找包含药物信息的行
                    lines = content.split('\n')

                    # 查找药品名
                    drug_pattern = re.compile(r'([^\s]{2,30}(?:片|胶囊|注射液|注射用|颗粒|丸|口服液|散|凝胶|软膏))')
                    date_pattern = re.compile(r'(202[4-6]-\d{2}-\d{2})')

                    i = 0
                    while i < len(lines):
                        line = lines[i].strip()

                        # 检查是否是药品名称
                        if drug_pattern.search(line) and len(line) < 100:
                            drug_name = drug_pattern.search(line).group(1)

                            # 查找附近的适应症和日期
                            indication = ''
                            for j in range(i+1, min(i+10, len(lines))):
                                next_line = lines[j].strip()
                                if date_pattern.search(next_line):
                                    approval_date = date_pattern.search(next_line).group(1)
                                if len(next_line) > 10 and any(keyword in next_line for keyword in
                                    ['治疗', '用于', '患者', '癌', '瘤', '白血病', '淋巴瘤', '骨髓瘤']):
                                    indication = next_line[:200]
                                    break

                            # 只保留2025-2026年且涉及癌症的药物
                            is_cancer = any(kw in (indication + drug_name) for kw in
                                ['癌', '瘤', '白血病', '淋巴瘤', '骨髓瘤', 'NSCLC', 'GIST', 'HCC',
                                 '肺癌', '肝癌', '乳腺癌', '胰腺癌', '前列腺癌', '卵巢癌',
                                 '宫颈癌', '黑色素瘤', '胶质瘤', '肉瘤'])

                            if is_cancer and (not indication or
                                any(kw in indication for kw in ['2025', '2026', '2024'])):
                                added = save_drug_to_db({
                                    'drug_name': drug_name,
                                    'indication': indication,
                                    'applicant': '',
                                    'date': '',
                                    'detail_url': url
                                })
                                if added:
                                    collected += 1
                                    print(f"  ✅ 找到: {drug_name}")

                        i += 1

                except Exception as e:
                    print(f"  ⚠️ 访问出错: {e}")
                    continue

            # 保存HTML供调试
            output_file = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                       'cde_playwright_output.html')
            try:
                with open(output_file, 'w', encoding='utf-8') as f:
                    f.write(page.content())
                print(f"\nHTML已保存: {os.path.basename(output_file)}")
            except Exception as e:
                print(f"  HTML保存失败: {e}")

            browser.close()

    except Exception as e:
        print(f"Playwright错误: {e}")

    return collected

# 执行收集
print("启动浏览器收集...")
added = collect_cde_with_playwright()
print(f"\n✅ Playwright收集完成，新增 {added} 条数据")

# 统计
conn = sqlite3.connect(db_path)
cursor = conn.cursor()
total = cursor.execute("SELECT COUNT(*) FROM approved_drugs WHERE regulatory_agency = 'NMPA'").fetchone()[0]
print(f"\nNMPA药物总数: {total}")

years = cursor.execute("""
    SELECT substr(approval_date, 1, 4) as year, COUNT(*) as cnt
    FROM approved_drugs
    WHERE regulatory_agency = 'NMPA' AND approval_date IS NOT NULL AND approval_date != ''
    GROUP BY year ORDER BY year DESC
""").fetchall()

print("\n按批准年份:")
for y in years:
    print(f"  {y[0]}: {y[1]} 条")
conn.close()
