"""
脚本管理器 - 负责脚本的发现、加载和元数据管理
"""
from pathlib import Path
from typing import List, Dict, Any, Optional
from core.script_discovery import ScriptDiscovery
from core.script_metadata import ScriptMetadata
from core.user_preferences import UserPreferences
from core.script_organization import ScriptOrganization
from core.script_operations import ScriptOperations


class ScriptManager:
    def __init__(self):
        self._scripts_dir = Path(__file__).parent.parent / "scripts"
        self._user_profile_file = Path(__file__).parent.parent / "user_profile.json"
        
        # 初始化各个模块
        self.user_preferences_manager = UserPreferences(self._user_profile_file)
        self.user_preferences = self.user_preferences_manager.user_preferences
        self.script_discovery = ScriptDiscovery(self._scripts_dir, self.user_preferences)
        self.script_metadata = ScriptMetadata()
        self.script_organization = ScriptOrganization(self.user_preferences)
        self.script_operations = ScriptOperations(self.user_preferences)
        
        self.scripts = []
        
        # 确保目录存在
        self._scripts_dir.mkdir(exist_ok=True)
        self.discover_scripts()
        # 确保用户配置文件被创建
        self.save_user_preferences(self.user_preferences)

    @property
    def scripts_dir(self):
        """返回脚本目录路径"""
        return str(self._scripts_dir)

    @property
    def user_profile_file(self):
        """返回用户配置文件路径"""
        return str(self._user_profile_file)

    def discover_scripts(self):
        """发现脚本并应用排序"""
        discovered_scripts = self.script_discovery.discover_scripts()
        
        # 现在处理新发现的脚本，只将之前未记录的脚本添加到排序数组的末尾
        current_script_ids = {script['id'] for script in discovered_scripts}
        saved_script_order = self.get_script_order()

        # 清理僵尸 ID：过滤掉磁盘上已不存在的脚本 ID
        cleaned_script_order = [sid for sid in saved_script_order if sid in current_script_ids]
        if len(cleaned_script_order) != len(saved_script_order):
            saved_script_order = cleaned_script_order
            # 同步写回 scriptOrder
            self.user_preferences.setdefault('layout', {})['scriptOrder'] = saved_script_order

            # 清理 scripts 字典中已不存在的脚本配置
            scripts_config = self.user_preferences.get('scripts', {})
            stale_script_ids = [sid for sid in scripts_config if sid not in current_script_ids]
            for sid in stale_script_ids:
                del scripts_config[sid]

            # 清理 id_mappings 中的失效映射
            id_mappings = self.user_preferences.get('id_mappings', {})
            stale_keys = [k for k, v in id_mappings.items() if v not in current_script_ids]
            for key in stale_keys:
                del id_mappings[key]

        # 找出新脚本（不在已保存的排序中的脚本）
        new_script_ids = [script_id for script_id in current_script_ids if script_id not in saved_script_order]
        
        # 将新脚本添加到排序数组的末尾，但只在有新脚本时才保存（避免覆盖用户手动排序）
        if new_script_ids:
            updated_script_order = saved_script_order + new_script_ids
            self.user_preferences.get("layout", {})["scriptOrder"] = updated_script_order
            saved_script_order = updated_script_order
        # 如果没有新脚本，我们不修改已保存的排序，继续使用当前的 saved_script_order
        
        # 现在对发现的脚本应用保存的排序
        self.scripts = self._apply_saved_script_order_list(discovered_scripts, saved_script_order)
        # 更新 script_organization 的脚本列表
        self.script_organization.scripts = self.scripts

        # 初始化分类排序：确保所有脚本的分类都在 categoryOrder 中
        layout_prefs = self.user_preferences.setdefault('layout', {})
        category_order = layout_prefs.setdefault('categoryOrder', [])
        
        # 收集当前所有脚本实际使用的分类
        for script in self.scripts:
            cat = script.get('category', '未分类')
            if cat and cat != '未分类':
                # 将新分类追加到 categoryOrder 末尾
                if cat not in category_order:
                    category_order.append(cat)

    def _apply_saved_script_order_list(self, scripts_list, order_list=None):
        """根据保存的排序对脚本列表进行排序"""
        if order_list is None:
            order_list = self.get_script_order()
            
        if order_list and len(order_list) > 0:
            # 创建一个映射，把ID映射到排序位置
            order_map = {}
            for index, id in enumerate(order_list):
                order_map[id] = index
            
            # 按照保存的顺序对脚本进行排序
            return sorted(scripts_list, key=lambda s: order_map.get(s['id'], float('inf')))
        else:
            # 如果没有保存的顺序，返回原列表
            return scripts_list



    def get_all_scripts(self) -> List[Dict[str, Any]]:
        """获取所有脚本（发现阶段已完成全部配置覆盖）"""
        # 重新发现脚本以确保最新状态
        self.discover_scripts()
        
        scripts = self.scripts.copy()
        
        # 只应用参数默认值（分类/图标已在 discover_scripts 中处理）
        for script in scripts:
            script_id = script['id']
            user_config = self.user_preferences.get('scripts', {}).get(script_id, {})
            if 'parameter_defaults' in user_config:
                param_map = {p['name']: p for p in script.get('parameters', [])}
                for param_name, saved_default in user_config['parameter_defaults'].items():
                    if param_name in param_map:
                        param_map[param_name]['defaultValue'] = saved_default
        
        return scripts

    def get_script_by_id(self, script_id: str) -> Optional[Dict[str, Any]]:
        """根据ID获取脚本"""
        for script in self.scripts:
            if script['id'] == script_id:
                return script
        return None

    def build_command(self, script: Dict[str, Any], params: Dict[str, Any]) -> str:
        """构建执行命令"""
        return self.script_metadata.build_command(script, params)

    def get_categories(self) -> List[str]:
        """获取所有分类"""
        return self.script_organization.get_categories()

    def search_scripts(self, query: str) -> List[Dict[str, Any]]:
        """搜索脚本"""
        return self.script_organization.search_scripts(query)

    def get_user_preferences(self) -> Dict[str, Any]:
        """获取用户偏好设置"""
        return self.user_preferences_manager.get_user_preferences()

    def save_user_preferences(self, preferences: Dict[str, Any]) -> bool:
        """保存用户偏好设置"""
        result = self.user_preferences_manager.save_user_preferences(preferences)
        # 更新所有模块持有的 user_preferences 引用，确保它们都指向最新的对象
        self.user_preferences = preferences
        self.script_discovery.user_preferences = self.user_preferences
        self.script_organization.user_preferences = self.user_preferences
        self.script_operations.user_preferences = self.user_preferences
        return result

    def load_user_preferences(self):
        """加载用户偏好设置"""
        self.user_preferences_manager.load_user_preferences()
        self.user_preferences = self.user_preferences_manager.user_preferences

    def add_custom_category(self, category_name):
        """添加自定义分类，并同步更新到排序列表"""
        result = self.script_organization.add_custom_category(category_name)
        if result:
            # 如果成功添加了一个新的自定义分类，也将其添加到排序列表的末尾
            layout_prefs = self.user_preferences.setdefault('layout', {})
            category_order = layout_prefs.setdefault('categoryOrder', [])
            if category_name not in category_order:
                category_order.append(category_name)
        
        self.save_user_preferences(self.user_preferences)
        return result

    def remove_custom_category(self, category_name):
        """移除分类（后端一步完成所有操作）"""
        # 在 user_profile 中删除分类 + 重置脚本（不写回 main.py，category 由 user_profile 管理）
        self.script_organization.remove_custom_category(category_name)

        # 保存配置
        self.save_user_preferences(self.user_preferences)
        return True

    def assign_script_to_category(self, script_id, category_name):
        """将脚本分配到指定分类"""
        result = self.script_organization.assign_script_to_category(script_id, category_name)
        return self.save_user_preferences(self.user_preferences)

    def update_script_metadata(self, script_id, metadata_changes):
        """更新脚本文件中的元数据"""
        # 传递获取脚本的函数给操作模块
        def get_script_by_id_func(id):
            return self.get_script_by_id(id)
        
        result = self.script_operations.update_script_metadata(script_id, metadata_changes, get_script_by_id_func)
        if result['success']:
            # 重新发现脚本以更新内存中的数据
            self.discover_scripts()
        return result

    def rename_script_folder(self, script_id, new_name):
        """重命名脚本文件夹并保存状态"""
        # 传递获取脚本的函数给操作模块
        def get_script_by_id_func(id):
            return self.get_script_by_id(id)
        
        result = self.script_operations.rename_script_folder(script_id, new_name, get_script_by_id_func)
        
        if result.get('success'):
            # 1. 首先，保存已在 script_operations 中被原子化修改的 user_preferences
            self.save_user_preferences(self.user_preferences)
            
            # 2. 然后，重新发现脚本。此时 discover_scripts 会读到刚保存的正确状态，
            #    从而正确排序，不会再把重命名的脚本视为新脚本。
            self.discover_scripts()
            
        return result

    def save_script_order(self, script_order):
        """保存脚本排序"""
        return self.script_organization.save_script_order(script_order, self.save_user_preferences)

    def get_script_order(self):
        """获取脚本排序"""
        return self.script_organization.get_script_order()

    def save_category_order(self, category_order):
        """保存分类排序"""
        return self.script_organization.save_category_order(category_order, self.save_user_preferences)

    def get_category_order(self):
        """获取分类排序"""
        return self.script_organization.get_category_order()

    def delete_script(self, script_id):
        """协调删除脚本的整个过程，包括文件和配置"""
        # 1. 获取脚本文件夹名称以备后用（用于清理id_mappings）
        script_to_delete = self.get_script_by_id(script_id)
        if not script_to_delete:
            return {"success": False, "error": f"找不到ID为 {script_id} 的脚本"}
        folder_name = Path(script_to_delete['file_path']).parent.name

        # 2. 删除脚本文件夹
        delete_result = self.script_operations.delete_script_folder(script_id, self.get_script_by_id)
        if not delete_result.get('success'):
            return delete_result

        # 3. 清理 user_preferences
        try:
            # 从 scriptOrder 移除
            if 'layout' in self.user_preferences and 'scriptOrder' in self.user_preferences['layout']:
                if script_id in self.user_preferences['layout']['scriptOrder']:
                    self.user_preferences['layout']['scriptOrder'].remove(script_id)

            # 从 scripts 配置中移除
            if 'scripts' in self.user_preferences and script_id in self.user_preferences['scripts']:
                del self.user_preferences['scripts'][script_id]

            # 从 id_mappings 中移除
            if 'id_mappings' in self.user_preferences and folder_name in self.user_preferences['id_mappings']:
                del self.user_preferences['id_mappings'][folder_name]

            # 4. 保存更新后的配置
            self.save_user_preferences(self.user_preferences)

            # 5. 重新扫描脚本以更新内存状态
            self.discover_scripts()

            return {"success": True, "message": f"脚本 '{folder_name}' 已被删除。"}
        except Exception as e:
            return {"success": False, "error": f"清理脚本配置时出错: {e}"}


    def save_script_setting(self, script_id, key, value):
        """保存单个脚本的特定设置，并在设置分类时确保同步"""
        if 'scripts' not in self.user_preferences:
            self.user_preferences['scripts'] = {}
        if script_id not in self.user_preferences['scripts']:
            self.user_preferences['scripts'][script_id] = {}
        
        self.user_preferences['scripts'][script_id][key] = value

        # 如果正在更改分类，确保新分类被注册到 categoryOrder
        if key == 'category' and value and value != '未分类':
            layout_prefs = self.user_preferences.setdefault('layout', {})
            category_order = layout_prefs.setdefault('categoryOrder', [])
            if value not in category_order:
                category_order.append(value)
                # 同时注册为自定义分类
                custom_categories = self.user_preferences.setdefault('custom_categories', [])
                if value not in custom_categories:
                    custom_categories.append(value)

        return self.save_user_preferences(self.user_preferences)

    def save_parameter_default(self, script_id, param_name, value):
        """保存特定脚本的特定参数的默认值"""
        scripts_config = self.user_preferences.setdefault('scripts', {})
        script_config = scripts_config.setdefault(script_id, {})
        param_defaults = script_config.setdefault('parameter_defaults', {})
        param_defaults[param_name] = value
        return self.save_user_preferences(self.user_preferences)