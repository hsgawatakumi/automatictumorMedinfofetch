#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
CDE抗肿瘤药物采集 - 简化版
先安装依赖，再执行采集
"""
import subprocess
import sys
import os
from pathlib import Path

def main():
    project_root = Path(__file__).parent
    
    print("=" * 70)
    print("CDE官网抗肿瘤药物自动化采集程序")
    print("=" * 70)
    
    # 步骤1: 安装依赖
    print("\n[步骤1] 安装Python依赖...")
    try:
        subprocess.check_call([
            sys.executable, "-m", "pip", "install", 
            "playwright", "playwright-stealth"
        ], cwd=str(project_root))
        print("✓ 依赖安装成功")
    except Exception as e:
        print(f"✗ 依赖安装失败: {e}")
        print("请手动执行: pip install playwright playwright-stealth")
        return
    
    # 步骤2: 安装Chromium
    print("\n[步骤2] 安装Chromium浏览器...")
    try:
        subprocess.check_call([
            sys.executable, "-m", "playwright", "install", "chromium"
        ], cwd=str(project_root))
        print("✓ Chromium安装成功")
    except Exception as e:
        print(f"✗ Chromium安装失败: {e}")
        print("请手动执行: playwright install chromium")
        return
    
    # 步骤3: 运行采集
    print("\n[步骤3] 启动浏览器并开始采集...")
    print("这将打开一个浏览器窗口，请勿关闭！")
    
    try:
        # 导入并运行采集器
        sys.path.insert(0, str(project_root))
        from collect_cde_playwright import main as run_collector
        
        import asyncio
        asyncio.run(run_collector())
        
    except KeyboardInterrupt:
        print("\n用户中断采集")
    except Exception as e:
        print(f"\n采集失败: {e}")
        import traceback
        traceback.print_exc()

if __name__ == '__main__':
    main()
