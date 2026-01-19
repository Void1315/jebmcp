# 🚀 JEBMCP: JEB & MCP

**JEBMCP** 将 **JEB 反编译能力** 与 **MCP (Model Context Protocol)** 相结合，提供高效的分析和自动化能力。  
它通过 **JSON-RPC / SSE / stdio** 与 JEB 交互，并提供一套 Python 脚本，帮助你完成方法调用关系获取、类/方法重命名、代码分析等任务。

---

## 🌟 目录

1. [简介](#简介)  
2. [客户端兼容性](#客户端兼容性)  
3. [安装](#安装)  
4. [使用方法](#使用方法)  
5. [项目结构](#项目结构)  
6. [批量重命名工具](#批量重命名工具)  
7. [许可证](#许可证)  
8. [更多资源](#更多资源)

---

## 🧐 简介

JEBMCP 主要特性：  
- 集成 JEB 与 MCP，支持项目分析与操作  
- 提供 Python 工具接口，便于自动化调用  
- 支持多种交互方式（JSON-RPC / SSE / stdio）  
- 支持方法/类重命名、调用关系追踪、反编译结果获取等功能  

---

## 💻 客户端兼容性

不同客户端对交互方式的支持情况：  

- **Claude / Claude code**  
  - 支持 SSE  
  - 支持 HTTP  
  - 支持 stdio  

- **Trae / Cursor / Vscode**  
  - 支持 stdio  

提示：  
- 使用 **Cursor / Trae / Vscode** 时，请确保 MCP 服务通过 `stdio` 模式运行。  
- 使用 **Claude / Claude code** 时，可以选择 `sse` 或 `http`，获得更灵活的交互方式。  

---

## ⚙️ 安装

1. 克隆仓库  
   ```bash
   git clone https://github.com/xi0yu/jebmcp.git
   ```

2. 进入项目目录  
   ```bash
   cd jebmcp
   ```

3. 安装依赖  
   确保已安装 Python 3.x，然后执行：  
   ```bash
   pip install -r requirements.txt
   ```

## 使用方法

### 方式一：Python 直接启动（SSE 协议）

适用于 Claude / Claude Code，使用 SSE 或 HTTP 协议直接启动 MCP 服务器：

**选项 1：SSE 传输（传统方式）**
```bash
python src/server.py --transport sse --host 127.0.0.1 --port 16162
```
注意：使用 Ctrl+C 关闭时可能会显示一些 CancelledError 警告，这是正常的，不影响服务器关闭。

**选项 2：HTTP 传输（推荐，关闭更干净）**
```bash
python src/server.py --transport http --host 127.0.0.1 --port 16162
```

启动后，在 Claude Code 中配置：

**SSE 传输配置：**
```json
{
   "mcpServers": {
      "jeb": {
         "url": "http://127.0.0.1:16162/sse"
      }
   }
}
```

**HTTP 传输配置：**
```json
{
   "mcpServers": {
      "jeb": {
         "url": "http://127.0.0.1:16162/mcp"
      }
   }
}
```

**注意**：启动前请确保已在 JEB 中加载 `MCP.py` 脚本。

### 方式二：使用 NPM 包（推荐）

**JEBMCP** 已发布到 NPM 官网，可以直接使用 `npx` 执行，无需下载本地 `server.py`：

```json
{
   "mcpServers": {
      "jeb": {
         "command": "npx",
         "args": ["-y", "@xi0yu/jebmcp-proxy"]
      }
   }
}
```

### 方式二：本地运行

1. 配置 MCP 服务
   - **Claude / Cursor / Trae** 在 AI 配置中配置 mcpServers 
   ```json
   {
      "mcpServers": {
         "jeb": {
            "command": "python",
            "args": [
               "${JEB_MCP_PATH}/server.py"
            ],
            "autoApprove": [
               "ping",
               "has_projects",
               "get_projects",
               "get_current_project_info",
               "get_current_app_manifest",
               "get_class_decompiled_code",
               "get_method_decompiled_code",
               "get_method_smali_code",
               "get_class_methods",
               "get_class_fields",
               "get_class_superclass",
               "get_class_interfaces",
               "get_class_type_tree",
               "get_method_callers",
               "get_method_overrides",
               "get_field_callers",
               "find_class",
               "find_method",
               "find_field",
               "parse_protobuf_class",
               "is_class_renamed",
               "is_method_renamed",
               "is_field_renamed",
               "is_package",
               "rename_class_name",
               "rename_method_name",
               "rename_field_name",
               "rename_local_variable",
               "set_parameter_name",
               "reset_parameter_name",
               "get_live_artifact_ids",
               "switch_active_artifact"
            ]
         }
      }
   }
   ```

   - **Claude 参考** [自定义 mcp 配置教程](https://docs.anthropic.com/zh-CN/docs/claude-code/mcp)
   ```bash
   # 使用claude code参考如下方式
   claude mcp add jeb -- "npx -y @xi0yu/jebmcp-proxy"
   ```


2. 在 JEB 中配置 MCP 服务（两种方式都需要）
   - 打开 JEB 客户端
   - 导航到 `工具` -> `脚本`
   - 加载 `MCP.py` 脚本

**注意**：无论使用哪种方式，都需要下载本项目中的 `MCP.py` 等文件到本地，供 JEB 执行。NPM 包只是替代了 `server.py` 的运行方式。

---

## 🛠️ 项目结构

### server.py
- **用途**：为 **Claude / Cursor / Trae** 等工具集成 MCP 提供服务端支持  
- **注意**：不是命令行工具，用户无需手动运行  

### MCP.py
- **用途**：通过 JEB 客户端脚本运行，调用 MCP 功能  
- **注意**：不支持直接命令行执行，需在 JEB 内部使用  

---

## 🏷️ 局部变量重命名工具

新增的 `rename_local_variable` 工具支持重命名方法中的局部变量。

### 功能说明

该工具可以重命名方法的反编译代码中的局部变量名称，帮助提高代码可读性。

### 参数说明

- `class_name`: 类签名，支持多种格式：
  - 纯类名：如 "MainActivity"
  - 包名+类名（点号格式）：如 "com.example.MainActivity"
  - JNI 格式签名：如 "Lcom/example/MainActivity;"
- `method_name`: 方法名称（如构造方法使用 `<init>`）
- `old_var_name`: 当前局部变量名
- `new_var_name`: 新的局部变量名

### 使用示例

```python
# 重命名构造方法中的局部变量
result = client.call("rename_local_variable", {
    "class_name": "com.example.MainActivity",
    "method_name": "<init>",
    "old_var_name": "arr_z",
    "new_var_name": "jacocoFlags"
})
```

### 返回结果

```json
{
    "success": true,
    "class_name": "com.example.MainActivity",
    "method_name": "<init>",
    "old_var_name": "arr_z",
    "new_var_name": "jacocoFlags",
    "message": "Local variable renamed successfully"
}
```

---

## 📝 许可证

[![Stars](https://img.shields.io/github/stars/xi0yu/jebmcp?style=social)](https://github.com/xi0yu/jebmcp/stargazers)
[![Forks](https://img.shields.io/github/forks/xi0yu/jebmcp?style=social)](https://github.com/xi0yu/jebmcp/network/members)
[![License](https://img.shields.io/badge/License-Apache%202.0-blue.svg)](https://opensource.org/licenses/Apache-2.0)

---

## ⭐ Star History

[![Star History Chart](https://api.star-history.com/svg?repos=xi0yu/jebmcp&type=Date)](https://www.star-history.com/#xi0yu/jebmcp&Date)

---

## 🌍 更多资源

- [JEB 官方文档](https://www.pnfsoftware.com/jeb/apidoc)  
- [MCP 文档](https://mcp-docs.cn/introduction)  

感谢使用 JEBMCP，希望它能帮助你更高效地进行逆向工程任务！
