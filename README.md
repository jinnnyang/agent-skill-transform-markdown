# Transform Markdown Skill

This skill provides a powerful toolchain for splitting, transforming, and merging oversized Markdown documents that exceed the context limits of Large Language Models (LLMs). It supports any text-based operation, such as translation, summarization, or refinement, by leveraging LLMs.

## Core Concept: Split-Transform-Merge

The core idea is to break down a large, complex task into three manageable steps:

1.  **Split**: Use `scripts/split.py` to safely break a large Markdown file into smaller, format-preserving chunks.
2.  **Transform**: Use `scripts/transform.py` to process each chunk individually. This is where the LLM performs the desired text transformation.
3.  **Merge**: Use `scripts/merge.py` to seamlessly merge the processed chunks back into a single, final document.

## Key Features & Enhancements

The `transform.py` script is the core of this skill and has been enhanced with advanced context-aware features to solve common problems when processing split documents.

### Context-Aware Transformation

To address issues with text continuity and heading consistency across different chunks, `transform.py` now includes two powerful arguments:

-   `--lookback <int>`: Provides the LLM with the last `n` characters of the previously processed chunk. This allows the model to maintain sentence and paragraph continuity across file boundaries.
-   `--heading-adjustment`: Instructs the script to perform a pre-scan of all input files to generate a global document outline. This outline is then passed to the LLM, enabling it to intelligently adjust heading levels (`#`, `##`, etc.) in each chunk to ensure they are consistent with the overall document structure.

### How to Use the Advanced Features

To leverage these new capabilities, use the `context-aware-transform.md` prompt template along with the new arguments.

**Example Command:**

```bash
python scripts/transform.py ^
  --input "./cache/input_chunks/" ^
  --output "./cache/output_chunks/" ^
  --api-key "YOUR_API_KEY" ^
  --prompt-template "references/context-aware-transform.md" ^
  --prompt-arguments "source_lang=English,target_lang=Chinese" ^
  --ast-node ^
  --lookback 200 ^
  --heading-adjustment
```

This command instructs the script to:
- Process all chunks in the `input_chunks` directory.
- Use the `context-aware-transform.md` prompt, which is specifically designed to utilize the extra context.
- Look back 200 characters from the previous chunk (`--lookback 200`).
- Enable the global outline feature to adjust heading levels (`--heading-adjustment`).

By using this advanced workflow, the final merged document will have smoother transitions and a more coherent and consistent structure.
