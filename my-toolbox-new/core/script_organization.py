"""
脚本组织管理器 - 负责脚本排序和分类管理
"""
from typing import List, Dict, Any, Optional


class ScriptOrganization:
    def __init__(self, user_preferences):
        self.user_preferences = user_preferences
        self.scripts = []

    def get_categories(self) -> List[str]:
        """获取所有分类"""
        categories = set()
        for script in self.scripts:
            category = script.get('category', '未分类')
            categories.add(category)
        return sorted(list(categories))

    def search_scripts(self, query: str) -> List[Dict[str, Any]]:
        """搜索脚本"""
        query = query.lower()
        results = []
        for script in self.scripts:
            if (query in script.get('name', '').lower() or 
                query in script.get('description', '').lower() or 
                query in script.get('category', '').lower()):
                results.append(script)
        return results

    def add_custom_category(self, category_name):
        """添加自定义分类"""
        custom_categories = self.user_preferences.get("custom_categories", [])
        if category_name not in custom_categories:
            custom_categories.append(category_name)
            self.user_preferences["custom_categories"] = custom_categories
            return True
        return False

    def remove_custom_category(self, category_name):
        """移除自定义分类，并同步更新排序列表"""
        custom_categories = self.user_preferences.get("custom_categories", [])
        if category_name in custom_categories:
            custom_categories.remove(category_name)
            self.user_preferences["custom_categories"] = custom_categories

            # 同步从 categoryOrder 列表中移除
            layout_prefs = self.user_preferences.setdefault('layout', {})
            category_order = layout_prefs.setdefault('categoryOrder', [])
            if category_name in category_order:
                category_order.remove(category_name)

            # 同时更新所有脚本的分类信息
            for script_id, script_info in self.user_preferences.get("scripts", {}).items():
                if script_info.get("category") == category_name:
                    script_info["category"] = "未分类"  # 重置为默认分类
            return True
        return False

    def assign_script_to_category(self, script_id, category_name):
        """将脚本分配到指定分类"""
        if "scripts" not in self.user_preferences:
            self.user_preferences["scripts"] = {}
        
        if script_id not in self.user_preferences["scripts"]:
            self.user_preferences["scripts"][script_id] = {}
        
        self.user_preferences["scripts"][script_id]["category"] = category_name
        return True
    
    def save_script_order(self, script_order, save_func):
        """保存脚本排序"""
        try:
            # 确保 layout 字段存在
            if "layout" not in self.user_preferences:
                self.user_preferences["layout"] = {}
            
            # 保存脚本排序
            self.user_preferences["layout"]["scriptOrder"] = script_order
            return save_func(self.user_preferences)
        except Exception as e:
            print(f"保存脚本排序时出错: {e}")
            return False

    def get_script_order(self):
        """获取脚本排序"""
        try:
            layout = self.user_preferences.get("layout", {})
            return layout.get("scriptOrder", [])
        except Exception as e:
            print(f"获取脚本排序时出错: {e}")
            return []

    def save_category_order(self, category_order, save_func):
        """保存分类排序"""
        try:
            # 确保 layout 字段存在
            if "layout" not in self.user_preferences:
                self.user_preferences["layout"] = {}
            
            # 保存分类排序
            self.user_preferences["layout"]["categoryOrder"] = category_order
            return save_func(self.user_preferences)
        except Exception as e:
            print(f"保存分类排序时出错: {e}")
            return False

    def get_category_order(self):
        """获取分类排序"""
        try:
            layout = self.user_preferences.get("layout", {})
            return layout.get("categoryOrder", [])
        except Exception as e:
            print(f"获取分类排序时出错: {e}")
            return []

    def get_all_script_defined_categories(self) -> set:
        """
        获取所有在脚本文件（元数据）中直接定义的分类。
        这用于区分是脚本自带的分类还是用户后加的纯自定义分类。
        """
        categories = set()
        # self.scripts 是由 ScriptManager 发现并加载的脚本列表
        for script in self.scripts:
            # script_discovery.py确保了元数据中总是有'category'键
            category = script.get('category')
            if category:
                categories.add(category)
        return categories