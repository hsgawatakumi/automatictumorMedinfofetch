#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""诊断CDE网站翻页机制 - 深入版"""

import os
import sys
import time
from playwright.sync_api import sync_playwright

CDE_BASE_URL = "https://www.cde.org.cn/main/xxgk/listpage/2f78f372d351c6851af7431c7710a731"

def diagnose_pagination():
    with sync_playwright() as p:
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

        # 监听所有网络请求
        def handle_request(request):
            url = request.url
            if 'cde.org.cn' in url:
                print(f"  [Request] {request.method} {url[:120]}")

        page.on('request', handle_request)

        try:
            print("访问网站...")
            page.goto(CDE_BASE_URL, wait_until="domcontentloaded", timeout=60000)
            time.sleep(5)

            print("点击菜单...")
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

            # 查找突破性治疗表格
            breakthrough_table_index = page.evaluate("""
                () => {
                    const tables = document.querySelectorAll('table');
                    for (let i = 0; i < tables.length; i++) {
                        const rows = tables[i].querySelectorAll('tr');
                        if (rows.length > 5) {
                            const header = rows[0].innerText;
                            if (header.indexOf('序号') >= 0 && header.indexOf('药品名称') >= 0) {
                                const headerCells = rows[0].querySelectorAll('td');
                                const headers = Array.from(headerCells).map(c => c.textContent.trim());
                                if (!headers.includes('承办日期') && headers.includes('申请日期')) {
                                    return i;
                                }
                            }
                        }
                    }
                    return -1;
                }
            """)

            print(f"\n突破性治疗表格索引: {breakthrough_table_index}")

            # 获取第一页数据
            def get_page_data(table_idx):
                return page.evaluate("""
                    (tableIdx) => {
                        const tables = document.querySelectorAll('table');
                        const targetTable = tables[tableIdx];
                        if (!targetTable) return { found: false };

                        const rows = targetTable.querySelectorAll('tr');
                        const data = [];
                        for (let j = 1; j < Math.min(rows.length, 12); j++) {
                            const cells = rows[j].querySelectorAll('td');
                            if (cells.length >= 5) {
                                data.push({
                                    seq: cells[0]?.innerText?.trim() || '',
                                    drugName: cells[2]?.innerText?.trim() || ''
                                });
                            }
                        }
                        return { found: true, data: data };
                    }
                """, table_idx)

            print("\n=== 第 1 页数据 ===")
            page_data = get_page_data(breakthrough_table_index)
            if page_data.get('found'):
                for item in page_data['data'][:5]:
                    print(f"  序号 {item['seq']}: {item['drugName']}")

            # 分析layui分页器
            print("\n=== 分析layui分页器 ===")
            page.evaluate("""
                () => {
                    // 查找layui分页器
                    const laypageElements = document.querySelectorAll('.layui-laypage');
                    console.log('Layui分页器数量:', laypageElements.length);

                    for (let i = 0; i < laypageElements.length; i++) {
                        const p = laypageElements[i];
                        console.log(`\\n分页器${i}:`);
                        console.log('  包含表格索引:', p.getAttribute('lay-id') || '无');

                        // 查找下一页按钮
                        const nextBtn = p.querySelector('.layui-laypage-next');
                        if (nextBtn) {
                            console.log('  下一页按钮:', nextBtn.className, 'data-page:', nextBtn.getAttribute('data-page'));
                        }
                    }

                    // 查找所有分页相关的数据
                    const allDivs = document.querySelectorAll('div[lay-id]');
                    console.log('\\n有lay-id的div数量:', allDivs.length);
                    for (let d of allDivs) {
                        console.log('  div lay-id:', d.getAttribute('lay-id'), 'class:', d.className.substring(0, 50));
                    }
                }
            """)

            time.sleep(2)

            # 尝试方法1：直接触发layui事件
            print("\n=== 方法1: 触发layui分页事件 ===")
            page.evaluate("""
                () => {
                    // 找到包含突破性治疗表格的分页器
                    const tables = document.querySelectorAll('table');
                    const targetTable = tables[13];  // 突破性治疗表格

                    // 向上查找layui分页器
                    let container = targetTable?.parentElement;
                    let laypage = null;
                    for (let i = 0; i < 10; i++) {
                        if (container) {
                            const lps = container.querySelectorAll('.layui-laypage');
                            if (lps.length > 0) {
                                laypage = lps[0];
                                break;
                            }
                            container = container.parentElement;
                        }
                    }

                    if (laypage) {
                        console.log('找到关联的分页器');

                        // 查找下一页按钮
                        const nextBtn = laypage.querySelector('.layui-laypage-next');
                        if (nextBtn) {
                            console.log('点击下一页按钮...');
                            // 尝试派发click事件
                            const event = new MouseEvent('click', { bubbles: true, cancelable: true });
                            nextBtn.dispatchEvent(event);
                            console.log('已派发click事件');
                        }
                    } else {
                        console.log('未找到关联的分页器，尝试直接调用layui方法');
                        // 尝试直接调用layui分页方法
                        if (window.laypage) {
                            console.log('laypage对象存在');
                        }
                    }
                }
            """)

            print("等待5秒...")
            time.sleep(5)

            print("\n=== 方法1后数据 ===")
            page_data2 = get_page_data(breakthrough_table_index)
            if page_data2.get('found'):
                for item in page_data2['data'][:5]:
                    print(f"  序号 {item['seq']}: {item['drugName']}")

            # 尝试方法2：使用Playwright等待网络请求
            print("\n=== 方法2: 使用waitForResponse ===")
            page.evaluate("""
                () => {
                    const nextBtn = document.querySelector('.layui-laypage-next');
                    if (nextBtn) {
                        console.log('再次点击下一页...');
                        nextBtn.click();
                    }
                }
            """)

            # 等待网络响应
            print("等待网络响应...")
            try:
                response = page.wait_for_response(
                    lambda r: 'cde.org.cn' in r.url and ('listpage' in r.url or 'xxgk' in r.url),
                    timeout=10000
                )
                print(f"捕获到响应: {response.url[:100]}")
            except Exception as e:
                print(f"未捕获到预期的网络响应: {e}")

            time.sleep(3)

            print("\n=== 方法2后数据 ===")
            page_data3 = get_page_data(breakthrough_table_index)
            if page_data3.get('found'):
                for item in page_data3['data'][:5]:
                    print(f"  序号 {item['seq']}: {item['drugName']}")

            # 尝试方法3：直接修改页码
            print("\n=== 方法3: 直接操作页码 ===")
            page.evaluate("""
                () => {
                    // 查找所有带data-page属性的元素
                    const pageElements = document.querySelectorAll('[data-page]');
                    console.log('带data-page的元素数量:', pageElements.length);

                    // 尝试找到第2页的链接
                    for (let el of pageElements) {
                        const page = el.getAttribute('data-page');
                        if (page === '2') {
                            console.log('找到第2页元素:', el.tagName, el.className, el.textContent.trim());
                            // 点击它
                            el.click();
                            return;
                        }
                    }

                    // 如果没找到，尝试直接调用layui
                    console.log('未找到第2页元素，尝试其他方法');

                    // 尝试找到layui laypage对象
                    const laypageDivs = document.querySelectorAll('.layui-laypage');
                    for (let lp of laypageDivs) {
                        const layId = lp.getAttribute('lay-id');
                        if (layId) {
                            console.log('找到lay-id:', layId);
                            // 尝试通过lay-id找到对应的table
                        }
                    }
                }
            """)

            time.sleep(5)

            print("\n=== 方法3后数据 ===")
            page_data4 = get_page_data(breakthrough_table_index)
            if page_data4.get('found'):
                for item in page_data4['data'][:5]:
                    print(f"  序号 {item['seq']}: {item['drugName']}")

        except Exception as e:
            print(f"错误: {e}")
            import traceback
            traceback.print_exc()
        finally:
            input("按Enter键关闭浏览器...")
            browser.close()


if __name__ == '__main__':
    diagnose_pagination()