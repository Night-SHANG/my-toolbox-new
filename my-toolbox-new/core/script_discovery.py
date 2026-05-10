"""
脚本发现器 - 负责脚本的发现和加载
"""
import os
import hashlib
from pathlib import Path
import ast
from typing import List, Dict, Any, Optional
from core.icon_manager import IconManager


class ScriptDiscovery:
    def __init__(self, scripts_dir: Path, user_preferences: Dict[str, Any]):
        self._scripts_dir = scripts_dir
        self.user_preferences = user_preferences
        # 确保目录存在
        self._scripts_dir.mkdir(exist_ok=True)
    
    def discover_scripts(self) -> List[Dict[str, Any]]:
        """动态发现脚本（遵循 main.py 入口约定）"""
        discovered_scripts = []
        scripts_dir = Path(self._scripts_dir)
        icon_manager = IconManager(Path(__file__).parent.parent)  # 循环外复用同一实例

        if not scripts_dir.exists():
            scripts_dir.mkdir(exist_ok=True)
            return discovered_scripts

        for script_folder in scripts_dir.iterdir():
            if not script_folder.is_dir():
                continue

            entry_point_file = script_folder / "main.py"
            if not entry_point_file.exists():
                continue

            try:
                metadata = self._get_metadata_from_ast(entry_point_file)
                if metadata is None:
                    continue

                folder_name = script_folder.name
                # 注意：base_id 现在只基于文件夹，因为入口总是 main.py
                base_id = f"{folder_name}"
                
                # ID管理逻辑
                mapped_id = self._get_mapped_id(base_id)
                if mapped_id:
                    metadata['id'] = mapped_id
                else:
                    path_hash = hashlib.md5(base_id.encode('utf-8')).hexdigest()[:8]
                    generated_id = f"{folder_name.lower().replace(' ', '_')}_{path_hash}"
                    metadata['id'] = generated_id
                    self._record_id_mapping(base_id, generated_id)

                metadata['name'] = folder_name
                metadata['file_path'] = str(entry_point_file)

                script_id = metadata['id']
                scripts_config = self.user_preferences.setdefault('scripts', {})
                user_script_config = scripts_config.get(script_id, {})

                # === 分类：user_profile.json 是唯一权威源 ===
                if 'category' in user_script_config:
                    # 已有用户配置 → 直接使用，忽略 main.py
                    metadata['category'] = user_script_config['category']
                else:
                    # 首次发现 → 用 main.py 的默认值，并记录到 user_profile
                    default_category = metadata.get('category', '未分类')
                    metadata['category'] = default_category
                    scripts_config.setdefault(script_id, {})['category'] = default_category

                # === 图标：同样的单一源头逻辑 ===
                if user_script_config.get('icon'):
                    # 已有用户自定义图标 → 直接使用
                    metadata['icon'] = user_script_config['icon']
                else:
                    # 首次发现 → 使用自动发现的图标
                    metadata['icon'] = icon_manager.get_script_icon(script_folder)

                discovered_scripts.append(metadata)

            except Exception as e:
                print(f"解析脚本 {entry_point_file} 时出错: {e}")
        
        return discovered_scripts

    def _get_metadata_from_ast(self, file_path: Path) -> Optional[Dict[str, Any]]:
        """使用AST安全地从脚本文件中提取元数据"""
        with open(file_path, 'r', encoding='utf-8') as f:
            source = f.read()
        
        tree = ast.parse(source, filename=str(file_path))
        
        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef) and node.name == 'get_metadata':
                for sub_node in node.body:
                    if isinstance(sub_node, ast.Return):
                        # 安全地评估返回值
                        try:
                            metadata = ast.literal_eval(sub_node.value)
                            if isinstance(metadata, dict):
                                # 确保关键字段存在
                                metadata.setdefault('description', '暂无描述')
                                metadata.setdefault('parameters', [])
                                metadata.setdefault('dependencies', [])
                                return metadata
                        except (ValueError, TypeError, SyntaxError, MemoryError, RecursionError):
                            # 如果返回值不是一个字面量字典，则无法安全解析
                            return None
        return None

    def _get_mapped_id(self, base_id: str) -> Optional[str]:
        """获取基础ID对应的映射ID（用于处理文件夹重命名的情况）"""
        # 检查ID映射（如果存在的话）
        id_mappings = self.user_preferences.get('id_mappings', {})
        return id_mappings.get(base_id)

    def _record_id_mapping(self, base_id: str, mapped_id: str):
        """记录基础ID到映射ID的映射关系"""
        if "id_mappings" not in self.user_preferences:
            self.user_preferences["id_mappings"] = {}
        self.user_preferences["id_mappings"][base_id] = mapped_id

    def _find_icon_in_folder(self, folder_path):
        """在文件夹中查找图标文件"""
        for icon_file in folder_path.glob("*.ico"):
            return str(icon_file)
        for icon_file in folder_path.glob("*.png"):
            return str(icon_file)
        for icon_file in folder_path.glob("*.jpg"):
            return str(icon_file)
        for icon_file in folder_path.glob("*.jpeg"):
            return str(icon_file)
        for icon_file in folder_path.glob("*.gif"):
            return str(icon_file)
        for icon_file in folder_path.glob("*.svg"):
            return str(icon_file)
        return None

    def _get_default_icon_for_folder(self, folder_path):
        """获取文件夹的默认图标（优先使用文件夹内的图标，然后使用默认图标库）"""
        # 首先检查文件夹内是否有图标
        icon_path = self._find_icon_in_folder(folder_path)
        if icon_path:
            return icon_path
        
        # 如果没有找到，返回默认图标
        return ''  # 默认图标