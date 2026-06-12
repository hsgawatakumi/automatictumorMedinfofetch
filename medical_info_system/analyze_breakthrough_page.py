#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试分析突破性治疗页面的弹窗结构
"""

import time
import logging
from playwright.sync_api import sync_playwright

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

CDE_BASE_URL = "https://www.cde.org.cn/main/xxgk/listpage/2f78f372d351c6851af7431c7710a731"


def analyze_page():
    with sync_playwright() as p:
        browser = p.chromium.launch(
            headless=False,
            slow_mo=1000,
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
            
            logger.info("查找菜单...")
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
            
            logger.info("获取表格数据...")
            tables_info = page.evaluate("""
                () => {
                    const tables = document.querySelectorAll('table');
                    const result = [];
                    
                    tables.forEach((table, idx) => {
                        const rows = table.querySelectorAll('tr');
                        if (rows.length > 5) {
                            const headerRow = rows[0];
                            const headerCells = headerRow.querySelectorAll('td, th');
                            const headers = Array.from(headerCells).map(c => c.textContent.trim());
                            
                            result.push({
                                index: idx,
                                rows_count: rows.length,
                                headers: headers,
                                sample_row: rows[1] ? Array.from(rows[1].querySelectorAll('td')).map(c => c.textContent.trim()) : []
                            });
                        }
                    });
                    
                    return result;
                }
            """)
            
            logger.info(f"找到 {len(tables_info)} 个表格:")
            for info in tables_info:
                logger.info(f"  表格 {info['index']}: {info['rows_count']} 行")
                logger.info(f"    表头: {info['headers']}")
                logger.info(f"    样例行: {info['sample_row']}")
            
            logger.info("点击第一行查看弹窗...")
            page.evaluate("""
                () => {
                    const tables = document.querySelectorAll('table');
                    for (let table of tables) {
                        const rows = table.querySelectorAll('tr');
                        if (rows.length > 5) {
                            const row = rows[1];
                            if (row) {
                                row.scrollIntoView({ behavior: 'smooth', block: 'center' });
                                
                                const dblClickEvent = new MouseEvent('dblclick', {
                                    view: window,
                                    bubbles: true,
                                    cancelable: true
                                });
                                row.dispatchEvent(dblClickEvent);
                                
                                return { success: true, row_text: row.textContent.trim() };
                            }
                        }
                    }
                    return { success: false };
                }
            """)
            time.sleep(3)
            
            logger.info("分析弹窗内容...")
            popup_info = page.evaluate("""
                () => {
                    const result = {};
                    
                    // 查找所有可能的弹窗容器
                    const possiblePopups = [];
                    const allDivs = document.querySelectorAll('div');
                    
                    allDivs.forEach(div => {
                        const style = window.getComputedStyle(div);
                        if (style.display !== 'none' && style.zIndex > 1000) {
                            possiblePopups.push({
                                id: div.id,
                                class: div.className,
                                html: div.innerHTML.substring(0, 1000)
                            });
                        }
                    });
                    
                    result.possible_popups = possiblePopups;
                    
                    // 查找所有包含"拟定适应症"的内容
                    const allText = document.body.innerText;
                    const indicationMatch = allText.match(/拟定适应症[\\s\\S]{0,500}/);
                    if (indicationMatch) {
                        result.indication_context = indicationMatch[0];
                    }
                    
                    // 查找所有表格
                    const tables = document.querySelectorAll('table');
                    const tablesData = [];
                    tables.forEach((table, idx) => {
                        tablesData.push({
                            index: idx,
                            id: table.id,
                            class: table.className,
                            html: table.outerHTML.substring(0, 2000)
                        });
                    });
                    result.tables_in_popup = tablesData;
                    
                    return result;
                }
            """)
            
            logger.info("弹窗分析结果:")
            logger.info(f"  找到 {len(popup_info.get('possible_popups', []))} 个可能的弹窗")
            for popup in popup_info.get('possible_popups', []):
                logger.info(f"    ID: {popup.get('id')}, Class: {popup.get('class')}")
            
            if popup_info.get('indication_context'):
                logger.info(f"  适应症上下文: {popup_info['indication_context']}")
            
            logger.info(f"  弹窗中的表格: {len(popup_info.get('tables_in_popup', []))}")
            for table in popup_info.get('tables_in_popup', []):
                logger.info(f"    表格 {table['index']}: ID={table.get('id')}, Class={table.get('class')}")
            
            logger.info("等待10秒让您查看页面...")
            time.sleep(10)
            
        except Exception as e:
            logger.error(f"分析失败: {e}")
            import traceback
            traceback.print_exc()
        finally:
            browser.close()


if __name__ == '__main__':
    analyze_page()
