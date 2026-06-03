"""
定时任务调度模块
使用APScheduler实现定时自动运行各采集模块
"""

import os
import sys
import time
import logging
from datetime import datetime
from typing import Dict, Optional
import threading

# 添加项目路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
from apscheduler.events import EVENT_JOB_EXECUTED, EVENT_JOB_ERROR

from src.database import DatabaseManager, init_database
from src.utils.config_manager import ConfigManager, create_config_manager
from src.utils.translator import TranslationService, create_translation_service
from src.collectors.fda_collector import FDADrugCollector, create_fda_collector
from src.collectors.pubmed_collector import PubMedCollector
from src.collectors.clinical_trials_collector import ClinicalTrialsCollector

logger = logging.getLogger(__name__)


class SchedulerManager:
    """定时任务调度管理类"""
    
    def __init__(
        self,
        db_manager: DatabaseManager,
        config_manager: ConfigManager,
        translation_service: TranslationService
    ):
        """
        初始化调度管理器
        
        Args:
            db_manager: 数据库管理器
            config_manager: 配置管理器
            translation_service: 翻译服务
        """
        self.db_manager = db_manager
        self.config_manager = config_manager
        self.translation_service = translation_service
        
        # 创建调度器
        self.scheduler = BackgroundScheduler(
            timezone='Asia/Shanghai',  # 使用北京时间
            executors={
                'default': {
                    'type': 'threadpool',
                    'max_workers': 3
                }
            }
        )
        
        # 添加事件监听
        self.scheduler.add_listener(
            self._job_executed_listener,
            EVENT_JOB_EXECUTED | EVENT_JOB_ERROR
        )
        
        # 初始化采集器
        self.collectors = {}
        self._init_collectors()
        
        # 任务状态
        self.job_status: Dict = {}
        self.is_running = False
        
        logger.info("定时任务调度管理器初始化完成")
    
    def _init_collectors(self):
        """初始化各采集模块"""
        # FDA采集器
        self.collectors['fda_approved'] = create_fda_collector(
            self.db_manager,
            self.config_manager,
            self.translation_service
        )
        
        # PubMed采集器
        self.collectors['academic_papers'] = PubMedCollector(
            self.db_manager,
            self.config_manager,
            self.translation_service
        )
        
        # ClinicalTrials.gov采集器
        self.collectors['clinical_trials'] = ClinicalTrialsCollector(
            self.db_manager,
            self.config_manager,
            self.translation_service
        )
        
        logger.info(f"已初始化 {len(self.collectors)} 个采集器")
    
    def _job_executed_listener(self, event):
        """任务执行事件监听器"""
        job_id = event.job_id
        
        if event.exception:
            logger.error(f"任务 {job_id} 执行失败: {event.exception}")
            self.job_status[job_id] = {
                'status': 'failed',
                'error': str(event.exception),
                'time': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            }
        else:
            logger.info(f"任务 {job_id} 执行成功")
            self.job_status[job_id] = {
                'status': 'success',
                'time': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            }
    
    def _run_fda_approved(self):
        """运行FDA已批准药物采集"""
        logger.info("开始执行FDA已批准药物采集任务")
        
        try:
            collector = self.collectors.get('fda_approved')
            if collector:
                result = collector.run()
                logger.info(f"FDA采集完成: {result}")
        except Exception as e:
            logger.error(f"FDA采集任务失败: {e}")
    
    def _run_fda_nda(self):
        """运行FDA NDA申请采集"""
        logger.info("开始执行FDA NDA申请采集任务")
        # NDA采集逻辑（待实现）
        logger.info("FDA NDA采集任务完成")
    
    def _run_nmpa_approved(self):
        """运行NMPA已批准药物采集"""
        logger.info("开始执行NMPA已批准药物采集任务")
        # NMPA采集逻辑（待实现）
        logger.info("NMPA采集任务完成")
    
    def _run_cde_special(self):
        """运行CDE特殊审评品种采集"""
        logger.info("开始执行CDE特殊审评品种采集任务")
        # CDE采集逻辑（待实现）
        logger.info("CDE特殊品种采集任务完成")
    
    def _run_academic_papers(self):
        """运行学术文献检索"""
        logger.info("开始执行学术文献检索任务")
        
        try:
            collector = self.collectors.get('academic_papers')
            if collector:
                result = collector.run()
                logger.info(f"PubMed文献检索完成: {result}")
        except Exception as e:
            logger.error(f"PubMed检索任务失败: {e}")
    
    def _run_clinical_trials(self):
        """运行临床试验采集"""
        logger.info("开始执行临床试验采集任务")
        
        try:
            collector = self.collectors.get('clinical_trials')
            if collector:
                result = collector.run()
                logger.info(f"ClinicalTrials.gov采集完成: {result}")
        except Exception as e:
            logger.error(f"ClinicalTrials.gov采集任务失败: {e}")
    
    def _run_conference_abstracts(self):
        """运行会议摘要采集"""
        logger.info("开始执行会议摘要采集任务")
        # 会议摘要采集逻辑（待实现）
        logger.info("会议摘要采集任务完成")
    
    def setup_jobs(self):
        """设置定时任务"""
        # 获取定时任务配置
        scheduler_config = self.config_manager.get_scheduler_config()
        
        # 定义任务映射
        job_configs = [
            ('fda_approved', self._run_fda_approved, scheduler_config.get('fda_approved', '0 2 * * *')),
            ('fda_nda', self._run_fda_nda, scheduler_config.get('fda_nda', '0 3 * * *')),
            ('nmpa_approved', self._run_nmpa_approved, scheduler_config.get('nmpa_approved', '0 4 * * *')),
            ('cde_special', self._run_cde_special, scheduler_config.get('cde_special', '0 5 * * *')),
            ('academic_papers', self._run_academic_papers, scheduler_config.get('academic_papers', '0 1 * * 1')),
            ('clinical_trials', self._run_clinical_trials, scheduler_config.get('clinical_trials', '0 1 * * 2')),
            ('conference_abstracts', self._run_conference_abstracts, scheduler_config.get('conference_abstracts', '0 6 * * *')),
        ]
        
        # 添加任务
        for job_id, job_func, cron_expression in job_configs:
            try:
                # 解析cron表达式
                trigger = CronTrigger.from_crontab(cron_expression, timezone='Asia/Shanghai')
                
                # 添加任务
                self.scheduler.add_job(
                    job_func,
                    trigger=trigger,
                    id=job_id,
                    name=job_id,
                    replace_existing=True
                )
                
                logger.info(f"添加定时任务: {job_id}, cron: {cron_expression}")
                
            except Exception as e:
                logger.error(f"添加任务失败 {job_id}: {e}")
    
    def start(self):
        """启动调度器"""
        if not self.is_running:
            self.setup_jobs()
            self.scheduler.start()
            self.is_running = True
            logger.info("定时任务调度器已启动")
    
    def stop(self):
        """停止调度器"""
        if self.is_running:
            self.scheduler.shutdown()
            self.is_running = False
            logger.info("定时任务调度器已停止")
    
    def pause_job(self, job_id: str):
        """暂停指定任务"""
        try:
            self.scheduler.pause_job(job_id)
            logger.info(f"任务 {job_id} 已暂停")
        except Exception as e:
            logger.error(f"暂停任务失败: {e}")
    
    def resume_job(self, job_id: str):
        """恢复指定任务"""
        try:
            self.scheduler.resume_job(job_id)
            logger.info(f"任务 {job_id} 已恢复")
        except Exception as e:
            logger.error(f"恢复任务失败: {e}")
    
    def trigger_job(self, job_id: str):
        """手动触发指定任务"""
        try:
            self.scheduler.modify_job(job_id, next_run_time=datetime.now())
            logger.info(f"任务 {job_id} 已触发")
        except Exception as e:
            logger.error(f"触发任务失败: {e}")
    
    def get_jobs_info(self) -> list:
        """获取所有任务信息"""
        jobs = self.scheduler.get_jobs()
        
        job_info = []
        for job in jobs:
            status = self.job_status.get(job.id, {})
            
            job_info.append({
                'job_id': job.id,
                'next_run_time': job.next_run_time.strftime('%Y-%m-%d %H:%M:%S') if job.next_run_time else '未安排',
                'trigger': str(job.trigger),
                'status': status.get('status', 'pending'),
                'last_run_time': status.get('time', '未运行'),
                'error': status.get('error', '')
            })
        
        return job_info
    
    def get_scheduler_status(self) -> Dict:
        """获取调度器状态"""
        return {
            'is_running': self.is_running,
            'jobs_count': len(self.scheduler.get_jobs()),
            'timezone': 'Asia/Shanghai',
            'collectors_initialized': len(self.collectors)
        }
    
    def run_all_now(self):
        """立即运行所有任务"""
        logger.info("手动触发所有采集任务")
        
        for job_id, collector in self.collectors.items():
            try:
                if collector:
                    result = collector.run()
                    logger.info(f"{job_id} 完成: {result}")
            except Exception as e:
                logger.error(f"{job_id} 失败: {e}")


def create_scheduler_manager(
    db_manager: DatabaseManager,
    config_manager: ConfigManager,
    translation_service: TranslationService
) -> SchedulerManager:
    """
    创建调度管理器实例

    Args:
        db_manager: 数据库管理器
        config_manager: 配置管理器
        translation_service: 翻译服务

    Returns:
        调度管理器实例
    """
    return SchedulerManager(
        db_manager=db_manager,
        config_manager=config_manager,
        translation_service=translation_service
    )


def run_scheduler_standalone():
    """独立运行调度器（用于后台服务）"""
    import signal

    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler('data/logs/scheduler.log'),
            logging.StreamHandler()
        ]
    )

    base_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    db_path = os.path.join(base_path, 'data', 'medical_info.db')
    config_path = os.path.join(base_path, 'config', 'config.yaml')

    db_manager = init_database(db_path)
    config_manager = create_config_manager(config_path)
    translation_config = config_manager.get_translation_config()
    translation_service = create_translation_service(translation_config)

    scheduler_manager = create_scheduler_manager(
        db_manager, config_manager, translation_service
    )

    scheduler_manager.start()

    logger.info("调度器已启动，等待任务执行...")
    logger.info("按 Ctrl+C 停止调度器")

    def signal_handler(sig, frame):
        logger.info("收到停止信号，正在关闭调度器...")
        scheduler_manager.stop()
        scheduler_manager.db_manager.close()
        logger.info("调度器已停止")
        sys.exit(0)

    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)

    try:
        while scheduler_manager.is_running:
            time.sleep(60)
            status = scheduler_manager.get_scheduler_status()
            logger.info(f"调度器状态: {status}")
    except KeyboardInterrupt:
        signal_handler(None, None)


if __name__ == "__main__":

    logging.basicConfig(level=logging.INFO)

    base_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    db_path = os.path.join(base_path, 'data', 'medical_info.db')
    config_path = os.path.join(base_path, 'config', 'config.yaml')

    db_manager = init_database(db_path)
    config_manager = create_config_manager(config_path)
    translation_config = config_manager.get_translation_config()
    translation_service = create_translation_service(translation_config)

    scheduler_manager = create_scheduler_manager(
        db_manager, config_manager, translation_service
    )

    print("设置定时任务...")
    scheduler_manager.setup_jobs()

    jobs_info = scheduler_manager.get_jobs_info()
    for job in jobs_info:
        print(f"任务: {job['job_id']}, 下次运行: {job['next_run_time']}")

    scheduler_manager.start()

    print("调度器已启动")
    print("等待10秒...")

    time.sleep(10)

    status = scheduler_manager.get_scheduler_status()
    print(f"调度器状态: {status}")

    scheduler_manager.stop()
    scheduler_manager.db_manager.close()

    print("测试完成")