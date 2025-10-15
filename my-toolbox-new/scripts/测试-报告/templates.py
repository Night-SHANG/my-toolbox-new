# templates.py

def get_report_template():
    """返回报告的字符串模板"""
    return """
# 每日报告 - {date}

## 心情
- {mood}

## 天气
- {weather}

## 备注
{notes}
"""
