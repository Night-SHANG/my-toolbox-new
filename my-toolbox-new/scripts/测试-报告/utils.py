# utils.py
import datetime

def get_current_date_str():
    """获取当前日期的字符串"""
    return datetime.date.today().isoformat()

def get_mock_weather():
    """返回一个模拟的天气数据"""
    return "晴朗"
