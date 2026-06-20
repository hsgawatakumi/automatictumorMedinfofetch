const fs = require('fs');
const path = require('path');
const baseDir = 'e:/TRAE progect/自动化医学信息收集系统';

function removeRecursive(targetPath) {
  if (!fs.existsSync(targetPath)) {
    console.log('[跳过] 不存在:', targetPath);
    return;
  }
  try {
    const stat = fs.statSync(targetPath);
    if (stat.isDirectory()) {
      const files = fs.readdirSync(targetPath);
      files.forEach(f => removeRecursive(path.join(targetPath, f)));
      fs.rmdirSync(targetPath);
      console.log('[删除目录]', targetPath);
    } else {
      fs.unlinkSync(targetPath);
      console.log('[删除文件]', targetPath);
    }
  } catch (err) {
    console.log('[错误]', targetPath, err.message);
  }
}

const targets = [
  path.join(baseDir, 'medical_info_system'),
  path.join(baseDir, 'Procfile'),
  path.join(baseDir, 'railway.json'),
  path.join(baseDir, 'runtime.txt'),
  path.join(baseDir, '.streamlit'),
  path.join(baseDir, 'update_routes.js'),
  path.join(baseDir, 'check_filter.py'),
  path.join(baseDir, 'check_recent_drugs.py'),
  path.join(baseDir, 'complete_anticancer_report.py'),
  path.join(baseDir, 'analyze_db_state.py'),
  path.join(baseDir, 'analyze_approved_drugs.py'),
  path.join(baseDir, 'analyze_filter.py'),
  path.join(baseDir, 'debug_filter.py'),
  path.join(baseDir, 'verify_report.py'),
  path.join(baseDir, 'requirements.txt'),
  path.join(baseDir, 'node_modules'), // 本地开发目录
  path.join(baseDir, 'data'), // 本地数据文件
];

targets.forEach(removeRecursive);

console.log('\n✓ Python 残留文件和目录删除完成！');
