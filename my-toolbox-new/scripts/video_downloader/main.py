import argparse
import os
import subprocess
import sys
from pathlib import Path

def get_metadata():
    """返回脚本的元数据，供工具箱自动生成UI界面。"""
    return {'name': '视频下载', 'description': '基于yt-dlp和ffmpeg，支持格式选择、内嵌字幕和元数据，自动合并音视频。', 'parameters': [{'name': 'url', 'label': '视频链接 (URL)', 'type': 'text', 'required': True, 'placeholder': '输入一个视频或播放列表的链接'}, {'name': 'output_path', 'label': '保存位置', 'type': 'folder', 'required': True, 'placeholder': '选择视频下载的目标文件夹'}, {'name': 'quality', 'label': '下载选项', 'type': 'choice', 'required': True, 'defaultValue': 'best_mp4', 'choices': [{'value': 'best_mp4', 'label': '最佳画质 (MP4)'}, {'value': 'best_webm', 'label': '最佳画质 (WebM)'}, {'value': '1080p_mp4', 'label': '1080p (MP4)'}, {'value': '720p_mp4', 'label': '720p (MP4)'}, {'value': 'audio_mp3', 'label': '仅音频 (MP3)'}]}, {'name': 'subtitles', 'label': '下载并内嵌字幕', 'type': 'boolean', 'defaultValue': True}, {'name': 'cookies', 'label': '使用浏览器Cookie (用于会员内容)', 'type': 'choice', 'defaultValue': 'none', 'choices': [{'value': 'none', 'label': '不使用'}, {'value': 'chrome', 'label': 'Chrome'}, {'value': 'firefox', 'label': 'Firefox'}, {'value': 'edge', 'label': 'Edge'}]}, {'name': 'use_config', 'label': '忽略以上选项，直接使用yt-dlp.conf文件', 'type': 'boolean', 'defaultValue': False}], 'category': '下载', 'icon': 'C:\\Users\\Night Shang\\Desktop\\gjx\\my-toolbox-new\\assets\\icons\\icon-mo.ico'}

def main():
    """主执行函数"""
    parser = argparse.ArgumentParser(description='增强版视频下载器')
    parser.add_argument('--url', type=str, required=True)
    parser.add_argument('--output_path', type=str, required=True)
    parser.add_argument('--quality', type=str, required=True)
    parser.add_argument('--subtitles', action='store_true')
    parser.add_argument('--cookies', type=str, default='none')
    parser.add_argument('--use_config', action='store_true')
    args = parser.parse_args()
    script_dir = Path(__file__).parent
    yt_dlp_exe = script_dir / 'yt-dlp.exe'
    ffmpeg_exe = script_dir / 'ffmpeg.exe'
    if not yt_dlp_exe.exists():
        print(f'❌ 错误: 未在脚本目录中找到 yt-dlp.exe 程序。\n')
        print(f'请确保 {yt_dlp_exe} 存在。\n')
        return
    cmd = [str(yt_dlp_exe)]
    print('🚀 开始构建下载命令...')
    if args.use_config:
        print("ℹ️ 检测到'使用yt-dlp.conf'选项，将忽略其他参数设置。\n")
        cmd.extend(['--paths', args.output_path])
    else:
        cmd.append('--no-config')
        print('ℹ️ 将忽略任何存在的 .conf 配置文件。\n')
        quality_map = {'best_mp4': 'bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best', 'best_webm': 'bestvideo[ext=webm]+bestaudio[ext=webm]/best[ext=webm]/best', '1080p_mp4': 'bestvideo[height<=1080][ext=mp4]+bestaudio[ext=m4a]/best[height<=1080][ext=mp4]/best', '720p_mp4': 'bestvideo[height<=720][ext=mp4]+bestaudio[ext=m4a]/best[height<=720][ext=mp4]/best'}
        if args.quality == 'audio_mp3':
            cmd.extend(['-x', '--audio-format', 'mp3', '--audio-quality', '0'])
            print('🎶 下载选项：仅音频 (MP3)\n')
        else:
            cmd.extend(['-f', quality_map.get(args.quality, 'best')])
            print(f'🎬 下载选项：{args.quality}\n')
        if args.subtitles:
            cmd.extend(['--write-subs', '--embed-subs', '--sub-langs', 'zh-Hans,en,ja,ko'])
            print('💬 字幕选项：下载并内嵌中英日韩字幕\n')
        cmd.extend(['--embed-metadata', '--embed-thumbnail'])
        print('🖼️ 元数据：将内嵌封面和视频信息\n')
        if args.cookies != 'none':
            cmd.extend(['--cookies-from-browser', args.cookies])
            print(f'🍪 Cookie选项：使用 {args.cookies} 浏览器\n')
        cmd.extend(['-o', os.path.join(args.output_path, '%(title)s [%(id)s].%(ext)s')])
    cmd.append(args.url)
    print('\n🔧 最终执行命令 (为简化已省略完整路径):')
    print(f"yt-dlp.exe {' '.join(cmd[1:])}")
    if not ffmpeg_exe.exists() and args.quality != 'audio_mp3':
        print('\n⚠️ 警告: 未在脚本目录中找到 ffmpeg.exe。\n')
        print('如果下载的视频需要合并音视频（例如1080p以上），操作可能会失败。\n')
    print('\n⏳ 开始执行下载，请稍候...\n')
    try:
        creationflags = subprocess.CREATE_NO_WINDOW if sys.platform == 'win32' else 0
        process = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, encoding='utf-8', errors='replace', creationflags=creationflags)
        while True:
            line = process.stdout.readline()
            if not line:
                break
            print(line.strip())
        process.wait()
        print('\n------------------------------------')
        if process.returncode == 0:
            print('🎉 任务成功完成！')
        else:
            print(f'❌ 任务失败，yt-dlp退出代码: {process.returncode}')
    except FileNotFoundError:
        print(f'❌ 致命错误: 无法启动 yt-dlp.exe。请检查程序是否存在且路径正确。\n')
    except Exception as e:
        print(f'❌ 发生未知错误: {e}\n')
if __name__ == '__main__':
    main()