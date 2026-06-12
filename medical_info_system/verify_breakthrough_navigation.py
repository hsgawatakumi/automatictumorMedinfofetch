#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
验证通过菜单导航到突破性治疗列表的正确性
"""

import time
import logging
from playwright.sync_api import sync_playwright

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

CDE_BASE_URL = "https://www.cde.org.cn/main/xxgk/listpage/2f78f372d351c6851af7431c7710a731"


def verify_navigation():
    """验证导航到突破性治疗列表"""
    with sync_playwright() as p:
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
            logger.info(f"访问: {CDE_BASE_URL}")
            page.goto(CDE_BASE_URL, wait_until="domcontentloaded", timeout=60000)
            time.sleep(5)
            
            # 1. 首先检查默认页面
            logger.info("\n1. 检查默认页面（应该是优先审评）...")
            check_current_page(page, "默认页面")
            
            # 2. 点击突破性治疗公示
            logger.info("\n2. 点击'突破性治疗公示'菜单...")
            page.evaluate("""
                () => {
                    const menuItems = document.querySelectorAll('li');
                    for (let item of menuItems) {
                        if (item.textContent.trim() === '突破性治疗公示') {
                            console.log('找到突破性治疗公示菜单');
                            item.click();
                            return true;
                        }
                    }
                    return false;
                }
            """)
            time.sleep(2)
            
            # 3. 点击纳入突破性治疗品种名单
            logger.info("\n3. 点击'纳入突破性治疗品种名单'...")
            page.evaluate("""
                () => {
                    const menuItems = document.querySelectorAll('li');
                    for (let item of menuItems) {
                        if (item.textContent.trim() === '纳入突破性治疗品种名单') {
                            console.log('找到纳入突破性治疗品种名单菜单');
                            item.click();
                            return true;
                        }
                    }
                    return false;
                }
            """)
            time.sleep(5)
            
            # 4. 检查导航后的页面
            logger.info("\n4. 检查导航后的页面（应该是突破性治疗）...")
            check_current_page(page, "导航后页面")
            
            # 5. 获取第一行药物名称
            logger.info("\n5. 获取第一行药物名称...")
            first_drug = page.evaluate("""
                () => {
                    const tables = document.querySelectorAll('table');
                    for (let table of tables) {
                        const rows = table.querySelectorAll('tr');
                        if (rows.length > 5) {
                            const header = rows[0].innerText;
                            if (header.includes('序号') && header.includes('药品名称')) {
                                const cells = rows[1].querySelectorAll('td');
                                if (cells.length >= 3) {
                                    return {
                                        drugName: cells[2].textContent.trim(),
                                        acceptance: cells[1].textContent.trim(),
                                        appDate: cells.length > 4 ? cells[4].textContent.trim() : 'N/A'
                                    };
                                }
                            }
                        }
                    }
                    return null;
                }
            """)
            
            if first_drug:
                logger.info(f"  药物名称: {first_drug['drugName']}")
                logger.info(f"  受理号: {first_drug['acceptance']}")
                logger.info(f"  申请日期: {first_drug['appDate']}")
            
            logger.info("\n等待10秒让您查看...")
            time.sleep(10)
            
        except Exception as e:
            logger.error(f"验证失败: {e}")
            import traceback
            traceback.print_exc()
        finally:
            browser.close()


def check_current_page(page, label):
    """检查当前页面的表格结构"""
    tables = page.evaluate("""
        () => {
            const tables = document.querySelectorAll('table');
            const result = [];
            
            for (let i = 0; i < tables.length; i++) {
                const rows = tables[i].querySelectorAll('tr');
                if (rows.length > 5) {
                    const header = rows[0].innerText;
                    if (header.includes('序号') && header.includes('药品名称')) {
                        const headerCells = rows[0].querySelectorAll('td, th');
                        const columns = Array.from(headerCells).map(c => c.textContent.trim());
                        
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
    
    logger.info(f"\n{label} - 找到 {len(tables)} 个数据表格:")
    for table in tables:
        logger.info(f"  表格 {table['index']}:")
        logger.info(f"    列名: {table['columns']}")
        logger.info(f"    第一行: {table['firstRow']}")
        
        columns_str = ','.join(table['columns'])
        if '承办日期' in columns_str and '申请日期' in columns_str:
            logger.info(f"    判定: ✅ 优先审评（有承办日期和申请日期）")
            logger.info(f"    申请日期列位置: cells[{table['columns'].index('申请日期')}]")
        elif '公示日期' in columns_str and '承办日期' not in columns_str:
            logger.info(f"    判定: ✅ 突破性治疗（无承办日期，有公示日期）")
            logger.info(f"    申请日期列位置: cells[{table['columns'].index('申请日期')}]")
        else:
            logger.info(f"    判定: 未知")


if __name__ == '__main__':
    verify_navigation()
