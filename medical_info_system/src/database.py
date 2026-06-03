"""
数据库初始化模块
创建所有数据表并初始化数据库连接
"""

import sqlite3
import os
from datetime import datetime
from typing import Optional, List, Dict, Any
import logging

logger = logging.getLogger(__name__)


class DatabaseManager:
    """数据库管理类"""
    
    def __init__(self, db_path: str):
        """
        初始化数据库管理器
        
        Args:
            db_path: 数据库文件路径
        """
        self.db_path = db_path
        self.conn: Optional[sqlite3.Connection] = None
        self._ensure_db_exists()
    
    def _ensure_db_exists(self):
        """确保数据库文件和目录存在"""
        db_dir = os.path.dirname(self.db_path)
        if db_dir and not os.path.exists(db_dir):
            os.makedirs(db_dir, exist_ok=True)
            logger.info(f"创建数据库目录: {db_dir}")
    
    def connect(self):
        """建立数据库连接"""
        if self.conn is None:
            self.conn = sqlite3.connect(self.db_path, check_same_thread=False)
            self.conn.row_factory = sqlite3.Row
            # 启用外键约束
            self.conn.execute("PRAGMA foreign_keys = ON")
            logger.info(f"数据库连接成功: {self.db_path}")
        return self.conn
    
    def close(self):
        """关闭数据库连接"""
        if self.conn:
            self.conn.close()
            self.conn = None
            logger.info("数据库连接已关闭")
    
    def init_tables(self):
        """初始化所有数据表"""
        conn = self.connect()
        cursor = conn.cursor()
        
        # 创建已批准药物信息表
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS approved_drugs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            regulatory_agency TEXT NOT NULL,
            drug_name_en TEXT,
            drug_name_cn TEXT,
            generic_name_en TEXT,
            generic_name_cn TEXT,
            brand_name_en TEXT,
            brand_name_cn TEXT,
            applicant TEXT,
            application_number TEXT,
            approval_number TEXT,
            approval_date DATE,
            indication TEXT NOT NULL,
            dosage_form TEXT,
            route_of_administration TEXT,
            mechanism_of_action TEXT,
            companion_diagnosis TEXT,
            cd_target TEXT,
            cd_product TEXT,
            clinical_trial_data TEXT,
            previous_approved_indications TEXT,
            previous_withdrawn_indications TEXT,
            previous_fda_approvals TEXT,
            previous_nmpa_approvals TEXT,
            label_download_url TEXT,
            label_cloud_path TEXT,
            detail_url TEXT,
            data_collection_time DATETIME,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(regulatory_agency, approval_number, indication)
        )
        """)
        
        # 创建FDA NDA申请药物信息表
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS nda_drugs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            regulatory_agency TEXT NOT NULL DEFAULT 'FDA',
            nda_number TEXT NOT NULL,
            nda_status TEXT NOT NULL,
            nda_submission_date DATE,
            drug_name_en TEXT,
            drug_name_cn TEXT,
            generic_name_en TEXT,
            generic_name_cn TEXT,
            applicant TEXT,
            indication TEXT,
            dosage_form TEXT,
            route_of_administration TEXT,
            mechanism_of_action TEXT,
            target_gene TEXT,
            trial_phase TEXT,
            expected_approval_date DATE,
            status_change_history TEXT,
            detail_url TEXT,
            data_collection_time DATETIME,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(nda_number)
        )
        """)
        
        # 创建CDE优先审评/突破性治疗品种表
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS cde_special_drugs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            regulatory_agency TEXT NOT NULL DEFAULT 'NMPA/CDE',
            program_type TEXT NOT NULL,
            drug_name_en TEXT,
            drug_name_cn TEXT,
            generic_name_en TEXT,
            generic_name_cn TEXT,
            applicant TEXT,
            application_number TEXT,
            inclusion_date DATE,
            inclusion_reason TEXT,
            indication TEXT,
            dosage_form TEXT,
            route_of_administration TEXT,
            mechanism_of_action TEXT,
            target_gene TEXT,
            review_status TEXT,
            review_progress TEXT,
            approval_result TEXT,
            approval_date DATE,
            detail_url TEXT,
            data_collection_time DATETIME,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(program_type, application_number)
        )
        """)
        
        # 创建学术文献信息表
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS academic_papers (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title_en TEXT NOT NULL,
            title_cn TEXT,
            authors TEXT,
            journal_name TEXT NOT NULL,
            publication_date DATE,
            doi TEXT UNIQUE,
            abstract_en TEXT,
            abstract_cn TEXT,
            target_gene TEXT,
            tumor_type TEXT,
            tumor_type_cn TEXT,
            drug_name TEXT,
            study_type TEXT,
            key_findings TEXT,
            pmid TEXT,
            url TEXT,
            data_collection_time DATETIME,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
        )
        """)
        
        # 创建学术会议摘要表
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS conference_abstracts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            conference_name TEXT NOT NULL,
            conference_year INTEGER NOT NULL,
            abstract_number TEXT,
            title_en TEXT NOT NULL,
            title_cn TEXT,
            authors TEXT,
            presentation_type TEXT,
            session_name TEXT,
            tumor_type TEXT,
            tumor_type_cn TEXT,
            target_gene TEXT,
            drug_name TEXT,
            study_phase TEXT,
            key_findings_en TEXT,
            key_findings_cn TEXT,
            url TEXT,
            data_collection_time DATETIME,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(conference_name, conference_year, abstract_number)
        )
        """)
        
        # 创建临床试验信息表
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS clinical_trials (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            platform TEXT NOT NULL,
            trial_id TEXT NOT NULL,
            trial_status TEXT NOT NULL,
            study_title_en TEXT,
            study_title_cn TEXT,
            tumor_type TEXT,
            tumor_type_cn TEXT,
            gene_marker TEXT,
            conditions TEXT,
            interventions TEXT,
            intervention_drug TEXT,
            phase TEXT,
            study_type TEXT,
            enrollment INTEGER,
            inclusion_criteria_en TEXT,
            inclusion_criteria_cn TEXT,
            exclusion_criteria_en TEXT,
            exclusion_criteria_cn TEXT,
            study_location TEXT,
            sponsor TEXT,
            start_date DATE,
            primary_completion_date DATE,
            last_update_posted DATE,
            results_url TEXT,
            url TEXT,
            data_collection_time DATETIME,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(platform, trial_id)
        )
        """)
        
        # 创建系统运行日志表
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS system_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            module_name TEXT NOT NULL,
            action TEXT NOT NULL,
            status TEXT NOT NULL,
            message TEXT,
            records_processed INTEGER DEFAULT 0,
            records_added INTEGER DEFAULT 0,
            records_updated INTEGER DEFAULT 0,
            error_count INTEGER DEFAULT 0,
            start_time DATETIME,
            end_time DATETIME,
            duration_seconds REAL,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP
        )
        """)
        
        # 创建翻译统计表
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS translation_stats (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            provider TEXT NOT NULL,
            chars_translated INTEGER DEFAULT 0,
            requests_count INTEGER DEFAULT 0,
            baidu_remaining_chars INTEGER,
            date DATE NOT NULL,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(provider, date)
        )
        """)
        
        # 创建索引以提高查询性能
        indexes = [
            "CREATE INDEX IF NOT EXISTS idx_approved_drugs_agency ON approved_drugs(regulatory_agency)",
            "CREATE INDEX IF NOT EXISTS idx_approved_drugs_date ON approved_drugs(approval_date)",
            "CREATE INDEX IF NOT EXISTS idx_approved_drugs_indication ON approved_drugs(indication)",
            "CREATE INDEX IF NOT EXISTS idx_approved_drugs_moa ON approved_drugs(mechanism_of_action)",
            "CREATE INDEX IF NOT EXISTS idx_nda_drugs_status ON nda_drugs(nda_status)",
            "CREATE INDEX IF NOT EXISTS idx_nda_drugs_date ON nda_drugs(nda_submission_date)",
            "CREATE INDEX IF NOT EXISTS idx_cde_special_type ON cde_special_drugs(program_type)",
            "CREATE INDEX IF NOT EXISTS idx_cde_special_date ON cde_special_drugs(inclusion_date)",
            "CREATE INDEX IF NOT EXISTS idx_academic_papers_journal ON academic_papers(journal_name)",
            "CREATE INDEX IF NOT EXISTS idx_academic_papers_date ON academic_papers(publication_date)",
            "CREATE INDEX IF NOT EXISTS idx_academic_papers_gene ON academic_papers(target_gene)",
            "CREATE INDEX IF NOT EXISTS idx_academic_papers_tumor ON academic_papers(tumor_type)",
            "CREATE INDEX IF NOT EXISTS idx_conference_abstracts_conf ON conference_abstracts(conference_name, conference_year)",
            "CREATE INDEX IF NOT EXISTS idx_clinical_trials_platform ON clinical_trials(platform)",
            "CREATE INDEX IF NOT EXISTS idx_clinical_trials_status ON clinical_trials(trial_status)",
            "CREATE INDEX IF NOT EXISTS idx_clinical_trials_gene ON clinical_trials(gene_marker)",
            "CREATE INDEX IF NOT EXISTS idx_clinical_trials_tumor ON clinical_trials(tumor_type)",
            "CREATE INDEX IF NOT EXISTS idx_system_logs_module ON system_logs(module_name)",
            "CREATE INDEX IF NOT EXISTS idx_system_logs_time ON system_logs(start_time)",
        ]
        
        for index_sql in indexes:
            cursor.execute(index_sql)
        
        conn.commit()
        logger.info("数据库表初始化完成")
    
    def execute_query(self, query: str, params: tuple = None) -> List[Dict]:
        """
        执行查询并返回结果
        
        Args:
            query: SQL查询语句
            params: 查询参数
            
        Returns:
            查询结果列表
        """
        conn = self.connect()
        cursor = conn.cursor()
        if params:
            cursor.execute(query, params)
        else:
            cursor.execute(query)
        rows = cursor.fetchall()
        return [dict(row) for row in rows]
    
    def execute_insert(self, table: str, data: Dict) -> int:
        """
        执行插入操作
        
        Args:
            table: 表名
            data: 数据字典
            
        Returns:
            插入记录的ID
        """
        conn = self.connect()
        cursor = conn.cursor()
        
        columns = ', '.join(data.keys())
        placeholders = ', '.join(['?' for _ in data])
        query = f"INSERT OR REPLACE INTO {table} ({columns}) VALUES ({placeholders})"
        
        cursor.execute(query, tuple(data.values()))
        conn.commit()
        return cursor.lastrowid
    
    def execute_update(self, table: str, data: Dict, condition: str, condition_params: tuple) -> int:
        """
        执行更新操作
        
        Args:
            table: 表名
            data: 更新数据字典
            condition: WHERE条件
            condition_params: 条件参数
            
        Returns:
            更新的记录数
        """
        conn = self.connect()
        cursor = conn.cursor()
        
        # 添加updated_at字段
        data['updated_at'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        
        set_clause = ', '.join([f"{k} = ?" for k in data.keys()])
        query = f"UPDATE {table} SET {set_clause} WHERE {condition}"
        
        params = tuple(data.values()) + condition_params
        cursor.execute(query, params)
        conn.commit()
        return cursor.rowcount
    
    def execute_batch_insert(self, table: str, data_list: List[Dict]) -> int:
        """
        执行批量插入操作
        
        Args:
            table: 表名
            data_list: 数据列表
            
        Returns:
            插入的记录数
        """
        if not data_list:
            return 0
        
        conn = self.connect()
        cursor = conn.cursor()
        
        columns = ', '.join(data_list[0].keys())
        placeholders = ', '.join(['?' for _ in data_list[0]])
        query = f"INSERT OR REPLACE INTO {table} ({columns}) VALUES ({placeholders})"
        
        params_list = [tuple(d.values()) for d in data_list]
        cursor.executemany(query, params_list)
        conn.commit()
        return cursor.rowcount
    
    def get_record_count(self, table: str, condition: str = None, params: tuple = None) -> int:
        """
        获取记录数量
        
        Args:
            table: 表名
            condition: WHERE条件（可选）
            params: 条件参数（可选）
            
        Returns:
            记录数量
        """
        conn = self.connect()
        cursor = conn.cursor()
        
        if condition:
            query = f"SELECT COUNT(*) FROM {table} WHERE {condition}"
            cursor.execute(query, params)
        else:
            query = f"SELECT COUNT(*) FROM {table}"
            cursor.execute(query)
        
        return cursor.fetchone()[0]
    
    def get_last_collection_time(self, module_name: str) -> Optional[str]:
        """
        获取指定模块的最后采集时间
        
        Args:
            module_name: 模块名称
            
        Returns:
            最后采集时间字符串
        """
        query = """
        SELECT end_time FROM system_logs 
        WHERE module_name = ? AND status = 'success' 
        ORDER BY end_time DESC LIMIT 1
        """
        result = self.execute_query(query, (module_name,))
        if result:
            return result[0]['end_time']
        return None
    
    def log_system_action(self, log_data: Dict):
        """
        记录系统运行日志
        
        Args:
            log_data: 日志数据字典
        """
        self.execute_insert('system_logs', log_data)
    
    def update_translation_stats(self, provider: str, chars_count: int, requests_count: int, baidu_remaining: int = None):
        """
        更新翻译统计
        
        Args:
            provider: 翻译服务提供商
            chars_count: 翻译字符数
            requests_count: 请求数量
            baidu_remaining: 百度翻译剩余字符数（可选）
        """
        today = datetime.now().strftime('%Y-%m-%d')
        
        # 检查是否已有今天的记录
        existing = self.execute_query(
            "SELECT * FROM translation_stats WHERE provider = ? AND date = ?",
            (provider, today)
        )
        
        if existing:
            # 更新现有记录
            self.execute_update(
                'translation_stats',
                {
                    'chars_translated': existing[0]['chars_translated'] + chars_count,
                    'requests_count': existing[0]['requests_count'] + requests_count,
                    'baidu_remaining_chars': baidu_remaining
                },
                "provider = ? AND date = ?",
                (provider, today)
            )
        else:
            # 创建新记录
            self.execute_insert(
                'translation_stats',
                {
                    'provider': provider,
                    'chars_translated': chars_count,
                    'requests_count': requests_count,
                    'baidu_remaining_chars': baidu_remaining,
                    'date': today
                }
            )


def init_database(db_path: str) -> DatabaseManager:
    """
    初始化数据库
    
    Args:
        db_path: 数据库文件路径
        
    Returns:
        数据库管理器实例
    """
    db_manager = DatabaseManager(db_path)
    db_manager.init_tables()
    return db_manager


if __name__ == "__main__":
    # 测试数据库初始化
    import sys
    logging.basicConfig(level=logging.INFO)
    
    db_path = "data/medical_info.db"
    db = init_database(db_path)
    
    print("数据库初始化完成")
    print(f"数据库路径: {db_path}")
    
    # 显示所有表
    tables = db.execute_query("SELECT name FROM sqlite_master WHERE type='table'")
    print(f"创建的表: {[t['name'] for t in tables]}")
    
    db.close()