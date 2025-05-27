# 智能文档解析与 Markdown 转换器 (Auto Doc Markdown Converter)

## 📖 简介

`智能文档解析与 Markdown 转换器` 是一个功能强大的工具，旨在帮助用户轻松地将常见的文档格式（如 `.docx` 和 `.pdf`）转换为结构清晰、易于阅读和编辑的 Markdown 文件。它利用先进的大型语言模型 (LLM) 技术，智能地识别文档中的标题层级（H1-H4）和段落，确保转换后的 Markdown 文件能够准确反映原文的逻辑结构。

无论您是需要处理单个文件还是批量转换整个目录中的文档，本工具都能提供高效、自动化的解决方案。

## ✨ 特性

*   **广泛的格式支持**: 支持处理微软 Word (`.docx`) 和可移植文档格式 (`.pdf`) 文件。
*   **精准文本提取**: 自动从源文档中提取纯文本内容，为后续分析做准备。
*   **LLM 智能分析**: 通过可配置的大型语言模型 API 对提取的文本进行深度分析，智能识别各级标题 (H1-H6) 和段落 (P)。
*   **高质量 Markdown 输出**: 将 LLM 分析后的结构化内容精确转换为符合标准的 Markdown 格式。
*   **便捷的命令行界面 (CLI)**: 提供简单易用的命令行工具，方便集成到自动化流程或直接使用。
*   **批量处理能力**: 支持对单个文件或整个目录下的所有受支持文件进行批量转换。
*   **详细日志记录**: 在处理过程中输出详细的日志信息，方便用户追踪进度、快速定位和排查潜在问题。
*   **并发处理长文档**: 对于超过特定长度的文档，能够并发向大模型发送请求，以提高处理速度。可通过环境变量 `MAX_CONCURRENT_LLM_REQUESTS` 配置并发数。
*   **Markdown 预览修复**: Web 应用中的 Markdown 预览功能已修复，现在能够正确渲染 Markdown 内容为 HTML 格式进行展示。

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

为了使本工具能够与阿里云 DashScope 的 OpenAI 兼容模式 API 正常通信，您需要在运行程序前配置以下环境变量：

*   `LLM_API_KEY`: **必需项**。您的阿里云 DashScope API 密钥。此密钥通常以 `sk-` 开头。
    *   示例: `LLM_API_KEY="sk-xxxxxxxxxxxxxxxxxxxxxxxxxxxx"` (请将 `sk-xxxxxxxxxxxxxxxxxxxxxxxxxxxx` 替换为您的真实密钥)。
*   `LLM_API_ENDPOINT`: **必需项**。阿里云 DashScope OpenAI 兼容模式的基础 URL。
    *   示例: `LLM_API_ENDPOINT="https://dashscope.aliyuncs.com/compatible-mode/v1"`
*   `LLM_MODEL_ID`: **可选项**。指定要使用的具体 LLM 模型 ID。如果未设置此环境变量，程序将默认使用 `qwen-plus` 模型。
    *   常用模型示例: `qwen-plus` (默认), `qwen-turbo`, `qwen-max`, `qwen-long`。请查阅最新的阿里云 DashScope 文档以获取可用模型列表和选择最适合您需求的模型。
    *   示例: `LLM_MODEL_ID="qwen-turbo"`
*   `LLM_API_CALL_TIMEOUT`: (可选) LLM API 调用的超时时间，单位为秒。默认为 `300` 秒 (5分钟)。根据您的网络情况和处理文本的复杂程度，您可能需要调整此值。
    *   示例: `LLM_API_CALL_TIMEOUT="180"` (设置为3分钟)
*   `MAX_CONCURRENT_LLM_REQUESTS`: **可选项**。指定在处理长文档时，可以同时向大型语言模型发送的并发请求的最大数量。默认值为 `5`。
    *   当文档内容较多，需要被分割成多个块进行处理时，此设置生效。
    *   增加此值可能会加快处理速度，但也可能增加系统负载和 API 请求频率。请根据您的机器性能和 API 服务商的速率限制进行调整。
    *   示例: `MAX_CONCURRENT_LLM_REQUESTS="10"`

**重要提示**:
*   `LLM_API_KEY` 和 `LLM_API_ENDPOINT` 是程序运行所必需的核心配置。如果未正确设置，程序将无法调用 LLM API，从而导致处理失败。
*   请确保从您的阿里云控制台的 **DashScope 服务**页面获取准确的 API 密钥。API 端点通常是固定的，但仍建议核对官方文档。

**如何设置环境变量**:
*   **Linux/macOS**:
    *   临时设置 (当前终端会话有效):
        ```bash
        export LLM_API_KEY="sk-xxxxxxxxxxxxxxxxxxxxxxxxxxxx"
        export LLM_API_ENDPOINT="https://dashscope.aliyuncs.com/compatible-mode/v1"
        export LLM_MODEL_ID="qwen-plus" # 可选
        export LLM_API_CALL_TIMEOUT="180" # 可选, 示例设置为3分钟
        export MAX_CONCURRENT_LLM_REQUESTS="5" # 可选, 默认值为5
        ```
    *   永久设置: 将上述 `export` 命令添加到您的 shell 配置文件中 (例如 `~/.bashrc`, `~/.zshrc`)，然后重新加载配置文件 (例如 `source ~/.bashrc`) 或重启终端。
*   **Windows**:
    *   临时设置 (当前命令提示符会话有效):
        ```cmd
        set LLM_API_KEY="sk-xxxxxxxxxxxxxxxxxxxxxxxxxxxx"
        set LLM_API_ENDPOINT="https://dashscope.aliyuncs.com/compatible-mode/v1"
        set LLM_MODEL_ID="qwen-plus" # 可选
        set LLM_API_CALL_TIMEOUT="180" # 可选, 示例设置为3分钟
        set MAX_CONCURRENT_LLM_REQUESTS="5" # 可选, 默认值为5
        ```
    *   永久设置: 通过 "环境变量" 系统设置界面进行配置。

请务必使用您自己的有效凭证替换示例中的占位符。

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

## 🌐 运行 Web 应用 (Flask)

除了命令行界面，本项目还提供了一个基于 Flask 的 Web 应用，允许用户通过浏览器上传文档并获取转换后的 Markdown。

### 前提条件

1.  **完成安装**: 请确保您已按照 [环境要求与安装](#️-环境要求与安装) 部分的说明完成了所有依赖的安装 (特别是 `Flask`，它已包含在 `requirements.txt` 中)。
2.  **配置环境变量**: 运行 Web 应用前，必须正确设置 [配置](#️-配置) 部分描述的环境变量 (`LLM_API_KEY`, `LLM_API_ENDPOINT`, 以及可选的 `LLM_MODEL_ID`)。这些变量对于 Web 应用的核心文档处理功能同样至关重要。

### 启动 Web 应用

您可以选择以下任一方式从项目的根目录启动 Flask 开发服务器：

**方式一：直接运行 `app.py`**

这种方式简单直接，适合快速启动。

```bash
# 确保您当前位于项目的根目录下
python webapp/app.py
```
启动后，应用通常会监听 `http://0.0.0.0:5000/` 或 `http://127.0.0.1:5000/`。控制台输出会显示确切的监听地址。

**方式二：使用 `flask run` 命令 (推荐)**

这是 Flask 官方推荐的启动开发服务器的方式，提供了更灵活的配置选项。

1.  **设置必要的环境变量** (只需在当前终端会话设置一次，或将其添加到您的 shell 配置文件中，如 `.bashrc`, `.zshrc` 等):

    *   **Linux/macOS**:
        ```bash
        export FLASK_APP=webapp/app.py
        export FLASK_ENV=development  # 启用调试模式，生产环境请勿使用
        ```
    *   **Windows (CMD)**:
        ```cmd
        set FLASK_APP=webapp\app.py
        set FLASK_ENV=development
        ```
    *   **Windows (PowerShell)**:
        ```powershell
        $env:FLASK_APP="webapp\app.py"
        $env:FLASK_ENV="development"
        ```
    *   **说明**:
        *   `FLASK_APP` 指向 Flask 应用的入口文件。
        *   `FLASK_ENV=development` 会启用调试模式，这在开发阶段非常有用，但在生产环境中不应使用。

2.  **运行 Flask 应用**:
    ```bash
    flask run --host=0.0.0.0 --port=5000
    ```
    *   `--host=0.0.0.0` 使服务器可以从网络中的任何 IP 地址访问（对于虚拟机或容器环境很方便），如果只想本机访问，可以省略或使用 `127.0.0.1`。
    *   `--port=5000` 指定监听端口，您可以根据需要更改。
    *   如果已设置 `FLASK_ENV=development`，则通常无需显式传递 `--debug` 选项给 `flask run`。

### 访问 Web 应用

启动成功后，打开您的 Web 浏览器，并访问控制台输出中显示的地址，通常是：

```
http://127.0.0.1:5000/
```

您应该能看到 "Flask Web App 正在运行!" 的消息。后续步骤将实现文件上传和下载的用户界面。

## 🧪 手动测试 Web 应用

在您按照前面的说明成功安装了所有依赖、配置了必要的环境变量并启动了 Flask Web 应用后，您可以按照以下步骤手动测试其功能。

**前提条件:**
1.  **Python 环境已配置**: 确保您的 Python 环境 (推荐 Python 3.8+) 已设置，并且项目的虚拟环境（如果使用）已激活。
2.  **依赖已安装**: 已在项目根目录下运行 `pip install -r requirements.txt`。
3.  **环境变量已设置**:
    *   `LLM_API_KEY`: 设置为您的有效 DashScope API 密钥。
    *   `LLM_API_ENDPOINT`: 设置为 DashScope OpenAI 兼容模式的基础 URL (例如, `https://dashscope.aliyuncs.com/compatible-mode/v1`)。
    *   `LLM_MODEL_ID`: (可选) 设置为您希望使用的模型 ID (例如, `qwen-plus`)。如果未设置，将使用默认模型。
    *   **注意**: 对于当前阶段的测试，如果您想完全模拟而不产生实际的 LLM API 调用费用，您可以临时修改 `auto_doc_markdown_converter/src/llm_processor.py` 文件，在 `analyze_text_with_llm` 函数的开头直接返回一个固定的模拟字符串，例如：
        ```python
        # auto_doc_markdown_converter/src/llm_processor.py
        def analyze_text_with_llm(text: str) -> Optional[str]: # 确保导入 Optional
            logger.info("LLM 分析被 Mock，返回固定模拟输出。")
            return "H1: 模拟标题\nP: 这是一个通过 Mock LLM 生成的模拟段落。"
            # ... (原有的真实 API 调用逻辑) ...
        ```
        测试完毕后，请记得移除或注释掉此 mock 代码以恢复真实 LLM 调用。
4.  **Web 应用已启动**: 按照 "[运行 Web 应用 (Flask)](#️-运行-web-应用-flask)" 部分的说明，已成功启动 Flask 开发服务器 (例如，通过 `python webapp/app.py`)。服务器应在控制台显示正在运行，并监听类似 `http://127.0.0.1:5000/` 的地址。

**测试步骤:**

1.  **访问 Web 界面**:
    *   打开您的 Web 浏览器 (推荐使用 Chrome, Firefox 等现代浏览器)。
    *   在地址栏输入 Flask 应用运行的地址 (通常是 `http://127.0.0.1:5000/`) 并回车。
    *   **预期结果**: 您应该能看到“智能文档清洗与 Markdown 转换工具”的页面，包含文件选择区域和“开始处理”按钮，并且页面样式已正确加载。

2.  **测试单个文件上传与处理**:
    *   准备一个小型、有效的 `.docx` 文件 (例如，内容为 "你好世界" 的 `test_doc.docx`)。
    *   点击页面上的“选择文件”或类似按钮，选择您准备的 `test_doc.docx` 文件。
    *   点击“开始处理”按钮。
    *   **预期行为与结果**:
        *   页面上的状态区域 (`uploadStatus`) 应依次显示类似“正在准备上传...”、“正在上传文件...”、“正在处理文件，请稍候...”、“处理完成！”的提示。
        *   在“处理结果”区域 (`resultsArea`)，应出现一个针对 `test_doc.docx` 的条目，显示：
            *   原始文件名。
            *   处理状态为“处理成功”。
            *   一个名为 `test_doc.md` (或类似) 的下载链接。
            *   一个“预览 Markdown”按钮。
        *   点击“预览 Markdown”按钮：页面上应在该条目下方动态加载并显示 Markdown 内容的预览。如果使用了上述的 LLM mock，预览内容应为：
            ```
            H1: 模拟标题
            P: 这是一个通过 Mock LLM 生成的模拟段落。
            ```
            (实际 Markdown 渲染后可能是： `# 模拟标题\n\n这是一个通过 Mock LLM 生成的模拟段落。`)
        *   点击下载链接：浏览器应开始下载 `test_doc.md` 文件。打开该文件，其内容应与预览内容一致。
    *   重复此步骤，但使用一个小型、有效的 `.pdf` 文件进行测试。预期行为和结果类似。

3.  **测试多个文件上传与处理**:
    *   准备一个 `.docx` 文件和一个 `.pdf` 文件。
    *   点击“选择文件”按钮，同时选中这两个文件。
    *   点击“开始处理”按钮。
    *   **预期行为与结果**:
        *   状态区域正常更新。
        *   “处理结果”区域应为这两个文件分别显示处理结果条目，每个条目都应包含成功的状态、下载链接和预览按钮。
        *   分别测试每个文件的下载和预览功能，应均能正常工作。

4.  **测试不支持的文件类型**:
    *   准备一个文本文件 (例如 `.txt`) 或图片文件 (例如 `.jpg`)。
    *   选择该文件并点击“开始处理”。
    *   **预期行为与结果**:
        *   在“处理结果”区域，该文件的条目应显示处理状态为“处理失败”，并给出类似“不支持的文件类型”的错误信息。

5.  **测试未选择文件即提交**:
    *   不选择任何文件，直接点击“开始处理”按钮。
    *   **预期行为与结果**:
        *   页面应给出提示，例如在“处理结果”区域显示“请至少选择一个文件。”。

**问题排查提示:**
*   如果在测试过程中遇到问题，请首先检查运行 Flask 应用的服务器控制台。通常，详细的错误信息和日志会输出在那里。
*   确认所有环境变量都已正确设置并对 Flask 应用可见。
*   打开浏览器的开发者工具 (通常按 F12)，检查“控制台 (Console)”和“网络 (Network)”面板，看是否有前端 JavaScript 错误或 API 请求失败的信息。

---

## 🔄 工作流程

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

### 注意：开发工具限制与未完成功能

在本次开发迭代中，我们遇到了一些底层开发工具在处理文件写入操作（特别是较大或较复杂的代码块）时的限制，表现为持续的超时或操作失败。这些限制阻碍了以下原计划功能的实现：

*   **文档内图片提取与转换**: 从 `.docx` 或 `.pdf` 文件中自动提取图片并将其转换为 Markdown 兼容格式的功能未能完成。
*   **文档内表格提取与转换**: 从 `.docx` 或 `.pdf` 文件中自动提取表格并将其转换为 Markdown 表格的功能未能完成。
*   **高级前端预览与交互**:
    *   **对照预览**: 实现让用户并排比较原始文档（如 DOCX 的 HTML 形式）和转换后 Markdown 的功能未能完成。
    *   **详细的 UI 处理反馈**: 在文件处理过程中提供更细致的前端状态更新的功能未能完成。

我们希望在未来的开发中，如果相关工具问题得到解决或有更稳定的开发环境，能够重新审视并实现这些有价值的功能。目前的版本主要集中在核心的文本结构分析和转换为 Markdown。

---
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
