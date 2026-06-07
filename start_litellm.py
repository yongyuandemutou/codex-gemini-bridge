import sys
import litellm
from litellm.proxy.proxy_cli import run_server

# 1. 备份原生的核心发包函数
original_acompletion = litellm.acompletion

# 2. 编写强行篡改参数的劫持函数
async def patched_acompletion(*args, **kwargs):
    if "messages" in kwargs:
        fixed = []
        for msg in kwargs["messages"]:
            # 【绝杀修复】：把惹祸的 tool 角色强行转化为普通用户对话，彻底骗过 Gemini 的校验
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
        # 把洗白后的数据强行塞回去
        kwargs["messages"] = fixed
        
    # 3. 带着完美的数据，调用真正的核心函数
    return await original_acompletion(*args, **kwargs)

# 4. 偷天换日：将 LiteLLM 的核心函数替换为我们的劫持函数
litellm.acompletion = patched_acompletion

# 5. 启动服务器
sys.argv = ["litellm", "--config", "config.yaml"]
if __name__ == "__main__":
    print("\n[🚀 终极补丁就绪] 成功挂载底层 acompletion 数据劫持钩子！\n")
    run_server()
