import argparse
try:
    import requests
    from ascii_magic import AsciiArt
except ImportError:
    print('错误：缺少 requests 或 ascii_magic 模块。')
    print('请在工具箱中为此脚本配置虚拟环境并安装依赖。')
    exit(1)

def get_metadata():
    """获取脚本元数据"""
    return {'name': 'github_user_info', 'description': '查询指定GitHub用户的信息，并将其头像转为字符画。', 'dependencies': ['requests', 'ascii_magic'], 'parameters': [{'name': 'username', 'type': 'text', 'label': 'GitHub 用户名', 'required': True, 'defaultValue': 'torvalds'}], 'category': '测试', 'icon': ''}

def main():
    parser = argparse.ArgumentParser(description='Fetch GitHub user info and ASCII art avatar.')
    parser.add_argument('--username', type=str, required=True)
    args = parser.parse_args()
    api_url = f'https://api.github.com/users/{args.username}'
    print(f'正在从 {api_url} 获取数据...')
    try:
        response = requests.get(api_url)
        response.raise_for_status()
        data = response.json()
        print('\n--- 用户信息 ---')
        print(f"名称: {data.get('name', 'N/A')}")
        print(f"用户名: {data.get('login', 'N/A')}")
        print(f"简介: {data.get('bio', '无')}")
        print(f"粉丝: {data.get('followers', 0)}")
        print(f"正在关注: {data.get('following', 0)}")
        print(f"公开仓库数: {data.get('public_repos', 0)}")
        print(f"主页: {data.get('html_url', 'N/A')}")
        print('-----------------')
        avatar_url = data.get('avatar_url')
        if avatar_url:
            print('\n正在生成头像字符画...')
            try:
                my_art = AsciiArt.from_url(avatar_url)
                my_art.to_terminal(columns=60)
                print('\n✅ 任务完成！')
            except Exception as art_error:
                print(f'\n❌ 无法生成字符画: {art_error}')
        else:
            print('\n该用户没有设置头像。')
    except requests.exceptions.RequestException as e:
        print(f'\n❌ 网络请求失败或用户不存在: {e}')
    except Exception as e:
        print(f'\n❌ 发生未知错误: {e}')
if __name__ == '__main__':
    main()