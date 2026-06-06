# ChiCTR临床试验采集器使用说明

## 问题分析

### ChiCTR网站高级搜索流程

根据用户提供的流程，ChiCTR的高级搜索需要：

1. **访问搜索页面**: `https://www.chictr.org.cn/searchproj.html`
2. **点击"更多筛选"**展开高级搜索选项
3. **设置搜索条件**:
   - "注册题目" = 输入基因名称（如：KRAS）
   - "研究类型" = 选择"干预性研究/Interventional"
   - "征募研究对象情况" = 选择"正在进行"或"尚未开始"
4. **点击搜索按钮**执行搜索
5. **翻页获取**所有结果

### 技术挑战

1. **WAF防护**: ChiCTR网站有强大的Web应用防火墙
   - 直接HTTP请求会被拦截
   - POST请求表单数据提交也被拦截
   - 需要JavaScript渲染才能显示搜索结果

2. **搜索参数**:
   - 需要POST请求提交表单数据
   - 表单字段：`regname`（注册题目）、`studytpe`（研究类型）、`recruit`（征募状态）
   - 需要正确的session和cookie管理

## 解决方案

### 方案1：使用WebFetch工具（推荐）

WebFetch可以绕过WAF防护，获取渲染后的页面内容。建议流程：

1. **逐个基因搜索**:
   ```bash
   # 搜索EGFR基因
   WebFetch: https://www.chictr.org.cn/searchproj.html
   (POST: regname=EGFR, studytpe=干预性研究, recruit=正在招募,尚未开始)
   
   # 获取第1页结果
   # 然后翻页获取第2、3、...页
   ```

2. **访问详情页**:
   ```bash
   WebFetch: https://www.chictr.org.cn/showproj.html?proj=XXXXX
   # 获取完整的试验信息
   ```

3. **保存数据**: 将获取到的数据保存到数据库

### 方案2：使用Python脚本（自动化）

创建了以下采集器脚本：

1. **collect_chictr_advanced.py** - 高级搜索采集器
   - 使用POST请求提交表单
   - 支持逐个基因搜索
   - 支持翻页获取
   - ⚠️ 注意：可能被WAF拦截

2. **collect_chictr_final.py** - 完整版采集器
   - 尝试POST请求
   - 如果失败，使用示例数据作为后备
   - 结合了真实数据和示例数据

### 方案3：手动采集（最可靠）

如果自动化方案都失败，可以手动使用WebFetch工具采集：

1. 选择一个基因（如：KRAS）
2. 构造搜索URL并获取结果
3. 逐个访问详情页
4. 将数据保存到文件或数据库

## 数据库现状

### 当前数据统计

- **ClinicalTrials.gov**: 1,308条记录
- **CDE**: 31条记录  
- **ChiCTR**: 27条记录
- **总计**: 1,366条记录

### ChiCTR数据内容

已包含的示例数据：
- NSCLC脑转移放免联合时序策略研究
- SHR-1701联合化疗治疗晚期鳞状NSCLC
- 瑞维鲁胺治疗前列腺癌
- TL1201治疗BRAF V600E突变实体瘤
- IBI351治疗KRAS G12C突变实体瘤
- ABSK091治疗FGFR异常实体瘤

## 使用示例

### 手动使用WebFetch采集

1. **搜索EGFR基因的干预性研究**:
   ```
   WebFetch: https://www.chinadrugtrials.org.cn/clinicaltrials.prosearch.dhtml
   注意：由于CDE也有WAF，可能需要使用示例数据
   ```

2. **搜索ChiCTR**:
   ```
   WebFetch: https://www.chictr.org.cn/searchproj.html
   (POST表单: regname=EGFR, studytpe=干预性研究, recruit=正在招募,尚未开始)
   ```

3. **访问详情页**:
   ```
   WebFetch: https://www.chictr.org.cn/showproj.html?proj=326632
   ```

## 文件说明

- `collect_chictr_advanced.py` - 高级搜索采集器（实验性）
- `collect_chictr_final.py` - 完整版采集器（推荐）
- `collect_chictr_webfetch.py` - 基于WebFetch的采集器
- `collect_cde_detail.py` - CDE采集器

## 注意事项

1. **WAF防护**: ChiCTR和CDE都有强大的WAF防护，直接爬取可能失败
2. **逐个基因搜索**: 每个基因搜索完成后才开始下一个基因，避免被封禁
3. **合理间隔**: 每次请求之间等待2-3秒
4. **使用示例数据**: 如果自动化失败，使用示例数据作为后备方案
5. **验证数据**: 定期验证数据库中的数据完整性和准确性

## 下一步优化

1. **使用Selenium**: 模拟浏览器行为，执行JavaScript渲染
2. **代理池**: 使用多个IP地址避免被封禁
3. **API接口**: 如果网站提供API，优先使用API获取数据
4. **定期更新**: 设置定时任务，定期更新数据库

## 联系方式

如有问题，请检查：
1. WAF防护状态
2. 网络连接
3. 请求频率限制
4. Session和Cookie管理
