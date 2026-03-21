# -*- coding: utf-8 -*-
import argparse
import sys
import json
from pathlib import Path
import traceback

# 确保脚本目录在 Python 路径中，以便导入兄弟模块
sys.path.insert(0, str(Path(__file__).parent.resolve()))

try:
    from openai import OpenAI
    from markdown_parser import MarkdownParser, MarkdownRenderer, Node, Text
except ImportError as e:
    print(f"错误：无法导入必要的模块。请确保 'openai.py' 和 'markdown_parser.py' 与此脚本位于同一目录中。")
    print(f"详细信息: {e}")
    sys.exit(1)

def load_config_fallback() -> dict:
    """安全地加载 ../assets/config.json 文件作为回退配置。"""
    config_path = Path(__file__).parent.parent / "assets" / "config.json"
    if not config_path.is_file():
        return {}
    try:
        with open(config_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except (json.JSONDecodeError, IOError):
        print(f"警告：无法读取或解析回退配置文件: {config_path}")
        return {}

def parse_prompt_arguments(args_str: str) -> dict:
    """将逗号分隔的 key=value 字符串解析为字典。"""
    args_dict = {}
    if not args_str:
        return args_dict
    for pair in args_str.split(','):
        if '=' in pair:
            key, value = pair.split('=', 1)
            args_dict[key.strip()] = value.strip()
    return args_dict

def call_llm(client: OpenAI, model_id: str, prompt: str) -> str | None:
    """调用大语言模型并返回结果文本。"""
    print(f"  - 正在使用模型 '{model_id}' 调用 API...")
    try:
        response = client.chat.completions.create(
            model=model_id,
            messages=[{"role": "user", "content": prompt}]
        )
        if response.choices and len(response.choices) > 0:
            content = response.choices[0].message.content
            if content:
                return content.strip()
        print("  - 错误：API 返回了非预期的响应格式。")
        return None
    except Exception as e:
        print(f"  - 错误：API 请求期间发生错误: {e}")
        return None

def process_raw(text: str, client: OpenAI, model_id: str, prompt_template: str, prompt_args: dict) -> str | None:
    """原始模式处理：将整个文本作为单个单元进行转换。"""
    format_args = prompt_args.copy()
    format_args['text'] = text
    try:
        prompt = prompt_template.format(**format_args)
    except KeyError as e:
        print(f"错误：Prompt 模板缺少参数: {e}")
        return None
    
    return call_llm(client, model_id, prompt)

def _transform_node_recursive(node: Node, client: OpenAI, model_id: str, prompt_template: str, prompt_args: dict) -> Node:
    """递归遍历并转换 AST 节点。"""
    # 1. 如果是文本节点，则转换其内容
    if isinstance(node, Text):
        if not node.text.strip():
            return Text('')  # 保留空的或只有空格的文本节点
        
        print(f"  - 正在处理文本: \"{node.text[:40].strip()}...\"")
        
        # 使用与原始模式相同的格式化逻辑
        format_args = prompt_args.copy()
        format_args['text'] = node.text
        try:
            prompt = prompt_template.format(**format_args)
        except KeyError as e:
            print(f"  - 错误：为文本节点创建 prompt 时出错: {e}。将使用原始文本。")
            return Text(node.text)

        transformed_content = call_llm(client, model_id, prompt)
        
        if transformed_content is None:
            print(f"  - 警告：API 调用失败。将保留原始文本。")
            return Text(node.text)
            
        return Text(transformed_content)

    # 2. 如果是叶子节点但不是文本（例如 CodeBlock），则原样返回一个副本
    if not hasattr(node, 'children') or not node.children:
        args = node.__dict__.copy()
        args.pop('type', None)
        args.pop('parent', None)
        return node.__class__(**args)

    # 3. 如果是容器节点，则对其子节点进行递归转换
    new_children = [_transform_node_recursive(child, client, model_id, prompt_template, prompt_args) for child in node.children]
    
    # 创建一个具有已转换子节点的新容器节点
    new_node_args = node.__dict__.copy()
    new_node_args['children'] = new_children
    # The base 'Node' sets 'type' and 'parent', but they are not expected in the
    # constructors of subclasses like 'Heading'. We remove them before re-instantiating.
    new_node_args.pop('type', None)
    new_node_args.pop('parent', None)
    return node.__class__(**new_node_args)

def process_ast(text: str, client: OpenAI, model_id: str, prompt_template: str, prompt_args: dict) -> str | None:
    """AST 模式处理：解析、遍历、转换和重新渲染。"""
    parser = MarkdownParser()
    renderer = MarkdownRenderer()
    
    print("  - 正在将 Markdown 解析为 AST...")
    original_root = parser.parse(text)
    
    print("  - 正在递归转换 AST 节点...")
    transformed_root = _transform_node_recursive(original_root, client, model_id, prompt_template, prompt_args)
    
    print("  - 正在将新的 AST 渲染回 Markdown...")
    return renderer.render(transformed_root)

def main():
    parser = argparse.ArgumentParser(
        description="使用大语言模型（LLM）对 Markdown 文件或目录进行通用转换。",
        formatter_class=argparse.RawTextHelpFormatter
    )
    # --- I/O 参数 ---
    parser.add_argument('--input', required=True, help='输入的 Markdown 文件或目录路径。')
    parser.add_argument('--output', required=True, help='输出转换后的文件或目录路径。')
    
    # --- LLM 配置参数 ---
    parser.add_argument('--api-key', help='LLM API 密钥。如果未提供，将尝试从环境变量 OPENAI_API_KEY 读取。')
    parser.add_argument('--base-url', help='LLM API 的基础 URL。如果未提供，将尝试从环境变量 OPENAI_BASE_URL 读取。')
    parser.add_argument('--model-id', help='要使用的模型 ID。如果未提供，将从配置文件中读取。')
    
    # --- Prompt 参数 ---
    parser.add_argument('--prompt-template', required=True, help='包含转换指令的模板文件路径。模板中应包含 {text} 占位符。')
    parser.add_argument('--prompt-arguments', default='', help='用于填充模板的额外参数，格式为 "key1=value1,key2=value2"。')
    
    # --- 模式切换 ---
    parser.add_argument('--ast-node', action='store_true', help='启用 AST 节点模式。在此模式下，脚本将逐个处理文本节点以保留 Markdown 结构。')

    args = parser.parse_args()

    # --- 1. 准备路径和参数 ---
    input_path = Path(args.input)
    output_path = Path(args.output)
    prompt_template_path = Path(args.prompt_template)
    prompt_args = parse_prompt_arguments(args.prompt_arguments)

    if not input_path.exists():
        print(f"错误：输入路径不存在: {input_path}")
        sys.exit(1)
    if not prompt_template_path.is_file():
        print(f"错误：Prompt 模板文件不存在: {prompt_template_path}")
        sys.exit(1)

    with open(prompt_template_path, 'r', encoding='utf-8') as f:
        prompt_template = f.read()

    # --- 2. 初始化 LLM 客户端 (带回退逻辑) ---
    fallback_config = load_config_fallback()

    # 优先级: 命令行参数 > 配置文件 > 环境变量 (部分参数)
    api_key = args.api_key or fallback_config.get('api_key')
    base_url = args.base_url or fallback_config.get('base_url')
    model_id = args.model_id or fallback_config.get('model_id')

    if not model_id:
        print("错误：必须通过命令行参数 (--model-id) 或在 ../assets/config.json 文件中提供模型 ID。")
        sys.exit(1)

    try:
        client = OpenAI(api_key=api_key, base_url=base_url)
    except ValueError as e:
        print(f"错误：初始化 API 客户端失败: {e}")
        print("请确保通过命令行参数、../assets/config.json 或环境变量提供了 API 密钥。")
        sys.exit(1)

    # --- 3. 确定要处理的文件列表 ---
    files_to_process = []
    if input_path.is_dir():
        if not output_path.exists():
            output_path.mkdir(parents=True, exist_ok=True)
        elif not output_path.is_dir():
            print(f"错误：输入是目录，但输出不是目录: {output_path}")
            sys.exit(1)
        
        for file in sorted(input_path.glob('*.md')):
            files_to_process.append((file, output_path / file.name))
    elif input_path.is_file():
        if output_path.is_dir():
             # 如果输出是目录，则在其中创建同名文件
            output_path = output_path / input_path.name
        output_path.parent.mkdir(parents=True, exist_ok=True)
        files_to_process.append((input_path, output_path))
    
    if not files_to_process:
        print("未找到要处理的 Markdown 文件。")
        return

    # --- 4. 循环处理文件 ---
    print(f"--- 开始转换任务 ---")
    print(f"模式: {'AST 节点模式' if args.ast_node else '原始文本模式'}")
    print(f"找到 {len(files_to_process)} 个文件。")

    for src, dest in files_to_process:
        print(f"\n--- 正在处理: {src.name} ---")
        try:
            with open(src, 'r', encoding='utf-8') as f:
                source_text = f.read()

            if not source_text.strip():
                print("  - 文件为空，直接复制。")
                with open(dest, 'w', encoding='utf-8') as f:
                    f.write(source_text)
                continue

            if args.ast_node:
                transformed_text = process_ast(source_text, client, model_id, prompt_template, prompt_args)
            else:
                transformed_text = process_raw(source_text, client, model_id, prompt_template, prompt_args)

            if transformed_text is None:
                print(f"失败: {src.name}。转换失败。")
                continue

            with open(dest, 'w', encoding='utf-8') as f:
                f.write(transformed_text)
            print(f"成功: {src.name} -> {dest}")

        except Exception as e:
            print(f"处理文件 {src.name} 时发生意外错误: {e}")
            traceback.print_exc()

    print("\n--- 转换任务完成 ---")

if __name__ == "__main__":
    main()
