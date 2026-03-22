---
name: transform-markdown
description: 提供一套强大的工具流，用于对超大型Markdown文档进行拆分、转换和合并，以突破LLM的上下文限制。支持任意基于LLM的文本操作，如翻译、总结、润色等。
---

# 技能：超大型Markdown文档处理工具流

本技能提供一套完整的命令行工具，用于对无法直接在LLM中处理的超大型Markdown文件进行“拆分-转换-合并”操作，同时提供高效的文档探查和局部读取能力。

## 何时使用

- 当您需要**翻译、总结或转换**一个体积过大、超出LLM上下文窗口的Markdown文件时。
- 当您想在不破坏Markdown格式的前提下，对文档中的**所有文本内容**进行精细化处理时。
- 当您需要快速**预览一个大型Markdown文件的结构**或只读取其中一小部分内容时。

## 核心概念：拆分-转换-合并 (Split-Transform-Merge)

本技能的核心思想是将一个复杂的大任务分解为三个简单步骤：

1.  **拆分 (Split)**: 使用 `split.py` 将一个巨大的Markdown文件安全地拆分成多个保留了原始格式的小文件块。
2.  **转换 (Transform)**: 使用 `transform.py` 逐个处理这些小文件块。您可以提供自定义的Prompt，让大语言模型（LLM）执行翻译、总结、润色等任何文本任务。
3.  **合并 (Merge)**: 使用 `merge.py` 将所有处理后的小文件块按原始顺序无缝地合并成一个最终的完整文档。

---

## 工作流

### 工作流 1: 完整的大型文档转换流程

这是一个典型的端到端翻译示例，您可以将其应用于任何文本转换任务。

#### **第 1 步: 拆分 (Split)**

假设您有一个名为 `my_book.md` 的大型文件。首先，使用 `split.py` 将其拆分。

```bash
# 将 my_book.md 拆分成大小约 4000 字符的块，并存入 ./cache/input_chunks/ 目录
python <transform-markdown-skill-path>/scripts/split.py --filename "my_book.md" --size 4000 --output-dir "./cache/input_chunks/"
```

#### **第 2 步: 转换 (Transform)**

现在，使用 `transform.py` 对每个小块进行翻译。`--ast-node` 参数是此步骤的关键，它能确保在翻译文本的同时，完美保留所有的Markdown格式（如列表、代码块、表格等）。

```bash
# 使用 --ast-node 模式处理 ./cache/input_chunks/ 目录中的所有文件
# 将翻译后的结果存入 ./cache/output_chunks/
python <transform-markdown-skill-path>/scripts/transform.py ^
  --input "./cache/input_chunks/" ^
  --output "./cache/output_chunks/" ^
  --api-key "YOUR_API_KEY" ^
  --base-url "https://api.example.com/v1" ^
  --model-id "gpt-4-turbo" ^
  --prompt-template "<transform-markdown-skill-path>/references/clean-and-translate.md" ^
  --prompt-arguments "source_lang=English,target_lang=Chinese" ^
  --ast-node
```
*   **提示**: 您可以修改 `references/clean-and-translate.md` 文件来定制您自己的Prompt。

#### **第 3 步: 合并 (Merge)**

最后，使用 `merge.py` 将所有翻译好的小块合并成最终的文档。

```bash
# 合并 ./cache/output_chunks/ 目录中的所有文件，并保存为 my_book_translated.md
python <transform-markdown-skill-path>/scripts/merge.py --input-dir "./cache/output_chunks/" --filename "my_book_translated.md"
```

---

### 工作流 3: 上下文感知的智能转换

这个高级工作流利用了 `--lookback` 和 `--heading-adjustment` 参数，以解决在处理拆分文档时遇到的两个核心问题：边界处的文本连续性和全局标题层级的一致性。

**使用场景**:
- 当您需要确保拆分块之间的句子和段落能够平滑过渡时。
- 当您需要自动纠正和统一合并后文档的标题层级时。

#### **第 1 步: 拆分 (Split)**

此步骤与标准工作流相同。

```bash
# 将 my_book.md 拆分成大小约 4000 字符的块
python <transform-markdown-skill-path>/scripts/split.py --filename "my_book.md" --size 4000 --output-dir "./cache/input_chunks/"
```

#### **第 2 步: 上下文感知转换 (Context-Aware Transform)**

这是此工作流的关键。我们使用新的参数和专门设计的 Prompt 模板。

```bash
# 使用 --lookback 和 --heading-adjustment 参数进行转换
python <transform-markdown-skill-path>/scripts/transform.py ^
  --input "./cache/input_chunks/" ^
  --output "./cache/output_chunks/" ^
  --api-key "YOUR_API_KEY" ^
  --base-url "https://api.example.com/v1" ^
  --model-id "gpt-4-turbo" ^
  --prompt-template "<transform-markdown-skill-path>/references/context-aware-transform.md" ^
  --prompt-arguments "source_lang=English,target_lang=Chinese" ^
  --ast-node ^
  --lookback 200 ^
  --heading-adjustment
```
*   `--lookback 200`: 在处理每个块时，向前看前一个块的最后 200 个字符，以确保句子连续性。
*   `--heading-adjustment`: 启用全局大纲分析，自动调整每个块中的标题级别。
*   `--prompt-template`: 使用 `context-aware-transform.md`，这个模板经过专门设计，可以指导 LLM 如何利用 `lookback` 和 `heading` 上下文。

#### **第 3 步: 合并 (Merge)**

此步骤与标准工作流相同。

```bash
# 合并所有处理好的块
python <transform-markdown-skill-path>/scripts/merge.py --input-dir "./cache/output_chunks/" --filename "my_book_translated_smart.md"
```

通过这个工作流，`my_book_translated_smart.md` 将拥有更流畅的文本过渡和更规范的标题结构。

---

### 工作流 2: 探查与局部读取

在处理一个未知的超大文件前，使用 `read.py` 可以帮您节省大量时间和Token。

#### **选项 1: 生成大纲**

使用 `--outline` 参数快速预览整个文档的标题结构和每个章节的行数范围。

```bash
python <transform-markdown-skill-path>/scripts/read.py --filename "my_very_large_document.md" --outline
```

**示例输出:**
```
--- 文件大纲 ---
- (行: 32) 杭州中德企业信用服务有限公司投资价值评估报告
  - (行: 34) 执行摘要
  - (行: 42) 一、公司基本情况
    - (行: 44) 1.1 工商信息
    - (行: 57) 1.2 央行备案资质
    - (行: 68) 1.3 股权结构
  - (行: 77) 二、企业征信行业分析
```

#### **选项 2: 读取指定范围**

在了解大纲后，使用 `--range` 参数只读取您感兴趣的部分。

```bash
# 只读取第 160 到 300 行的内容
python <transform-markdown-skill-path>/scripts/read.py --filename "my_very_large_document.md" --range 160-300
```

---

## 核心脚本概览

-   `markdown_parser.py`: **核心引擎**。一个强大的、从头构建的Markdown解析器和渲染器，为所有其他脚本提供AST（抽象语法树）处理能力。
-   `split.py`: **拆分器**。将一个大型Markdown文件安全地拆分成多个保留格式的小文件块。
-   `transform.py`: **转换器**。调用LLM对文件或文件块进行“原始”或“AST节点”模式的文本转换。现在支持上下文感知的转换，能够处理块之间的连续性和标题层级。
-   `merge.py`: **合并器**。将多个文件块按正确顺序无缝地合并成一个单一的Markdown文档。
-   `read.py`: **阅读器**。用于高效地生成大型Markdown文件的大纲或读取指定行范围。
-   `openai.py`: 一个无外部依赖的轻量级OpenAI API客户端。
