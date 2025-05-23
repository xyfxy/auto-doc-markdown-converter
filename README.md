# 智能文档解析与 Markdown 转换器 (Auto Doc Markdown Converter)

## 📖 简介

`智能文档解析与 Markdown 转换器` 是一个功能强大的工具，旨在帮助用户轻松地将常见的文档格式（如 `.docx` 和 `.pdf`）转换为结构清晰、易于阅读和编辑的 Markdown 文件。它利用先进的大型语言模型 (LLM) 技术，智能地识别文档中的标题层级（H1-H4）和段落，确保转换后的 Markdown 文件能够准确反映原文的逻辑结构。

无论您是需要处理单个文件还是批量转换整个目录中的文档，本工具都能提供高效、自动化的解决方案。

## ✨ 特性

*   **广泛的格式支持**: 支持处理微软 Word (`.docx`) 和可移植文档格式 (`.pdf`) 文件。
*   **精准文本提取**: 自动从源文档中提取纯文本内容，为后续分析做准备。
*   **LLM 智能分析**: 通过可配置的大型语言模型 API 对提取的文本进行深度分析，智能识别各级标题 (H1-H4) 和段落 (P)。
*   **高质量 Markdown 输出**: 将 LLM 分析后的结构化内容精确转换为符合标准的 Markdown 格式。
*   **便捷的命令行界面 (CLI)**: 提供简单易用的命令行工具，方便集成到自动化流程或直接使用。
*   **批量处理能力**: 支持对单个文件或整个目录下的所有受支持文件进行批量转换。
*   **详细日志记录**: 在处理过程中输出详细的日志信息，方便用户追踪进度、快速定位和排查潜在问题。

## 🛠️ 环境要求与安装

### 环境要求

*   **Python**: Python 3.8 或更高版本。
*   **操作系统**: 跨平台，可在 Windows, macOS, Linux 上运行。

### 安装步骤

1.  **克隆项目** (如果您直接获取了源代码):
    ```bash
    git clone https://github.com/your_username/auto_doc_markdown_converter.git
    cd auto_doc_markdown_converter
    ```

2.  **创建并激活虚拟环境** (强烈推荐):
    *   使用 `venv`:
        ```bash
        python -m venv .venv
        # Windows
        source .venv/Scripts/activate
        # macOS/Linux
        source .venv/bin/activate
        ```
    *   或使用 `conda`:
        ```bash
        conda create -n automd python=3.8  # 可指定 Python 版本
        conda activate automd
        ```

3.  **安装依赖**:
    项目的所有依赖都记录在 `requirements.txt` 文件中。请在激活虚拟环境后运行以下命令进行安装：
    ```bash
    pip install -r requirements.txt
    ```

## ⚙️ 配置

为了使本工具能够与大型语言模型 (LLM) API 正常通信，特别是针对阿里云百炼服务，您需要在运行程序前配置以下环境变量：

*   `LLM_API_KEY`: **必需项**。您的阿里云账户的 API 密钥 (AccessKey Secret)。请确保此密钥具有访问百炼服务的权限。您可以从阿里云控制台获取。
*   `LLM_API_ENDPOINT`: **必需项**。阿里云百炼服务的 API 端点。对于文本生成模型，通常的格式是 `https://bailian.aliyuncs.com/v2/models/apps/text_generation/do`。**强烈建议您从阿里云百炼控制台的应用详情或 API 文档中获取您账户和区域对应的准确端点地址。**
*   `LLM_MODEL_ID`: **可选项**。指定要使用的百炼模型 ID。如果未设置此环境变量，程序将默认使用 `qwen-plus` 模型。您可以根据需要在百炼平台选择其他兼容的模型 ID (例如 `qwen-turbo`, `qwen-max` 等) 并通过此环境变量指定。

**重要提示**: `LLM_API_KEY` 和 `LLM_API_ENDPOINT` 对于程序的核心功能（即文本分析和结构识别）至关重要。如果未正确设置，程序将无法启动或在尝试调用 LLM API 时失败。

**如何设置环境变量**:
*   **Linux/macOS**:
    *   临时设置 (当前终端会话有效):
        ```bash
        export LLM_API_KEY="您的阿里云AccessKeySecret"
        export LLM_API_ENDPOINT="您从阿里云控制台获取的准确API端点"
        export LLM_MODEL_ID="qwen-max" # 可选，示例为qwen-max
        ```
    *   永久设置: 将上述 `export` 命令添加到您的 shell 配置文件中 (例如 `~/.bashrc`, `~/.zshrc`)，然后重新加载配置文件 (例如 `source ~/.bashrc`) 或重启终端。
*   **Windows**:
    *   临时设置 (当前命令提示符会话有效):
        ```cmd
        set LLM_API_KEY="您的阿里云AccessKeySecret"
        set LLM_API_ENDPOINT="您从阿里云控制台获取的准确API端点"
        set LLM_MODEL_ID="qwen-max" # 可选，示例为qwen-max
        ```
    *   永久设置: 通过 "环境变量" 系统设置界面进行配置。

请确保从您的阿里云账户和百炼服务控制台获取准确的凭据和端点信息。

## 🚀 使用方法 (命令行界面 CLI)

本工具提供了一个命令行界面，方便您执行文档转换任务。

### 基本命令格式

```bash
python -m auto_doc_markdown_converter.main <input_path> <output_dir> [options]
```

### 参数说明

*   `<input_path>`: **必需参数**。
    *   指定输入文件的路径 (例如 `./mydoc.docx` 或 `../docs/report.pdf`)。
    *   或者，指定一个包含多个 `.docx` 和/或 `.pdf` 文件的目录路径 (例如 `./input_documents/`)。程序会自动查找并处理目录下的所有受支持文件。
*   `<output_dir>`: **必需参数**。
    *   指定用于保存生成的 Markdown (`.md`) 文件的目录路径 (例如 `./output_markdown/`)。
    *   如果指定的目录不存在，程序会自动尝试创建它。

### 选项说明

*   `-v`, `--verbose`: 可选参数。
    *   启用此选项后，程序会输出更详细的日志信息 (DEBUG 级别)，这对于追踪处理细节或进行问题排查非常有用。

### 示例

1.  **处理单个 `.docx` 文件**:
    ```bash
    python -m auto_doc_markdown_converter.main ./mydoc.docx ./markdown_output
    ```

2.  **处理单个 `.pdf` 文件并启用详细日志**:
    ```bash
    python -m auto_doc_markdown_converter.main /path/to/your/document.pdf ./markdown_output --verbose
    ```

3.  **处理指定目录下的所有受支持文件**:
    ```bash
    python -m auto_doc_markdown_converter.main ./input_document_folder/ ./processed_markdown_files/
    ```

## 🔄 工作流程

本工具处理文档的流程如下：

1.  **参数解析与环境检查**:
    *   程序首先解析用户通过命令行提供的输入路径、输出目录和选项。
    *   检查必要的环境变量 (`LLM_API_KEY`, `LLM_API_ENDPOINT`) 是否已设置。
    *   验证输入路径是否存在，并创建输出目录（如果尚不存在）。

2.  **文件发现与筛选**:
    *   如果输入路径是单个文件，则直接处理该文件。
    *   如果输入路径是一个目录，则遍历该目录，查找所有具有 `.docx` 或 `.pdf` 扩展名的文件。

3.  **针对每个文件的处理**:
    a.  **文本提取**: 根据文件类型（`.docx` 或 `.pdf`），调用相应的提取器从文件中读取并提取纯文本内容。
    b.  **LLM 内容分析**: 将提取出的纯文本发送给在环境变量中配置的大型语言模型 (LLM)。LLM 会对文本进行分析，并返回其识别出的文档结构信息，主要是各级标题 (H1-H4) 和段落 (P) 的标签及对应内容。
    c.  **Markdown 生成**: 根据 LLM 返回的结构化信息（例如 "H1: 这是主标题", "P: 这是一个段落。"），程序将其转换为标准的 Markdown 语法 (例如 `# 这是主标题`, `这是一个段落。`)。
    d.  **文件保存**: 将生成的 Markdown 内容保存到用户指定的输出目录中。输出的 Markdown 文件名将与原始输入文件名相同，但扩展名更改为 `.md` (例如，`mydoc.docx` 将被转换为 `mydoc.md`)。如果输出目录中已存在同名文件，它将被覆盖。

4.  **日志与完成报告**:
    *   在整个处理过程中，程序会通过控制台输出日志信息，包括当前正在处理的文件、遇到的任何警告或错误、以及最终的处理结果摘要。
    *   处理完成后，会显示成功处理的文件数量和发生错误的数量。

## ⚠️ 错误处理与日志

*   **健壮性**: 程序内置了对多种潜在错误的处理机制，包括：
    *   文件未找到或路径无效。
    *   读取文件或写入输出文件时的权限不足问题。
    *   调用 LLM API 失败（例如网络问题、API 密钥无效、端点错误、请求超时等）。
    *   LLM 返回的响应格式非预期或无法解析。
    *   不支持的文件类型。
*   **日志输出**:
    *   默认情况下，程序会输出 INFO 级别的日志信息，显示关键的处理步骤和结果。
    *   用户可以通过指定 `-v` 或 `--verbose` 选项来启用 DEBUG 级别的日志输出。这将提供更详尽的信息，有助于深入了解程序的内部运行状态和进行问题诊断。
    *   所有日志信息（包括时间戳、日志级别、模块名和消息内容）都会直接输出到控制台。

## 🚀 待办/未来功能 (TODO)

我们计划在未来的版本中继续改进和扩展此工具的功能：

*   **更广泛的 LLM 支持**: 增加对更多不同类型和提供商的大型语言模型 API 的支持。
*   **自定义 LLM Prompt**: 允许用户通过配置文件或命令行参数自定义发送给 LLM 的分析提示。
*   **多种输出格式**: 除了 Markdown，未来可能支持导出为 HTML 或其他格式。
*   **图形用户界面 (GUI)**: 开发一个用户友好的图形界面，使非技术用户也能轻松使用。
*   **更细致的结构识别**: 尝试识别列表、表格、代码块等更复杂的文档元素。
*   **配置文件支持**: 允许通过外部配置文件管理 LLM API 设置和其他程序选项。

## 🤝 贡献

我们欢迎并感谢所有形式的贡献！如果您对改进本项目有任何想法、建议或发现了 Bug，请随时通过以下方式参与：

*   **提交 Issue**: 在项目的 GitHub Issues 页面报告问题或提出功能请求。
*   **发起 Pull Request**: 如果您修复了 Bug 或实现了新功能，请遵循良好的代码风格并发起 Pull Request。建议在进行较大改动前先通过 Issue 与我们讨论。

## 📝 许可证

本项目基于 **MIT 许可证** 发布。有关详细信息，请参阅项目根目录下的 `LICENSE` 文件（如果存在）。

---
希望这个 README 对您有所帮助！
