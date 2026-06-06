"""
医学信息收集系统 - Streamlit Web界面
主入口文件
"""

import streamlit as st
import os
import sys
import logging
from datetime import datetime
import pandas as pd

# 添加项目路径（确保能正确导入src模块）
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(os.path.dirname(current_dir))
sys.path.insert(0, project_root)

from src.database import DatabaseManager, init_database
from src.utils.config_manager import ConfigManager, create_config_manager
from src.utils.translator import TranslationService, create_translation_service
from src.utils.http_client import RequestManager
from src.collectors.fda_collector import FDADrugCollector, create_fda_collector
from src.collectors.pubmed_collector import PubMedCollector
from src.collectors.clinical_trials_collector import ClinicalTrialsCollector
from src.collectors.nmpa_cde_collector import NMPACDECollector, create_nmpa_cde_collector
from src.collectors.conference_collector import ConferenceAbstractCollector, create_conference_collector

# 页面配置
st.set_page_config(
    page_title="医学信息收集系统",
    page_icon="🏥",
    layout="wide",
    initial_sidebar_state="expanded"
)

# 自定义CSS样式
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        color: #1f77b4;
        text-align: center;
        margin-bottom: 2rem;
    }
    .sub-header {
        font-size: 1.5rem;
        color: #2c3e50;
        margin-top: 1rem;
    }
    .metric-card {
        background-color: #f8f9fa;
        border-radius: 10px;
        padding: 1rem;
        margin: 0.5rem;
    }
    .status-running {
        color: #28a745;
        font-weight: bold;
    }
    .status-stopped {
        color: #dc3545;
        font-weight: bold;
    }
    .stDataFrame {
        font-size: 0.9rem;
    }
</style>
""", unsafe_allow_html=True)


class MedicalInfoSystem:
    """医学信息收集系统主类"""
    
    def __init__(self):
        """初始化系统"""
        # 使用绝对路径：app.py 在 src/web/ 下，需要回退两级到项目根目录
        base_path = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        self.config_path = os.path.join(base_path, "config/config.yaml")
        self.db_path = os.path.join(base_path, "data/medical_info.db")
        
        # 初始化配置管理器
        self.config_manager = self._init_config_manager()
        
        # 初始化数据库
        self.db_manager = self._init_database()
        
        # 初始化翻译服务
        self.translation_service = self._init_translation()
        
        # 初始化请求管理器
        self.request_manager = RequestManager(self.config_manager.get_proxy_config())
        
        # 初始化采集器
        self.collectors = self._init_collectors()
        
        # 系统状态
        self.scheduler_running = False
        # 记录各模块运行状态
        self.run_status = {}
    
    def _init_config_manager(self) -> ConfigManager:
        """初始化配置管理器"""
        return create_config_manager(self.config_path)
    
    def _init_database(self) -> DatabaseManager:
        """初始化数据库"""
        return init_database(self.db_path)
    
    def _init_translation(self) -> TranslationService:
        """初始化翻译服务"""
        translation_config = self.config_manager.get_translation_config()
        return create_translation_service(translation_config)
    
    def _init_collectors(self) -> dict:
        """初始化各采集模块"""
        collectors = {}
        try:
            collectors['fda_approved'] = create_fda_collector(
                self.db_manager, self.config_manager, self.translation_service
            )
        except Exception as e:
            logging.error(f"FDA采集器初始化失败: {e}")
        
        try:
            collectors['academic_papers'] = PubMedCollector(
                self.db_manager, self.config_manager, self.translation_service
            )
        except Exception as e:
            logging.error(f"PubMed采集器初始化失败: {e}")
        
        try:
            collectors['clinical_trials'] = ClinicalTrialsCollector(
                self.db_manager, self.config_manager, self.translation_service
            )
        except Exception as e:
            logging.error(f"临床试验采集器初始化失败: {e}")
        
        try:
            collectors['nmpa_cde'] = create_nmpa_cde_collector(
                self.db_manager, self.config_manager, self.translation_service
            )
        except Exception as e:
            logging.error(f"NMPA/CDE采集器初始化失败: {e}")
            
        try:
            collectors['conference_abstracts'] = create_conference_collector(
                self.db_manager, self.config_manager, self.translation_service
            )
        except Exception as e:
            logging.error(f"会议摘要采集器初始化失败: {e}")
        
        return collectors
    
    def run_collector(self, module_key: str) -> dict:
        """
        手动运行指定采集模块
        
        Args:
            module_key: 模块标识（如 fda_approved, academic_papers 等）
            
        Returns:
            运行结果字典
        """
        start_time = datetime.now()
        result = {
            'success': False,
            'module': module_key,
            'start_time': str(start_time),
            'message': '',
            'records_processed': 0,
            'records_added': 0,
            'duration': 0,
        }
        
        collector = self.collectors.get(module_key)
        
        # 确定实际使用的采集器和模式
        actual_collector = None
        run_mode = None
        
        if module_key in ['fda_nda']:
            actual_collector = self.collectors.get('fda_approved')
            run_mode = 'nda'
        elif module_key in ['nmpa_approved']:
            actual_collector = self.collectors.get('nmpa_cde')
            run_mode = 'nmpa'
        elif module_key in ['cde_special']:
            actual_collector = self.collectors.get('nmpa_cde')
            run_mode = 'cde'
        else:
            actual_collector = collector
            run_mode = None
        
        if not actual_collector:
            result['message'] = f'模块 {module_key} 的采集器未初始化'
            return result
        
        try:
            logging.info(f"手动启动采集模块: {module_key}")
            
            # 根据模块选择正确的运行模式
            if run_mode:
                run_result = actual_collector.run(mode=run_mode)
            else:
                run_result = actual_collector.run()
            
            end_time = datetime.now()
            duration = (end_time - start_time).total_seconds()
            
            result['success'] = True
            result['records_processed'] = run_result.get('records_processed', 0)
            result['records_added'] = run_result.get('records_added', run_result.get('records_inserted', 0))
            result['duration'] = round(duration, 1)
            result['message'] = run_result.get('message', '采集完成')
            
            # 记录到系统日志
            self.db_manager.log_system_action({
                'module_name': module_key,
                'action': 'manual_run',
                'status': 'success',
                'message': result['message'],
                'records_processed': result['records_processed'],
                'records_added': result['records_added'],
                'start_time': str(start_time),
                'end_time': str(end_time),
                'duration_seconds': duration
            })
            
        except Exception as e:
            end_time = datetime.now()
            duration = (end_time - start_time).total_seconds()
            result['message'] = f'采集失败: {str(e)}'
            result['duration'] = round(duration, 1)
            
            logging.error(f"采集模块 {module_key} 运行失败: {e}")
            
            # 记录失败日志
            self.db_manager.log_system_action({
                'module_name': module_key,
                'action': 'manual_run',
                'status': 'error',
                'message': str(e),
                'records_processed': 0,
                'start_time': str(start_time),
                'end_time': str(end_time),
                'duration_seconds': duration
            })
        
        return result
    
    def get_system_stats(self) -> dict:
        """获取系统统计信息"""
        stats = {
            'approved_drugs': self.db_manager.get_record_count('approved_drugs'),
            'nda_drugs': self.db_manager.get_record_count('nda_drugs'),
            'cde_special': self.db_manager.get_record_count('cde_special_drugs'),
            'academic_papers': self.db_manager.get_record_count('academic_papers'),
            'conference_abstracts': self.db_manager.get_record_count('conference_abstracts'),
            'clinical_trials': self.db_manager.get_record_count('clinical_trials'),
            'target_genes': len(self.config_manager.get_target_genes()),
            'tumor_types': len(self.config_manager.get_tumor_types()),
        }
        return stats
    
    def get_last_run_info(self) -> dict:
        """获取最近运行信息"""
        modules = ['fda_approved', 'fda_nda', 'nmpa_approved', 'cde_special', 
                   'academic_papers', 'clinical_trials']
        
        last_runs = {}
        for module in modules:
            last_time = self.db_manager.get_last_collection_time(module)
            last_runs[module] = last_time or '未运行'
        
        return last_runs


# 创建系统实例（不使用缓存以确保配置实时加载）
def get_system() -> MedicalInfoSystem:
    """获取系统实例"""
    return MedicalInfoSystem()


system = get_system()


def main():
    """主函数"""
    # 侧边栏导航
    st.sidebar.markdown("## 🏥 医学信息收集系统")
    st.sidebar.markdown("---")
    
    page = st.sidebar.radio(
        "导航菜单",
        ["📊 系统概览", "⚙️ 配置管理", "📋 数据查看", "📤 数据导出", "🔄 运行状态", "📖 使用说明"],
        index=0
    )
    
    st.sidebar.markdown("---")
    
    # 显示系统状态摘要
    stats = system.get_system_stats()
    st.sidebar.markdown("### 数据统计")
    st.sidebar.metric("已批准药物", stats['approved_drugs'])
    st.sidebar.metric("学术文献", stats['academic_papers'])
    st.sidebar.metric("临床试验", stats['clinical_trials'])
    
    # 根据选择显示不同页面
    if page == "📊 系统概览":
        show_overview_page()
    elif page == "⚙️ 配置管理":
        show_config_page()
    elif page == "📋 数据查看":
        show_data_page()
    elif page == "📤 数据导出":
        show_export_page()
    elif page == "🔄 运行状态":
        show_status_page()
    elif page == "📖 使用说明":
        show_help_page()


def show_overview_page():
    """显示系统概览页面"""
    st.markdown("<h1 class='main-header'>🏥 医学信息收集系统</h1>", unsafe_allow_html=True)
    
    st.markdown("""
    ### 系统简介
    本系统用于实时监控和整合全球抗肿瘤药物的监管审批信息、学术研究进展和临床试验动态。
    系统采用模块化设计，支持定时自动采集、数据标准化处理、中英文双语展示和本地持久化存储。
    """)
    
    # 系统统计卡片
    st.markdown("<h2 class='sub-header'>📊 数据统计</h2>", unsafe_allow_html=True)
    
    stats = system.get_system_stats()
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("已批准药物", stats['approved_drugs'], delta=None)
        st.metric("NDA申请药物", stats['nda_drugs'], delta=None)
    
    with col2:
        st.metric("CDE特殊品种", stats['cde_special'], delta=None)
        st.metric("学术文献", stats['academic_papers'], delta=None)
    
    with col3:
        st.metric("会议摘要", stats['conference_abstracts'], delta=None)
        st.metric("临床试验", stats['clinical_trials'], delta=None)
    
    with col4:
        st.metric("目标基因数", stats['target_genes'], delta=None)
        st.metric("肿瘤类型数", stats['tumor_types'], delta=None)
    
    st.markdown("---")
    
    # 最近运行状态
    st.markdown("<h2 class='sub-header'>🔄 最近运行状态</h2>", unsafe_allow_html=True)
    
    last_runs = system.get_last_run_info()
    
    run_data = {
        '模块': ['FDA已批准药物', 'FDA NDA申请', 'NMPA已批准药物', 'CDE特殊品种', 
                 '学术文献检索', '临床试验采集'],
        '最后运行时间': [last_runs['fda_approved'], last_runs['fda_nda'], 
                        last_runs['nmpa_approved'], last_runs['cde_special'],
                        last_runs['academic_papers'], last_runs['clinical_trials']],
        '定时配置': ['每日凌晨2:00', '每日凌晨3:00', '每日凌晨4:00', '每日凌晨5:00',
                    '每周一凌晨1:00', '每周二凌晨1:00']
    }
    
    st.dataframe(pd.DataFrame(run_data), use_container_width=True)
    
    st.markdown("---")
    
    # 系统配置摘要
    st.markdown("<h2 class='sub-header'>⚙️ 系统配置摘要</h2>", unsafe_allow_html=True)
    
    config_info = system.config_manager.get_system_info()
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.info(f"**翻译服务**: {config_info['translation_provider']}")
        st.info(f"**百度翻译**: {'已配置' if config_info['baidu_configured'] else '未配置'}")
        st.info(f"**代理服务**: {'已启用' if config_info['proxy_enabled'] else '未启用'}")
    
    with col2:
        st.info(f"**数据库路径**: {config_info['database_path']}")
        st.info(f"**定时任务数**: {len(config_info['scheduler_tasks'])}")
    
    # 快速操作按钮
    st.markdown("<h2 class='sub-header'>⚡ 快速操作</h2>", unsafe_allow_html=True)
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        if st.button("🔄 刷新数据统计", use_container_width=True):
            st.rerun()
    
    with col2:
        if st.button("📤 导出今日数据", use_container_width=True):
            st.info("请前往'数据导出'页面进行导出操作")
    
    with col3:
        if st.button("📖 查看使用说明", use_container_width=True):
            st.info("请前往'使用说明'页面查看详细文档")


def show_config_page():
    """显示配置管理页面"""
    st.markdown("<h1 class='main-header'>⚙️ 配置管理</h1>", unsafe_allow_html=True)
    
    # 创建标签页
    tab1, tab2, tab3, tab4, tab5 = st.tabs([
        "翻译服务", "基因列表", "肿瘤类型", "定时任务", "代理设置"
    ])
    
    # 翻译服务配置
    with tab1:
        st.markdown("### 翻译服务配置")
        
        translation_config = system.config_manager.get_translation_config()
        baidu_config = translation_config.get('baidu', {})
        
        # 翻译服务选择
        provider = st.selectbox(
            "翻译服务提供商",
            ["auto", "baidu", "helsinki"],
            index=0 if translation_config.get('provider') == 'auto' else 
                  1 if translation_config.get('provider') == 'baidu' else 2,
            help="auto: 优先百度翻译，失败则降级到开源模型"
        )
        
        if provider != translation_config.get('provider'):
            system.config_manager.set_translation_provider(provider)
            st.success(f"翻译服务已切换为: {provider}")
        
        # 百度翻译配置
        st.markdown("#### 百度翻译API配置")
        st.info("百度翻译API密钥已预配置，您只需填写APP ID即可使用")
        
        current_app_id = baidu_config.get('app_id', '')
        new_app_id = st.text_input(
            "百度翻译APP ID",
            value=current_app_id,
            placeholder="请输入您的百度翻译APP ID",
            help="在百度翻译开放平台申请: https://fanyi-api.baidu.com/"
        )
        
        if new_app_id != current_app_id and new_app_id:
            system.config_manager.set_baidu_app_id(new_app_id)
            system.translation_service.set_baidu_app_id(new_app_id)
            st.success("百度翻译APP ID已更新")
        
        # 百度翻译申请指南
        st.markdown("#### 百度翻译API申请指南")
        st.markdown("""
        1. 访问 [百度翻译开放平台](https://fanyi-api.baidu.com/)
        2. 注册账号并登录
        3. 进入"管理控制台" → "开发者信息"
        4. 创建应用，获取APP ID和密钥
        5. 标准版每月免费额度：200万字符
        """)
        
        # 翻译统计
        st.markdown("#### 翻译使用统计")
        trans_stats = system.translation_service.get_stats()
        
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("今日翻译字符", trans_stats['today'].get('baidu', 0) + trans_stats['today'].get('helsinki', 0))
        with col2:
            st.metric("今日请求次数", trans_stats['today'].get('requests', 0))
        with col3:
            st.metric("当前服务", trans_stats['current_provider'])
        
        # Helsinki模型状态
        st.markdown("#### 开源翻译模型状态")
        helsinki_available = trans_stats.get('helsinki_available', False)
        if helsinki_available:
            st.success("✅ Helsinki-NLP模型已加载可用")
        else:
            st.warning("⚠️ Helsinki-NLP模型未加载（首次使用时会自动下载）")
    
    # 基因列表配置
    with tab2:
        st.markdown("### 目标基因列表管理")
        
        genes = system.config_manager.get_target_genes()
        
        st.info(f"当前已配置 {len(genes)} 个肿瘤靶向基因")
        
        # 显示基因列表
        st.markdown("#### 当前基因列表")
        
        # 搜索和筛选
        search_gene = st.text_input("搜索基因", placeholder="输入基因名称搜索...")
        
        filtered_genes = genes
        if search_gene:
            filtered_genes = [g for g in genes if search_gene.upper() in g.upper()]
        
        # 分页显示
        page_size = 50
        total_pages = max(1, (len(filtered_genes) - 1) // page_size + 1)
        
        current_page = st.number_input("页码", min_value=1, max_value=total_pages, value=1)
        
        start_idx = (current_page - 1) * page_size
        end_idx = start_idx + page_size
        
        if filtered_genes:
            st.dataframe(
                pd.DataFrame({'基因名称': filtered_genes[start_idx:end_idx]}),
                use_container_width=True
            )
            st.caption(f"显示 {start_idx + 1}-{min(end_idx, len(filtered_genes))} / 共 {len(filtered_genes)} 个基因")
        else:
            st.info("未找到匹配的基因")
        
        # 添加/删除基因
        st.markdown("#### 基因操作")
        
        col1, col2 = st.columns(2)
        
        with col1:
            new_gene = st.text_input("添加新基因", placeholder="输入基因名称...")
            if st.button("添加基因") and new_gene:
                if new_gene.upper() not in genes:
                    system.config_manager.add_target_gene(new_gene.upper())
                    st.success(f"基因 {new_gene.upper()} 已添加")
                    st.rerun()
                else:
                    st.warning(f"基因 {new_gene.upper()} 已存在")
        
        with col2:
            remove_gene = st.selectbox("删除基因", options=genes)
            if st.button("删除基因") and remove_gene:
                system.config_manager.remove_target_gene(remove_gene)
                st.success(f"基因 {remove_gene} 已删除")
                st.rerun()
    
    # 肿瘤类型配置
    with tab3:
        st.markdown("### 肿瘤类型列表管理")
        
        tumor_types = system.config_manager.get_tumor_types()
        
        st.info(f"当前已配置 {len(tumor_types)} 种肿瘤类型（中英文对照）")
        
        # 显示肿瘤类型列表
        st.markdown("#### 当前肿瘤类型列表")
        
        # 搜索
        search_tumor = st.text_input("搜索肿瘤类型", placeholder="输入中文名称或英文名称...")
        
        filtered_tumors = tumor_types
        if search_tumor:
            filtered_tumors = [
                t for t in tumor_types 
                if search_tumor in t.get('cn', '') or search_tumor.lower() in t.get('en', '').lower()
            ]
        
        # 显示表格
        tumor_data = []
        for t in filtered_tumors:
            aliases = ', '.join(t.get('aliases_en', [])) if t.get('aliases_en') else ''
            tumor_data.append({
                '中文名称': t.get('cn', ''),
                '英文名称': t.get('en', ''),
                '英文别名': aliases
            })
        
        st.dataframe(pd.DataFrame(tumor_data), use_container_width=True)
        
        # 添加肿瘤类型
        st.markdown("#### 添加肿瘤类型")
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            new_cn = st.text_input("中文名称", placeholder="如：肺癌")
        
        with col2:
            new_en = st.text_input("英文名称", placeholder="如：Lung cancer")
        
        with col3:
            new_aliases = st.text_input("英文别名（逗号分隔）", placeholder="如：NSCLC, SCLC")
        
        if st.button("添加肿瘤类型"):
            if new_cn and new_en:
                aliases_list = [a.strip() for a in new_aliases.split(',') if a.strip()]
                system.config_manager.add_tumor_type(new_cn, new_en, aliases_list)
                st.success(f"肿瘤类型 '{new_cn}' 已添加")
                st.rerun()
            else:
                st.warning("请填写中文名称和英文名称")
    
    # 定时任务配置
    with tab4:
        st.markdown("### 定时任务配置")
        
        scheduler_config = system.config_manager.get_scheduler_config()
        
        st.info("所有时间均为北京时间（Asia/Shanghai）")
        
        tasks = [
            ('fda_approved', 'FDA已批准药物采集', '每日凌晨2:00'),
            ('fda_nda', 'FDA NDA申请采集', '每日凌晨3:00'),
            ('nmpa_approved', 'NMPA已批准药物采集', '每日凌晨4:00'),
            ('cde_special', 'CDE特殊审评品种采集', '每日凌晨5:00'),
            ('academic_papers', '学术文献检索', '每周一凌晨1:00'),
            ('clinical_trials', '临床试验采集', '每周二凌晨1:00'),
        ]
        
        for task_key, task_name, default_time in tasks:
            current_cron = scheduler_config.get(task_key, '')
            
            st.markdown(f"#### {task_name}")
            
            col1, col2 = st.columns(2)
            
            with col1:
                st.text(f"当前配置: {current_cron}")
                st.caption(f"默认: {default_time}")
            
            with col2:
                # 简化的时间选择
                hour = st.selectbox(
                    "小时", 
                    range(0, 24), 
                    index=int(current_cron.split()[1]) if current_cron else 2,
                    key=f"hour_{task_key}"
                )
                
                if st.button(f"更新 {task_name}", key=f"btn_{task_key}"):
                    # 构建cron表达式
                    if '每周' in default_time:
                        day_of_week = 1 if task_key == 'academic_papers' else 2
                        new_cron = f"0 {hour} * * {day_of_week}"
                    else:
                        new_cron = f"0 {hour} * * *"
                    
                    system.config_manager.set_scheduler_time(task_key, new_cron)
                    st.success(f"定时任务已更新为: {new_cron}")
    
    # 代理设置
    with tab5:
        st.markdown("### 代理设置")
        
        proxy_config = system.config_manager.get_proxy_config()
        
        use_proxy = st.checkbox(
            "启用代理", 
            value=proxy_config.get('use_proxy', False),
            help="启用代理可以避免被目标网站封禁IP"
        )
        
        if use_proxy != proxy_config.get('use_proxy'):
            system.config_manager.set('proxy.use_proxy', use_proxy)
            st.success(f"代理设置已更新")
        
        st.markdown("#### 代理列表配置")
        
        current_proxies = proxy_config.get('proxy_list', [])
        
        st.info("当前使用内置免费代理池。如需更稳定的代理，请配置自己的代理列表。")
        
        # 代理输入
        proxy_input = st.text_area(
            "代理列表（每行一个）",
            placeholder="http://proxy1:port\nhttp://proxy2:port\n...",
            help="格式: http://地址:端口 或 socks5://地址:端口"
        )
        
        if st.button("更新代理列表"):
            if proxy_input:
                new_proxies = [p.strip() for p in proxy_input.split('\n') if p.strip()]
                system.config_manager.set_proxy_list(new_proxies)
                st.success(f"已添加 {len(new_proxies)} 个代理")
            else:
                system.config_manager.set_proxy_list([])
                st.success("已清空代理列表，将使用内置代理池")
        
        # 请求间隔设置
        st.markdown("#### 请求间隔设置")
        
        col1, col2 = st.columns(2)
        
        with col1:
            delay_min = st.number_input(
                "最小间隔（秒）",
                min_value=1, max_value=10,
                value=proxy_config.get('request_delay_min', 3)
            )
        
        with col2:
            delay_max = st.number_input(
                "最大间隔（秒）",
                min_value=2, max_value=15,
                value=proxy_config.get('request_delay_max', 5)
            )
        
        if st.button("更新请求间隔"):
            system.config_manager.set('proxy.request_delay_min', delay_min)
            system.config_manager.set('proxy.request_delay_max', delay_max)
            st.success(f"请求间隔已更新: {delay_min}-{delay_max}秒")


def show_data_page():
    """显示数据查看页面"""
    st.markdown("<h1 class='main-header'>📋 数据查看</h1>", unsafe_allow_html=True)
    
    # 创建标签页
    tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs([
        "已批准药物", "NDA申请", "CDE特殊品种", "学术文献", "会议摘要", "临床试验"
    ])
    
    # 已批准药物
    with tab1:
        st.markdown("### 已批准药物列表")
        
        # 筛选条件
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            agency_filter = st.selectbox(
                "监管机构",
                ["全部", "FDA", "NMPA"],
                key="agency_filter"
            )
        
        with col2:
            date_filter = st.date_input(
                "批准日期范围（起始）",
                value=None,
                key="date_start"
            )
        
        with col3:
            date_end = st.date_input(
                "批准日期范围（结束）",
                value=None,
                key="date_end"
            )
        
        with col4:
            search_keyword = st.text_input(
                "关键词搜索",
                placeholder="药品名称或适应症...",
                key="drug_search"
            )
        
        # 构建查询
        conditions = []
        params = []
        
        if agency_filter != "全部":
            conditions.append("regulatory_agency = ?")
            params.append(agency_filter)
        
        if date_filter:
            conditions.append("approval_date >= ?")
            params.append(str(date_filter))
        
        if date_end:
            conditions.append("approval_date <= ?")
            params.append(str(date_end))
        
        if search_keyword:
            conditions.append("(drug_name_en LIKE ? OR drug_name_cn LIKE ? OR indication LIKE ?)")
            keyword_param = f"%{search_keyword}%"
            params.extend([keyword_param, keyword_param, keyword_param])
        
        where_clause = " AND ".join(conditions) if conditions else ""
        
        # 查询数据
        where_part = f"WHERE {where_clause}" if where_clause else ""
        query = f"SELECT * FROM approved_drugs {where_part} ORDER BY approval_date DESC LIMIT 100"
        
        try:
            drugs = system.db_manager.execute_query(query, tuple(params) if params else None)
            
            if drugs:
                # 显示数据
                display_data = []
                for drug in drugs:
                    display_data.append({
                        '监管机构': drug.get('regulatory_agency', ''),
                        '药品名称(英文)': drug.get('drug_name_en', ''),
                        '药品名称(中文)': drug.get('drug_name_cn', ''),
                        '通用名(英文)': drug.get('generic_name_en', ''),
                        '通用名(中文)': drug.get('generic_name_cn', ''),
                        '批准日期': drug.get('approval_date', ''),
                        '适应症': drug.get('indication', ''),
                        '作用机制': drug.get('mechanism_of_action', ''),
                        '申请人': drug.get('applicant', ''),
                    })
                
                st.dataframe(pd.DataFrame(display_data), use_container_width=True)
                st.caption(f"显示 {len(drugs)} 条记录")
                
                # 详情查看
                if st.checkbox("查看详细信息"):
                    selected_id = st.selectbox(
                        "选择记录",
                        options=[d.get('id') for d in drugs],
                        format_func=lambda x: f"ID: {x}"
                    )
                    
                    if selected_id:
                        detail = system.db_manager.execute_query(
                            "SELECT * FROM approved_drugs WHERE id = ?",
                            (selected_id,)
                        )
                        if detail:
                            st.json(detail[0])
            else:
                st.info("暂无数据，请先运行数据采集任务")
        
        except Exception as e:
            st.error(f"查询失败: {e}")
    
    # NDA申请药物
    with tab2:
        st.markdown("### FDA NDA申请药物列表")
        
        nda_drugs = system.db_manager.execute_query(
            "SELECT * FROM nda_drugs ORDER BY nda_submission_date DESC LIMIT 100"
        )
        
        if nda_drugs:
            display_data = []
            for drug in nda_drugs:
                display_data.append({
                    'NDA编号': drug.get('nda_number', ''),
                    '状态': drug.get('nda_status', ''),
                    '提交日期': drug.get('nda_submission_date', ''),
                    '药品名称(英文)': drug.get('drug_name_en', ''),
                    '药品名称(中文)': drug.get('drug_name_cn', ''),
                    '申请人': drug.get('applicant', ''),
                    '适应症': drug.get('indication', ''),
                })
            
            st.dataframe(pd.DataFrame(display_data), use_container_width=True)
            st.caption(f"显示 {len(nda_drugs)} 条记录")
        else:
            st.info("暂无NDA申请数据")
    
    # CDE特殊品种
    with tab3:
        st.markdown("### CDE优先审评/突破性治疗品种")
        
        cde_drugs = system.db_manager.execute_query(
            "SELECT * FROM cde_special_drugs ORDER BY application_date DESC LIMIT 100"
        )
        
        if cde_drugs:
            display_data = []
            for drug in cde_drugs:
                display_data.append({
                    '项目类型': drug.get('drug_type', ''),
                    '药品名称(中文)': drug.get('drug_name', ''),
                    '药品名称(英文)': drug.get('drug_name_en', ''),
                    '受理号': drug.get('acceptance_number', ''),
                    '申请人': drug.get('applicant', ''),
                    '申请日期': drug.get('application_date', ''),
                    '批准日期': drug.get('approval_date', ''),
                    '状态': drug.get('status', ''),
                    '适应症': drug.get('indication', ''),
                    '分子靶点': drug.get('molecular_target', ''),
                    '基因标记': drug.get('gene_marker', ''),
                    '详细描述': drug.get('description', ''),
                })
            
            st.dataframe(pd.DataFrame(display_data), use_container_width=True)
            st.caption(f"显示 {len(cde_drugs)} 条记录")
        else:
            st.info("暂无CDE特殊品种数据")
    
    # 学术文献
    with tab4:
        st.markdown("### 学术文献列表")
        
        # 筛选
        col1, col2, col3 = st.columns(3)
        
        with col1:
            journal_filter = st.selectbox(
                "期刊",
                ["全部", "NEJM", "Lancet", "Nature Medicine", "Cancer Discovery", 
                 "JCO", "Annals of Oncology", "CCR"],
                key="journal_filter"
            )
        
        with col2:
            gene_filter = st.text_input("基因筛选", placeholder="如：EGFR, KRAS...")
        
        with col3:
            tumor_filter = st.text_input("肿瘤类型筛选", placeholder="如：肺癌...")
        
        # 查询
        conditions = []
        params = []
        
        if journal_filter != "全部":
            conditions.append("journal_name LIKE ?")
            params.append(f"%{journal_filter}%")
        
        if gene_filter:
            conditions.append("target_gene LIKE ?")
            params.append(f"%{gene_filter}%")
        
        if tumor_filter:
            conditions.append("(tumor_type LIKE ? OR tumor_type_cn LIKE ?)")
            params.extend([f"%{tumor_filter}%", f"%{tumor_filter}%"])
        
        where_clause = " AND ".join(conditions) if conditions else ""
        
        where_part = f"WHERE {where_clause}" if where_clause else ""
        query = f"SELECT * FROM academic_papers {where_part} ORDER BY publication_date DESC LIMIT 100"
        
        papers = system.db_manager.execute_query(query, tuple(params) if params else None)
        
        if papers:
            display_data = []
            for paper in papers:
                display_data.append({
                    '标题(英文)': paper.get('title_en', '')[:50] + '...' if len(paper.get('title_en', '')) > 50 else paper.get('title_en', ''),
                    '标题(中文)': paper.get('title_cn', '')[:50] + '...' if len(paper.get('title_cn', '')) > 50 else paper.get('title_cn', ''),
                    '期刊': paper.get('journal_name', ''),
                    '发表日期': paper.get('publication_date', ''),
                    '目标基因': paper.get('target_gene', ''),
                    '肿瘤类型': paper.get('tumor_type_cn', '') or paper.get('tumor_type', ''),
                    'DOI': paper.get('doi', ''),
                })
            
            st.dataframe(pd.DataFrame(display_data), use_container_width=True)
            st.caption(f"显示 {len(papers)} 条记录")
        else:
            st.info("暂无学术文献数据")
    
    # 会议摘要
    with tab5:
        st.markdown("### 学术会议摘要列表")
        
        abstracts = system.db_manager.execute_query(
            "SELECT * FROM conference_abstracts ORDER BY conference_year DESC, abstract_number LIMIT 100"
        )
        
        if abstracts:
            display_data = []
            for abstract in abstracts:
                display_data.append({
                    '会议': abstract.get('conference_name', ''),
                    '年份': abstract.get('conference_year', ''),
                    '摘要编号': abstract.get('abstract_number', ''),
                    '标题(英文)': abstract.get('title_en', '')[:50] + '...' if len(abstract.get('title_en', '')) > 50 else abstract.get('title_en', ''),
                    '报告类型': abstract.get('presentation_type', ''),
                    '肿瘤类型': abstract.get('tumor_type_cn', '') or abstract.get('tumor_type', ''),
                    '目标基因': abstract.get('target_gene', ''),
                })
            
            st.dataframe(pd.DataFrame(display_data), use_container_width=True)
            st.caption(f"显示 {len(abstracts)} 条记录")
        else:
            st.info("暂无会议摘要数据")
    
    # 临床试验
    with tab6:
        st.markdown("### 临床试验列表")
        
        # 筛选
        col1, col2, col3 = st.columns(3)
        
        with col1:
            platform_filter = st.selectbox(
                "平台",
                ["全部", "ClinicalTrials.gov", "CDE", "ChiCTR"],
                key="platform_filter"
            )
        
        with col2:
            status_filter = st.selectbox(
                "试验状态",
                ["全部", "Recruiting", "Active, not recruiting", "Completed", "Terminated"],
                key="status_filter"
            )
        
        with col3:
            trial_search = st.text_input("关键词", placeholder="试验ID或药物名称...")
        
        # 查询
        conditions = []
        params = []
        
        if platform_filter != "全部":
            conditions.append("platform = ?")
            params.append(platform_filter)
        
        if status_filter != "全部":
            conditions.append("trial_status = ?")
            params.append(status_filter)
        
        if trial_search:
            conditions.append("(trial_id LIKE ? OR intervention_drug LIKE ? OR study_title_en LIKE ?)")
            keyword_param = f"%{trial_search}%"
            params.extend([keyword_param, keyword_param, keyword_param])
        
        where_clause = " AND ".join(conditions) if conditions else ""
        
        where_part = f"WHERE {where_clause}" if where_clause else ""
        query = f"SELECT * FROM clinical_trials {where_part} ORDER BY last_update_posted DESC LIMIT 100"
        
        trials = system.db_manager.execute_query(query, tuple(params) if params else None)
        
        if trials:
            display_data = []
            for trial in trials:
                display_data.append({
                    '平台': trial.get('platform', ''),
                    '试验ID': trial.get('trial_id', ''),
                    '状态': trial.get('trial_status', ''),
                    '标题(英文)': trial.get('study_title_en', '')[:50] + '...' if len(trial.get('study_title_en', '')) > 50 else trial.get('study_title_en', ''),
                    '分期': trial.get('phase', ''),
                    '肿瘤类型': trial.get('tumor_type_cn', '') or trial.get('tumor_type', ''),
                    '基因标记': trial.get('gene_marker', ''),
                    '干预药物': trial.get('intervention_drug', ''),
                    '申办方': trial.get('sponsor', ''),
                })
            
            st.dataframe(pd.DataFrame(display_data), use_container_width=True)
            st.caption(f"显示 {len(trials)} 条记录")
        else:
            st.info("暂无临床试验数据")


def show_export_page():
    """显示数据导出页面"""
    st.markdown("<h1 class='main-header'>📤 数据导出</h1>", unsafe_allow_html=True)
    
    st.markdown("""
    ### 导出说明
    选择数据类型、时间范围和筛选条件，然后点击导出按钮生成文件。
    导出文件将保存到云端存储，可一键下载。
    """)
    
    # 数据类型选择
    data_type = st.selectbox(
        "数据类型",
        ["已批准药物", "NDA申请药物", "CDE特殊品种", "学术文献", "会议摘要", "临床试验"]
    )
    
    # 时间范围
    col1, col2 = st.columns(2)
    
    with col1:
        start_date = st.date_input("起始日期", value=None)
    
    with col2:
        end_date = st.date_input("结束日期", value=None)
    
    # 筛选条件
    col1, col2 = st.columns(2)
    
    with col1:
        tumor_type_filter = st.text_input("肿瘤类型筛选", placeholder="如：肺癌")
    
    with col2:
        gene_filter = st.text_input("基因筛选", placeholder="如：EGFR")
    
    # 导出格式
    export_format = st.selectbox("导出格式", ["CSV", "Excel", "JSON"])
    
    # 导出按钮
    if st.button("生成导出文件", use_container_width=True):
        # 映射数据类型到表名
        table_map = {
            "已批准药物": "approved_drugs",
            "NDA申请药物": "nda_drugs",
            "CDE特殊品种": "cde_special_drugs",
            "学术文献": "academic_papers",
            "会议摘要": "conference_abstracts",
            "临床试验": "clinical_trials"
        }
        
        table_name = table_map[data_type]
        
        # 构建查询条件
        conditions = []
        params = []
        
        if start_date:
            date_field = {
                "approved_drugs": "approval_date",
                "nda_drugs": "nda_submission_date",
                "cde_special_drugs": "inclusion_date",
                "academic_papers": "publication_date",
                "conference_abstracts": "conference_year",
                "clinical_trials": "last_update_posted"
            }.get(table_name, "created_at")
            conditions.append(f"{date_field} >= ?")
            params.append(str(start_date))
        
        if end_date:
            date_field = {
                "approved_drugs": "approval_date",
                "nda_drugs": "nda_submission_date",
                "cde_special_drugs": "inclusion_date",
                "academic_papers": "publication_date",
                "conference_abstracts": "conference_year",
                "clinical_trials": "last_update_posted"
            }.get(table_name, "created_at")
            conditions.append(f"{date_field} <= ?")
            params.append(str(end_date))
        
        if tumor_type_filter:
            tumor_field = {
                "approved_drugs": "indication",
                "clinical_trials": "tumor_type",
                "academic_papers": "tumor_type",
                "conference_abstracts": "tumor_type"
            }.get(table_name, None)
            if tumor_field:
                conditions.append(f"{tumor_field} LIKE ?")
                params.append(f"%{tumor_type_filter}%")
        
        if gene_filter:
            gene_field = {
                "clinical_trials": "gene_marker",
                "academic_papers": "target_gene",
                "conference_abstracts": "target_gene"
            }.get(table_name, None)
            if gene_field:
                conditions.append(f"{gene_field} LIKE ?")
                params.append(f"%{gene_filter}%")
        
        where_clause = " AND ".join(conditions) if conditions else ""
        where_part = f"WHERE {where_clause}" if where_clause else ""
        query = f"SELECT * FROM {table_name} {where_part}"
        
        # 查询数据
        data = system.db_manager.execute_query(query, tuple(params) if params else None)
        
        if data:
            # 生成导出文件
            import pandas as pd
            df = pd.DataFrame(data)
            
            # 文件名
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"{table_name}_{timestamp}"
            
            # 导出路径
            exports_path = system.config_manager.get_exports_path()
            full_exports_path = os.path.join(
                os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                exports_path
            )
            os.makedirs(full_exports_path, exist_ok=True)
            
            # 根据格式导出
            if export_format == "CSV":
                file_path = os.path.join(full_exports_path, f"{filename}.csv")
                df.to_csv(file_path, index=False, encoding='utf-8-sig')
            elif export_format == "Excel":
                file_path = os.path.join(full_exports_path, f"{filename}.xlsx")
                df.to_excel(file_path, index=False)
            elif export_format == "JSON":
                file_path = os.path.join(full_exports_path, f"{filename}.json")
                df.to_json(file_path, orient='records', force_ascii=False)
            
            st.success(f"导出成功！共 {len(data)} 条记录")
            st.info(f"文件路径: {file_path}")
            
            # 显示预览
            st.markdown("#### 数据预览")
            st.dataframe(df.head(10), use_container_width=True)
        else:
            st.warning("没有符合条件的数据")


def show_status_page():
    """显示运行状态页面"""
    st.markdown("<h1 class='main-header'>🔄 运行状态</h1>", unsafe_allow_html=True)
    
    # 系统状态概览
    st.markdown("### 系统状态概览")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric("定时任务", "运行中" if system.scheduler_running else "已停止")
    
    with col2:
        stats = system.get_system_stats()
        st.metric("总数据量", sum(stats.values()))
    
    with col3:
        trans_stats = system.translation_service.get_stats()
        st.metric("今日翻译", trans_stats['today'].get('requests', 0))
    
    st.markdown("---")
    
    # 模块运行状态
    st.markdown("### 各模块运行状态")
    
    modules = [
        ('FDA已批准药物', 'fda_approved', '每日凌晨2:00'),
        ('FDA NDA申请', 'fda_nda', '每日凌晨3:00'),
        ('NMPA已批准药物', 'nmpa_approved', '每日凌晨4:00'),
        ('CDE特殊品种', 'cde_special', '每日凌晨5:00'),
        ('学术文献检索', 'academic_papers', '每周一凌晨1:00'),
        ('临床试验采集', 'clinical_trials', '每周二凌晨1:00'),
    ]
    
    status_data = []
    for name, key, schedule in modules:
        last_run = system.db_manager.get_last_collection_time(key)
        
        # 查询最近运行日志
        logs = system.db_manager.execute_query(
            "SELECT * FROM system_logs WHERE module_name = ? ORDER BY start_time DESC LIMIT 1",
            (key,)
        )
        
        status = '未运行'
        records_processed = 0
        
        if logs:
            log = logs[0]
            status = log.get('status', '未知')
            records_processed = log.get('records_processed', 0)
        
        status_data.append({
            '模块名称': name,
            '定时配置': schedule,
            '最后运行': last_run or '从未运行',
            '运行状态': status,
            '处理记录数': records_processed,
        })
    
    st.dataframe(pd.DataFrame(status_data), use_container_width=True)
    
    st.markdown("---")
    
    # 手动触发运行
    st.markdown("### 手动触发任务")
    
    st.info("💡 点击下方按钮可手动启动对应的数据采集任务。采集过程中请勿关闭页面，运行结果将实时显示。")
    
    # 定义所有可手动运行的模块
    manual_modules = [
        {
            'name': 'FDA已批准药物',
            'key': 'fda_approved',
            'icon': '💊',
            'desc': '通过openFDA API采集FDA批准的抗肿瘤药物信息',
            'collector_available': 'fda_approved' in system.collectors,
        },
        {
            'name': 'FDA NDA申请',
            'key': 'fda_nda',
            'icon': '📋',
            'desc': '采集FDA新药申请(NDA)状态信息',
            'collector_available': 'fda_approved' in system.collectors,
        },
        {
            'name': 'NMPA已批准药物',
            'key': 'nmpa_approved',
            'icon': '🇨🇳',
            'desc': '采集国家药监局批准的抗肿瘤药物信息',
            'collector_available': 'nmpa_cde' in system.collectors,
        },
        {
            'name': 'CDE特殊品种',
            'key': 'cde_special',
            'icon': '⭐',
            'desc': '采集CDE优先审评/突破性治疗品种信息',
            'collector_available': 'nmpa_cde' in system.collectors,
        },
        {
            'name': '学术文献检索',
            'key': 'academic_papers',
            'icon': '📚',
            'desc': '通过PubMed API检索抗肿瘤药物相关学术文献',
            'collector_available': 'academic_papers' in system.collectors,
        },
        {
            'name': '临床试验采集',
            'key': 'clinical_trials',
            'icon': '🔬',
            'desc': '通过ClinicalTrials.gov API采集抗肿瘤药物临床试验信息',
            'collector_available': 'clinical_trials' in system.collectors,
        },
        {
            'name': '会议摘要采集',
            'key': 'conference_abstracts',
            'icon': '📣',
            'desc': '采集ASCO/ESMO/AACR等肿瘤学会议摘要',
            'collector_available': 'conference_abstracts' in system.collectors,
        },
    ]
    
    # 使用3列布局显示按钮
    for i in range(0, len(manual_modules), 3):
        cols = st.columns(3)
        for j in range(3):
            if i + j < len(manual_modules):
                mod = manual_modules[i + j]
                with cols[j]:
                    st.markdown(f"**{mod['icon']} {mod['name']}**")
                    st.caption(mod['desc'])
                    
                    if mod['collector_available']:
                        if st.button(
                            f"▶️ 运行{mod['name']}",
                            key=f"run_{mod['key']}",
                            use_container_width=True,
                            type="primary"
                        ):
                            with st.spinner(f"正在运行 {mod['name']} 采集任务，请稍候..."):
                                result = system.run_collector(mod['key'])
                            
                            if result['success']:
                                st.success(
                                    f"✅ {mod['name']} 采集完成！\n"
                                    f"- 处理记录: {result['records_processed']} 条\n"
                                    f"- 新增记录: {result['records_added']} 条\n"
                                    f"- 耗时: {result['duration']} 秒"
                                )
                            else:
                                st.error(
                                    f"❌ {mod['name']} 采集失败！\n"
                                    f"- 错误信息: {result['message']}\n"
                                    f"- 耗时: {result['duration']} 秒"
                                )
                    else:
                        st.button(
                            f"🔒 {mod['name']}（待开发）",
                            key=f"run_{mod['key']}",
                            use_container_width=True,
                            disabled=True
                        )
                        st.caption("🚧 采集模块开发中，敬请期待")
    
    st.markdown("---")
    
    # 系统日志
    st.markdown("### 系统日志（最近50条）")
    
    logs = system.db_manager.execute_query(
        "SELECT * FROM system_logs ORDER BY start_time DESC LIMIT 50"
    )
    
    if logs:
        log_data = []
        for log in logs:
            log_data.append({
                '模块': log.get('module_name', ''),
                '操作': log.get('action', ''),
                '状态': log.get('status', ''),
                '消息': log.get('message', '')[:50] + '...' if len(log.get('message', '')) > 50 else log.get('message', ''),
                '处理数': log.get('records_processed', 0),
                '开始时间': log.get('start_time', ''),
                '耗时(秒)': log.get('duration_seconds', ''),
            })
        
        st.dataframe(pd.DataFrame(log_data), use_container_width=True)
    else:
        st.info("暂无系统日志")


def show_help_page():
    """显示使用说明页面"""
    st.markdown("<h1 class='main-header'>📖 使用说明</h1>", unsafe_allow_html=True)
    
    st.markdown("""
    ## 系统概述
    
    本系统是一个自动化医学信息收集系统，用于实时监控和整合全球抗肿瘤药物的监管审批信息、学术研究进展和临床试验动态。
    
    ### 主要功能
    
    1. **监管机构药物信息采集**
       - FDA已批准抗肿瘤药物（openFDA API）
       - FDA NDA申请药物跟踪
       - NMPA已批准抗肿瘤药物
       - CDE优先审评/突破性治疗品种
    
    2. **学术文献与会议信息采集**
       - 核心医学期刊文献检索（PubMed API）
       - ASCO/ESMO/AACR年会摘要采集
    
    3. **临床试验信息采集**
       - ClinicalTrials.gov临床试验
       - CDE临床试验平台
       - ChiCTR中国临床试验注册中心
    
    4. **数据管理功能**
       - 中英文双语展示
       - 数据筛选和搜索
       - 多格式导出（CSV/Excel/JSON）
    
    ---
    
    ## 快速开始
    
    ### 1. 配置翻译服务
    
    进入 **⚙️ 配置管理** → **翻译服务** 页面：
    
    - 如果有百度翻译APP ID，填写即可使用高质量翻译
    - 如果没有，系统会自动使用免费的Helsinki-NLP开源模型
    
    百度翻译API申请步骤：
    1. 访问 https://fanyi-api.baidu.com/
    2. 注册账号并创建应用
    3. 获取APP ID（密钥已预配置）
    4. 标准版每月免费额度200万字符
    
    ### 2. 配置基因和肿瘤类型
    
    系统已预设完整的肿瘤靶向基因列表和中英文对照肿瘤类型列表。
    
    如需自定义：
    - 进入 **⚙️ 配置管理** → **基因列表** 添加或删除基因
    - 进入 **⚙️ 配置管理** → **肿瘤类型** 添加或删除肿瘤类型
    
    ### 3. 查看数据
    
    进入 **📋 数据查看** 页面：
    - 选择数据类型标签页
    - 使用筛选条件过滤数据
    - 点击详情查看完整信息
    
    ### 4. 导出数据
    
    进入 **📤 数据导出** 页面：
    - 选择数据类型
    - 设置时间范围和筛选条件
    - 选择导出格式（CSV/Excel/JSON）
    - 点击导出生成文件
    
    ---
    
    ## 定时任务
    
    系统自动按以下时间运行采集任务（北京时间）：
    
    | 任务 | 运行时间 |
    |------|----------|
    | FDA已批准药物采集 | 每日凌晨2:00 |
    | FDA NDA申请采集 | 每日凌晨3:00 |
    | NMPA已批准药物采集 | 每日凌晨4:00 |
    | CDE特殊品种采集 | 每日凌晨5:00 |
    | 学术文献检索 | 每周一凌晨1:00 |
    | 临床试验采集 | 每周二凌晨1:00 |
    
    可在 **⚙️ 配置管理** → **定时任务** 页面修改运行时间。
    
    ---
    
    ## 数据来源
    
    ### 监管机构
    - **FDA**: openFDA API (https://api.fda.gov)
    - **NMPA**: 国家药品监督管理局官网
    - **CDE**: 药品审评中心官网
    
    ### 学术文献
    - **PubMed**: NCBI E-utilities API
    - 已配置API密钥，无需额外申请
    
    ### 临床试验
    - **ClinicalTrials.gov**: API v2.0
    - **CDE**: chinadrugtrials.org.cn
    - **ChiCTR**: chictr.org.cn
    
    ---
    
    ## 技术支持
    
    如有问题或建议，请联系系统管理员。
    
    ---
    
    ## 更新日志
    
    ### v1.0.0 (当前版本)
    - 完成核心框架开发
    - 实现数据库和配置管理
    - 实现翻译服务双备份机制
    - Web界面基础功能
    - 数据查看和导出功能
    
    ### 待开发功能
    - FDA药物采集模块
    - NMPA药物采集模块
    - PubMed文献检索模块
    - ClinicalTrials.gov采集模块
    - 会议摘要采集模块
    - 定时任务调度系统
    """)


if __name__ == "__main__":
    main()