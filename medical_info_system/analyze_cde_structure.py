#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
分析CDE突破性治疗页面的表格结构
"""

import time
import logging
from playwright.sync_api import sync_playwright

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

CDE_BASE_URL = "https://www.cde.org.cn/main/xxgk/listpage/2f78f372d351c6851af7431c7710a731"


def analyze_table_structure():
    with sync_playwright() as p:
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
            
            # 点击突破性治疗公示
            logger.info("点击菜单...")
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
            
            # 分析表格结构
            logger.info("\n分析突破性治疗页面的表格结构...")
            
            result = page.evaluate("""
                () => {
                    const tables = document.querySelectorAll('table');
                    const result = {
                        table_count: tables.length,
                        tables: []
                    };
                    
                    // 检查每个表格
                    for (let i = 0; i < tables.length; i++) {
                        const table = tables[i];
                        const rows = table.querySelectorAll('tr');
                        
                        // 获取表头
                        let headers = [];
                        if (rows.length > 0) {
                            const headerCells = rows[0].querySelectorAll('td, th');
                            headers = Array.from(headerCells).map(c => c.textContent.trim());
                        }
                        
                        // 获取前3行数据
                        let sampleRows = [];
                        for (let j = 1; j < Math.min(4, rows.length); j++) {
                            const cells = rows[j].querySelectorAll('td');
                            const rowData = Array.from(cells).map(c => c.textContent.trim());
                            sampleRows.push(rowData);
                        }
                        
                        result.tables.push({
                            index: i,
                            rows_count: rows.length,
                            headers: headers,
                            sample_rows: sampleRows,
                            has_seq: headers.includes('序号'),
                            has_drug_name: headers.includes('药品名称'),
                            has_acceptance: headers.includes('受理号'),
                            has_applicant: headers.includes('申请人'),
                            has_date: headers.some(h => h.includes('日期'))
                        });
                    }
                    
                    return result;
                }
            """)
            
            logger.info(f"\n找到 {result['table_count']} 个表格:")
            for table in result['tables']:
                if table['rows_count'] > 5:  # 只显示有数据的表格
                    logger.info(f"\n  表格 {table['index']}:")
                    logger.info(f"    行数: {table['rows_count']}")
                    logger.info(f"    表头: {table['headers']}")
                    logger.info(f"    第一行数据: {table['sample_rows'][0] if table['sample_rows'] else '无'}")
                    logger.info(f"    第二行数据: {table['sample_rows'][1] if len(table['sample_rows']) > 1 else '无'}")
                    logger.info(f"    是否包含序号: {table['has_seq']}")
                    logger.info(f"    是否包含药品名称: {table['has_drug_name']}")
                    logger.info(f"    是否包含受理号: {table['has_acceptance']}")
                    logger.info(f"    是否包含申请人: {table['has_applicant']}")
                    logger.info(f"    是否包含日期: {table['has_date']}")
            
            # 查找TQB3454片的位置
            logger.info("\n查找TQB3454片...")
            search_result = page.evaluate("""
                () => {
                    const tables = document.querySelectorAll('table');
                    for (let i = 0; i < tables.length; i++) {
                        const rows = tables[i].querySelectorAll('tr');
                        for (let j = 1; j < rows.length; j++) {
                            const text = rows[j].textContent;
                            if (text.includes('TQB3454')) {
                                const cells = rows[j].querySelectorAll('td');
                                return {
                                    table_index: i,
                                    row_index: j,
                                    cells: Array.from(cells).map(c => ({
                                        text: c.textContent.trim(),
                                        index: cells.indexOf(c)
                                    }))
                                };
                            }
                        }
                    }
                    return null;
                }
            """)
            
            if search_result:
                logger.info(f"找到TQB3454片:")
                logger.info(f"  表格索引: {search_result['table_index']}")
                logger.info(f"  行索引: {search_result['row_index']}")
                logger.info(f"  单元格数据:")
                for cell in search_result['cells']:
                    logger.info(f"    单元格{cell['index']}: {cell['text']}")
            else:
                logger.warning("未找到TQB3454片")
            
            # 双击TQB3454片查看详情
            if search_result:
                logger.info("\n双击TQB3454片查看弹窗...")
                
                page.evaluate("""
                    () => {
                        const tables = document.querySelectorAll('table');
                        const rows = tables[0].querySelectorAll('tr');
                        const targetRow = rows[3]; // 第3行是TQB3454片
                        if (targetRow) {
                            targetRow.scrollIntoView({ behavior: 'smooth', block: 'center' });
                            const dblClickEvent = new MouseEvent('dblclick', {
                                view: window,
                                bubbles: true,
                                cancelable: true
                            });
                            targetRow.dispatchEvent(dblClickEvent);
                        }
                    }
                """)
                
                time.sleep(3)
                
                # 分析弹窗内容
                popup_result = page.evaluate("""
                    () => {
                        // 查找弹窗
                        const bodyText = document.body.innerText;
                        
                        // 提取所有包含TQB3454的内容
                        const tqbInfo = [];
                        const lines = bodyText.split('\\n');
                        for (let i = 0; i < lines.length; i++) {
                            if (lines[i].includes('TQB3454')) {
                                tqbInfo.push({
                                    line: i,
                                    text: lines[i],
                                    context_before: lines[Math.max(0, i-2)],
                                    context_after: lines[Math.min(lines.length-1, i+2)]
                                });
                            }
                        }
                        
                        // 查找拟定适应症
                        const indicationMatch = bodyText.match(/拟定适应症[\\s\\S]{0,500}/);
                        
                        return {
                            tqb_lines: tqbInfo,
                            indication_context: indicationMatch ? indicationMatch[0] : null
                        };
                    }
                """)
                
                logger.info("弹窗内容分析:")
                if popup_result['tqb_lines']:
                    logger.info(f"  找到 {len(popup_result['tqb_lines'])} 处TQB3454相关内容")
                    for info in popup_result['tqb_lines']:
                        logger.info(f"    行{info['line']}: {info['text']}")
                
                if popup_result['indication_context']:
                    logger.info(f"  拟定适应症相关内容: {popup_result['indication_context'][:200]}")
            
            logger.info("\n等待10秒让您查看页面...")
            time.sleep(10)
            
        except Exception as e:
            logger.error(f"分析失败: {e}")
            import traceback
            traceback.print_exc()
        finally:
            browser.close()


if __name__ == '__main__':
    analyze_table_structure()
