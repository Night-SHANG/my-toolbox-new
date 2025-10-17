import argparse
import os
import sys
try:
    import qrcode
    from PIL import Image
except ImportError as e:
    missing_package = e.name
    print(f'错误：缺少必要的依赖包 -> {missing_package}')
    print(f'请在工具箱中为此脚本配置虚拟环境，并安装依赖: pip install "qrcode[pil]" ')
    sys.exit(1)

def get_metadata():
    """
    返回脚本的元数据，供工具箱UI使用。
    """
    return {'description': '根据输入的文本或URL链接，生成一个二维码图片文件。', 'dependencies': ['qrcode[pil]'], 'parameters': [{'name': 'data', 'type': 'text', 'label': '要编码的文本或URL', 'required': True, 'defaultValue': 'https://www.google.com'}, {'name': 'output_path', 'type': 'folder', 'label': '选择保存文件夹', 'required': True, 'defaultValue': ''}, {'name': 'box_size', 'type': 'number', 'label': '尺寸 (单个模块的像素数)', 'required': False, 'defaultValue': 10}, {'name': 'border', 'type': 'number', 'label': '边框宽度 (模块数)', 'required': False, 'defaultValue': 4}], 'category': '测试'}

def main():
    """
    主执行函数，用于生成和保存二维码。
    """
    parser = argparse.ArgumentParser(description='生成二维码图片。')
    parser.add_argument('--data', type=str, required=True, help='要编码到二维码中的数据')
    parser.add_argument('--output_path', type=str, required=True, help='保存二维码图片的文件路径')
    parser.add_argument('--box_size', type=int, default=10, help='每个模块的像素大小')
    parser.add_argument('--border', type=int, default=4, help='边框的模块宽度')
    args = parser.parse_args()
    output_folder = args.output_path
    output_filename = 'qrcode.png'
    full_save_path = os.path.join(output_folder, output_filename)
    if not os.path.exists(output_folder):
        print(f"输出目录 '{output_folder}' 不存在，正在尝试创建...")
        try:
            os.makedirs(output_folder)
            print(f'成功创建目录: {output_folder}')
        except OSError as e:
            print(f'❌ 创建目录失败: {e}')
            sys.exit(1)
    print(f'正在根据以下文本生成二维码: {args.data}')
    try:
        qr = qrcode.QRCode(version=1, error_correction=qrcode.constants.ERROR_CORRECT_L, box_size=args.box_size, border=args.border)
        qr.add_data(args.data)
        qr.make(fit=True)
        img = qr.make_image(fill_color='black', back_color='white')
        img.save(full_save_path)
        print(f'✅ 二维码已成功保存到: {os.path.abspath(full_save_path)}')
    except Exception as e:
        print(f'❌ 生成二维码时发生错误: {e}')
        sys.exit(1)
if __name__ == '__main__':
    main()