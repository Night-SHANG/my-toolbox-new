import argparse
import os
from pathlib import Path
try:
    import requests
    from bs4 import BeautifulSoup
    from snownlp import SnowNLP
    from wordcloud import WordCloud
    import jieba
except ImportError as e:
    print(f'错误：缺少必要的依赖包 -> {e.name}')
    print('请在工具箱中为此脚本配置虚拟环境，并安装所有声明的依赖。')
    exit(1)

def get_metadata():
    """返回脚本的元数据，供工具箱自动生成UI界面。"""
    return {'name': 'web_analyzer', 'description': '输入一个网址，提取正文进行情感分析，并生成中文词云图。', 'dependencies': ['requests', 'beautifulsoup4', 'snownlp', 'wordcloud', 'jieba'], 'parameters': [{'name': 'url', 'label': '目标网页URL', 'type': 'text', 'required': True, 'placeholder': '例如：https://www.bbc.com/zhongwen/simp'}, {'name': 'output_path', 'label': '词云图保存位置', 'type': 'folder', 'required': True, 'placeholder': '选择一个文件夹用于保存生成的图片'}, {'name': 'filename', 'label': '输出文件名', 'type': 'text', 'defaultValue': 'wordcloud.png', 'placeholder': '例如：my_word_cloud.png'}, {'name': 'font_path', 'label': '中文字体文件路径 (可选)', 'type': 'file', 'required': False, 'placeholder': '若不指定，程序会尝试使用默认字体'}], 'category': '测试', 'icon': 'C:\\Users\\Night Shang\\Desktop\\gjx\\my-toolbox-new\\assets\\icons\\icon-mo.ico'}

def main():
    """主执行函数"""
    parser = argparse.ArgumentParser(description='分析网页内容并生成词云图。')
    parser.add_argument('--url', type=str, required=True, help='目标网页URL')
    parser.add_argument('--output_path', type=str, required=True, help='词云图片保存文件夹')
    parser.add_argument('--filename', type=str, default='wordcloud.png', help='输出图片的文件名')
    parser.add_argument('--font_path', type=str, default=None, help='中文字体文件路径')
    args = parser.parse_args()
    print(f'🚀 开始分析网页: {args.url}')
    try:
        print('第一步：正在获取网页内容...')
        headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'}
        response = requests.get(args.url, headers=headers, timeout=15)
        response.raise_for_status()
        response.encoding = response.apparent_encoding
        print('✅ 内容获取成功！')
        print('\n第二步：正在使用 BeautifulSoup 提取正文...')
        soup = BeautifulSoup(response.text, 'html.parser')
        paragraphs = soup.find_all('p')
        text = '\n'.join([p.get_text() for p in paragraphs])
        if not text:
            print('⚠️ 警告：未能从 <p> 标签中提取到有效文本，尝试提取整个body。')
            text = soup.body.get_text()
        if not text.strip():
            print('❌ 错误：无法从网页中提取任何有效文本。\n')
            return
        print('✅ 文本提取成功！')
        print('\n第三步：正在使用 SnowNLP 进行情感分析...')
        s = SnowNLP(text)
        sentiment_score = s.sentiments
        sentiment_text = '正面' if sentiment_score > 0.6 else '负面' if sentiment_score < 0.4 else '中性'
        print(f'✅ 情感分析完成！倾向得分: {sentiment_score:.4f} ({sentiment_text})')
        print('\n第四步：正在使用 jieba 和 wordcloud 生成词云图...')
        word_list = jieba.cut(text)
        segmented_text = ' '.join(word_list)
        font_path = args.font_path
        if font_path and (not os.path.exists(font_path)):
            print(f'⚠️ 警告：提供的字体路径不存在: {font_path}。将尝试使用默认字体。\n')
            font_path = None
        if not font_path:
            print('ℹ️ 提示：未提供有效的中文字体路径。\n')
            print('如果生成的词云图中中文显示为方框，请在参数中指定一个有效的中文字体文件（.ttf 或 .otf）。\n')
            print('例如：C:\\Windows\\Fonts\\msyh.ttc (微软雅黑)\n')
        try:
            wc = WordCloud(width=800, height=600, background_color='white', font_path=font_path, scale=1.5).generate(segmented_text)
            output_file = Path(args.output_path) / args.filename
            print(f'\n第五步：正在保存图片到: {output_file}\n')
            wc.to_file(output_file)
            print(f'\n🎉 任务完成！词云图已成功保存。\n')
        except Exception as e:
            print(f'❌ 生成词云图时出错: {e}\n')
            print('❌ 这通常是因为没有找到合适的中文字体。请尝试在参数中明确指定一个字体文件路径。\n')
    except requests.exceptions.RequestException as e:
        print(f'❌ 网络请求失败: {e}\n')
    except Exception as e:
        print(f'❌ 发生未知错误: {e}\n')
if __name__ == '__main__':
    main()