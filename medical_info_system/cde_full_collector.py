"""
完整的CDE药物信息采集脚本
使用数据库中的受理号信息进行批量采集
"""
import requests
import re
import os
import sqlite3
import time
import pdfplumber

class CDEFullCollector:
    def __init__(self):
        self.session = requests.Session()
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
        }
        self.download_dir = 'cde_pdfs'
        os.makedirs(self.download_dir, exist_ok=True)

        # 初始化session
        self.init_session()

        # 初始化数据库
        self.db_path = 'data/medical_info.db'
        self.conn = sqlite3.connect(self.db_path)
        self.cursor = self.conn.cursor()

    def init_session(self):
        """初始化session获取cookies"""
        self.session.get("https://www.cde.org.cn/", headers=self.headers, timeout=30)
        time.sleep(0.5)
        self.session.get("https://www.cde.org.cn/main/xxgk/listpage/b40868b5e21c038a6aa8b4319d21b07d", headers=self.headers, timeout=30)
        time.sleep(1)

    def get_detail_page(self, drug_id):
        """获取详情页HTML"""
        detail_url = f"https://www.cde.org.cn/main/xxgk/postmarketpage?acceptidCODE={drug_id}"
        resp = self.session.get(detail_url, headers=self.headers, timeout=30)
        return resp.text

    def extract_pdf_info(self, html_content):
        """提取PDF附件信息"""
        pattern = r'data-fileid="([^"]+)"[^>]*data-acceptid="([^"]+)"[^>]*data-filename="([^"]+)"'
        matches = re.findall(pattern, html_content)

        pdfs = []
        for match in matches:
            file_id, accept_id, filename = match
            pdfs.append({
                'file_id': file_id,
                'accept_id': accept_id,
                'filename': filename,
                'is_review_report': '技术审评报告' in filename,
                'is_instructions': '说明书' in filename,
            })
        return pdfs

    def download_pdf(self, file_id, accept_id, filename):
        """下载PDF"""
        download_url = f"https://www.cde.org.cn/main/xxgk/PostMarketDownload?attidCODE={file_id}&tableid={accept_id}"
        resp = self.session.get(download_url, headers=self.headers, timeout=60)

        if resp.status_code == 200 and resp.content[:4] == b'%PDF':
            # 清理文件名
            safe_filename = re.sub(r'[<>:"/\\|?*]', '_', filename)
            filepath = os.path.join(self.download_dir, safe_filename)
            with open(filepath, 'wb') as f:
                f.write(resp.content)
            return filepath
        return None

    def parse_pdf(self, filepath):
        """解析PDF提取信息"""
        info = {
            'indication': None,
            'mechanism': None,
            'companion_diagnosis': None,
            'clinical_evidence': None,
        }

        try:
            with pdfplumber.open(filepath) as pdf:
                pages_text = []
                for page in pdf.pages:
                    text = page.extract_text()
                    if text:
                        pages_text.append(text)

                full_text = '\n'.join(pages_text)

            # 1. 提取适应症 (在正文第3-8页)
            for i in range(2, min(8, len(pages_text))):
                page_text = pages_text[i]
                lines = page_text.split('\n')

                for j, line in enumerate(lines):
                    if '适应症' in line and '用法用量' not in line:
                        indication_parts = []
                        remaining = line.split('适应症')[-1].strip()
                        if remaining and len(remaining) > 5:
                            indication_parts.append(remaining)
                            for k in range(j+1, min(j+5, len(lines))):
                                next_line = lines[k].strip()
                                if any(kw in next_line for kw in ['用法用量', '受理的注册', '化学药品注册']):
                                    break
                                if next_line:
                                    indication_parts.append(next_line)
                            info['indication'] = ' '.join(indication_parts)
                            break
                if info['indication']:
                    break

            # 2. 提取作用机制
            mechanism_match = re.search(r'赛沃替尼是一种([^\n]{20,150}?)(?:已批准|本次|用于)', full_text)
            if mechanism_match:
                info['mechanism'] = mechanism_match.group(0)[:200]

            # 3. 提取伴随诊断标志物
            biomarker_match = re.search(r'(MET[^\n]{0,50}扩增|MET[^\n]{0,30}突变|EGFR[^\n]{0,30}突变|ALK[^\n]{0,30}融合)', full_text)
            if biomarker_match:
                info['companion_diagnosis'] = biomarker_match.group(0)[:100]

            # 4. 提取临床证据
            evidence_match = re.search(r'(?:ORR|客观缓解率)[^\n]{0,150}', full_text)
            if evidence_match:
                info['clinical_evidence'] = evidence_match.group(0)[:200]

        except Exception as e:
            print(f"解析PDF出错: {e}")

        return info

    def get_nmpa_drugs_from_db(self):
        """从数据库获取需要更新的NMPA药物"""
        self.cursor.execute('''
            SELECT DISTINCT a.application_number, a.drug_name_cn, a.indication
            FROM approved_drugs a
            WHERE a.regulatory_agency = "NMPA"
            AND (a.indication IS NULL OR a.indication = "")
            LIMIT 10
        ''')
        return self.cursor.fetchall()

    def update_drug_info(self, accept_id, info):
        """更新数据库"""
        try:
            self.cursor.execute('''
                UPDATE approved_drugs
                SET indication = COALESCE(?, indication),
                    mechanism_of_action = COALESCE(?, mechanism_of_action),
                    gene_marker = COALESCE(?, gene_marker),
                    clinical_trial_data = COALESCE(?, clinical_trial_data)
                WHERE application_number = ?
            ''', (
                info.get('indication'),
                info.get('mechanism'),
                info.get('companion_diagnosis'),
                info.get('clinical_evidence'),
                accept_id
            ))
            self.conn.commit()
            return self.cursor.rowcount > 0
        except Exception as e:
            print(f"更新失败: {e}")
            return False

    def collect_single_drug(self, drug_id, accept_id):
        """采集单个药物信息"""
        print(f"\n--- 采集: {accept_id} (ID: {drug_id}) ---")

        # 获取详情页
        html = self.get_detail_page(drug_id)

        # 提取PDF信息
        pdfs = self.extract_pdf_info(html)
        print(f"找到 {len(pdfs)} 个PDF")

        if not pdfs:
            print("⚠️ 没有PDF附件")
            return None

        all_info = {'accept_id': accept_id}

        for pdf in pdfs:
            print(f"  下载: {pdf['filename']}")
            filepath = self.download_pdf(pdf['file_id'], pdf['accept_id'], pdf['filename'])

            if filepath:
                print(f"  解析: {filepath}")
                info = self.parse_pdf(filepath)

                if pdf['is_review_report']:
                    all_info.update(info)

        # 更新数据库
        if all_info.get('indication'):
            success = self.update_drug_info(accept_id, all_info)
            if success:
                print(f"✅ 数据库已更新")
            return all_info
        else:
            print(f"❌ 未提取到适应症信息")
            return None

    def close(self):
        """关闭连接"""
        if self.conn:
            self.conn.close()

# 运行采集
if __name__ == "__main__":
    collector = CDEFullCollector()

    # 测试单个药物
    drug_id = "6b60c4ff3e3483324b483ea5807ab39b"  # 赛沃替尼片
    accept_id = "CXHS2400133"
    result = collector.collect_single_drug(drug_id, accept_id)

    if result:
        print("\n=== 采集结果 ===")
        print(f"适应症: {result.get('indication')}")
        print(f"作用机制: {result.get('mechanism')}")
        print(f"伴随诊断: {result.get('companion_diagnosis')}")
        print(f"临床证据: {result.get('clinical_evidence')}")

    collector.close()