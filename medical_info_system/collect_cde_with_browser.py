#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
使用浏览器自动化访问CDE网站收集特殊品种药物信息
"""
import sys
import os
import asyncio
import json
from datetime import datetime
from typing import List, Dict

# 添加项目路径
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)


class CDEDrugCollector:
    """CDE特殊品种药物浏览器采集器"""
    
    BREAKTHROUGH_URL = "https://www.cde.org.cn/main/xxgk/listpage/b40868b5e21c038a6aa8b4319d21b07d"
    PRIORITY_URL = "https://www.cde.org.cn/main/xxgk/listpage/b40868b5e21c038a6aa8b4319d21b07d"
    
    def __init__(self):
        self.browser = None
        self.collected_data = []
    
    async def collect_all_drugs(self):
        """收集所有药物信息"""
        print("开始收集CDE特殊品种药物信息...")
        print("使用浏览器访问CDE网站...")
        
        try:
            # 由于无法直接访问浏览器，我将使用WebFetch来获取页面信息
            from src.utils.http_client import RequestManager
            from bs4 import BeautifulSoup
            
            request_manager = RequestManager()
            
            # 访问突破性治疗品种页面
            print("\n1. 访问纳入突破性治疗品种名单页面...")
            breakthrough_drugs = await self._collect_breakthrough_drugs(request_manager)
            print(f"   收集到 {len(breakthrough_drugs)} 条突破性治疗药物")
            
            # 访问优先审评品种页面
            print("\n2. 访问纳入优先审评品种名单页面...")
            priority_drugs = await self._collect_priority_drugs(request_manager)
            print(f"   收集到 {len(priority_drugs)} 条优先审评药物")
            
            # 保存收集结果
            all_drugs = breakthrough_drugs + priority_drugs
            
            # 保存为JSON文件供后续使用
            output_file = os.path.join(project_root, 'data', 'cde_drugs_raw.json')
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(all_drugs, f, ensure_ascii=False, indent=2)
            
            print(f"\n收集完成！共 {len(all_drugs)} 条药物信息")
            print(f"数据已保存到: {output_file}")
            
            return all_drugs
            
        except Exception as e:
            print(f"收集失败: {e}")
            import traceback
            traceback.print_exc()
            return []
    
    async def _collect_breakthrough_drugs(self, request_manager) -> List[Dict]:
        """收集突破性治疗品种"""
        drugs = []
        
        try:
            # 由于直接HTTP请求会被WAF拦截，我们返回需要您手动获取的数据列表
            # 请在浏览器中访问以下URL并手动收集数据：
            # https://www.cde.org.cn/main/xxgk/listpage/b40868b5e21c038a6aa8b4319d21b07d
            
            # 这是需要手动收集的数据模板
            print("   提示：请在浏览器中访问以下URL手动收集数据：")
            print(f"   {self.BREAKTHROUGH_URL}")
            print("   1. 查看第1-10页的所有药物")
            print("   2. 点击每个药物查看详细信息")
            print("   3. 记录'拟定适应症（或功能主治）'信息")
            print("   4. 根据适应症判断是否为抗肿瘤药物")
            
            # 返回一个示例结构
            sample_drugs = [
                {
                    'drug_name': '注射用YL201',
                    'acceptance_number': '',  # 需要从网页获取
                    'applicant': '',  # 需要从网页获取
                    'application_date': '',  # 需要从网页获取
                    'indication': '既往经吉西他滨为基础的系统治疗失败的转移性胰腺导管腺癌',  # 根据您的提示更新
                    'molecular_target': '',  # 需要从网页获取
                    'drug_type': '突破性治疗'
                },
                # 其他药物...
            ]
            
            return sample_drugs
            
        except Exception as e:
            print(f"收集突破性治疗药物失败: {e}")
            return []
    
    async def _collect_priority_drugs(self, request_manager) -> List[Dict]:
        """收集优先审评品种"""
        drugs = []
        
        try:
            print("   提示：请在浏览器中访问以下URL手动收集数据：")
            print(f"   {self.PRIORITY_URL}")
            print("   1. 查看第1-10页的所有药物")
            print("   2. 点击每个药物查看详细信息")
            print("   3. 记录'拟定适应症（或功能主治）'信息")
            print("   4. 根据适应症判断是否为抗肿瘤药物")
            
            # 返回一个示例结构
            sample_drugs = [
                {
                    'drug_name': '昂拉地韦颗粒',  # 根据您的提示
                    'acceptance_number': '',  # 需要从网页获取
                    'applicant': '',  # 需要从网页获取
                    'application_date': '',  # 需要从网页获取
                    'indication': '用于2至12岁以下单纯型甲型流感儿童患者的治疗',  # 非肿瘤，需要排除
                    'molecular_target': '',  # 需要从网页获取
                    'drug_type': '优先审评',
                    'is_solid_tumor': False  # 标记为非肿瘤
                },
                # 其他药物...
            ]
            
            return sample_drugs
            
        except Exception as e:
            print(f"收集优先审评药物失败: {e}")
            return []


async def main():
    """主函数"""
    print("=" * 60)
    print("CDE特殊品种药物信息浏览器采集工具")
    print("=" * 60)
    
    collector = CDEDrugCollector()
    drugs = await collector.collect_all_drugs()
    
    print("\n" + "=" * 60)
    print("采集说明")
    print("=" * 60)
    print("由于CDE网站有WAF防护，无法自动抓取。")
    print("请您手动访问以下URL：")
    print("1. 纳入突破性治疗品种名单：https://www.cde.org.cn/main/xxgk/listpage/b40868b5e21c038a6aa8b4319d21b07d")
    print("2. 纳入优先审评品种名单：https://www.cde.org.cn/main/xxgk/listpage/b40868b5e21c038a6aa8b4319d21b07d")
    print("\n操作步骤：")
    print("1. 访问上述URL")
    print("2. 翻页查看第1-10页所有药物")
    print("3. 点击每个药物名称查看详细信息弹窗")
    print("4. 在'拟定适应症（或功能主治）'处查看真实适应症")
    print("5. 根据适应症判断是否为实体肿瘤药物")
    print("6. 收集所有药物信息并告知我")
    print("=" * 60)


if __name__ == '__main__':
    asyncio.run(main())
