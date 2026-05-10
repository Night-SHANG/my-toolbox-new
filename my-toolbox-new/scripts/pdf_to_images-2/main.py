import argparse
import os
import glob
try:
    import fitz  # pymupdf
except ImportError as e:
    print(f'错误：缺少必要的依赖包 -> {e.name}')
    print('请在工具箱中为此脚本配置虚拟环境，并安装依赖: pip install pymupdf')
    exit(1)

def get_metadata():
    """获取脚本元数据"""
    return {
        'name': 'PDF 转图片',
        'description': '将指定文件夹下的所有PDF文件，按页转换为PNG图片。每个PDF会创建独立的子文件夹存放图片。',
        'dependencies': ['pymupdf'],
        'parameters': [
            {
                'name': 'source_dir',
                'type': 'folder',
                'label': 'PDF 所在文件夹',
                'required': True,
                'placeholder': '选择包含PDF文件的文件夹'
            },
            {
                'name': 'scale',
                'type': 'number',
                'label': '放大倍数',
                'defaultValue': 2,
                'placeholder': '默认2倍，数值越大越清晰，文件也越大'
            }
        ],
        'category': '工具',
        'icon': ''
    }

import sys

def main():
    # 强制标准输出使用 utf-8 编码，防止控制台打印 emoji 时报错
    sys.stdout.reconfigure(encoding='utf-8')
    parser = argparse.ArgumentParser(description='PDF批量转PNG图片')
    parser.add_argument('--source_dir', type=str, required=True)
    parser.add_argument('--scale', type=int, default=2)
    args = parser.parse_args()

    source_dir = args.source_dir
    scale = args.scale

    if not os.path.isdir(source_dir):
        print(f'❌ 错误：指定的文件夹不存在: {source_dir}')
        return

    # 获取目录下所有 PDF 文件
    pdf_files = glob.glob(os.path.join(source_dir, '*.pdf'))

    if not pdf_files:
        print(f'❌ 在 {source_dir} 中未找到任何 PDF 文件。')
        return

    print(f'📄 找到 {len(pdf_files)} 个 PDF 文件，放大倍数: {scale}x')
    print(f'   源目录: {source_dir}\n')

    success_count = 0
    fail_count = 0

    for pdf_file in pdf_files:
        filename = os.path.basename(pdf_file)
        folder_name = os.path.splitext(filename)[0]
        output_folder = os.path.join(source_dir, folder_name)

        if not os.path.exists(output_folder):
            os.makedirs(output_folder)

        try:
            doc = fitz.open(pdf_file)
            total_pages = len(doc)
            print(f'🔄 正在处理: {filename} ({total_pages} 页)')

            for i, page in enumerate(doc):
                try:
                    pix = page.get_pixmap(matrix=fitz.Matrix(scale, scale))
                    output_filename = f'page_{i + 1:03d}.png'
                    output_path = os.path.join(output_folder, output_filename)
                    pix.save(output_path)
                except Exception as e:
                    print(f'   ⚠️ 第 {i + 1} 页出错: {e}')

            doc.close()
            print(f'   ✅ 完成 → {output_folder}')
            success_count += 1

        except Exception as e:
            print(f'   ❌ 打开文件失败: {e}')
            fail_count += 1

    print(f'\n🎉 全部处理完成！成功 {success_count} 个，失败 {fail_count} 个。')

if __name__ == '__main__':
    main()
