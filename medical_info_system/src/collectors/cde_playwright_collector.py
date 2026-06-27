import asyncio
import csv
import json
import logging
import os
import random
import re
import time
from datetime import datetime
from typing import Dict, List, Optional

from playwright.async_api import (
    async_playwright,
    Browser,
    BrowserContext,
    Page,
    Response,
)
from playwright_stealth import Stealth

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('cde_playwright_collector.log', encoding='utf-8'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

ANTI_TUMOR_KEYWORDS = [
    "癌", "瘤", "肿瘤", "白血病", "淋巴瘤", "骨髓瘤", "黑色素瘤",
    "胶质瘤", "肉瘤", "肝细胞癌", "非小细胞肺癌", "小细胞肺癌",
    "胰腺癌", "胃癌", "结直肠癌", "乳腺癌", "前列腺癌", "卵巢癌",
    "恶性肿瘤", "抗癌", "抗肿瘤"
]

PRIORITY_REVIEW_URL = "https://www.cde.org.cn/main/xxgk/listpage/2f78f372d351c6851af7431c7710a731"
BREAKTHROUGH_THERAPY_URL = "https://www.cde.org.cn/main/xxgk/listpage/da6efd086c099b7fc949121166f0130c"

CHECKPOINT_FILE = "cde_collect_checkpoint.json"
OUTPUT_FILE = "cde_anti_tumor_drugs.csv"

MAX_RETRIES = 3
PAGES_TO_COLLECT = 50


def is_anti_tumor(indication: str) -> bool:
    if not indication:
        return False
    return any(kw in indication for kw in ANTI_TUMOR_KEYWORDS)


def random_sleep(min_sec: float = 0.5, max_sec: float = 2.0):
    time.sleep(random.uniform(min_sec, max_sec))


def load_checkpoint() -> Dict:
    if os.path.exists(CHECKPOINT_FILE):
        try:
            with open(CHECKPOINT_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            logger.warning(f"加载断点失败: {e}")
    return {
        "priority_review": {"last_page": 0, "drugs_collected": 0},
        "breakthrough_therapy": {"last_page": 0, "drugs_collected": 0}
    }


def save_checkpoint(data: Dict):
    with open(CHECKPOINT_FILE, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def append_to_csv(drugs: List[Dict], filepath: str = OUTPUT_FILE):
    fieldnames = [
        "序号", "药物名称", "受理号", "申请人", "申请日期",
        "拟定适应症（或功能主治）", "分子靶点", "品种类型"
    ]
    file_exists = os.path.exists(filepath) and os.path.getsize(filepath) > 0
    with open(filepath, 'a', encoding='utf-8-sig', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        if not file_exists:
            writer.writeheader()
        for drug in drugs:
            writer.writerow(drug)
    logger.info(f"已追加 {len(drugs)} 条抗肿瘤药物数据到 {filepath}")


async def setup_browser(pw, headless: bool = False) -> tuple[Browser, BrowserContext]:
    browser = await pw.chromium.launch(
        headless=headless,
        args=[
            '--disable-blink-features=AutomationControlled',
            '--no-sandbox',
            '--disable-dev-shm-usage',
            '--disable-gpu',
        ]
    )
    context = await browser.new_context(
        viewport={'width': 1920, 'height': 1080},
        user_agent=(
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) '
            'AppleWebKit/537.36 (KHTML, like Gecko) '
            'Chrome/131.0.0.0 Safari/537.36'
        ),
        locale='zh-CN',
        timezone_id='Asia/Shanghai',
    )
    return browser, context


async def apply_stealth(page: Page):
    stealth = Stealth(
        navigator_languages_override=('zh-CN', 'zh'),
        navigator_platform_override='Win32',
    )
    await stealth.apply_stealth_async(page)


async def navigate_and_select_tab(page: Page, url: str, tab_name: str) -> bool:
    try:
        logger.info(f"正在访问: {url}")
        await page.goto(url, wait_until='domcontentloaded', timeout=60000)
        await page.wait_for_timeout(5000)

        title = await page.title()
        logger.info(f"页面标题: {title}")

        tab_items = await page.query_selector_all('.layui-tab-title li')
        for i, li in enumerate(tab_items):
            try:
                text = (await li.inner_text()).strip()
                logger.info(f"Tab {i}: {text}")
                if tab_name in text:
                    await li.click()
                    await page.wait_for_timeout(3000)
                    logger.info(f"已切换到 tab: {text}")
                    return True
            except Exception:
                continue

        logger.warning(f"未找到 tab '{tab_name}'，使用当前页面")
        return True
    except Exception as e:
        logger.error(f"访问页面失败: {e}")
        return False


async def get_total_pages(page: Page, page_selector: str) -> int:
    try:
        page_el = await page.query_selector(page_selector)
        if page_el:
            count_el = await page_el.query_selector('.layui-laypage-count')
            if count_el:
                text = await count_el.inner_text()
                match = re.search(r'共\s*(\d+)\s*条', text)
                if match:
                    total = int(match.group(1))
                    total_pages = (total + 9) // 10
                    logger.info(f"共 {total} 条记录，约 {total_pages} 页")
                    return min(total_pages, PAGES_TO_COLLECT)
    except Exception as e:
        logger.warning(f"获取总页数失败: {e}")
    return PAGES_TO_COLLECT


async def go_to_page(page: Page, page_selector: str, target_page: int) -> bool:
    for retry in range(MAX_RETRIES):
        try:
            page_container = await page.query_selector(page_selector)
            if not page_container:
                logger.warning(f"未找到分页容器: {page_selector}")
                return False

            page_links = await page_container.query_selector_all('a[data-page]')
            for link in page_links:
                try:
                    page_num = await link.get_attribute('data-page')
                    if page_num and int(page_num) == target_page:
                        await link.click()
                        await page.wait_for_timeout(random.uniform(2000, 3000))
                        return True
                except Exception:
                    continue

            skip_input = await page_container.query_selector('.layui-laypage-skip input')
            skip_btn = await page_container.query_selector('.layui-laypage-btn')
            if skip_input and skip_btn:
                await skip_input.fill(str(target_page))
                await skip_btn.click()
                await page.wait_for_timeout(random.uniform(2000, 3000))
                return True

            if retry < MAX_RETRIES - 1:
                await page.wait_for_timeout(2000)
                continue

            logger.warning(f"无法跳转到第 {target_page} 页")
            return False
        except Exception as e:
            logger.error(f"跳转到第 {target_page} 页失败 (重试 {retry + 1}): {e}")
            await page.wait_for_timeout(2000)
    return False


async def extract_table_rows(page: Page, tbody_selector: str) -> List[Dict]:
    rows = []
    try:
        tbody = await page.query_selector(tbody_selector)
        if not tbody:
            logger.warning(f"未找到表格: {tbody_selector}")
            return rows

        trs = await tbody.query_selector_all('tr')
        for i, tr in enumerate(trs):
            try:
                tds = await tr.query_selector_all('td')
                if len(tds) < 3:
                    continue

                row_data = {}
                texts = []
                for td in tds:
                    texts.append((await td.inner_text()).strip())

                row_data['texts'] = texts
                row_data['row_element'] = tr
                row_data['index'] = i + 1
                rows.append(row_data)
            except Exception as e:
                logger.debug(f"解析第 {i} 行失败: {e}")
                continue

        logger.info(f"从表格提取到 {len(rows)} 行数据")
    except Exception as e:
        logger.error(f"提取表格行失败: {e}")
    return rows


async def extract_detail_from_modal(page: Page) -> Dict:
    detail = {
        "药物名称": "",
        "受理号": "",
        "申请人": "",
        "申请日期": "",
        "拟定适应症（或功能主治）": "",
        "分子靶点": "",
    }
    try:
        await page.wait_for_timeout(2000)

        layer_iframe = await page.query_selector('.layui-layer-iframe iframe')
        if layer_iframe:
            logger.debug("检测到iframe弹窗，进入iframe")
            frame = await layer_iframe.content_frame()
            if frame:
                text = await frame.inner_text('body')
            else:
                text = ""
        else:
            layer_content = await page.query_selector('.layui-layer-content')
            if layer_content:
                text = await layer_content.inner_text()
            else:
                modals = await page.query_selector_all('[class*="layer"], [class*="modal"], [class*="dialog"]')
                text = ""
                for m in modals:
                    try:
                        t = await m.inner_text()
                        if len(t) > len(text):
                            text = t
                    except Exception:
                        pass

        if not text:
            text = await page.inner_text('body')

        lines = [line.strip() for line in text.split('\n') if line.strip()]

        field_map = {
            "药品名称": "药物名称",
            "药物名称": "药物名称",
            "通用名": "药物名称",
            "受理号": "受理号",
            "申请号": "受理号",
            "申请人": "申请人",
            "申报单位": "申请人",
            "注册申请人": "申请人",
            "申请日期": "申请日期",
            "公示日期": "申请日期",
            "受理日期": "申请日期",
            "分子靶点": "分子靶点",
            "靶点": "分子靶点",
            "作用靶点": "分子靶点",
        }

        for line in lines:
            for src_field, dst_field in field_map.items():
                if src_field in line and not detail[dst_field]:
                    parts = re.split(r'\s{2,}|\t', line)
                    for i, part in enumerate(parts):
                        if src_field in part and i + 1 < len(parts):
                            value = parts[i + 1].strip()
                            if value:
                                detail[dst_field] = value
                                break

        indication_found = False
        for i, line in enumerate(lines):
            if "拟定适应症" in line or "适应症" in line or "功能主治" in line:
                parts = re.split(r'\s{2,}|\t', line)
                indication_value = ""
                for j, part in enumerate(parts):
                    if "拟定适应症" in part or "适应症" in part or "功能主治" in part:
                        if j + 1 < len(parts):
                            indication_value = parts[j + 1].strip()
                        break

                if not indication_value:
                    match = re.search(r'(?:拟定适应症|适应症|功能主治)[（(]?[^）)]*[)）]?\s*(.+)', line)
                    if match:
                        indication_value = match.group(1).strip()

                full_indication = indication_value
                if i + 1 < len(lines):
                    next_line = lines[i + 1]
                    if next_line and not any(
                        kw in next_line for kw in [
                            "拟优先审评", "优先审评理由", "审评结论", "审核结论",
                            "药品名称", "受理号", "申请人", "剂型", "规格"
                        ]
                    ):
                        full_indication += " " + next_line.strip()

                detail["拟定适应症（或功能主治）"] = full_indication.strip()
                indication_found = True
                break

        return detail
    except Exception as e:
        logger.error(f"提取详情弹窗数据失败: {e}")
        return detail


async def close_modal(page: Page) -> bool:
    for retry in range(MAX_RETRIES):
        try:
            close_selectors = [
                '.layui-layer-close', '.layui-layer-close1', '.layui-layer-close2',
                '[class*="close"]', '[aria-label="close"]',
            ]
            for sel in close_selectors:
                btns = await page.query_selector_all(sel)
                for btn in btns:
                    try:
                        await btn.click()
                        await page.wait_for_timeout(1000)
                        return True
                    except Exception:
                        continue

            await page.keyboard.press('Escape')
            await page.wait_for_timeout(1000)
            return True
        except Exception as e:
            logger.warning(f"关闭弹窗失败 (重试 {retry + 1}): {e}")
            await page.wait_for_timeout(1000)
    return False


async def collect_page_drugs(
    page: Page,
    tbody_selector: str,
    drug_type: str,
    page_num: int,
) -> List[Dict]:
    anti_tumor_drugs = []
    try:
        rows = await extract_table_rows(page, tbody_selector)
        if not rows:
            logger.warning(f"第 {page_num} 页未找到数据行")
            return anti_tumor_drugs

        for idx, row in enumerate(rows):
            logger.info(f"处理第 {page_num} 页第 {idx + 1} 条...")
            texts = row.get('texts', [])
            drug_detail = {
                "序号": texts[0] if len(texts) > 0 else "",
                "药物名称": "",
                "受理号": texts[1] if len(texts) > 1 else "",
                "申请人": texts[2] if len(texts) > 2 else "",
                "申请日期": texts[4] if len(texts) > 4 else "",
                "拟定适应症（或功能主治）": "",
                "分子靶点": "",
                "品种类型": drug_type,
            }

            if len(texts) >= 3:
                drug_detail["药物名称"] = texts[2]
            if len(texts) >= 5:
                drug_detail["申请日期"] = texts[4]

            tr = row.get('row_element')
            if tr:
                for retry in range(MAX_RETRIES):
                    try:
                        await tr.dblclick()
                        await page.wait_for_timeout(random.uniform(2500, 4000))

                        detail = await extract_detail_from_modal(page)
                        for k, v in detail.items():
                            if v:
                                drug_detail[k] = v

                        if not drug_detail["药物名称"] and len(texts) >= 3:
                            drug_detail["药物名称"] = texts[2]

                        await close_modal(page)
                        await page.wait_for_timeout(1000)
                        break
                    except Exception as e:
                        logger.warning(f"打开详情失败 (重试 {retry + 1}): {e}")
                        await page.wait_for_timeout(2000)

            indication = drug_detail.get("拟定适应症（或功能主治）", "")
            if is_anti_tumor(indication):
                anti_tumor_drugs.append(drug_detail)
                logger.info(f"  -> 发现抗肿瘤药物: {drug_detail['药物名称']}")
                logger.info(f"     适应症: {indication[:80]}...")

            random_sleep(0.8, 2.0)

    except Exception as e:
        logger.error(f"采集第 {page_num} 页失败: {e}")

    return anti_tumor_drugs


async def api_probe(page: Page) -> Optional[str]:
    try:
        logger.info("开始API探测...")
        api_requests = []

        async def handle_response(response: Response):
            try:
                url = response.url
                if any(x in url.lower() for x in ['api', 'getlist', 'list', 'page']):
                    if response.request.resource_type in ['xhr', 'fetch']:
                        api_requests.append({
                            'url': url,
                            'method': response.request.method,
                            'status': response.status,
                            'resource_type': response.request.resource_type,
                        })
            except Exception:
                pass

        page.on('response', handle_response)

        await page.reload(wait_until='networkidle', timeout=60000)
        await page.wait_for_timeout(3000)

        page.remove_listener('response', handle_response)

        logger.info(f"探测到 {len(api_requests)} 个潜在API请求")
        for req in api_requests[:15]:
            logger.info(f"  - [{req['status']}] {req['method']} {req['url'][:120]}")

        return None
    except Exception as e:
        logger.warning(f"API探测失败: {e}")
        return None


async def collect_cde_category(
    drug_type: str,
    url: str,
    tab_name: str,
    tbody_selector: str,
    page_selector: str,
    headless: bool = False,
):
    checkpoint = load_checkpoint()
    start_page = checkpoint.get(drug_type, {}).get("last_page", 0) + 1

    logger.info(f"\n{'='*60}")
    logger.info(f"开始采集 {drug_type} ({tab_name})")
    logger.info(f"从第 {start_page} 页开始，计划采集 {PAGES_TO_COLLECT} 页")
    logger.info(f"{'='*60}")

    async with async_playwright() as pw:
        browser, context = await setup_browser(pw, headless=headless)
        page = await context.new_page()
        await apply_stealth(page)

        try:
            success = await navigate_and_select_tab(page, url, tab_name)
            if not success:
                logger.error(f"无法访问 {tab_name} 页面")
                return

            await api_probe(page)

            total_pages = await get_total_pages(page, page_selector)
            logger.info(f"计划采集 {total_pages} 页")

            total_anti_tumor = 0
            for page_num in range(start_page, total_pages + 1):
                logger.info(f"\n{'-'*50}")
                logger.info(f"正在处理第 {page_num} 页 / 共 {total_pages} 页")

                if page_num > 1:
                    ok = await go_to_page(page, page_selector, page_num)
                    if not ok:
                        logger.warning(f"跳转到第 {page_num} 页失败，跳过")
                        continue

                await page.wait_for_timeout(random.uniform(1500, 2500))

                anti_tumor_drugs = await collect_page_drugs(
                    page, tbody_selector, drug_type, page_num
                )

                if anti_tumor_drugs:
                    append_to_csv(anti_tumor_drugs)
                    total_anti_tumor += len(anti_tumor_drugs)

                if drug_type not in checkpoint:
                    checkpoint[drug_type] = {}
                checkpoint[drug_type]["last_page"] = page_num
                checkpoint[drug_type]["drugs_collected"] = total_anti_tumor
                save_checkpoint(checkpoint)

                logger.info(f"第 {page_num} 页完成，本页 {len(anti_tumor_drugs)} 个抗肿瘤药，累计 {total_anti_tumor} 个")
                random_sleep(3, 5)

            logger.info(f"\n{drug_type} 采集完成，共发现 {total_anti_tumor} 个抗肿瘤药物")

        except Exception as e:
            logger.error(f"采集 {drug_type} 时发生错误: {e}")
        finally:
            await browser.close()
            logger.info(f"{drug_type} 浏览器已关闭")


async def main():
    logger.info("\n" + "=" * 60)
    logger.info("CDE官网抗肿瘤药物自动化采集系统启动")
    logger.info(f"采集目标: 优先审评品种 + 突破性治疗品种，各 {PAGES_TO_COLLECT} 页")
    logger.info(f"输出文件: {OUTPUT_FILE} (UTF-8 BOM编码)")
    logger.info("=" * 60)

    headless_mode = True
    logger.info("使用无头模式 (headless=True)")

    await collect_cde_category(
        drug_type="priority_review",
        url=PRIORITY_REVIEW_URL,
        tab_name="纳入优先审评品种名单",
        tbody_selector="#includePriorityTbody",
        page_selector="#includePriorityPage",
        headless=headless_mode,
    )

    await collect_cde_category(
        drug_type="breakthrough_therapy",
        url=BREAKTHROUGH_THERAPY_URL,
        tab_name="纳入突破性治疗品种名单",
        tbody_selector="#breakIncludePriorityTbody",
        page_selector="#breakIncludePriorityPage",
        headless=headless_mode,
    )

    logger.info("\n" + "=" * 60)
    logger.info("所有采集任务完成！")
    if os.path.exists(OUTPUT_FILE):
        import pandas as pd
        df = pd.read_csv(OUTPUT_FILE, encoding='utf-8-sig')
        logger.info(f"总共采集到 {len(df)} 条抗肿瘤药物数据")
        logger.info(f"数据预览:")
        logger.info(df[['药物名称', '申请人', '品种类型']].head(10).to_string())
    logger.info("=" * 60)


if __name__ == "__main__":
    asyncio.run(main())
