import argparse
import os
from pathlib import Path
try:
    from PIL import Image
except ImportError:
    print('错误：缺少 Pillow 模块。请在工具箱中为此脚本配置虚拟环境并安装依赖。')
    exit(1)

def get_metadata():
    """获取脚本元数据"""
    return {'name': 'image_converter', 'description': '将图片文件转换为不同的格式，如JPEG, PNG, WEBP等。', 'dependencies': ['Pillow'], 'parameters': [{'name': 'input_file', 'type': 'file', 'label': '源图片文件', 'required': True}, {'name': 'output_format', 'type': 'choice', 'label': '目标格式', 'choices': [{'value': 'JPEG', 'label': 'JPEG'}, {'value': 'PNG', 'label': 'PNG'}, {'value': 'WEBP', 'label': 'WEBP'}, {'value': 'GIF', 'label': 'GIF'}, {'value': 'BMP', 'label': 'BMP'}, {'value': 'ICO', 'label': 'ICO (图标)'}], 'defaultValue': 'JPEG'}, {'name': 'quality', 'type': 'number', 'label': '图片质量 (1-100)', 'defaultValue': 85, 'placeholder': '仅对JPEG/WEBP有效'}, {'name': 'keep_original', 'type': 'boolean', 'label': '保留原始文件', 'defaultValue': True}], 'category': '图片', 'icon': ''}

def main():
    parser = argparse.ArgumentParser(description='Image format converter.')
    parser.add_argument('--input_file', type=str, required=True)
    parser.add_argument('--output_format', type=str, required=True)
    parser.add_argument('--quality', type=int, default=85)
    parser.add_argument('--keep_original', action='store_true')
    args = parser.parse_args()
    input_path = Path(args.input_file)
    if not input_path.exists():
        print(f'错误：输入文件不存在: {input_path}')
        return
    try:
        print(f'正在打开图片: {input_path.name}...')
        img = Image.open(input_path)
        output_ext = args.output_format.lower()
        output_path = input_path.with_suffix(f'.{output_ext}')
        if input_path == output_path:
            print('目标格式与源格式相同，无需转换。')
            return
        print(f'正在转换为 {args.output_format} 格式...')
        save_params = {'quality': args.quality}
        if args.output_format.upper() in ['JPEG', 'BMP'] and img.mode in ('RGBA', 'P'):
            print('图片包含透明通道，将转换为RGB模式进行保存...')
            img = img.convert('RGB')
        if args.output_format.upper() not in ['JPEG', 'WEBP']:
            save_params.pop('quality', None)
        img.save(output_path, **save_params)
        print(f'✅ 转换成功！文件已保存至: {output_path}')
        if not args.keep_original:
            print(f'正在删除原始文件: {input_path.name}...')
            os.remove(input_path)
            print('原始文件已删除。')
    except Exception as e:
        print(f'❌ 处理图片时发生错误: {e}')
if __name__ == '__main__':
    main()