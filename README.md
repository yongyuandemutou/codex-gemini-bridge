# 🌉 Codex-Gemini-Bridge (Codex 桌面端完美接入 Gemini 指南)

本项目提供了一套轻量级、极客风的中间件解决方案。通过给 LiteLLM 打内存补丁，完美解决 OpenAI 最新版 Codex 桌面端（强制使用 `/v1/responses` 协议）与 Google Gemini API 在“工具调用 (Tool Calls)”与“历史记录校验”上的底层冲突。

实现效果：**让最强的开源大模型 (Gemini 3.1 Pro) 拥有四肢，完美接管 Codex 桌面端并执行本地计算机操作！**

## 🌟 核心特性
- **协议劫持**：无缝支持 Codex 最新的 `/v1/responses` 私有协议。
- **历史记录洗白补丁 (Monkey Patch)**：解决 Gemini 接口严苛的工具调用（Tool Calls）校验规则，防止报错 500。
- **工具冲突过滤**：自动剥离冲突的插件参数，确保本地代码执行器（MCP node_repl）顺畅运行。
- **沙盒隔离**：环境极度干净，对 macOS 系统零污染。

---

## 🛠️ 从零开始的安装指南 (Mac 专属)

假设你是一台全新的 Mac，请打开终端 (Terminal)，一步步执行以下操作：

### 第一步：安装基础环境
我们需要安装 `pipx`（用于创建纯净的 Python 沙盒环境）以及 `litellm` 中间件。

```bash
# 1. 安装 Homebrew (如果你的 Mac 还没有安装的话)
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"

# 2. 安装 pipx 并配置环境变量
brew install pipx
pipx ensurepath

# 3. 重新打开一个终端窗口，安装 LiteLLM
pipx install litellm
第二步：搭建代理专属工作区
在本地创建一个专属文件夹，存放我们的配置文件和补丁启动器。

mkdir -p ~/AI_Proxy
cd ~/AI_Proxy
1. 创建 config.yaml 文件
在 ~/AI_Proxy 目录下创建该文件，填入以下内容（注意替换你的真实 Gemini API Key）：

model_list:
  - model_name: gemini-3.1-pro-preview
    litellm_params:
      model: gemini/gemini-3.1-pro-preview
      api_key: "AIza你的真实_Gemini_API_Key填在这里"
      stream: false # 必须关闭流式输出以确保复杂工具的稳定执行
      drop_params: true
2. 创建核心补丁文件 start_litellm.py
在同一目录下创建该文件，填入以下 Python 代码：

import sys
import litellm
from litellm.proxy.proxy_cli import run_server

# 备份原生的发包函数
original_acompletion = litellm.acompletion

# 强行篡改参数的劫持函数 (Monkey Patch)
async def patched_acompletion(*args, **kwargs):
    if "messages" in kwargs:
        fixed = []
        for msg in kwargs["messages"]:
            # 【绝杀修复】：把 Codex 传来的残缺 tool 角色转化为普通用户对话，骗过 Gemini 校验
            if msg.get("role") == "tool":
                fixed.append({
                    "role": "user",
                    "content": f"[System: 本地工具执行结果反馈]\n{msg.get('content')}"
                })
            # 【防空修复】：防止有些 Assistant 消息为空报错
            elif msg.get("role") == "assistant":
                content = msg.get("content")
                if not content and not msg.get("tool_calls"):
                    msg["content"] = "正在处理中..."
                fixed.append(msg)
            else:
                fixed.append(msg)
        kwargs["messages"] = fixed
    return await original_acompletion(*args, **kwargs)

# 偷天换日挂载补丁
litellm.acompletion = patched_acompletion

# 启动服务器
sys.argv = ["litellm", "--config", "config.yaml"]
if __name__ == "__main__":
    print("\n[🚀 终极补丁就绪] 成功挂载底层 acompletion 数据劫持钩子！\n")
    run_server()
第三步：配置“一键启动”快捷命令
为了以后方便使用，我们将启动命令写入 Mac 的环境变量中：

echo 'alias start-ai="cd ~/AI_Proxy && ~/.local/pipx/venvs/litellm/bin/python start_litellm.py"' >> ~/.zshrc
source ~/.zshrc
以后你只需要在任何终端输入 start-ai 即可瞬间启动环境！

第四步：修改 Codex 桌面端配置
请先完全退出 Codex App (Cmd + Q)。
在终端执行 nano ~/.codex/config.toml 或用其他编辑器打开该文件，确保你的配置如下（关键部分不能漏）：

# 强制绑定自定义节点与模型
model = "gemini-3.1-pro-preview"
model_provider = "litellm"

[model_providers.litellm]
name = "LiteLLM Proxy"
base_url = "http://127.0.0.1:4000/v1"
wire_api = "responses"
requires_openai_auth = false
experimental_bearer_token = "sk-dummy"

# --- 下方保留你原有的 mcp_servers.node_repl 等环境探测配置 ---

# 【关键修复】务必关闭默认的浏览器插件，否则会触发 Gemini API 的工具冲突报错 (500)
[plugins."browser@openai-bundled"]
enabled = false
🎯 最终使用
打开终端，输入 start-ai，保持后台运行。
打开 Codex 桌面端，开始与 Gemini 一起编程！它现在可以读取你本地目录、执行脚本了！
