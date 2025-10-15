"""
图标管理器 - 处理脚本图标的获取、设置和管理
"""
import json
import os
from pathlib import Path
import shutil
from typing import Optional, Dict, Any, List


class IconManager:
    def __init__(self, base_dir: Path):
        self.base_dir = base_dir
        self.scripts_dir = base_dir / "scripts"
        self.assets_dir = base_dir / "assets"
        self.icons_dir = self.assets_dir / "icons"
        
        # 确保图标目录存在
        self.icons_dir.mkdir(parents=True, exist_ok=True)
        
        # 默认图标文件
        self.default_icon_path = self.icons_dir / "icon-mo.ico"
        self.error_icon_path = self.icons_dir / "debug.ico"

    def find_icon_in_folder(self, folder_path: Path) -> Optional[Path]:
        """
        在文件夹中查找图标文件，优先查找名为icon的文件
        """
        if not folder_path.exists():
            return None
            
        # 首先查找名为icon的图标文件
        for ext in ['.ico', '.png', '.jpg', '.jpeg', '.gif', '.svg']:
            icon_file = folder_path / f"icon{ext}"
            if icon_file.exists():
                return icon_file
        
        # 如果没有找到名为icon的文件，则查找其他图标文件
        for ext in ['.ico', '.png', '.jpg', '.jpeg', '.gif', '.svg']:
            for icon_file in folder_path.glob(f"*{ext}"):
                # 跳过临时文件或隐藏文件
                if icon_file.name.startswith('.'):
                    continue
                return icon_file
        
        return None

    def get_script_icon(self, script_folder_path: Path) -> str:
        """
        获取脚本的图标路径
        优先级：
        1. 用户自定义的图标（保存在用户配置中）
        2. 脚本文件夹内的图标文件（优先icon命名的文件）
        3. 默认图标（icon-mo.ico）
        """
        # 首先尝试在脚本文件夹中查找图标
        icon_path = self.find_icon_in_folder(script_folder_path)
        
        if icon_path:
            return str(icon_path)
        else:
            # 如果没有找到图标，返回默认图标
            if self.default_icon_path.exists():
                return str(self.default_icon_path)
            else:
                # 如果连默认图标都不存在，则返回空字符串
                return ""

    def set_custom_icon(self, script_folder_path: Path, icon_path: str) -> Dict[str, Any]:
        """
        设置脚本的自定义图标
        将图标文件复制到脚本文件夹并重命名为icon
        """
        try:
            script_folder_path = Path(script_folder_path) if isinstance(script_folder_path, str) else script_folder_path
            icon_path = Path(icon_path) if isinstance(icon_path, str) else icon_path
            
            if not icon_path.exists():
                return {"success": False, "error": "图标文件不存在"}
            
            # 获取图标文件扩展名
            ext = icon_path.suffix
            
            # 在脚本文件夹中创建新的图标文件
            new_icon_path = script_folder_path / f"icon{ext}"
            
            # 删除已存在的旧图标文件
            if new_icon_path.exists():
                new_icon_path.unlink()
            
            # 复制新图标到脚本文件夹
            shutil.copy2(icon_path, new_icon_path)
            
            return {
                "success": True,
                "icon_path": str(new_icon_path),
                "message": "图标设置成功"
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }

    def get_available_icons_in_folder(self, script_folder_path: Path) -> List[str]:
        """
        获取脚本文件夹中所有可用的图标文件
        """
        icons = []
        script_folder_path = Path(script_folder_path) if isinstance(script_folder_path, str) else script_folder_path
        
        for ext in ['.ico', '.png', '.jpg', '.jpeg', '.gif', '.svg']:
            for icon_file in script_folder_path.glob(f"*{ext}"):
                if not icon_file.name.startswith('.'):
                    icons.append(str(icon_file))
        
        # 按名称排序，但将icon命名的文件放在前面
        icons.sort(key=lambda x: (not Path(x).name.startswith('icon'), Path(x).name))
        
        return icons

    def get_default_icons(self) -> List[str]:
        """
        获取系统默认图标库
        """
        icons = []
        
        for ext in ['.ico', '.png', '.jpg', '.jpeg', '.gif', '.svg']:
            for icon_file in self.icons_dir.glob(f"*{ext}"):
                if not icon_file.name.startswith('.'):
                    icons.append(str(icon_file))
        
        return icons
    
    def get_error_icon_path(self) -> str:
        """
        获取错误图标路径
        """
        if self.error_icon_path.exists():
            return str(self.error_icon_path)
        else:
            return "❌"  # 默认错误图标