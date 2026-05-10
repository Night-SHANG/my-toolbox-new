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
        'name': 'PDF 多功能工具',
        'description': '集成PDF转图片、图片转PDF、合并、拆分、提取文本五大功能，基于pymupdf。',
        'dependencies': ['pymupdf'],
        'parameters': [
            {
                'name': 'mode',
                'type': 'choice',
                'label': '操作模式',
                'required': True,
                'defaultValue': 'pdf_to_img',
                'choices': [
                    {'value': 'pdf_to_img', 'label': 'PDF → 图片 (批量)'},
                    {'value': 'img_to_pdf', 'label': '图片 → PDF'},
                    {'value': 'merge', 'label': '合并多个 PDF'},
                    {'value': 'split', 'label': '拆分 PDF (提取指定页)'},
                    {'value': 'extract_text', 'label': '提取文本'}
                ]
            },
            {
                'name': 'input_folder',
                'type': 'folder',
                'label': '输入文件夹',
                'required': False,
                'placeholder': '选择包含PDF或图片的文件夹',
                'showWhen': {'mode': ['pdf_to_img', 'img_to_pdf', 'merge']}
            },
            {
                'name': 'input_file',
                'type': 'file',
                'label': '输入文件',
                'required': False,
                'placeholder': '选择单个PDF文件',
                'showWhen': {'mode': ['split', 'extract_text']}
            },
            {
                'name': 'output_folder',
                'type': 'folder',
                'label': '输出文件夹',
                'required': True,
                'placeholder': '所有结果保存到此文件夹'
            },
            {
                'name': 'scale',
                'type': 'number',
                'label': '放大倍数',
                'defaultValue': 2,
                'placeholder': '默认2倍，数值越大越清晰',
                'showWhen': {'mode': ['pdf_to_img']}
            },
            {
                'name': 'page_range',
                'type': 'text',
                'label': '页码范围',
                'required': False,
                'placeholder': '例如: 1-3,5,7-10',
                'showWhen': {'mode': ['split']}
            },
            {
                'name': 'output_filename',
                'type': 'text',
                'label': '输出文件名',
                'required': False,
                'defaultValue': 'output',
                'placeholder': '无需后缀名，默认 output',
                'showWhen': {'mode': ['img_to_pdf', 'merge']}
            }
        ],
        'category': '工具',
        'icon': ''
    }


# ============================================================
# 功能实现
# ============================================================

def do_pdf_to_images(input_folder, output_folder, scale):
    """PDF → 图片：将文件夹下所有 PDF 按页导出为 PNG"""
    pdf_files = glob.glob(os.path.join(input_folder, '*.pdf'))
    if not pdf_files:
        print(f'❌ 在 {input_folder} 中未找到任何 PDF 文件。')
        return

    print(f'📄 找到 {len(pdf_files)} 个 PDF 文件，放大倍数: {scale}x\n')
    success = 0

    for pdf_file in pdf_files:
        filename = os.path.basename(pdf_file)
        folder_name = os.path.splitext(filename)[0]
        sub_folder = os.path.join(output_folder, folder_name)
        os.makedirs(sub_folder, exist_ok=True)

        try:
            doc = fitz.open(pdf_file)
            print(f'🔄 处理: {filename} ({len(doc)} 页)')
            for i, page in enumerate(doc):
                pix = page.get_pixmap(matrix=fitz.Matrix(scale, scale))
                pix.save(os.path.join(sub_folder, f'page_{i + 1:03d}.png'))
            doc.close()
            print(f'   ✅ 完成 → {sub_folder}')
            success += 1
        except Exception as e:
            print(f'   ❌ 失败: {e}')

    print(f'\n🎉 处理完成！成功 {success}/{len(pdf_files)} 个。')


def do_images_to_pdf(input_folder, output_folder, output_filename):
    """图片 → PDF：将文件夹下所有图片合成为一个 PDF"""
    extensions = ('*.png', '*.jpg', '*.jpeg', '*.bmp', '*.webp', '*.tiff')
    image_files = []
    for ext in extensions:
        image_files.extend(glob.glob(os.path.join(input_folder, ext)))

    # 按文件名排序，确保顺序正确
    image_files.sort()

    if not image_files:
        print(f'❌ 在 {input_folder} 中未找到任何图片文件。')
        print(f'   支持的格式: {", ".join(extensions)}')
        return

    print(f'🖼️ 找到 {len(image_files)} 张图片，开始合成 PDF...\n')

    doc = fitz.open()
    for i, img_path in enumerate(image_files):
        try:
            img = fitz.open(img_path)
            # 获取图片尺寸，创建对应大小的页面
            rect = img[0].rect
            pdf_bytes = img.convert_to_pdf()
            img.close()

            img_pdf = fitz.open('pdf', pdf_bytes)
            doc.insert_pdf(img_pdf)
            img_pdf.close()
            print(f'   [{i + 1}/{len(image_files)}] {os.path.basename(img_path)}')
        except Exception as e:
            print(f'   ⚠️ 跳过 {os.path.basename(img_path)}: {e}')

    output_path = os.path.join(output_folder, f'{output_filename}.pdf')
    doc.save(output_path)
    doc.close()
    print(f'\n✅ PDF 已生成 → {output_path}')


def do_merge_pdfs(input_folder, output_folder, output_filename):
    """合并 PDF：将文件夹下所有 PDF 合并为一个"""
    pdf_files = sorted(glob.glob(os.path.join(input_folder, '*.pdf')))

    if not pdf_files:
        print(f'❌ 在 {input_folder} 中未找到任何 PDF 文件。')
        return

    if len(pdf_files) < 2:
        print(f'⚠️ 只找到 1 个 PDF 文件，无需合并。')
        return

    print(f'📎 找到 {len(pdf_files)} 个 PDF 文件，开始合并...\n')

    merged = fitz.open()
    for i, pdf_file in enumerate(pdf_files):
        try:
            doc = fitz.open(pdf_file)
            merged.insert_pdf(doc)
            print(f'   [{i + 1}/{len(pdf_files)}] {os.path.basename(pdf_file)} ({len(doc)} 页)')
            doc.close()
        except Exception as e:
            print(f'   ⚠️ 跳过 {os.path.basename(pdf_file)}: {e}')

    output_path = os.path.join(output_folder, f'{output_filename}.pdf')
    total_pages = len(merged)
    merged.save(output_path)
    merged.close()
    print(f'\n✅ 合并完成 → {output_path} (共 {total_pages} 页)')


def do_split_pdf(input_file, output_folder, page_range):
    """拆分 PDF：从单个 PDF 中提取指定页码"""
    if not page_range:
        print('❌ 请在"页码范围"参数中指定要提取的页码。')
        print('   格式示例: 1-3,5,7-10')
        return

    # 解析页码范围
    pages = []
    try:
        for part in page_range.split(','):
            part = part.strip()
            if '-' in part:
                start, end = part.split('-', 1)
                pages.extend(range(int(start), int(end) + 1))
            else:
                pages.append(int(part))
    except ValueError:
        print(f'❌ 页码格式错误: "{page_range}"')
        print('   正确格式示例: 1-3,5,7-10')
        return

    try:
        doc = fitz.open(input_file)
        total = len(doc)
        print(f'📄 打开: {os.path.basename(input_file)} (共 {total} 页)')
        print(f'📋 提取页码: {pages}\n')

        new_doc = fitz.open()
        extracted = 0
        for p in pages:
            if 1 <= p <= total:
                new_doc.insert_pdf(doc, from_page=p - 1, to_page=p - 1)
                print(f'   ✅ 第 {p} 页')
                extracted += 1
            else:
                print(f'   ⚠️ 第 {p} 页不存在（共 {total} 页），跳过')

        if extracted > 0:
            base_name = os.path.splitext(os.path.basename(input_file))[0]
            output_path = os.path.join(output_folder, f'{base_name}_提取.pdf')
            new_doc.save(output_path)
            print(f'\n✅ 提取完成 → {output_path} (共 {extracted} 页)')
        else:
            print('\n❌ 没有提取到任何页面。')

        new_doc.close()
        doc.close()
    except Exception as e:
        print(f'❌ 处理失败: {e}')


def do_extract_text(input_file, output_folder):
    """提取文本：从 PDF 中提取所有文字并保存为 TXT"""
    try:
        doc = fitz.open(input_file)
        total = len(doc)
        print(f'📄 打开: {os.path.basename(input_file)} (共 {total} 页)\n')

        all_text = []
        for i, page in enumerate(doc):
            text = page.get_text()
            if text.strip():
                all_text.append(f'--- 第 {i + 1} 页 ---\n{text}')
                print(f'   第 {i + 1} 页: 提取到 {len(text)} 个字符')
            else:
                print(f'   第 {i + 1} 页: (无文字内容)')

        doc.close()

        if all_text:
            base_name = os.path.splitext(os.path.basename(input_file))[0]
            output_path = os.path.join(output_folder, f'{base_name}.txt')
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write('\n\n'.join(all_text))
            print(f'\n✅ 文本已保存 → {output_path}')
        else:
            print('\n⚠️ 该 PDF 中未提取到任何文字内容（可能是扫描件/图片PDF）。')
    except Exception as e:
        print(f'❌ 处理失败: {e}')


# ============================================================
# 主函数
# ============================================================

def main():
    parser = argparse.ArgumentParser(description='PDF多功能工具')
    parser.add_argument('--mode', type=str, required=True)
    parser.add_argument('--input_folder', type=str, default='')
    parser.add_argument('--input_file', type=str, default='')
    parser.add_argument('--output_folder', type=str, required=True)
    parser.add_argument('--scale', type=int, default=2)
    parser.add_argument('--page_range', type=str, default='')
    parser.add_argument('--output_filename', type=str, default='output')
    args = parser.parse_args()

    os.makedirs(args.output_folder, exist_ok=True)

    print(f'🔧 PDF 多功能工具\n')

    if args.mode == 'pdf_to_img':
        if not args.input_folder:
            print('❌ "PDF转图片"模式需要指定"输入文件夹"。')
            return
        do_pdf_to_images(args.input_folder, args.output_folder, args.scale)

    elif args.mode == 'img_to_pdf':
        if not args.input_folder:
            print('❌ "图片转PDF"模式需要指定"输入文件夹"。')
            return
        do_images_to_pdf(args.input_folder, args.output_folder, args.output_filename)

    elif args.mode == 'merge':
        if not args.input_folder:
            print('❌ "合并PDF"模式需要指定"输入文件夹"。')
            return
        do_merge_pdfs(args.input_folder, args.output_folder, args.output_filename)

    elif args.mode == 'split':
        if not args.input_file:
            print('❌ "拆分PDF"模式需要指定"输入文件"。')
            return
        do_split_pdf(args.input_file, args.output_folder, args.page_range)

    elif args.mode == 'extract_text':
        if not args.input_file:
            print('❌ "提取文本"模式需要指定"输入文件"。')
            return
        do_extract_text(args.input_file, args.output_folder)

    else:
        print(f'❌ 未知的操作模式: {args.mode}')

if __name__ == '__main__':
    main()
