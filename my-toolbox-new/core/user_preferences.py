"""
用户偏好管理器 - 负责用户偏好设置和配置管理
"""
import json
from pathlib import Path
from typing import Dict, Any


class UserPreferences:
    def __init__(self, user_profile_file: Path):
        self._user_profile_file = user_profile_file
        self.user_preferences = {}
        self.load_user_preferences()

    def get_user_preferences(self) -> Dict[str, Any]:
        """获取用户偏好设置"""
        return self.user_preferences

    def save_user_preferences(self, preferences: Dict[str, Any]) -> bool:
        """保存用户偏好设置"""
        try:
            self.user_preferences = preferences
            with open(self._user_profile_file, 'w', encoding='utf-8') as f:
                json.dump(preferences, f, ensure_ascii=False, indent=2)
            return True
        except Exception as e:
            print(f"保存用户偏好设置时出错: {e}")
            return False

    def load_user_preferences(self):
        """加载用户偏好设置"""
        if Path(self._user_profile_file).exists():
            try:
                with open(self._user_profile_file, 'r', encoding='utf-8') as f:
                    self.user_preferences = json.load(f)
            except Exception as e:
                print(f"加载用户偏好设置时出错: {e}")
                self.user_preferences = {}
        else:
            self.user_preferences = {
                "scripts": {},
                "layout": {},
                "favorites": [],
                "categories": {},
                "custom_categories": []  # 添加自定义分类，不包含系统分类
            }