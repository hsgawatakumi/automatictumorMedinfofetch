#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
CDE官网抗肿瘤药物自动化采集脚本
使用Playwright + playwright-stealth方案绕过WAF防护
"""
import asyncio
import csv
import json
import os
import random
import sys
import time
from datetime import datetime
from pathlib import Path

# 添加项目路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))


class CDECancerDrugCollector:
    """CDE抗肿瘤药物采集器"""
    
    BREAKTHROUGH_LIST_URL = "https://www.cde.org.cn/main/xxgk/listpage/9f9c74c73e0f7f8a0d38327fb2570e9f"
    PRIORITY_LIST_URL = "https://www.cde.org.cn/main/xxgk/listpage/2f78f37271f3f38a0d38327fb2570e9f"
    
    # 抗肿瘤关键词列表
    CANCER_KEYWORDS = [
        '癌', '瘤', '肿瘤', '白血病', '淋巴瘤', '骨髓瘤', '黑色素瘤', 
        '胶质瘤', '肉瘤', '肝细胞癌', '非小细胞肺癌', '小细胞肺癌', 
        '胰腺癌', '胃癌', '结直肠癌', '乳腺癌', '前列腺癌', '卵巢癌',
        '宫颈癌', '子宫内膜癌', '肾癌', '膀胱癌', '甲状腺癌', '胆管癌',
        '鼻咽癌', '食管癌', '头颈部癌', '神经内分泌瘤', '腺癌', '鳞癌',
        'NSCLC', 'SCLC', '实体瘤', '腺瘤', '间皮瘤', '睾丸癌', '卵巢癌'
    ]
    
    def __init__(self):
        self.browser = None
        self.context = None
        self.page = None
        self.collected_data = []
        self.progress_file = project_root / 'data' / 'cde_collection_progress.json'
        self.log_file = project_root / 'data' / 'cde_collection.log'
        
        # 确保数据目录存在
        (project_root / 'data').mkdir(exist_ok=True)
        
    async def initialize(self):
        """初始化Playwright和浏览器"""
        try:
            from playwright.async_api import async_playwright
            from playwright_stealth import stealth_async
            
            print("正在启动Playwright浏览器...")
            
            self.playwright = await async_playwright().start()
            
            # 使用持久化上下文配置
            self.context = await self.playwright.chromium.launch_persistent_context(
                user_data_dir=str(project_root / 'data' / 'chrome_profile'),
                headless=False,  # 初次调试用有头模式
                args=[
                    '--disable-blink-features=AutomationControlled',
                    '--disable-web-security',
                    '--no-sandbox',
                    '--disable-setuid-sandbox',
                    '--disable-dev-shm-usage'
                ]
            )
            
            # 应用stealth插件
            if len(self.context.pages) > 0:
                self.page = self.context.pages[0]
                await stealth_async(self.page)
            else:
                self.page = await self.context.new_page()
                await stealth_async(self.page)
            
            # 配置视口和语言
            await self.page.set_viewport_size({"width": 1920, "height": 1080})
            await self.page.set_extra_http_headers({
                "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8"
            })
            
            print("浏览器启动成功！")
            return True
            
        except Exception as e:
            print(f"浏览器启动失败: {e}")
            import traceback
            traceback.print_exc()
            return False
    
    async def collect_drug_list(self, url: str, list_type: str, max_pages: int = 10):
        """采集药物列表"""
        all_drugs = []
        
        print(f"\n开始采集{list_type}名单...")
        print(f"目标URL: {url}")
        
        try:
            # 访问页面
            await self.page.goto(url, wait_until="networkidle", timeout=60000)
            await asyncio.sleep(2)  # 等待页面完全加载
            
            # 遍历所有页面
            for page_num in range(1, max_pages + 1):
                print(f"\n正在处理第 {page_num}/{max_pages} 页...")
                
                # 检查当前页是否有数据
                try:
                    # 等待表格加载
                    await self.page.wait_for_selector("table", timeout=5000)
                    await asyncio.sleep(1.5)
                    
                    # 获取当前页所有药物行
                    drug_rows = await self.get_page_drug_rows()
                    print(f"  第{page_num}页找到 {len(drug_rows)} 个药物")
                    
                    # 处理每一行
                    for row_index, row_data in enumerate(drug_rows, 1):
                        try:
                            # 点击药物名称获取详情
                            drug_detail = await self.get_drug_detail(row_data, list_type)
                            if drug_detail:
                                all_drugs.append(drug_detail)
                                print(f"  [{row_index}] {drug_detail['drug_name']} - 已提取")
                            
                            # 随机延迟
                            await asyncio.sleep(random.uniform(0.5, 1.5))
                            
                        except Exception as e:
                            print(f"  [{row_index}] 处理失败: {e}")
                            await self.log_error(f"处理第{page_num}页第{row_index}行失败: {e}")
                            continue
                    
                    # 页间延迟
                    await asyncio.sleep(random.uniform(3, 5))
                    
                    # 点击下一页
                    if page_num < max_pages:
                        success = await self.click_next_page()
                        if not success:
                            print(f"  无法跳转到第{page_num+1}页，停止采集")
                            break
                        await asyncio.sleep(2)  # 等待新页面加载
                    
                except Exception as e:
                    print(f"  处理第{page_num}页失败: {e}")
                    await self.log_error(f"处理第{page_num}页失败: {e}")
                    continue
            
        except Exception as e:
            print(f"采集过程失败: {e}")
            await self.log_error(f"采集失败: {e}")
        
        return all_drugs
    
    async def get_page_drug_rows(self):
        """获取当前页的药物行数据"""
        rows = []
        
        try:
            # 等待表格加载
            table = await self.page.wait_for_selector("table tbody", timeout=5000)
            
            # 获取所有行
            tr_elements = await table.query_selector_all("tr")
            
            for tr in tr_elements:
                row_data = {}
                
                # 获取所有单元格
                tds = await tr.query_selector_all("td")
                if len(tds) >= 5:
                    row_data['序号'] = await tds[0].inner_text()
                    row_data['药物名称'] = await tds[1].inner_text()
                    row_data['受理号'] = await tds[2].inner_text()
                    row_data['申请人'] = await tds[3].inner_text()
                    row_data['申请日期'] = await tds[4].inner_text()
                    
                    # 获取药物名称链接
                    link = await tds[1].query_selector("a")
                    if link:
                        row_data['link_element'] = link
                    
                    rows.append(row_data)
                    
        except Exception as e:
            print(f"获取页面行失败: {e}")
        
        return rows
    
    async def get_drug_detail(self, row_data: dict, list_type: str) -> dict:
        """获取药物详情"""
        drug_info = {
            '名单类型': list_type,
            '序号': row_data.get('序号', ''),
            '药物名称': row_data.get('药物名称', ''),
            '受理号': row_data.get('受理号', ''),
            '申请人': row_data.get('申请人', ''),
            '申请日期': row_data.get('申请日期', ''),
            '拟定适应症': '',
            '分子靶点': '',
            '是否抗肿瘤': False
        }
        
        try:
            # 点击药物名称
            if 'link_element' in row_data:
                link = row_data['link_element']
                await link.click()
                
                # 等待弹窗出现
                await asyncio.sleep(1)
                
                # 查找弹窗内容
                modal = await self.page.wait_for_selector(
                    ".ant-modal, .modal, [role='dialog'], .el-dialog",
                    timeout=5000
                )
                
                if modal:
                    # 获取弹窗全部文本
                    modal_text = await modal.inner_text()
                    
                    # 提取拟定适应症
                    if '拟定适应症' in modal_text or '功能主治' in modal_text:
                        lines = modal_text.split('\n')
                        for i, line in enumerate(lines):
                            if '拟定适应症' in line or '功能主治' in line:
                                if i + 1 < len(lines):
                                    drug_info['拟定适应症'] = lines[i + 1].strip()
                                break
                            # 直接匹配
                            for keyword in ['适应症', '适应证', '功能主治']:
                                if keyword in line and i + 1 < len(lines):
                                    drug_info['拟定适应症'] = lines[i + 1].strip()
                                    break
                    
                    # 提取分子靶点（如果有）
                    if '分子靶点' in modal_text or '靶点' in modal_text:
                        lines = modal_text.split('\n')
                        for i, line in enumerate(lines):
                            if '分子靶点' in line or '靶点' in line:
                                if i + 1 < len(lines):
                                    drug_info['分子靶点'] = lines[i + 1].strip()
                                break
                    
                    # 判断是否为抗肿瘤药物
                    drug_info['是否抗肿瘤'] = self.is_cancer_drug(drug_info['拟定适应症'])
                    
                    # 关闭弹窗
                    close_button = await modal.query_selector(
                        "button[class*='close'], .ant-modal-close, [aria-label='Close'], button:has-text('×')"
                    )
                    if close_button:
                        await close_button.click()
                    else:
                        # 按ESC关闭
                        await self.page.keyboard.press("Escape")
                    
                    await asyncio.sleep(0.5)
                    
        except Exception as e:
            print(f"获取详情失败: {e}")
            # 确保关闭弹窗
            try:
                await self.page.keyboard.press("Escape")
                await asyncio.sleep(0.5)
            except:
                pass
        
        return drug_info
    
    def is_cancer_drug(self, indication: str) -> bool:
        """判断是否为抗肿瘤药物"""
        if not indication:
            return False
        
        indication_lower = indication.lower()
        for keyword in self.CANCER_KEYWORDS:
            if keyword.lower() in indication_lower or keyword in indication:
                return True
        
        return False
    
    async def click_next_page(self) -> bool:
        """点击下一页"""
        try:
            # 查找下一页按钮
            next_button = await self.page.query_selector(
                "button:has-text('下一页'), .ant-pagination-next, .el-pagination button[class*='next']"
            )
            
            if next_button:
                # 检查是否禁用
                is_disabled = await next_button.get_attribute("disabled")
                aria_disabled = await next_button.get_attribute("aria-disabled")
                
                if is_disabled == "true" or aria_disabled == "true":
                    return False
                
                await next_button.click()
                await asyncio.sleep(1.5)
                return True
            
            # 尝试直接点击页码按钮
            page_buttons = await self.page.query_selector_all(
                ".ant-pagination-item, .el-pagination button[class*='number']"
            )
            
            if page_buttons:
                for btn in page_buttons:
                    btn_text = await btn.inner_text()
                    if btn_text.strip().isdigit():
                        await btn.click()
                        await asyncio.sleep(1.5)
                        return True
            
            return False
            
        except Exception as e:
            print(f"点击下一页失败: {e}")
            return False
    
    async def log_error(self, message: str):
        """记录错误日志"""
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        log_entry = f"[{timestamp}] {message}\n"
        
        with open(self.log_file, 'a', encoding='utf-8') as f:
            f.write(log_entry)
    
    async def save_to_csv(self, drugs: list, filename: str):
        """保存为CSV文件"""
        if not drugs:
            print("没有数据可保存")
            return
        
        filepath = project_root / 'data' / filename
        
        with open(filepath, 'w', newline='', encoding='utf-8-sig') as f:
            writer = csv.DictWriter(f, fieldnames=[
                '名单类型', '序号', '药物名称', '受理号', '申请人', 
                '申请日期', '拟定适应症', '分子靶点', '是否抗肿瘤'
            ])
            writer.writeheader()
            writer.writerows(drugs)
        
        print(f"\n数据已保存到: {filepath}")
        print(f"共 {len(drugs)} 条记录")
        
        # 统计抗肿瘤药物数量
        cancer_drugs = [d for d in drugs if d.get('是否抗肿瘤', False)]
        print(f"其中抗肿瘤药物: {len(cancer_drugs)} 条")
    
    async def close(self):
        """关闭浏览器"""
        if self.context:
            await self.context.close()
        if self.playwright:
            await self.playwright.stop()


async def main():
    """主函数"""
    print("=" * 70)
    print("CDE官网抗肿瘤药物自动化采集程序")
    print("使用Playwright + playwright-stealth方案")
    print("=" * 70)
    
    collector = CDECancerDrugCollector()
    
    try:
        # 初始化浏览器
        success = await collector.initialize()
        if not success:
            print("浏览器初始化失败，请检查是否已安装Playwright和Chromium")
            print("执行命令: pip install playwright && playwright install chromium")
            return
        
        # 采集突破性治疗名单
        breakthrough_drugs = await collector.collect_drug_list(
            collector.BREAKTHROUGH_LIST_URL,
            "突破性治疗",
            max_pages=10
        )
        
        # 采集优先审评名单
        priority_drugs = await collector.collect_drug_list(
            collector.PRIORITY_LIST_URL,
            "优先审评",
            max_pages=10
        )
        
        # 合并数据
        all_drugs = breakthrough_drugs + priority_drugs
        
        # 保存CSV
        await collector.save_to_csv(all_drugs, 'cde_anticancer_drugs.csv')
        
        # 筛选抗肿瘤药物
        cancer_drugs = [d for d in all_drugs if d.get('是否抗肿瘤', False)]
        
        if cancer_drugs:
            await collector.save_to_csv(cancer_drugs, 'cde_cancer_drugs_only.csv')
        
        print("\n" + "=" * 70)
        print("采集完成！")
        print("=" * 70)
        
    except KeyboardInterrupt:
        print("\n用户中断采集...")
    except Exception as e:
        print(f"\n采集失败: {e}")
        import traceback
        traceback.print_exc()
    finally:
        await collector.close()


if __name__ == '__main__':
    asyncio.run(main())
