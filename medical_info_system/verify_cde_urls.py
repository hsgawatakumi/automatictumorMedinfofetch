#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
验证CDE链接 - 检查突破性治疗和优先审评的URL
"""

import time
import logging
from playwright.sync_api import sync_playwright

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# 原始链接（可能是优先审评）
OLD_URL = "https://www.cde.org.cn/main/xxgk/listpage/2f78f372d351c6851af7431c7710a731"
# 用户提供的链接（可能是突破性治疗）
NEW_URL = "https://www.cde.org.cn/main/xxgk/listpage/b40868b5e21c038a6aa8b4319d21b07d"


def check_page(page_num, url, label):
    """检查页面内容"""
    logger.info(f"\n{'='*60}")
    logger.info(f"检查 {label}: {url}")
    logger.info(f"{'='*60}")
    
    page.goto(url, wait_until="domcontentloaded", timeout=60000)
    time.sleep(5)
    
    # 获取菜单信息
    menu_info = page.evaluate("""
        () => {
            const menuItems = document.querySelectorAll('li');
            const menus = [];
            
            for (let item of menuItems) {
                const text = item.textContent.trim();
                if (text.includes('公示') || text.includes('名单') || text.includes('审评') || text.includes('治疗')) {
                    menus.push({
                        text: text,
                        hasChildren: item.querySelectorAll('li').length > 0
                    });
                }
            }
            
            return menus.slice(0, 10); // 只返回前10个
        }
    """)
    
    logger.info("找到的菜单项:")
    for item in menu_info:
        logger.info(f"  - {item['text']}")
    
    # 获取表格信息
    tables = page.evaluate("""
        () => {
            const tables = document.querySelectorAll('table');
            const result = [];
            
            for (let i = 0; i < tables.length; i++) {
                const rows = tables[i].querySelectorAll('tr');
                if (rows.length > 5) {
                    const header = rows[0].innerText;
                    if (header.includes('序号') && header.includes('药品名称')) {
                        // 获取列名
                        const headerCells = rows[0].querySelectorAll('td, th');
                        const columns = Array.from(headerCells).map(c => c.textContent.trim());
                        
                        // 获取第一行数据
                        const firstRowCells = rows[1].querySelectorAll('td');
                        const firstRow = Array.from(firstRowCells).map(c => c.textContent.trim());
                        
                        result.push({
                            index: i,
                            columns: columns,
                            firstRow: firstRow
                        });
                    }
                }
            }
            
            return result;
        }
    """)
    
    logger.info(f"\n找到 {len(tables)} 个数据表格:")
    for table in tables:
        logger.info(f"  表格 {table['index']}:")
        logger.info(f"    列名: {table['columns']}")
        logger.info(f"    第一行: {table['firstRow']}")
        
        # 判断是优先审评还是突破性治疗
        columns_str = ','.join(table['columns'])
        if '承办日期' in columns_str:
            logger.info(f"    判定: 优先审评（有承办日期）")
        elif '公示日期' in columns_str:
            logger.info(f"    判定: 突破性治疗（无承办日期，有公示日期）")
        else:
            logger.info(f"    判定: 未知")


def main():
    with sync_playwright() as p:
        global browser, context, page
        
        logger.info("启动浏览器...")
        browser = p.chromium.launch(
            headless=False,
            slow_mo=500,
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
            # 检查原始链接
            check_page(1, OLD_URL, "原始链接")
            
            # 等待
            time.sleep(3)
            
            # 检查用户提供的链接
            check_page(2, NEW_URL, "用户提供的链接")
            
            logger.info("\n等待10秒让您查看...")
            time.sleep(10)
            
        except Exception as e:
            logger.error(f"检查失败: {e}")
            import traceback
            traceback.print_exc()
        finally:
            browser.close()


if __name__ == '__main__':
    main()
