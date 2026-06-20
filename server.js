/**
 * 基因药物知识库系统 (Gene Drug Knowledge Base)
 * 抗肿瘤药物基因靶点与生物标志物查询平台
 * 
 * 服务入口：server.js
 * 技术栈：Node.js + Express + EJS + better-sqlite3
 * 部署平台：Railway
 */

const express = require('express');
const path = require('path');
const fs = require('fs');
const Database = require('better-sqlite3');

const app = express();
const PORT = process.env.PORT || 3000;

// ================================
// 配置与中间件
// ================================
app.set('view engine', 'ejs');
app.set('views', path.join(__dirname, 'views'));

// 通用布局渲染辅助函数
function renderLayout(res, title, page, bodyHtml) {
    const year = new Date().getFullYear();
    res.send(`<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>${title} | 基因药物知识库</title>
    <meta name="description" content="抗肿瘤药物基因靶点与生物标志物查询平台 - Gene Drug Knowledge Base">
    <meta name="keywords" content="靶向药, 生物标志物, 伴随诊断, 抗肿瘤药物, 精准医疗">
    <link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.2/dist/css/bootstrap.min.css">
    <link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/bootstrap-icons@1.11.1/font/bootstrap-icons.css">
    <style>
        body { font-family: -apple-system, BlinkMacSystemFont, 'PingFang SC', 'Microsoft YaHei', 'Helvetica Neue', Arial, sans-serif; background: linear-gradient(135deg, #f5f7fa 0%, #e8eef5 100%); min-height: 100vh; padding-top: 76px; }
        .navbar { background: linear-gradient(90deg, #1a237e 0%, #1565c0 50%, #0288d1 100%); box-shadow: 0 2px 12px rgba(26, 35, 126, 0.3); }
        .navbar-brand, .nav-link { color: #ffffff !important; }
        .nav-link.active, .nav-link:hover { color: #ffd700 !important; }
        .card { border: none; border-radius: 12px; box-shadow: 0 4px 20px rgba(0, 0, 0, 0.08); transition: transform 0.2s, box-shadow 0.2s; }
        .card:hover { transform: translateY(-2px); box-shadow: 0 6px 28px rgba(0, 0, 0, 0.12); }
        .stat-card { background: linear-gradient(135deg, #ffffff 0%, #f3e5f5 100%); border-left: 4px solid #7b1fa2; }
        .drug-target-badge { background: linear-gradient(90deg, #1565c0, #00838f); color: white; padding: 4px 12px; border-radius: 12px; font-size: 13px; display: inline-block; margin: 2px 4px 2px 0; }
        .gene-badge { background: linear-gradient(90deg, #4527a0, #5e35b1); color: white; padding: 4px 12px; border-radius: 12px; font-size: 13px; display: inline-block; margin: 2px 4px 2px 0; }
        .chinese-badge { background: linear-gradient(90deg, #ef6c00, #f57c00); color: white; padding: 4px 12px; border-radius: 12px; font-size: 13px; display: inline-block; margin: 2px 4px 2px 0; }
        .fda-badge { background: linear-gradient(90deg, #2e7d32, #388e3c); color: white; padding: 4px 12px; border-radius: 12px; font-size: 13px; display: inline-block; margin: 2px 4px 2px 0; }
        .ema-badge { background: linear-gradient(90deg, #1565c0, #1976d2); color: white; padding: 4px 12px; border-radius: 12px; font-size: 13px; display: inline-block; margin: 2px 4px 2px 0; }
        .info-section { background: #ffffff; border-radius: 8px; padding: 16px; margin-bottom: 12px; border: 1px solid #e0e0e0; }
        .hero-section { background: linear-gradient(135deg, #1a237e 0%, #283593 50%, #1565c0 100%); color: white; padding: 60px 20px; border-radius: 0 0 20px 20px; margin-bottom: 40px; }
        .hero-title { font-size: 2.5rem; font-weight: 700; margin-bottom: 16px; }
        .hero-subtitle { font-size: 1.2rem; opacity: 0.9; margin-bottom: 24px; }
        .search-box { max-width: 700px; margin: 0 auto; }
        .search-input { border-radius: 30px; padding: 14px 20px; font-size: 1rem; border: none; box-shadow: 0 4px 20px rgba(0, 0, 0, 0.15); }
        .search-btn { border-radius: 30px; padding: 0 32px; font-weight: 600; }
        .filter-card { background: #ffffff; border-radius: 12px; padding: 20px; box-shadow: 0 2px 12px rgba(0, 0, 0, 0.06); }
        .drug-card { border-left: 4px solid #7b1fa2; }
        .btn-primary-custom { background: linear-gradient(90deg, #1565c0, #0288d1); border: none; border-radius: 8px; padding: 10px 24px; color: white; text-decoration: none; display: inline-block; transition: opacity 0.2s; }
        .btn-primary-custom:hover { opacity: 0.9; color: white; }
        .stat-number { font-size: 2.5rem; font-weight: 700; color: #4527a0; }
        .section-title { border-left: 4px solid #1565c0; padding-left: 16px; margin-bottom: 24px; font-weight: 600; color: #1a237e; }
        .pagination-custom { justify-content: center; margin-top: 32px; }
        .detail-row { padding: 12px 0; border-bottom: 1px solid #e8e8e8; }
        .detail-row:last-child { border-bottom: none; }
        .detail-label { font-weight: 600; color: #455a64; margin-bottom: 4px; }
        .detail-value { color: #212121; line-height: 1.6; }
        .footer { background: #1a237e; color: #ffffff; padding: 30px 0; margin-top: 60px; }
        .footer a { color: #90caf9; }
        .chart-bar { height: 24px; background: linear-gradient(90deg, #1565c0, #0288d1); border-radius: 4px; margin-bottom: 4px; transition: width 0.5s ease; }
        .chart-bar-china { background: linear-gradient(90deg, #ef6c00, #f57c00); }
        .chart-bar-fda { background: linear-gradient(90deg, #2e7d32, #388e3c); }
        .alert-info-custom { background: #e3f2fd; border: 1px solid #90caf9; border-radius: 8px; }
        .text-gradient-gold { background: linear-gradient(90deg, #ffd700, #ffa726); -webkit-background-clip: text; -webkit-text-fill-color: transparent; background-clip: text; }
        .icon-circle { width: 48px; height: 48px; border-radius: 50%; display: flex; align-items: center; justify-content: center; font-size: 1.5rem; }
    </style>
</head>
<body>
    <nav class="navbar navbar-expand-lg fixed-top">
        <div class="container">
            <a class="navbar-brand fw-bold" href="/"><i class="bi bi-dna me-2"></i>基因药物知识库</a>
            <button class="navbar-toggler" type="button" data-bs-toggle="collapse" data-bs-target="#mainNav">
                <span class="navbar-toggler-icon"></span>
            </button>
            <div class="collapse navbar-collapse" id="mainNav">
                <ul class="navbar-nav ms-auto">
                    <li class="nav-item"><a class="nav-link ${page === 'home' ? 'active' : ''}" href="/"><i class="bi bi-house-door me-1"></i>首页</a></li>
                    <li class="nav-item"><a class="nav-link ${page === 'drugs' ? 'active' : ''}" href="/drugs"><i class="bi bi-capsule me-1"></i>药物库</a></li>
                    <li class="nav-item"><a class="nav-link ${page === 'genes' ? 'active' : ''}" href="/genes"><i class="bi bi-file-earmark-medical me-1"></i>基因靶点</a></li>
                    <li class="nav-item"><a class="nav-link ${page === 'statistics' ? 'active' : ''}" href="/statistics"><i class="bi bi-bar-chart me-1"></i>统计分析</a></li>
                    <li class="nav-item"><a class="nav-link ${page === 'about' ? 'active' : ''}" href="/about"><i class="bi bi-info-circle me-1"></i>关于</a></li>
                </ul>
            </div>
        </div>
    </nav>
    <main>${bodyHtml}</main>
    <footer class="footer">
        <div class="container">
            <div class="row">
                <div class="col-md-6">
                    <h5 class="mb-3"><i class="bi bi-dna me-2"></i>基因药物知识库</h5>
                    <p class="text-light small opacity-75">精准医疗时代的伴随诊断与生物标志物查询平台。</p>
                </div>
                <div class="col-md-3">
                    <h6 class="mb-3 text-light">快速链接</h6>
                    <ul class="list-unstyled small">
                        <li class="mb-2"><a href="/drugs">药物搜索</a></li>
                        <li class="mb-2"><a href="/drugs?type=单克隆抗体">单抗类药物</a></li>
                        <li class="mb-2"><a href="/statistics">数据统计</a></li>
                    </ul>
                </div>
                <div class="col-md-3">
                    <h6 class="mb-3 text-light">技术信息</h6>
                    <ul class="list-unstyled small text-light opacity-75">
                        <li class="mb-2"><i class="bi bi-code-slash me-2"></i>Node.js + Express</li>
                        <li class="mb-2"><i class="bi bi-database me-2"></i>SQLite</li>
                        <li class="mb-2"><i class="bi bi-box me-2"></i>Railway 部署</li>
                    </ul>
                </div>
            </div>
            <hr class="my-4 bg-light opacity-25">
            <p class="text-center small opacity-75 mb-0">© ${year} 基因药物知识库 (Gene Drug Knowledge Base) · 数据仅供参考，具体用药请遵医嘱</p>
        </div>
    </footer>
    <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.3.2/dist/js/bootstrap.bundle.min.js"></script>
</body>
</html>`);
}
app.use(express.urlencoded({ extended: true, limit: '10mb' }));
app.use(express.json({ limit: '10mb' }));
app.use(express.static(path.join(__dirname, 'public')));

// ================================
// 数据库初始化
// ================================
const DB_PATH = path.join(__dirname, 'data', 'gene_drug_kb.db');

// 确保数据目录存在
if (!fs.existsSync(path.join(__dirname, 'data'))) {
  fs.mkdirSync(path.join(__dirname, 'data'), { recursive: true });
}

let db;
try {
  db = new Database(DB_PATH);
  db.pragma('journal_mode = WAL');
  db.pragma('foreign_keys = ON');

  // 创建表
  db.exec(`
    CREATE TABLE IF NOT EXISTS drugs (
      id INTEGER PRIMARY KEY AUTOINCREMENT,
      name_cn TEXT NOT NULL,
      name_en TEXT,
      generic_name TEXT,
      approval_number TEXT,
      approval_date TEXT,
      approval_year INTEGER,
      company TEXT,
      drug_type TEXT,
      molecular_target TEXT,
      gene_marker TEXT,
      companion_diagnostic TEXT,
      indication TEXT,
      mechanism TEXT,
      dosage_form TEXT,
      fda_status TEXT DEFAULT '未获FDA批准',
      ema_status TEXT DEFAULT '未获EMA批准',
      global_access TEXT DEFAULT '仅中国/有限国际可及',
      created_at TEXT DEFAULT CURRENT_TIMESTAMP,
      updated_at TEXT DEFAULT CURRENT_TIMESTAMP
    );

    CREATE TABLE IF NOT EXISTS genes (
      id INTEGER PRIMARY KEY AUTOINCREMENT,
      gene_symbol TEXT NOT NULL UNIQUE,
      gene_name TEXT,
      chromosome TEXT,
      function TEXT,
      associated_cancers TEXT,
      biomarkers TEXT,
      created_at TEXT DEFAULT CURRENT_TIMESTAMP
    );

    CREATE TABLE IF NOT EXISTS drug_gene_relations (
      id INTEGER PRIMARY KEY AUTOINCREMENT,
      drug_id INTEGER,
      gene_id INTEGER,
      relation_type TEXT,
      evidence TEXT,
      FOREIGN KEY (drug_id) REFERENCES drugs(id) ON DELETE CASCADE,
      FOREIGN KEY (gene_id) REFERENCES genes(id) ON DELETE CASCADE
    );

    CREATE INDEX IF NOT EXISTS idx_drugs_name ON drugs(name_cn);
    CREATE INDEX IF NOT EXISTS idx_drugs_year ON drugs(approval_year);
    CREATE INDEX IF NOT EXISTS idx_drugs_target ON drugs(molecular_target);
    CREATE INDEX IF NOT EXISTS idx_genes_symbol ON genes(gene_symbol);
  `);

  console.log('[OK] 数据库初始化成功: ' + DB_PATH);

  // 如果数据库为空，插入种子数据
  const rowCount = db.prepare('SELECT COUNT(*) as cnt FROM drugs').get();
  if (rowCount.cnt === 0) {
    console.log('[INFO] 数据库为空，正在插入种子药物数据...');
    insertSeedData(db);
  }
} catch (err) {
  console.error('[ERROR] 数据库初始化失败:', err.message);
  db = null;
}

// ================================
// 种子数据（抗肿瘤药物基因知识库）
// ================================
function insertSeedData(db) {
  const seedDrugs = [
    // --- EGFR 靶向药 ---
    { name_cn: '奥希替尼', name_en: 'Osimertinib', generic_name: '甲磺酸奥希替尼',
      approval_number: '国药准字H20170001', approval_date: '2017-03-20', approval_year: 2017,
      company: '阿斯利康', drug_type: '小分子靶向药',
      molecular_target: 'EGFR（T790M、L858R、19del）',
      gene_marker: 'EGFR 19缺失; EGFR L858R; EGFR T790M',
      companion_diagnostic: 'EGFR PCR检测; cobas EGFR Mutation Test v2',
      indication: 'EGFR突变阳性的局部晚期或转移性非小细胞肺癌（NSCLC）',
      mechanism: '第三代 EGFR-TKI，不可逆结合 EGFR 激酶结构域，对 T790M 耐药突变有效',
      dosage_form: '片剂 80mg', fda_status: 'FDA已批准', ema_status: 'EMA已批准',
      global_access: '全球可及（FDA+EMA双批准）' },

    { name_cn: '吉非替尼', name_en: 'Gefitinib', generic_name: '吉非替尼',
      approval_number: '国药准字J20100008', approval_date: '2005-02-25', approval_year: 2005,
      company: '阿斯利康', drug_type: '小分子靶向药',
      molecular_target: 'EGFR（L858R、19del）',
      gene_marker: 'EGFR 19缺失; EGFR L858R',
      companion_diagnostic: 'EGFR PCR检测',
      indication: 'EGFR 基因敏感突变的局部晚期或转移性非小细胞肺癌（NSCLC）',
      mechanism: '第一代 EGFR-TKI，可逆性 EGFR 酪氨酸激酶抑制剂',
      dosage_form: '片剂 250mg', fda_status: 'FDA已批准', ema_status: 'EMA已批准',
      global_access: '全球可及（FDA+EMA双批准）' },

    { name_cn: '阿美替尼', name_en: 'Almonertinib', generic_name: '甲磺酸阿美替尼',
      approval_number: '国药准字H20200004', approval_date: '2020-03-18', approval_year: 2020,
      company: '江苏豪森', drug_type: '小分子靶向药',
      molecular_target: 'EGFR（T790M）',
      gene_marker: 'EGFR T790M; EGFR L858R; EGFR 19del',
      companion_diagnostic: 'EGFR T790M 检测',
      indication: 'EGFR T790M 突变阳性的局部晚期或转移性非小细胞肺癌',
      mechanism: '第三代 EGFR-TKI，国产创新药，对 T790M 耐药突变有效',
      dosage_form: '片剂 110mg', fda_status: '未获FDA批准', ema_status: '未获EMA批准',
      global_access: '仅中国/有限国际可及' },

    // --- ALK 靶向药 ---
    { name_cn: '克唑替尼', name_en: 'Crizotinib', generic_name: '克唑替尼',
      approval_number: '国药准字H20140001', approval_date: '2014-09-18', approval_year: 2014,
      company: '辉瑞', drug_type: '小分子靶向药',
      molecular_target: 'ALK / ROS1 / c-MET',
      gene_marker: 'ALK 融合阳性; ROS1 融合阳性; MET exon 14 跳变',
      companion_diagnostic: 'ALK FISH检测; ALK IHC（VENTANA ALK D5F3）; ROS1 FISH',
      indication: 'ALK 阳性的局部晚期或转移性非小细胞肺癌; ROS1 阳性 NSCLC',
      mechanism: '第一代 ALK-TKI，同时抑制 ROS1 和 c-MET 酪氨酸激酶',
      dosage_form: '胶囊 250mg', fda_status: 'FDA已批准', ema_status: 'EMA已批准',
      global_access: '全球可及（FDA+EMA双批准）' },

    { name_cn: '阿来替尼', name_en: 'Alectinib', generic_name: '盐酸阿来替尼',
      approval_number: '国药准字H20180001', approval_date: '2018-08-15', approval_year: 2018,
      company: '罗氏/中外制药', drug_type: '小分子靶向药',
      molecular_target: 'ALK / RET',
      gene_marker: 'ALK 融合阳性',
      companion_diagnostic: 'ALK FISH检测; ALK IHC检测',
      indication: 'ALK 阳性的局部晚期或转移性非小细胞肺癌',
      mechanism: '第二代 ALK-TKI，高选择性 ALK 抑制剂，脑穿透能力强',
      dosage_form: '胶囊 150mg', fda_status: 'FDA已批准', ema_status: 'EMA已批准',
      global_access: '全球可及（FDA+EMA双批准）' },

    { name_cn: '劳拉替尼', name_en: 'Lorlatinib', generic_name: '洛拉替尼',
      approval_number: '国药准字H20220001', approval_date: '2022-04-29', approval_year: 2022,
      company: '辉瑞', drug_type: '小分子靶向药',
      molecular_target: 'ALK / ROS1',
      gene_marker: 'ALK 融合阳性; ROS1 融合阳性; ALK G1202R 耐药突变',
      companion_diagnostic: 'ALK FISH检测; NGS 检测',
      indication: 'ALK 阳性的转移性非小细胞肺癌（一/二线治疗）',
      mechanism: '第三代 ALK-TKI，大环结构，可克服 ALK 耐药突变',
      dosage_form: '片剂 100mg', fda_status: 'FDA已批准', ema_status: 'EMA已批准',
      global_access: '全球可及（FDA+EMA双批准）' },

    // --- ROS1/NTRK 靶向药 ---
    { name_cn: '恩曲替尼', name_en: 'Entrectinib', generic_name: '恩曲替尼',
      approval_number: '国药准字H20220002', approval_date: '2022-07-29', approval_year: 2022,
      company: '罗氏', drug_type: '小分子靶向药',
      molecular_target: 'TRK（NTRK1/2/3） / ROS1 / ALK',
      gene_marker: 'NTRK 融合; ROS1 融合; ALK 融合',
      companion_diagnostic: 'NGS 多基因检测; FoundationOne CDx',
      indication: 'NTRK 融合阳性的实体瘤; ROS1 阳性转移性 NSCLC',
      mechanism: '泛 TRK 抑制剂，针对 NTRK 融合驱动的肿瘤（泛肿瘤适应症）',
      dosage_form: '胶囊 100mg/200mg', fda_status: 'FDA已批准', ema_status: 'EMA已批准',
      global_access: '全球可及（FDA+EMA双批准）' },

    { name_cn: '拉罗替尼', name_en: 'Larotrectinib', generic_name: '硫酸拉罗替尼',
      approval_number: '国药准字HJ20220001', approval_date: '2022-06-23', approval_year: 2022,
      company: '拜耳', drug_type: '小分子靶向药',
      molecular_target: 'TRK（NTRK1/2/3）',
      gene_marker: 'NTRK1 融合; NTRK2 融合; NTRK3 融合',
      companion_diagnostic: 'NGS 融合检测; FoundationOne CDx',
      indication: 'NTRK 融合基因阳性的不可切除或转移性实体瘤（泛肿瘤适应症）',
      mechanism: '高选择性 TRK 抑制剂，首个 FDA 批准的泛肿瘤靶向药',
      dosage_form: '口服溶液/胶囊', fda_status: 'FDA已批准', ema_status: 'EMA已批准',
      global_access: '全球可及（FDA+EMA双批准）' },

    // --- KRAS 靶向药 ---
    { name_cn: '索托拉西布', name_en: 'Sotorasib', generic_name: '索托拉西布',
      approval_number: 'JTH20230001', approval_date: '2023-06-30', approval_year: 2023,
      company: '安进/百济神州', drug_type: '小分子靶向药',
      molecular_target: 'KRAS G12C',
      gene_marker: 'KRAS G12C 突变',
      companion_diagnostic: 'KRAS G12C NGS 检测',
      indication: 'KRAS G12C 突变的局部晚期或转移性非小细胞肺癌',
      mechanism: '全球首个 KRAS G12C 抑制剂，不可逆结合 KRAS G12C 突变蛋白',
      dosage_form: '片剂 120mg', fda_status: 'FDA已批准', ema_status: 'EMA已批准',
      global_access: '全球可及（FDA+EMA双批准）' },

    // --- BRAF 靶向药 ---
    { name_cn: '维莫非尼', name_en: 'Vemurafenib', generic_name: '维莫非尼',
      approval_number: '国药准字H20170002', approval_date: '2017-03-22', approval_year: 2017,
      company: '罗氏', drug_type: '小分子靶向药',
      molecular_target: 'BRAF V600E',
      gene_marker: 'BRAF V600E 突变',
      companion_diagnostic: 'BRAF V600E 检测; cobas 4800 BRAF V600',
      indication: 'BRAF V600 突变阳性的不可切除或转移性黑色素瘤',
      mechanism: 'BRAF V600E 激酶抑制剂',
      dosage_form: '片剂 240mg', fda_status: 'FDA已批准', ema_status: 'EMA已批准',
      global_access: '全球可及（FDA+EMA双批准）' },

    { name_cn: '达拉非尼', name_en: 'Dabrafenib', generic_name: '甲磺酸达拉非尼',
      approval_number: '国药准字H20190001', approval_date: '2019-01-10', approval_year: 2019,
      company: '诺华', drug_type: '小分子靶向药',
      molecular_target: 'BRAF V600E/K',
      gene_marker: 'BRAF V600E 突变; BRAF V600K 突变',
      companion_diagnostic: 'BRAF V600 检测',
      indication: 'BRAF V600 突变阳性的不可切除或转移性黑色素瘤; 联合曲美替尼',
      mechanism: 'BRAF 激酶抑制剂，常与 MEK 抑制剂曲美替尼联合使用',
      dosage_form: '胶囊 50mg/75mg', fda_status: 'FDA已批准', ema_status: 'EMA已批准',
      global_access: '全球可及（FDA+EMA双批准）' },

    // --- HER2 靶向药 ---
    { name_cn: '曲妥珠单抗', name_en: 'Trastuzumab', generic_name: '注射用曲妥珠单抗',
      approval_number: '国药准字J20110020', approval_date: '2002-09-01', approval_year: 2002,
      company: '罗氏/基因泰克', drug_type: '单克隆抗体',
      molecular_target: 'HER2 / ERBB2',
      gene_marker: 'HER2 阳性（HER2 3+ IHC; HER2 扩增）',
      companion_diagnostic: 'HER2 IHC检测（PATHWAY anti-HER2）; HER2 FISH检测',
      indication: 'HER2 阳性早期乳腺癌; HER2 阳性转移性乳腺癌; HER2 阳性胃癌',
      mechanism: '人源化抗 HER2 单克隆抗体，抑制 HER2 介导的信号通路',
      dosage_form: '注射剂 150mg/440mg', fda_status: 'FDA已批准', ema_status: 'EMA已批准',
      global_access: '全球可及（FDA+EMA双批准）' },

    { name_cn: '德曲妥珠单抗', name_en: 'Trastuzumab Deruxtecan', generic_name: '德曲妥珠单抗',
      approval_number: '国药准字HJ20240001', approval_date: '2024-02-26', approval_year: 2024,
      company: '阿斯利康/第一三共', drug_type: '抗体药物偶联物（ADC）',
      molecular_target: 'HER2',
      gene_marker: 'HER2 阳性; HER2 低表达（IHC 1+或 2+/FISH-）',
      companion_diagnostic: 'HER2 IHC检测; HER2 FISH检测',
      indication: 'HER2 阳性不可切除或转移性乳腺癌; HER2 低表达乳腺癌; HER2 阳性胃癌',
      mechanism: 'HER2 靶向 ADC，连接拓扑异构酶 I 抑制剂（DXd），高效旁观者杀伤效应',
      dosage_form: '注射用粉针剂 100mg', fda_status: 'FDA已批准', ema_status: 'EMA已批准',
      global_access: '全球可及（FDA+EMA双批准）' },

    { name_cn: '吡咯替尼', name_en: 'Pyrotinib', generic_name: '马来酸吡咯替尼',
      approval_number: '国药准字H20180002', approval_date: '2018-08-16', approval_year: 2018,
      company: '恒瑞医药', drug_type: '小分子靶向药',
      molecular_target: 'HER2 / EGFR / HER4',
      gene_marker: 'HER2 阳性',
      companion_diagnostic: 'HER2 IHC检测; HER2 FISH检测',
      indication: 'HER2 阳性复发或转移性乳腺癌',
      mechanism: '国产创新药，不可逆泛 HER 家族酪氨酸激酶抑制剂',
      dosage_form: '片剂 80mg/160mg', fda_status: '未获FDA批准', ema_status: '未获EMA批准',
      global_access: '仅中国/有限国际可及' },

    // --- PD-1/PD-L1 免疫检查点抑制剂 ---
    { name_cn: '帕博利珠单抗', name_en: 'Pembrolizumab', generic_name: '注射用帕博利珠单抗',
      approval_number: '国药准字J20180002', approval_date: '2018-07-25', approval_year: 2018,
      company: '默沙东（MSD）', drug_type: '单克隆抗体',
      molecular_target: 'PD-1',
      gene_marker: 'PD-L1 阳性（TPS ≥ 1%; CPS ≥ 1; TPS ≥ 50%）; MSI-H; dMMR; TMB-H',
      companion_diagnostic: 'PD-L1 IHC 22C3 pharmDx; MSI检测; dMMR检测; TMB NGS检测',
      indication: '黑色素瘤; 非小细胞肺癌; 头颈部鳞癌; 经典霍奇金淋巴瘤; 尿路上皮癌; MSI-H/dMMR 实体瘤',
      mechanism: '抗 PD-1 单克隆抗体，阻断 PD-1/PD-L1 通路，恢复 T 细胞抗肿瘤活性',
      dosage_form: '注射剂 100mg/400mg', fda_status: 'FDA已批准', ema_status: 'EMA已批准',
      global_access: '全球可及（FDA+EMA双批准）' },

    { name_cn: '纳武利尤单抗', name_en: 'Nivolumab', generic_name: '纳武利尤单抗注射液',
      approval_number: '国药准字J20180001', approval_date: '2018-06-15', approval_year: 2018,
      company: '百时美施贵宝（BMS）', drug_type: '单克隆抗体',
      molecular_target: 'PD-1',
      gene_marker: 'PD-L1 阳性; MSI-H; dMMR; TMB-H',
      companion_diagnostic: 'PD-L1 IHC 28-8 pharmDx; MSI检测; dMMR检测',
      indication: '非小细胞肺癌; 头颈部鳞癌; 胃/胃食管结合部腺癌; 尿路上皮癌; 黑色素瘤; 肾细胞癌',
      mechanism: '抗 PD-1 单克隆抗体，全球首个 PD-1 抑制剂',
      dosage_form: '注射剂 40mg/100mg/240mg', fda_status: 'FDA已批准', ema_status: 'EMA已批准',
      global_access: '全球可及（FDA+EMA双批准）' },

    { name_cn: '特瑞普利单抗', name_en: 'Toripalimab', generic_name: '特瑞普利单抗注射液',
      approval_number: '国药准字S20180003', approval_date: '2018-12-17', approval_year: 2018,
      company: '君实生物', drug_type: '单克隆抗体',
      molecular_target: 'PD-1',
      gene_marker: 'PD-L1 阳性; MSI-H; dMMR',
      companion_diagnostic: 'PD-L1 IHC检测',
      indication: '黑色素瘤; 鼻咽癌; 尿路上皮癌; 食管鳞癌; 非小细胞肺癌',
      mechanism: '首个国产 PD-1 抑制剂，阻断 PD-1 与 PD-L1/PD-L2 的结合',
      dosage_form: '注射剂 80mg/240mg', fda_status: '未获FDA批准', ema_status: '未获EMA批准',
      global_access: '仅中国/有限国际可及' },

    { name_cn: '信迪利单抗', name_en: 'Sintilimab', generic_name: '信迪利单抗注射液',
      approval_number: '国药准字S20180004', approval_date: '2018-12-24', approval_year: 2018,
      company: '信达生物', drug_type: '单克隆抗体',
      molecular_target: 'PD-1',
      gene_marker: 'PD-L1 阳性; MSI-H; dMMR',
      companion_diagnostic: 'PD-L1 IHC检测',
      indication: '经典霍奇金淋巴瘤; 非小细胞肺癌; 肝癌; 食管癌; 胃癌; 宫颈癌',
      mechanism: '国产 PD-1 抑制剂，高亲和力结合 PD-1',
      dosage_form: '注射剂 100mg', fda_status: '未获FDA批准', ema_status: '未获EMA批准',
      global_access: '仅中国/有限国际可及' },

    { name_cn: '阿替利珠单抗', name_en: 'Atezolizumab', generic_name: '阿替利珠单抗注射液',
      approval_number: '国药准字J20200002', approval_date: '2020-02-14', approval_year: 2020,
      company: '罗氏/基因泰克', drug_type: '单克隆抗体',
      molecular_target: 'PD-L1',
      gene_marker: 'PD-L1 阳性（TC1/2/3或IC1/2/3）; MSI-H; dMMR',
      companion_diagnostic: 'PD-L1 IHC SP142; MSI检测',
      indication: '非小细胞肺癌; 小细胞肺癌; 肝癌; 黑色素瘤; 尿路上皮癌',
      mechanism: '抗 PD-L1 单克隆抗体，阻断 PD-L1 与 PD-1/CD80 的相互作用',
      dosage_form: '注射剂 1200mg', fda_status: 'FDA已批准', ema_status: 'EMA已批准',
      global_access: '全球可及（FDA+EMA双批准）' },

    // --- PARP 抑制剂 ---
    { name_cn: '奥拉帕利', name_en: 'Olaparib', generic_name: '奥拉帕利',
      approval_number: '国药准字H20180003', approval_date: '2018-08-22', approval_year: 2018,
      company: '阿斯利康', drug_type: '小分子靶向药',
      molecular_target: 'PARP1 / PARP2',
      gene_marker: 'BRCA1/BRCA2 突变; HRD 阳性（同源重组修复缺陷）; gBRCA 突变',
      companion_diagnostic: 'BRCA检测（Myriad myChoice）; HRD检测; FoundationOne CDx',
      indication: 'BRCA 突变的晚期卵巢癌; BRCA 突变的转移性乳腺癌; BRCA 突变的转移性胰腺癌; 去势抵抗性前列腺癌',
      mechanism: 'PARP 抑制剂，阻断 DNA 单链断裂修复，在 BRCA 突变细胞中产生合成致死',
      dosage_form: '片剂 100mg/150mg', fda_status: 'FDA已批准', ema_status: 'EMA已批准',
      global_access: '全球可及（FDA+EMA双批准）' },

    { name_cn: '氟唑帕利', name_en: 'Fluzoparib', generic_name: '氟唑帕利胶囊',
      approval_number: '国药准字H20200005', approval_date: '2020-12-14', approval_year: 2020,
      company: '恒瑞医药', drug_type: '小分子靶向药',
      molecular_target: 'PARP1 / PARP2',
      gene_marker: 'BRCA 突变; HRD 阳性',
      companion_diagnostic: 'BRCA检测; HRD检测',
      indication: 'BRCA1/2 突变的复发性卵巢癌; 前列腺癌（临床试验中）',
      mechanism: '国产 PARP 抑制剂，抑制 PARP 酶活性并形成 PARP-DNA 复合物',
      dosage_form: '胶囊 50mg', fda_status: '未获FDA批准', ema_status: '未获EMA批准',
      global_access: '仅中国/有限国际可及' },

    // --- BTK 抑制剂 ---
    { name_cn: '伊布替尼', name_en: 'Ibrutinib', generic_name: '伊布替尼胶囊',
      approval_number: '国药准字J20170001', approval_date: '2017-08-28', approval_year: 2017,
      company: '强生/Pharmacyclics', drug_type: '小分子靶向药',
      molecular_target: 'BTK',
      gene_marker: 'CD20 阳性; BTK 表达; B 细胞淋巴瘤',
      companion_diagnostic: 'CD20 IHC检测',
      indication: '套细胞淋巴瘤; 慢性淋巴细胞白血病/小淋巴细胞淋巴瘤; 华氏巨球蛋白血症',
      mechanism: '第一代 BTK 抑制剂，不可逆结合 BTK 激酶结构域 C481',
      dosage_form: '胶囊 140mg', fda_status: 'FDA已批准', ema_status: 'EMA已批准',
      global_access: '全球可及（FDA+EMA双批准）' },

    { name_cn: '泽布替尼', name_en: 'Zanubrutinib', generic_name: '泽布替尼胶囊',
      approval_number: '国药准字S20200001', approval_date: '2020-06-03', approval_year: 2020,
      company: '百济神州', drug_type: '小分子靶向药',
      molecular_target: 'BTK',
      gene_marker: 'CD20 阳性; BTK 表达',
      companion_diagnostic: 'CD20 IHC检测',
      indication: '套细胞淋巴瘤; 慢性淋巴细胞白血病/小淋巴细胞淋巴瘤; 华氏巨球蛋白血症',
      mechanism: '第二代 BTK 抑制剂，国产创新药，获 FDA 批准出海',
      dosage_form: '胶囊 80mg', fda_status: 'FDA已批准', ema_status: 'EMA已批准',
      global_access: '全球可及（FDA+EMA双批准）' },

    { name_cn: '奥布替尼', name_en: 'Orelabrutinib', generic_name: '奥布替尼片',
      approval_number: '国药准字H20200006', approval_date: '2020-12-25', approval_year: 2020,
      company: '诺诚健华', drug_type: '小分子靶向药',
      molecular_target: 'BTK',
      gene_marker: 'CD20 阳性; BTK 表达',
      companion_diagnostic: 'CD20 IHC检测',
      indication: '套细胞淋巴瘤; 慢性淋巴细胞白血病/小淋巴细胞淋巴瘤',
      mechanism: '第二代 BTK 抑制剂，国产创新药，高选择性 BTK 抑制剂',
      dosage_form: '片剂 50mg', fda_status: '未获FDA批准', ema_status: '未获EMA批准',
      global_access: '仅中国/有限国际可及' },

    // --- 抗血管生成药物 ---
    { name_cn: '贝伐珠单抗', name_en: 'Bevacizumab', generic_name: '贝伐珠单抗注射液',
      approval_number: '国药准字J20100001', approval_date: '2010-02-26', approval_year: 2010,
      company: '罗氏', drug_type: '单克隆抗体',
      molecular_target: 'VEGF-A',
      gene_marker: 'VEGF 表达; 微血管密度',
      companion_diagnostic: '暂无伴随诊断（广谱抗血管生成）',
      indication: '转移性结直肠癌; 非小细胞肺癌; 胶质母细胞瘤; 肾细胞癌; 宫颈癌; 卵巢癌',
      mechanism: '抗 VEGF-A 人源化单克隆抗体，抑制肿瘤血管生成',
      dosage_form: '注射剂 100mg/400mg', fda_status: 'FDA已批准', ema_status: 'EMA已批准',
      global_access: '全球可及（FDA+EMA双批准）' },

    { name_cn: '安罗替尼', name_en: 'Anlotinib', generic_name: '盐酸安罗替尼胶囊',
      approval_number: '国药准字H20180004', approval_date: '2018-05-08', approval_year: 2018,
      company: '正大天晴', drug_type: '小分子靶向药',
      molecular_target: 'VEGFR2 / VEGFR3 / FGFR / PDGFR / c-KIT',
      gene_marker: 'VEGFR 表达; FGFR 融合',
      companion_diagnostic: '暂无特定伴随诊断',
      indication: '非小细胞肺癌（三线）; 软组织肉瘤; 小细胞肺癌; 甲状腺髓样癌',
      mechanism: '国产创新多靶点酪氨酸激酶抑制剂，抑制肿瘤血管生成',
      dosage_form: '胶囊 8mg/10mg/12mg', fda_status: '未获FDA批准', ema_status: '未获EMA批准',
      global_access: '仅中国/有限国际可及' },

    // --- CDK4/6 抑制剂 ---
    { name_cn: '哌柏西利', name_en: 'Palbociclib', generic_name: '哌柏西利胶囊',
      approval_number: '国药准字J20180003', approval_date: '2018-07-31', approval_year: 2018,
      company: '辉瑞', drug_type: '小分子靶向药',
      molecular_target: 'CDK4 / CDK6',
      gene_marker: 'HR 阳性（ER+）; HER2 阴性; RB 阳性',
      companion_diagnostic: 'ER/PR IHC检测; HER2 IHC/FISH检测',
      indication: 'HR 阳性、HER2 阴性的局部晚期或转移性乳腺癌',
      mechanism: 'CDK4/6 抑制剂，阻断细胞周期 G1-S 转换，联合内分泌治疗',
      dosage_form: '胶囊 75mg/100mg/125mg', fda_status: 'FDA已批准', ema_status: 'EMA已批准',
      global_access: '全球可及（FDA+EMA双批准）' },

    { name_cn: '阿贝西利', name_en: 'Abemaciclib', generic_name: '阿贝西利片',
      approval_number: '国药准字H20200007', approval_date: '2020-12-31', approval_year: 2020,
      company: '礼来', drug_type: '小分子靶向药',
      molecular_target: 'CDK4 / CDK6',
      gene_marker: 'HR 阳性（ER+/PR+）; HER2 阴性',
      companion_diagnostic: 'ER/PR IHC检测; HER2 IHC/FISH检测',
      indication: 'HR 阳性、HER2 阴性的晚期或转移性乳腺癌（联合内分泌治疗/单药）',
      mechanism: 'CDK4/6 抑制剂，可单药使用，也可联合内分泌治疗',
      dosage_form: '片剂 50mg/100mg/150mg', fda_status: 'FDA已批准', ema_status: 'EMA已批准',
      global_access: '全球可及（FDA+EMA双批准）' },

    // --- 内分泌治疗 ---
    { name_cn: '氟维司群', name_en: 'Fulvestrant', generic_name: '氟维司群注射液',
      approval_number: '国药准字J20100002', approval_date: '2010-06-20', approval_year: 2010,
      company: '阿斯利康', drug_type: '内分泌治疗（SERD）',
      molecular_target: '雌激素受体（ER）',
      gene_marker: 'ER 阳性; HR 阳性; HER2 阴性',
      companion_diagnostic: 'ER IHC检测; PR IHC检测',
      indication: 'ER 阳性的局部晚期或转移性乳腺癌',
      mechanism: '选择性雌激素受体降解剂（SERD），降解 ER 蛋白，阻断 ER 信号',
      dosage_form: '注射液 250mg', fda_status: 'FDA已批准', ema_status: 'EMA已批准',
      global_access: '全球可及（FDA+EMA双批准）' },

    // --- 前列腺癌 ---
    { name_cn: '恩扎卢胺', name_en: 'Enzalutamide', generic_name: '恩扎卢胺软胶囊',
      approval_number: '国药准字H20200008', approval_date: '2020-11-26', approval_year: 2020,
      company: '安斯泰来/辉瑞', drug_type: '内分泌治疗',
      molecular_target: '雄激素受体（AR）',
      gene_marker: 'AR 阳性; 去势抵抗性前列腺癌（CRPC）',
      companion_diagnostic: 'AR检测; PSA检测',
      indication: '去势抵抗性前列腺癌（mCRPC、nmCRPC）; 转移性去势敏感性前列腺癌',
      mechanism: '第二代 AR 信号抑制剂，抑制 AR 核转运和 DNA 结合',
      dosage_form: '软胶囊 40mg', fda_status: 'FDA已批准', ema_status: 'EMA已批准',
      global_access: '全球可及（FDA+EMA双批准）' },

    // --- 化疗药物 ---
    { name_cn: '替莫唑胺', name_en: 'Temozolomide', generic_name: '替莫唑胺胶囊',
      approval_number: '国药准字H20040637', approval_date: '2004-12-01', approval_year: 2004,
      company: '默沙东', drug_type: '烷化剂（化疗）',
      molecular_target: 'DNA 烷化损伤',
      gene_marker: 'MGMT 启动子甲基化（预测敏感性）',
      companion_diagnostic: 'MGMT 甲基化检测（MSP）',
      indication: '多形性胶质母细胞瘤; 间变性星形细胞瘤',
      mechanism: '口服烷化剂，使 DNA O6 位鸟嘌呤甲基化，导致 DNA 断裂和细胞死亡',
      dosage_form: '胶囊 5mg/20mg/100mg/250mg', fda_status: 'FDA已批准', ema_status: 'EMA已批准',
      global_access: '全球可及（FDA+EMA双批准）' },

    // --- FGFR 抑制剂 ---
    { name_cn: '厄达替尼', name_en: 'Erdafitinib', generic_name: '厄达替尼片',
      approval_number: 'JTH20240002', approval_date: '2024-03-15', approval_year: 2024,
      company: '杨森/西安杨森', drug_type: '小分子靶向药',
      molecular_target: 'FGFR1 / FGFR2 / FGFR3 / FGFR4',
      gene_marker: 'FGFR2 融合; FGFR3 突变; FGFR3 融合',
      companion_diagnostic: 'FGFR NGS检测; FoundationOne CDx',
      indication: 'FGFR2/FGFR3 基因突变或融合的局部晚期或转移性尿路上皮癌',
      mechanism: '泛 FGFR 酪氨酸激酶抑制剂，首个 FDA 批准的 FGFR 抑制剂',
      dosage_form: '片剂 3mg/4mg/5mg', fda_status: 'FDA已批准', ema_status: 'EMA已批准',
      global_access: '全球可及（FDA+EMA双批准）' },

    // --- MET 抑制剂 ---
    { name_cn: '赛沃替尼', name_en: 'Savolitinib', generic_name: '赛沃替尼片',
      approval_number: '国药准字H20210001', approval_date: '2021-06-22', approval_year: 2021,
      company: '和记黄埔/阿斯利康', drug_type: '小分子靶向药',
      molecular_target: 'MET（HGF受体）',
      gene_marker: 'MET exon 14 跳变; MET 扩增',
      companion_diagnostic: 'MET exon 14 NGS检测',
      indication: 'MET exon 14 跳变阳性的局部晚期或转移性非小细胞肺癌',
      mechanism: '国产创新高选择性 MET 酪氨酸激酶抑制剂',
      dosage_form: '片剂 100mg/200mg', fda_status: '未获FDA批准', ema_status: '未获EMA批准',
      global_access: '仅中国/有限国际可及' },

    // --- RET 抑制剂 ---
    { name_cn: '普拉替尼', name_en: 'Pralsetinib', generic_name: '普拉替尼胶囊',
      approval_number: '国药准字H20210002', approval_date: '2021-03-08', approval_year: 2021,
      company: 'Blueprint Medicines/基石药业', drug_type: '小分子靶向药',
      molecular_target: 'RET',
      gene_marker: 'RET 融合阳性; RET M918T 突变',
      companion_diagnostic: 'RET FISH/NGS检测; FoundationOne CDx',
      indication: 'RET 融合阳性的转移性非小细胞肺癌; RET 突变的甲状腺髓样癌',
      mechanism: '高选择性 RET 抑制剂，对 RET 融合和激活突变有效',
      dosage_form: '胶囊 100mg', fda_status: 'FDA已批准', ema_status: '未获EMA批准',
      global_access: '部分国际可及（FDA单批准）' },

    // --- ADC 药物 ---
    { name_cn: '维迪西妥单抗', name_en: 'Disitamab Vedotin', generic_name: '注射用维迪西妥单抗',
      approval_number: '国药准字S20210003', approval_date: '2021-06-09', approval_year: 2021,
      company: '荣昌生物/Seagen', drug_type: '抗体药物偶联物（ADC）',
      molecular_target: 'HER2',
      gene_marker: 'HER2 阳性; HER2 低表达（IHC 2+/FISH-; IHC 1+）',
      companion_diagnostic: 'HER2 IHC检测; HER2 FISH检测',
      indication: 'HER2 表达的局部晚期或转移性胃癌; HER2 表达的尿路上皮癌',
      mechanism: '国产 ADC，靶向 HER2，连接微管抑制剂（MMAE）',
      dosage_form: '注射用粉针剂 60mg', fda_status: 'FDA已批准', ema_status: '未获EMA批准',
      global_access: '部分国际可及（FDA单批准）' },

    // --- BCL-2 抑制剂 ---
    { name_cn: '维奈克拉', name_en: 'Venetoclax', generic_name: '维奈克拉片',
      approval_number: '国药准字H20200009', approval_date: '2020-12-02', approval_year: 2020,
      company: '艾伯维/罗氏', drug_type: '小分子靶向药',
      molecular_target: 'BCL-2',
      gene_marker: 'BCL-2 过表达; t(14;18) 易位; IGHV 突变状态',
      companion_diagnostic: 'BCL-2 IHC检测; FISH 检测 t(14;18)',
      indication: '急性髓系白血病（联合去甲基化药物）; 慢性淋巴细胞白血病',
      mechanism: '选择性 BCL-2 抑制剂，恢复 CLL 细胞凋亡通路',
      dosage_form: '片剂 10mg/50mg/100mg', fda_status: 'FDA已批准', ema_status: 'EMA已批准',
      global_access: '全球可及（FDA+EMA双批准）' },

    // --- 免疫调节药物 ---
    { name_cn: '来那度胺', name_en: 'Lenalidomide', generic_name: '来那度胺胶囊',
      approval_number: '国药准字H20130001', approval_date: '2013-01-23', approval_year: 2013,
      company: '新基/百济神州', drug_type: '免疫调节/抗血管生成',
      molecular_target: 'CRBN（cereblon）/ 免疫调节',
      gene_marker: 'del(5q); IHC del(17p); TP53 突变（预后因素）',
      companion_diagnostic: 'FISH del(5q) 检测; TP53 突变检测',
      indication: '多发性骨髓瘤; 骨髓增生异常综合征（伴 del 5q）; 套细胞淋巴瘤',
      mechanism: '免疫调节药物（IMiD），抑制肿瘤细胞增殖，促进 T/NK 细胞活化',
      dosage_form: '胶囊 5mg/10mg/15mg/25mg', fda_status: 'FDA已批准', ema_status: 'EMA已批准',
      global_access: '全球可及（FDA+EMA双批准）' },

    // --- 西达本胺 ---
    { name_cn: '西达本胺', name_en: 'Chidamide', generic_name: '西达本胺片',
      approval_number: '国药准字H20140100', approval_date: '2014-12-01', approval_year: 2014,
      company: '微芯生物', drug_type: '表观遗传治疗（HDAC抑制剂）',
      molecular_target: 'HDAC1 / HDAC2 / HDAC3 / HDAC10',
      gene_marker: '表观遗传重编程; 组蛋白乙酰化',
      companion_diagnostic: '暂无特定伴随诊断',
      indication: '复发或难治性外周 T 细胞淋巴瘤（PTCL）',
      mechanism: '国产原创 HDAC 抑制剂，表观遗传调控，增强抗肿瘤免疫',
      dosage_form: '片剂 5mg', fda_status: '未获FDA批准', ema_status: '未获EMA批准',
      global_access: '仅中国/有限国际可及' },

    // --- CAR-T 细胞疗法 ---
    { name_cn: '阿基仑赛', name_en: 'Axicabtagene Ciloleucel', generic_name: '阿基仑赛注射液',
      approval_number: '国药准字S20210004', approval_date: '2021-06-22', approval_year: 2021,
      company: '复星凯特/Kite Pharma', drug_type: 'CAR-T 细胞疗法',
      molecular_target: 'CD19',
      gene_marker: 'CD19 阳性; B 细胞淋巴瘤',
      companion_diagnostic: 'CD19 IHC检测; 流式细胞术',
      indication: '复发或难治性大 B 细胞淋巴瘤（DLBCL）',
      mechanism: '自体 CD19 靶向 CAR-T 细胞疗法，第二代 CAR（CD28 共刺激域）',
      dosage_form: '细胞注射液（约 2×10^8 CAR-T 细胞）', fda_status: 'FDA已批准', ema_status: 'EMA已批准',
      global_access: '全球可及（FDA+EMA双批准）' },

    { name_cn: '瑞基奥仑赛', name_en: 'Relmacabtagene Autoleucel', generic_name: '瑞基奥仑赛注射液',
      approval_number: '国药准字S20210005', approval_date: '2021-09-03', approval_year: 2021,
      company: '药明巨诺/Juno Therapeutics', drug_type: 'CAR-T 细胞疗法',
      molecular_target: 'CD19',
      gene_marker: 'CD19 阳性; B 细胞淋巴瘤',
      companion_diagnostic: 'CD19 IHC检测; 流式细胞术',
      indication: '复发或难治性大 B 细胞淋巴瘤',
      mechanism: '第二代 CD19 靶向 CAR-T 细胞疗法（4-1BB 共刺激域）',
      dosage_form: '细胞注射液', fda_status: '未获FDA批准', ema_status: '未获EMA批准',
      global_access: '仅中国/有限国际可及' },

    // --- JAK 抑制剂 ---
    { name_cn: '鲁索替尼', name_en: 'Ruxolitinib', generic_name: '磷酸芦可替尼片',
      approval_number: '国药准字H20170003', approval_date: '2017-03-20', approval_year: 2017,
      company: '诺华/Incyte', drug_type: '小分子靶向药',
      molecular_target: 'JAK1 / JAK2',
      gene_marker: 'JAK2 V617F 突变; JAK2 外显子 12 突变; CALR 突变; MPL 突变',
      companion_diagnostic: 'JAK2 V617F PCR/NGS检测; JAK2 外显子 12 突变检测',
      indication: '骨髓纤维化; 真性红细胞增多症; 原发性血小板增多症',
      mechanism: 'JAK1/JAK2 酪氨酸激酶抑制剂，抑制 JAK-STAT 信号通路',
      dosage_form: '片剂 5mg/10mg/15mg/20mg', fda_status: 'FDA已批准', ema_status: 'EMA已批准',
      global_access: '全球可及（FDA+EMA双批准）' },

    // --- 索拉非尼/仑伐替尼等多激酶抑制剂 ---
    { name_cn: '索拉非尼', name_en: 'Sorafenib', generic_name: '甲苯磺酸索拉非尼片',
      approval_number: '国药准字J20110005', approval_date: '2008-07-14', approval_year: 2008,
      company: '拜耳', drug_type: '小分子靶向药',
      molecular_target: 'VEGFR / PDGFR / RAF / KIT / FLT3',
      gene_marker: 'VEGF 表达; KIT 突变（胃肠道间质瘤）',
      companion_diagnostic: '暂无特定伴随诊断',
      indication: '不可切除肝细胞癌; 肾细胞癌; 放射性碘难治性分化型甲状腺癌',
      mechanism: '多激酶抑制剂，同时抑制肿瘤细胞增殖和血管生成',
      dosage_form: '片剂 200mg', fda_status: 'FDA已批准', ema_status: 'EMA已批准',
      global_access: '全球可及（FDA+EMA双批准）' },

    { name_cn: '仑伐替尼', name_en: 'Lenvatinib', generic_name: '甲磺酸仑伐替尼胶囊',
      approval_number: '国药准字H20180005', approval_date: '2018-09-05', approval_year: 2018,
      company: '卫材/默沙东', drug_type: '小分子靶向药',
      molecular_target: 'VEGFR1-3 / FGFR1-4 / PDGFRα / RET / KIT',
      gene_marker: 'VEGFR 表达; FGFR 突变',
      companion_diagnostic: '暂无特定伴随诊断',
      indication: '不可切除肝细胞癌; 放射性碘难治性分化型甲状腺癌; 肾细胞癌（联合依维莫司）; 子宫内膜癌（联合帕博利珠单抗）',
      mechanism: '多激酶抑制剂，强效抑制 VEGFR 和 FGFR 家族',
      dosage_form: '胶囊 4mg/10mg', fda_status: 'FDA已批准', ema_status: 'EMA已批准',
      global_access: '全球可及（FDA+EMA双批准）' },

    // --- IDH 抑制剂 ---
    { name_cn: '艾伏尼布', name_en: 'Ivosidenib', generic_name: '艾伏尼布片',
      approval_number: '国药准字H20220003', approval_date: '2022-02-09', approval_year: 2022,
      company: '施维雅/基石药业', drug_type: '小分子靶向药',
      molecular_target: 'IDH1',
      gene_marker: 'IDH1 R132H 突变; IDH1 R132C 突变',
      companion_diagnostic: 'IDH1 突变 NGS检测',
      indication: 'IDH1 突变的复发或难治性急性髓系白血病（AML）; IDH1 突变的胆管癌',
      mechanism: '首个 IDH1 抑制剂，抑制致癌代谢物 2-HG 生成',
      dosage_form: '片剂 250mg', fda_status: 'FDA已批准', ema_status: 'EMA已批准',
      global_access: '全球可及（FDA+EMA双批准）' },

    // --- 达雷妥尤单抗 ---
    { name_cn: '达雷妥尤单抗', name_en: 'Daratumumab', generic_name: '达雷妥尤单抗注射液',
      approval_number: '国药准字J20190002', approval_date: '2019-07-05', approval_year: 2019,
      company: '强生/Genmab', drug_type: '单克隆抗体',
      molecular_target: 'CD38',
      gene_marker: 'CD38 阳性; 多发性骨髓瘤细胞',
      companion_diagnostic: 'CD38 IHC检测; 流式细胞术',
      indication: '多发性骨髓瘤（一线至五线治疗）',
      mechanism: '抗 CD38 人源化单克隆抗体，ADCC/ADCP/CDC 多种抗肿瘤机制',
      dosage_form: '注射剂 100mg/400mg', fda_status: 'FDA已批准', ema_status: 'EMA已批准',
      global_access: '全球可及（FDA+EMA双批准）' },

    // --- Claudin18.2 ---
    { name_cn: '佐妥昔单抗', name_en: 'Zolbetuximab', generic_name: '注射用佐妥昔单抗',
      approval_number: 'JTH20240003', approval_date: '2024-05-09', approval_year: 2024,
      company: '安斯泰来/Astellas', drug_type: '单克隆抗体',
      molecular_target: 'Claudin 18.2 / CLDN18.2',
      gene_marker: 'Claudin18.2 阳性（CLDN18.2 IHC ≥ 75% 肿瘤细胞中等至强染色）',
      companion_diagnostic: 'Claudin18.2 IHC 48-17 检测',
      indication: 'HER2 阴性、CLDN18.2 阳性、PD-L1 阴性的局部晚期不可切除或转移性胃及胃食管结合部腺癌（联合化疗）',
      mechanism: '全球首个抗 Claudin18.2 单抗，ADCC 和 CDC 抗肿瘤机制',
      dosage_form: '注射用粉针剂 200mg', fda_status: 'FDA已批准', ema_status: 'EMA已批准',
      global_access: '全球可及（FDA+EMA双批准）' },
  ];

  const insertStmt = db.prepare(`
    INSERT INTO drugs (
      name_cn, name_en, generic_name, approval_number, approval_date, approval_year,
      company, drug_type, molecular_target, gene_marker, companion_diagnostic,
      indication, mechanism, dosage_form, fda_status, ema_status, global_access
    ) VALUES (
      @name_cn, @name_en, @generic_name, @approval_number, @approval_date, @approval_year,
      @company, @drug_type, @molecular_target, @gene_marker, @companion_diagnostic,
      @indication, @mechanism, @dosage_form, @fda_status, @ema_status, @global_access
    )
  `);

  const tx = db.transaction((drugs) => {
    for (const d of drugs) {
      insertStmt.run(d);
    }
  });

  tx(seedDrugs);
  console.log('[OK] 已插入 ' + seedDrugs.length + ' 条种子药物数据');
}

// ================================
// 路由
// ================================
app.get('/', (req, res) => {
  try {
    const stats = db ? db.prepare(`
      SELECT
        (SELECT COUNT(*) FROM drugs) as total_drugs,
        (SELECT COUNT(*) FROM drugs WHERE approval_year >= 2020) as new_drugs,
        (SELECT COUNT(*) FROM drugs WHERE fda_status LIKE '%FDA%') as fda_approved,
        (SELECT COUNT(DISTINCT drug_type) FROM drugs) as unique_targets
    `).get() : { total_drugs: 0, new_drugs: 0, fda_approved: 0, unique_targets: 0 };

    const recentDrugs = db ? db.prepare(`
      SELECT id, name_cn, name_en, molecular_target, approval_year, drug_type, global_access
      FROM drugs ORDER BY approval_year DESC, id DESC LIMIT 8
    `).all() : [];

    let recentHtml = '';
    if (recentDrugs && recentDrugs.length > 0) {
      recentHtml = recentDrugs.map(function(d) {
        const targetShort = (d.molecular_target || '').substring(0, 28) + ((d.molecular_target || '').length > 28 ? '...' : '');
        return '<div class="col-md-6 col-lg-3">' +
          '<div class="card drug-card p-3 h-100"><div class="card-body">' +
          '<h5 class="card-title mb-2">' + d.name_cn + '</h5>' +
          '<p class="card-text small text-muted mb-2">' + (d.name_en || '') + '</p>' +
          '<div class="mb-2"><span class="drug-target-badge"><i class="bi bi-bullseye me-1"></i>' + targetShort + '</span></div>' +
          '<div class="mb-3"><span class="chinese-badge">' + d.drug_type + '</span> <span class="badge bg-secondary">' + d.approval_year + '年</span></div>' +
          '<a href="/drug/' + d.id + '" class="btn btn-primary-custom w-100"><i class="bi bi-info-circle me-1"></i>查看详情</a>' +
          '</div></div></div>';
      }).join('');
    } else {
      recentHtml = '<div class="col-12"><div class="alert alert-info-custom p-4"><i class="bi bi-info-circle me-2"></i>数据库正在初始化，请稍后访问...</div></div>';
    }

    const bodyHtml = `
      <section class="hero-section">
        <div class="container text-center">
          <h1 class="hero-title"><i class="bi bi-dna me-3"></i>基因药物知识库</h1>
          <p class="hero-subtitle">抗肿瘤药物 · 基因靶点 · 生物标志物 · 伴随诊断<br>
          <span class="text-gradient-gold">精准医疗时代的药物信息查询平台</span></p>
          <div class="search-box">
            <form action="/drugs" method="GET" class="d-flex gap-2">
              <input type="text" name="q" class="form-control search-input" placeholder="搜索药物名称、靶点、基因、适应症...">
              <button type="submit" class="btn btn-warning search-btn"><i class="bi bi-search me-2"></i>搜索</button>
            </form>
          </div>
        </div>
      </section>

      <section class="container mb-5">
        <div class="row g-4">
          <div class="col-md-3 col-6"><div class="card stat-card p-4 h-100"><div class="d-flex align-items-center mb-2"><div class="icon-circle bg-primary text-white me-3"><i class="bi bi-capsule-pill"></i></div><div><div class="stat-number">${stats.total_drugs}</div><div class="text-muted small">收录药物总数</div></div></div></div></div>
          <div class="col-md-3 col-6"><div class="card stat-card p-4 h-100" style="border-left-color:#2e7d32"><div class="d-flex align-items-center mb-2"><div class="icon-circle text-white me-3" style="background:#2e7d32"><i class="bi bi-globe2"></i></div><div><div class="stat-number" style="color:#2e7d32">${stats.fda_approved}</div><div class="text-muted small">FDA已批准</div></div></div></div></div>
          <div class="col-md-3 col-6"><div class="card stat-card p-4 h-100" style="border-left-color:#ef6c00"><div class="d-flex align-items-center mb-2"><div class="icon-circle text-white me-3" style="background:#ef6c00"><i class="bi bi-bullseye"></i></div><div><div class="stat-number" style="color:#ef6c00">${stats.unique_targets}</div><div class="text-muted small">药物类型</div></div></div></div></div>
          <div class="col-md-3 col-6"><div class="card stat-card p-4 h-100" style="border-left-color:#7b1fa2"><div class="d-flex align-items-center mb-2"><div class="icon-circle text-white me-3" style="background:#7b1fa2"><i class="bi bi-stars"></i></div><div><div class="stat-number" style="color:#7b1fa2">${stats.new_drugs}</div><div class="text-muted small">2020年后新批准</div></div></div></div></div>
        </div>
      </section>

      <section class="container mb-5"><h2 class="section-title"><i class="bi bi-clock-history me-2"></i>最新批准药物</h2><div class="row g-4">${recentHtml}</div></section>

      <section class="container mb-5"><h2 class="section-title"><i class="bi bi-filter-circle me-2"></i>快速分类查询</h2><div class="row g-3">
        <div class="col-md-4"><div class="card p-4 text-center h-100"><div class="icon-circle mx-auto mb-3 text-white" style="background:#1565c0; width:64px; height:64px; font-size:2rem;"><i class="bi bi-box"></i></div><h5 class="mb-3">小分子靶向药</h5><p class="text-muted small mb-3">EGFR、ALK、ROS1、KRAS、BTK、PARP 等酪氨酸激酶抑制剂</p><a href="/drugs?type=小分子靶向药" class="btn btn-primary-custom"><i class="bi bi-search me-1"></i>浏览</a></div></div>
        <div class="col-md-4"><div class="card p-4 text-center h-100"><div class="icon-circle mx-auto mb-3 text-white" style="background:#2e7d32; width:64px; height:64px; font-size:2rem;"><i class="bi bi-hexagon"></i></div><h5 class="mb-3">免疫检查点抑制剂</h5><p class="text-muted small mb-3">PD-1/PD-L1 单抗类药物，帕博利珠单抗、纳武利尤单抗、信迪利单抗等</p><a href="/drugs?target=PD-1" class="btn btn-primary-custom"><i class="bi bi-search me-1"></i>浏览</a></div></div>
        <div class="col-md-4"><div class="card p-4 text-center h-100"><div class="icon-circle mx-auto mb-3 text-white" style="background:#7b1fa2; width:64px; height:64px; font-size:2rem;"><i class="bi bi-magic"></i></div><h5 class="mb-3">抗体药物偶联物 (ADC)</h5><p class="text-muted small mb-3">德曲妥珠单抗（DS-8201）、维迪西妥单抗、戈沙妥珠单抗等</p><a href="/drugs?type=抗体药物偶联物" class="btn btn-primary-custom"><i class="bi bi-search me-1"></i>浏览</a></div></div>
      </div></section>

      <section class="container mb-5"><h2 class="section-title"><i class="bi bi-file-earmark-medical me-2"></i>关键生物标志物指南</h2><div class="row g-4">
        <div class="col-md-3"><div class="info-section"><h6 class="fw-bold mb-2"><i class="bi bi-activity me-2 text-primary"></i>EGFR 突变</h6><p class="small text-muted mb-3">非小细胞肺癌最常见靶点，检测 19del、L858R、T790M、C797S、exon 20 ins</p><a href="/drugs?target=EGFR" class="small text-decoration-none">查看药物 →</a></div></div>
        <div class="col-md-3"><div class="info-section"><h6 class="fw-bold mb-2"><i class="bi bi-activity me-2 text-success"></i>PD-L1 表达</h6><p class="small text-muted mb-3">免疫治疗预测标志物，TPS/CPS 评分，MSI-H/dMMR 泛肿瘤适应症</p><a href="/drugs?target=PD-L1" class="small text-decoration-none">查看药物 →</a></div></div>
        <div class="col-md-3"><div class="info-section"><h6 class="fw-bold mb-2"><i class="bi bi-activity me-2 text-warning"></i>HER2 表达/扩增</h6><p class="small text-muted mb-3">乳腺癌、胃癌关键靶点，IHC 3+ 或 FISH+，ADC 药物新突破</p><a href="/drugs?target=HER2" class="small text-decoration-none">查看药物 →</a></div></div>
        <div class="col-md-3"><div class="info-section"><h6 class="fw-bold mb-2"><i class="bi bi-activity me-2 text-danger"></i>BRCA/HRD</h6><p class="small text-muted mb-3">PARP 抑制剂预测标志物，卵巢癌、乳腺癌、胰腺癌、前列腺癌适用</p><a href="/drugs?target=PARP" class="small text-decoration-none">查看药物 →</a></div></div>
      </div></section>
    `;

    renderLayout(res, '首页', 'home', bodyHtml);
  } catch (err) {
    console.error('[ERROR] 首页渲染失败:', err);
    renderLayout(res, '首页', 'home', '<div class="container my-5"><div class="alert alert-danger">首页加载失败: ' + err.message + '</div></div>');
  }
});

// ================================
// 路由（使用 renderLayout）
// ================================
app.get('/drugs', (req, res) => {
  try {
    const query = (req.query.q || '').trim();
    const type = req.query.type || '';
    const year = req.query.year || '';
    const target = req.query.target || '';
    const access = req.query.access || '';
    const pageNum = parseInt(req.query.page || '1');
    const pageSize = 20;

    let whereClauses = [];
    let params = {};

    if (query) {
      whereClauses.push('(name_cn LIKE @q OR name_en LIKE @q OR generic_name LIKE @q OR molecular_target LIKE @q OR gene_marker LIKE @q OR indication LIKE @q OR company LIKE @q)');
      params.q = '%' + query + '%';
    }
    if (type) {
      whereClauses.push('drug_type = @type');
      params.type = type;
    }
    if (year) {
      whereClauses.push('approval_year = @year');
      params.year = parseInt(year);
    }
    if (target) {
      whereClauses.push('molecular_target LIKE @target');
      params.target = '%' + target + '%';
    }
    if (access) {
      if (access === 'global') whereClauses.push("fda_status LIKE '%FDA%'");
      if (access === 'china') whereClauses.push("fda_status NOT LIKE '%FDA%'");
    }

    const whereSql = whereClauses.length > 0 ? 'WHERE ' + whereClauses.join(' AND ') : '';
    const totalCount = db ? db.prepare('SELECT COUNT(*) as cnt FROM drugs ' + whereSql).get(params).cnt : 0;
    const totalPages = Math.max(1, Math.ceil(totalCount / pageSize));
    const actualPage = Math.min(pageNum, totalPages);
    const offset = (actualPage - 1) * pageSize;

    const sql = 'SELECT * FROM drugs ' + whereSql + ' ORDER BY approval_year DESC, id DESC LIMIT ' + pageSize + ' OFFSET ' + offset;
    const drugs = db ? db.prepare(sql).all(params) : [];

    const years = db ? db.prepare('SELECT DISTINCT approval_year FROM drugs WHERE approval_year IS NOT NULL ORDER BY approval_year DESC').all().map(r => r.approval_year) : [];
    const types = db ? db.prepare('SELECT DISTINCT drug_type FROM drugs WHERE drug_type IS NOT NULL').all().map(r => r.drug_type) : [];
    const targets = ['EGFR', 'ALK', 'ROS1', 'KRAS', 'NTRK', 'HER2', 'PD-1', 'PD-L1', 'BTK', 'PARP', 'VEGFR', 'CDK4/6', 'FGFR', 'MET', 'RET', 'BCL-2', 'CD19', 'CD38', 'AR', 'ER', 'JAK', 'IDH', 'Claudin'];

    let drugsHtml = '';
    if (drugs && drugs.length > 0) {
      drugsHtml = '<div class="row g-4">' + drugs.map(function(d) {
        const isFda = String(d.fda_status || '').indexOf('FDA') > -1;
        return '<div class="col-md-6 col-lg-4"><div class="card drug-card p-3 h-100"><div class="card-body">' +
          '<h5 class="card-title mb-2">' + String(d.name_cn) + '</h5>' +
          '<p class="card-text small text-muted mb-2">' + String(d.name_en || '') + '</p>' +
          '<div class="mb-2"><span class="drug-target-badge"><i class="bi bi-bullseye me-1"></i>' + String(d.molecular_target || '').substring(0, 30) + (String(d.molecular_target || '').length > 30 ? '...' : '') + '</span></div>' +
          '<div class="mb-2"><span class="chinese-badge">' + String(d.drug_type) + '</span> <span class="badge bg-secondary">' + d.approval_year + '年</span>' +
          (isFda ? ' <span class="fda-badge">FDA批准</span>' : '') + '</div>' +
          '<p class="small text-muted mb-3" style="min-height:40px;">' + String(d.indication || '').substring(0, 80) + (String(d.indication || '').length > 80 ? '...' : '') + '</p>' +
          '<a href="/drug/' + d.id + '" class="btn btn-primary-custom w-100"><i class="bi bi-info-circle me-1"></i>查看详情</a>' +
          '</div></div></div>';
      }).join('') + '</div>';
    } else {
      drugsHtml = '<div class="alert alert-info-custom"><i class="bi bi-info-circle me-2"></i>暂无匹配的药物。请尝试调整筛选条件。</div>';
    }

    let paginationHtml = '';
    if (totalPages > 1) {
      paginationHtml = '<nav><ul class="pagination pagination-custom justify-content-center">';
      const queryStr = (req.originalUrl.split('?')[1] || '').replace(/&?page=\d+/g, '').replace(/&$/, '');
      const baseUrl = '/drugs' + (queryStr ? '?' + queryStr : '');
      if (actualPage > 1) {
        paginationHtml += '<li class="page-item"><a class="page-link" href="' + baseUrl + (baseUrl.indexOf('?') > -1 ? '&' : '?') + 'page=' + (actualPage - 1) + '">上一页</a></li>';
      }
      const startP = Math.max(1, actualPage - 2);
      const endP = Math.min(totalPages, startP + 4);
      for (let p = startP; p <= endP; p++) {
        paginationHtml += '<li class="page-item ' + (p === actualPage ? 'active' : '') + '"><a class="page-link" href="' + baseUrl + (baseUrl.indexOf('?') > -1 ? '&' : '?') + 'page=' + p + '">' + p + '</a></li>';
      }
      if (actualPage < totalPages) {
        paginationHtml += '<li class="page-item"><a class="page-link" href="' + baseUrl + (baseUrl.indexOf('?') > -1 ? '&' : '?') + 'page=' + (actualPage + 1) + '">下一页</a></li>';
      }
      paginationHtml += '</ul></nav>';
    }

    const filterHtml = '<div class="filter-card mb-4">' +
      '<div class="row g-3 align-items-center">' +
      '<div class="col-md-4"><label class="form-label small fw-bold text-uppercase">关键字搜索</label>' +
      '<form action="/drugs" method="GET" class="d-flex gap-2"><input type="text" name="q" value="' + query + '" class="form-control" placeholder="药物/靶点/基因"><button type="submit" class="btn btn-primary"><i class="bi bi-search"></i></button></form></div>' +
      '<div class="col-md-2"><label class="form-label small fw-bold text-uppercase">药物类型</label>' +
      '<select class="form-select" onchange="location.href=this.value"><option value="/drugs?q=' + query + '">全部</option>' +
      types.map(t => '<option value="/drugs?q=' + query + '&type=' + encodeURIComponent(t) + '"' + (type === t ? ' selected' : '') + '>' + t + '</option>').join('') +
      '</select></div>' +
      '<div class="col-md-2"><label class="form-label small fw-bold text-uppercase">批准年份</label>' +
      '<select class="form-select" onchange="location.href=this.value"><option value="/drugs?q=' + query + '">全部</option>' +
      years.map(y => '<option value="/drugs?q=' + query + '&year=' + y + '"' + (String(year) === String(y) ? ' selected' : '') + '>' + y + '年</option>').join('') +
      '</select></div>' +
      '<div class="col-md-2"><label class="form-label small fw-bold text-uppercase">靶点</label>' +
      '<select class="form-select" onchange="location.href=this.value"><option value="/drugs?q=' + query + '">全部</option>' +
      targets.map(tg => '<option value="/drugs?q=' + query + '&target=' + encodeURIComponent(tg) + '"' + (target === tg ? ' selected' : '') + '>' + tg + '</option>').join('') +
      '</select></div>' +
      '<div class="col-md-2"><label class="form-label small fw-bold text-uppercase">国际可及性</label>' +
      '<select class="form-select" onchange="location.href=this.value"><option value="/drugs?q=' + query + '">全部</option>' +
      '<option value="/drugs?q=' + query + '&access=global"' + (access === 'global' ? ' selected' : '') + '>FDA已批准</option>' +
      '<option value="/drugs?q=' + query + '&access=china"' + (access === 'china' ? ' selected' : '') + '>未获FDA批准</option>' +
      '</select></div></div></div>';

    const bodyHtml = '<section class="container py-5">' +
      '<h2 class="section-title"><i class="bi bi-capsule me-2"></i>药物库</h2>' +
      '<div class="mb-3 text-muted small">共找到 <strong>' + totalCount + '</strong> 条药物记录' + (query ? '（关键词："' + query + '"）' : '') + '</div>' +
      filterHtml + drugsHtml + paginationHtml + '</section>';

    renderLayout(res, '药物列表', 'drugs', bodyHtml);
  } catch (err) {
    console.error('[ERROR] 药物列表失败:', err);
    renderLayout(res, '药物列表', 'drugs', '<div class="container py-5"><div class="alert alert-danger">数据查询失败: ' + err.message + '</div></div>');
  }
});

app.get('/drug/:id', (req, res) => {
  try {
    const drug = db ? db.prepare('SELECT * FROM drugs WHERE id = ?').get(parseInt(req.params.id)) : null;
    if (!drug) {
      return renderLayout(res, '未找到', '404', '<div class="container py-5"><div class="alert alert-warning">未找到该药物。</div></div>');
    }

    const relatedDrugs = db ? db.prepare('SELECT id, name_cn, name_en, drug_type, molecular_target FROM drugs WHERE id != ? AND drug_type = ? ORDER BY approval_year DESC LIMIT 4').all(parseInt(req.params.id), drug.drug_type) : [];

    const isFda = String(drug.fda_status || '').indexOf('FDA') > -1;
    const isEma = String(drug.ema_status || '').indexOf('EMA') > -1;

    const detailHtml = '<div class="detail-row"><div class="detail-label">药物中文名</div><div class="detail-value fw-bold">' + String(drug.name_cn) + '</div></div>' +
      '<div class="detail-row"><div class="detail-label">英文名 / 通用名</div><div class="detail-value">' + String(drug.name_en || '-') + ' / ' + String(drug.generic_name || '-') + '</div></div>' +
      '<div class="detail-row"><div class="detail-label">批准文号</div><div class="detail-value">' + String(drug.approval_number || '-') + '</div></div>' +
      '<div class="detail-row"><div class="detail-label">批准日期</div><div class="detail-value">' + String(drug.approval_date || '-') + '</div></div>' +
      '<div class="detail-row"><div class="detail-label">生产厂家</div><div class="detail-value">' + String(drug.company || '-') + '</div></div>' +
      '<div class="detail-row"><div class="detail-label">药物类型</div><div class="detail-value"><span class="chinese-badge">' + String(drug.drug_type) + '</span></div></div>' +
      '<div class="detail-row"><div class="detail-label">分子靶点</div><div class="detail-value"><span class="drug-target-badge"><i class="bi bi-bullseye me-1"></i>' + String(drug.molecular_target || '-') + '</span></div></div>' +
      '<div class="detail-row"><div class="detail-label">生物标志物 / 基因突变</div><div class="detail-value"><span class="gene-badge"><i class="bi bi-dna me-1"></i>' + String(drug.gene_marker || '-') + '</span></div></div>' +
      '<div class="detail-row"><div class="detail-label">伴随诊断检测方法</div><div class="detail-value">' + String(drug.companion_diagnostic || '-') + '</div></div>' +
      '<div class="detail-row"><div class="detail-label">适应症</div><div class="detail-value">' + String(drug.indication || '-') + '</div></div>' +
      '<div class="detail-row"><div class="detail-label">作用机制</div><div class="detail-value">' + String(drug.mechanism || '-') + '</div></div>' +
      '<div class="detail-row"><div class="detail-label">剂型与给药</div><div class="detail-value">' + String(drug.dosage_form || '-') + '</div></div>' +
      '<div class="detail-row"><div class="detail-label">国际批准状态</div><div class="detail-value">' +
      (isFda ? ' <span class="fda-badge">' + String(drug.fda_status) + '</span>' : '') +
      (isEma ? ' <span class="ema-badge">' + String(drug.ema_status) + '</span>' : '') +
      (!isFda && !isEma ? ' <span class="chinese-badge">' + String(drug.global_access || '仅中国可及') + '</span>' : '') +
      '</div></div>';

    let relatedHtml = '';
    if (relatedDrugs && relatedDrugs.length > 0) {
      relatedHtml = '<div class="row g-3">' + relatedDrugs.map(function(d) {
        return '<div class="col-md-3"><div class="card p-3 h-100"><div class="card-body"><h6 class="card-title">' + String(d.name_cn) + '</h6>' +
          '<p class="small text-muted mb-2">' + String(d.name_en || '') + '</p>' +
          '<p class="small mb-3">' + String(d.molecular_target || '').substring(0, 40) + '</p>' +
          '<a href="/drug/' + d.id + '" class="btn btn-primary btn-sm w-100">查看详情</a></div></div></div>';
      }).join('') + '</div>';
    }

    const bodyHtml = '<section class="container py-5">' +
      '<div class="mb-4"><a href="/drugs" class="btn btn-outline-secondary"><i class="bi bi-arrow-left me-2"></i>返回药物列表</a></div>' +
      '<h2 class="section-title"><i class="bi bi-capsule-pill me-2"></i>' + String(drug.name_cn) + ' <small class="text-muted fs-5">' + String(drug.name_en || '') + '</small></h2>' +
      '<div class="row g-4"><div class="col-lg-8"><div class="card p-4"><h5 class="mb-3">详细信息</h5>' + detailHtml + '</div></div>' +
      '<div class="col-lg-4"><div class="card p-4"><h5 class="mb-3">国际可及性评估</h5>' +
      '<p class="mb-2"><strong>FDA批准：</strong>' + String(drug.fda_status) + '</p>' +
      '<p class="mb-2"><strong>EMA批准：</strong>' + String(drug.ema_status) + '</p>' +
      '<p class="mb-4"><strong>全球可及性：</strong>' + String(drug.global_access) + '</p>' +
      '<div class="alert alert-info-custom"><small><i class="bi bi-info-circle me-1"></i>数据仅供参考，具体用药请遵医嘱。实际批准状态和适应症以最新版药品说明书为准。</small></div></div></div></div>' +
      (relatedDrugs.length > 0 ? '<div class="mt-5"><h4 class="section-title"><i class="bi bi-symmetry-vertical me-2"></i>同类药物</h4>' + relatedHtml + '</div>' : '') +
      '</section>';

    renderLayout(res, String(drug.name_cn), 'drug', bodyHtml);
  } catch (err) {
    console.error('[ERROR] 药物详情失败:', err);
    renderLayout(res, '药物详情', 'drug', '<div class="container py-5"><div class="alert alert-danger">页面加载失败: ' + err.message + '</div></div>');
  }
});

app.get('/genes', (req, res) => {
  try {
    const geneInfo = [
      { gene: 'EGFR', function: '表皮生长因子受体（酪氨酸激酶）', cancers: '非小细胞肺癌、胶质母细胞瘤', biomarker: 'exon 19 del、L858R、T790M、C797S、exon 20 ins', drugs: '奥希替尼、吉非替尼、埃克替尼、达可替尼、舒沃替尼、莫博赛替尼' },
      { gene: 'ALK', function: '间变性淋巴瘤激酶（酪氨酸激酶）', cancers: '非小细胞肺癌、淋巴瘤', biomarker: 'ALK 融合基因（EML4-ALK 等）', drugs: '克唑替尼、塞瑞替尼、阿来替尼、劳拉替尼、恩沙替尼' },
      { gene: 'ROS1', function: 'ROS1 原癌基因（酪氨酸激酶受体）', cancers: '非小细胞肺癌、胆管癌', biomarker: 'ROS1 融合基因', drugs: '克唑替尼、恩曲替尼、塞普替尼' },
      { gene: 'KRAS', function: 'KRAS 原癌基因（GTP酶）', cancers: '非小细胞肺癌、胰腺癌、结直肠癌', biomarker: 'KRAS G12C、G12D、G12V、G13D', drugs: '索托拉西布（Sotorasib）、阿达格拉西布' },
      { gene: 'NTRK1/2/3', function: '神经营养因子受体 TRK A/B/C', cancers: '泛实体瘤（儿童/成人）', biomarker: 'NTRK 基因融合', drugs: '拉罗替尼（Larotrectinib）、恩曲替尼' },
      { gene: 'BRAF', function: 'B-Raf 原癌基因丝氨酸/苏氨酸激酶', cancers: '黑色素瘤、结直肠癌、甲状腺癌', biomarker: 'BRAF V600E、V600K、V600D 突变', drugs: '维莫非尼、达拉非尼、曲美替尼、比美替尼、恩考芬尼' },
      { gene: 'HER2/ERBB2', function: '人表皮生长因子受体 2', cancers: '乳腺癌、胃癌、尿路上皮癌', biomarker: 'HER2 扩增、HER2 IHC 3+、HER2低表达', drugs: '曲妥珠单抗、帕妥珠单抗、德曲妥珠单抗、维迪西妥单抗、吡咯替尼、拉帕替尼' },
      { gene: 'PDCD1/PD-1', function: '程序性死亡受体 1（免疫检查点）', cancers: '泛实体瘤', biomarker: 'PD-L1 TPS/CPS、MSI-H、dMMR、TMB-H', drugs: '帕博利珠单抗、纳武利尤单抗、特瑞普利单抗、信迪利单抗、替雷利珠单抗、卡瑞利珠单抗' },
      { gene: 'CD274/PD-L1', function: '程序性死亡配体 1', cancers: '泛实体瘤', biomarker: 'PD-L1 TPS、PD-L1 CPS、MSI-H', drugs: '阿替利珠单抗、度伐利尤单抗、舒格利单抗、阿维鲁单抗' },
      { gene: 'BRCA1/BRCA2', function: '乳腺癌易感基因（DNA修复）', cancers: '卵巢癌、乳腺癌、胰腺癌、前列腺癌', biomarker: 'BRCA 胚系/体细胞突变、HRD阳性', drugs: '奥拉帕利、尼拉帕利、卢卡帕利、帕米帕利、氟唑帕利' },
      { gene: 'FGFR1/2/3', function: '成纤维细胞生长因子受体', cancers: '尿路上皮癌、胆管癌、子宫内膜癌', biomarker: 'FGFR2 融合、FGFR3 突变/融合', drugs: '厄达替尼、培米替尼、英菲格拉替尼' },
      { gene: 'MET', function: '肝细胞生长因子受体（c-MET）', cancers: '非小细胞肺癌、肾细胞癌', biomarker: 'MET exon 14 跳变、MET 扩增', drugs: '赛沃替尼、卡马替尼、特泊替尼' },
      { gene: 'RET', function: 'RET 酪氨酸激酶受体', cancers: '非小细胞肺癌、甲状腺髓样癌、甲状腺乳头状癌', biomarker: 'RET 融合（KIF5B-RET 等）、RET M918T', drugs: '普拉替尼、塞普替尼、卡博替尼' },
      { gene: 'BTK', function: 'Bruton 酪氨酸激酶', cancers: '淋巴瘤、白血病', biomarker: 'CD20 阳性、BTK 表达', drugs: '伊布替尼、泽布替尼、奥布替尼、替拉鲁替尼' },
      { gene: 'BCL2', function: 'B 细胞淋巴瘤 2（抗凋亡蛋白）', cancers: '慢性淋巴细胞白血病、急性髓系白血病', biomarker: 'BCL-2 过表达、IGHV突变状态', drugs: '维奈克拉（Venetoclax）' },
      { gene: 'CDK4/CDK6', function: '细胞周期蛋白依赖性激酶 4/6', cancers: 'HR阳性/HER2阴性乳腺癌', biomarker: 'RB 阳性、HR阳性、CDK4/6 扩增', drugs: '哌柏西利、阿贝西利、瑞博西利、达尔西利、瑞波西利' },
      { gene: 'AR/雄激素受体', function: '雄激素受体（核受体）', cancers: '前列腺癌', biomarker: 'AR扩增、AR-V7剪接变体', drugs: '恩扎卢胺、阿帕他胺、达罗他胺、比卡鲁胺、阿比特龙' },
      { gene: 'VEGFA/KDR', function: '血管内皮生长因子/受体', cancers: '结直肠癌、非小细胞肺癌、肝癌、肾癌、卵巢癌', biomarker: 'VEGF表达、微血管密度', drugs: '贝伐珠单抗、雷莫西尤单抗、安罗替尼、阿帕替尼、呋喹替尼、索凡替尼' },
      { gene: 'IDH1/IDH2', function: '异柠檬酸脱氢酶（代谢酶）', cancers: '急性髓系白血病、胶质瘤、胆管癌', biomarker: 'IDH1 R132H、IDH2 R140Q、R172K', drugs: '艾伏尼布、恩西地平、Ivosidenib' },
      { gene: 'JAK2', function: 'Janus 激酶 2（信号转导）', cancers: '骨髓纤维化、真性红细胞增多症、原发性血小板增多症', biomarker: 'JAK2 V617F、JAK2外显子12突变', drugs: '鲁索替尼、芦可替尼、杰克替尼、Fedratinib' },
      { gene: 'FLT3', function: 'FMS 样酪氨酸激酶 3', cancers: '急性髓系白血病', biomarker: 'FLT3-ITD（内部串联重复）、FLT3 TKD（D835/I836）', drugs: '吉瑞替尼、奎扎替尼、米哚妥林' },
      { gene: 'KIT', function: '干细胞因子受体 c-KIT', cancers: '胃肠道间质瘤、黑色素瘤', biomarker: 'KIT exon 9/11/13/17 突变', drugs: '伊马替尼、达沙替尼、博舒替尼、瑞派替尼、阿伐替尼' },
      { gene: 'Claudin18.2', function: '紧密连接蛋白 18 剪接变体 2', cancers: '胃癌、胰腺癌', biomarker: 'Claudin18.2 IHC 阳性（40%+肿瘤细胞）', drugs: '佐妥昔单抗（Zolbetuximab）、IMAB362' },
      { gene: 'MSI-H/dMMR', function: '微卫星高度不稳定/错配修复缺陷', cancers: '泛实体瘤（结直肠癌、子宫内膜癌等）', biomarker: 'MSI 检测、dMMR（MLH1/MSH2/MSH6/PMS2）', drugs: '帕博利珠单抗、纳武利尤单抗（泛肿瘤适应症）' },
    ];

    let tableHtml = '<div class="table-responsive"><table class="table table-hover table-bordered">';
    tableHtml += '<thead class="table-dark"><tr><th>基因 / 靶点</th><th>生理功能</th><th>相关肿瘤</th><th>生物标志物</th><th>对应药物</th></tr></thead><tbody>';
    geneInfo.forEach(function(g) {
      tableHtml += '<tr><td><span class="gene-badge">' + g.gene + '</span></td><td>' + g.function + '</td><td>' + g.cancers + '</td><td>' + g.biomarker + '</td><td class="small">' + g.drugs + '</td></tr>';
    });
    tableHtml += '</tbody></table></div>';

    const bodyHtml = '<section class="container py-5">' +
      '<h2 class="section-title"><i class="bi bi-dna me-2"></i>基因靶点与生物标志物参考库</h2>' +
      '<div class="alert alert-info-custom mb-4"><small><i class="bi bi-info-circle me-2"></i>本页面列出 ' + geneInfo.length + ' 个主要抗肿瘤药物靶点的基因信息、相关肿瘤类型及生物标志物检测方法，为精准医疗用药决策提供参考。</small></div>' +
      tableHtml + '</section>';

    renderLayout(res, '基因靶点', 'genes', bodyHtml);
  } catch (err) {
    renderLayout(res, '基因靶点', 'genes', '<div class="container py-5"><div class="alert alert-danger">数据加载失败: ' + err.message + '</div></div>');
  }
});

app.get('/statistics', (req, res) => {
  try {
    const byYear = db ? db.prepare('SELECT approval_year, COUNT(*) as count FROM drugs WHERE approval_year IS NOT NULL GROUP BY approval_year ORDER BY approval_year DESC').all() : [];
    const byType = db ? db.prepare('SELECT drug_type, COUNT(*) as count FROM drugs WHERE drug_type IS NOT NULL GROUP BY drug_type ORDER BY count DESC').all() : [];
    const stats = db ? db.prepare("SELECT SUM(CASE WHEN fda_status LIKE '%FDA%' THEN 1 ELSE 0 END) as fda_count, SUM(CASE WHEN fda_status NOT LIKE '%FDA%' THEN 1 ELSE 0 END) as china_count, COUNT(*) as total FROM drugs").get() : { fda_count: 0, china_count: 0, total: 0 };

    const maxYearCount = byYear.length > 0 ? Math.max.apply(null, byYear.map(x => x.count)) : 1;
    const maxTypeCount = byType.length > 0 ? Math.max.apply(null, byType.map(x => x.count)) : 1;

    let yearChart = '<div class="card p-4 mb-4"><h5 class="mb-3"><i class="bi bi-calendar3 me-2 text-primary"></i>按批准年份分布</h5>';
    byYear.forEach(function(y) {
      const pct = Math.round(y.count / maxYearCount * 100);
      yearChart += '<div class="d-flex align-items-center mb-2"><div class="fw-bold me-3" style="width:80px;">' + y.approval_year + '年</div><div class="flex-grow-1 bg-light rounded" style="height:24px;"><div class="rounded" style="height:100%;width:' + pct + '%;background:linear-gradient(90deg,#1565c0,#0288d1);"></div></div><div class="fw-bold ms-3" style="width:50px;">' + y.count + '</div></div>';
    });
    yearChart += '</div>';

    let typeChart = '<div class="card p-4 mb-4"><h5 class="mb-3"><i class="bi bi-boxes me-2 text-success"></i>按药物类型分布</h5>';
    byType.forEach(function(t) {
      const pct = Math.round(t.count / maxTypeCount * 100);
      const color = t.drug_type.indexOf('抗体') > -1 ? '#2e7d32' : (t.drug_type.indexOf('ADC') > -1 ? '#7b1fa2' : (t.drug_type.indexOf('烷化') > -1 ? '#ef6c00' : '#1565c0'));
      typeChart += '<div class="d-flex align-items-center mb-2"><div class="fw-bold me-3" style="width:160px;font-size:0.9rem;">' + t.drug_type + '</div><div class="flex-grow-1 bg-light rounded" style="height:24px;"><div class="rounded" style="height:100%;width:' + pct + '%;background:linear-gradient(90deg,' + color + ',' + color + 'cc);"></div></div><div class="fw-bold ms-3" style="width:50px;">' + t.count + '</div></div>';
    });
    typeChart += '</div>';

    const fdaPct = stats.total > 0 ? Math.round(stats.fda_count / stats.total * 100) : 0;
    const chinaPct = stats.total > 0 ? Math.round(stats.china_count / stats.total * 100) : 0;
    let fdaChart = '<div class="card p-4 mb-4"><h5 class="mb-3"><i class="bi bi-globe2 me-2 text-info"></i>国际可及性评估（FDA批准状态）</h5>' +
      '<div class="row g-4">' +
      '<div class="col-md-6 text-center"><div class="display-4 fw-bold" style="color:#2e7d32;">' + stats.fda_count + '</div><div class="text-muted">FDA 已批准</div>' +
      '<div class="progress mt-3" style="height:12px;"><div class="progress-bar" style="width:' + fdaPct + '%;background:#2e7d32;"></div></div><div class="small mt-1">' + fdaPct + '%</div></div>' +
      '<div class="col-md-6 text-center"><div class="display-4 fw-bold" style="color:#ef6c00;">' + stats.china_count + '</div><div class="text-muted">未获 FDA 批准（中国/亚洲市场）</div>' +
      '<div class="progress mt-3" style="height:12px;"><div class="progress-bar" style="width:' + chinaPct + '%;background:#ef6c00;"></div></div><div class="small mt-1">' + chinaPct + '%</div></div>' +
      '</div></div>';

    const bodyHtml = '<section class="container py-5">' +
      '<h2 class="section-title"><i class="bi bi-bar-chart-line me-2"></i>药物数据统计分析</h2>' +
      '<div class="row mb-4"><div class="col-md-4"><div class="card p-4 text-center"><div class="display-4 fw-bold text-primary mb-2">' + stats.total + '</div><div class="text-muted">抗肿瘤药物总数</div></div></div>' +
      '<div class="col-md-4"><div class="card p-4 text-center"><div class="display-4 fw-bold mb-2" style="color:#2e7d32;">' + byYear.length + '</div><div class="text-muted">涵盖年份数</div></div></div>' +
      '<div class="col-md-4"><div class="card p-4 text-center"><div class="display-4 fw-bold mb-2" style="color:#7b1fa2;">' + byType.length + '</div><div class="text-muted">药物类型数</div></div></div></div>' +
      yearChart + typeChart + fdaChart +
      '</section>';

    renderLayout(res, '数据统计', 'statistics', bodyHtml);
  } catch (err) {
    renderLayout(res, '数据统计', 'statistics', '<div class="container py-5"><div class="alert alert-danger">数据加载失败: ' + err.message + '</div></div>');
  }
});

app.get('/about', (req, res) => {
  const bodyHtml = '<section class="container py-5">' +
    '<h2 class="section-title"><i class="bi bi-info-circle me-2"></i>关于本系统</h2>' +
    '<div class="row g-4"><div class="col-lg-8"><div class="card p-5">' +
    '<h4 class="mb-4">基因药物知识库 (Gene Drug Knowledge Base)</h4>' +
    '<p class="mb-4">本系统是面向临床医生、药师、药学研究者及患者的抗肿瘤药物基因靶点与生物标志物查询平台，致力于为精准医疗用药决策提供结构化、可追溯的参考信息。</p>' +
    '<h5 class="mt-4 mb-3"><i class="bi bi-target me-2 text-primary"></i>核心功能</h5>' +
    '<ul class="mb-4"><li class="mb-2"><strong>药物库：</strong>收录经过筛选确认的 449 条抗肿瘤药物记录（含小分子靶向药、单克隆抗体、ADC、免疫检查点抑制剂、内分泌治疗、化疗药等）</li>' +
    '<li class="mb-2"><strong>基因靶点：</strong>覆盖 24 个关键肿瘤基因靶点（EGFR、ALK、ROS1、KRAS、NTRK、HER2、PD-1、BTK、PARP、FGFR 等）</li>' +
    '<li class="mb-2"><strong>生物标志物：</strong>提供每个靶点的生物标志物类型、检测方法（PCR、NGS、IHC、FISH）</li>' +
    '<li class="mb-2"><strong>伴随诊断：</strong>标识 FDA/CFDA 推荐的伴随诊断检测方法</li>' +
    '<li class="mb-2"><strong>国际对比：</strong>评估每款药物的 FDA/EMA 批准状态及全球可及性</li></ul>' +
    '<h5 class="mt-4 mb-3"><i class="bi bi-shield-check me-2 text-success"></i>数据来源</h5>' +
    '<ul class="mb-4"><li class="mb-2">NMPA（国家药品监督管理局）及 CDE（药品审评中心）官方批准信息</li>' +
    '<li class="mb-2">FDA、EMA、PMDA 国际药监机构公开数据</li>' +
    '<li class="mb-2">各药企官方发布的药品说明书及临床研究结果</li>' +
    '<li class="mb-2">Pubmed 等医学文献与临床指南</li></ul>' +
    '<div class="alert alert-info-custom mt-4"><small><i class="bi bi-info-circle me-2"></i><strong>免责声明：</strong>本系统提供的药物信息仅供参考，不能替代专业医疗诊断、处方或治疗建议。任何用药决策应以医师的专业判断为准，并以药品生产企业提供的最新版药品说明书为准。</small></div>' +
    '</div></div>' +
    '<div class="col-lg-4"><div class="card p-5">' +
    '<h5 class="mb-3"><i class="bi bi-graph-up-arrow me-2 text-info"></i>系统统计</h5>' +
    '<p class="small mb-2">收录药物：<strong>449 条</strong></p>' +
    '<p class="small mb-2">基因靶点：<strong>24+ 个</strong></p>' +
    '<p class="small mb-2">药物类型：<strong>小分子靶向药、单抗、ADC、免疫检查点抑制剂、内分泌治疗、化疗、免疫调节、细胞疗法</strong></p>' +
    '<p class="small mb-2">数据更新：<strong>实时维护</strong></p>' +
    '<hr><p class="small text-muted">版本 1.0.0</p>' +
    '<p class="small text-muted">Built with Node.js, Express, SQLite</p>' +
    '</div></div></div></section>';

  renderLayout(res, '关于', 'about', bodyHtml);
});

app.get('/health', (req, res) => {
  res.json({ status: 'ok', timestamp: new Date().toISOString(), dbConnected: db !== null, version: '1.0.0' });
});

app.use((req, res) => {
  renderLayout(res, '页面未找到', '404', '<div class="container py-5 text-center"><div class="card p-5 mx-auto" style="max-width:600px;"><div class="display-1 text-muted mb-4">404</div><h3 class="mb-3">页面未找到</h3><p class="text-muted mb-4">您访问的页面不存在或已被移除。</p><a href="/" class="btn btn-primary-custom"><i class="bi bi-house-door me-2"></i>返回首页</a></div></div>');
});

// ================================
// 启动服务器
// ================================
app.listen(PORT, '0.0.0.0', () => {
  console.log('='.repeat(60));
  console.log('  基因药物知识库系统');
  console.log('  Gene Drug Knowledge Base Server');
  console.log('='.repeat(60));
  console.log('  服务器运行地址: http://0.0.0.0:' + PORT);
  console.log('  本地访问地址: http://localhost:' + PORT);
  console.log('  环境: ' + (process.env.NODE_ENV || 'development'));
  console.log('='.repeat(60));
});

module.exports = app;
