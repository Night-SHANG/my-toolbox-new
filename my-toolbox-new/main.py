"""
脚本工具箱 - 主入口
采用模块化架构，将核心功能实现为独立的CLI工具，
GUI前端作为控制器通过进程隔离的方式调用它们
"""
import webview
from core.api import Api


def main():
    api = Api()
    window = webview.create_window(
        "脚本工具箱", 
        "gui/index.html", 
        js_api=api, 
        width=1024, 
        height=768,
        min_size=(800, 600)
    )
    api.set_window(window)  # 使用方法而不是直接赋值
    
    # 启动应用
    webview.start(debug=False, gui='cef' if webview.settings.get('use_cef') else None)


if __name__ == '__main__':
    main()