import time

def get_metadata():
    """定义脚本的元数据"""
    return {'name': '计数测试-终止测试', 'description': '一个持续30秒的计数器，用于测试“终止任务”功能是否正常工作。', 'dependencies': [], 'parameters': [], 'category': '测试', 'icon': ''}

def main():
    print('--- 长时间任务测试开始 ---')
    print('本任务将每秒打印一个数字，持续30秒。请在此期间点击“终止任务”按钮。')
    for i in range(1, 31):
        print(f'计数: {i} / 30')
        time.sleep(1)
    print('\n--- 如果你看到了这条消息，说明“终止任务”没有生效 ---')
if __name__ == '__main__':
    main()