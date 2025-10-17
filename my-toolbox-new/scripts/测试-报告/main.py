import argparse
from utils import get_current_date_str, get_mock_weather
from templates import get_report_template

def get_metadata():
    """定义脚本的元数据"""
    return {'name': '测试-报告', 'description': '一个演示多文件脚本如何工作的示例。它会从辅助模块导入函数来生成一份报告。', 'dependencies': [], 'parameters': [{'name': 'mood', 'type': 'text', 'label': '今日心情', 'defaultValue': '不错'}, {'name': 'notes', 'type': 'textarea', 'label': '备注', 'placeholder': '记录一下今天发生的事吧...'}], 'category': '测试', 'icon': ''}

def main():
    parser = argparse.ArgumentParser(description='Daily Report Generator.')
    parser.add_argument('--mood', type=str, required=True)
    parser.add_argument('--notes', type=str, default='')
    args = parser.parse_args()
    report_date = get_current_date_str()
    weather = get_mock_weather()
    report_template = get_report_template()
    final_report = report_template.format(date=report_date, mood=args.mood, weather=weather, notes=args.notes)
    print('--- 您的每日报告已生成 ---')
    print(final_report)
    print('---------------------------')
if __name__ == '__main__':
    main()