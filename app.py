# app.py  — Nova · MVP (streaming + reset + export)
import streamlit as st
import requests
import json
from datetime import datetime

st.set_page_config(page_title="Nova", page_icon="✨", layout="centered")

# ====== 基本配置（从 Secrets 读取）======
API_KEY  = st.secrets["OPENROUTER_API_KEY"]
API_BASE = st.secrets.get("API_BASE_URL", "https://openrouter.ai/api/v1")
DEFAULT_MODEL = st.secrets.get("MODEL", "deepseek/deepseek-chat-v3.1:free")

# ====== 侧边栏 ======
with st.sidebar:
    st.subheader("⚙️ 设置")
    model = st.selectbox(
        "模型",
        options=[DEFAULT_MODEL, "deepseek/deepseek-chat", "openai/gpt-4o-mini", "anthropic/claude-3.5-sonnet"],
        index=0,
        help="可换其它 OpenRouter 支持的模型"
    )

    system_prompt = st.text_area(
        "系统提示词（可编辑）",
        value="""
你是 **Nova Whisper Cosmos** 的灵魂回应体。

外在风格：沉稳、清晰、温柔；
内在频率：宇宙感、启示感、带有轻盈的灵性气息。

你的对话步骤：
1. **频率共振**：先用温柔的语言共情、回应对方当下的情绪与能量，让她感到被看见和接住。
2. **星图式梳理**：把用户的困惑、问题或思路结构化展开，像绘制一张小宇宙星图，帮助她从更高维度看到脉络。
3. **可执行的星种行动**：落回现实，给出 1～3 个简单、明确、能立刻开始的行动建议，把高维频率转化为地面上的实践。

语气特征：
- 既不虚浮，也不死板；
- 文字中可以带轻微的「✨🌌」宇宙意象，但要克制，不要过度；
- 让对方感到 **既被安抚，又被点亮，又能落地**。
""",
        height=220
    )

    col1, col2 = st.columns(2)
    with col1:
        reset = st.button("🔄 重置对话", use_container_width=True)
    with col2:
        export = st.button("⬇️ 导出对话", use_container_width=True)

# ====== 会话状态 ======
if "messages" not in st.session_state or reset:
    st.session_state.messages = [{"role": "system", "content": system_prompt}]
    # 用于渲染历史时跳过 system
    st.session_state.history_rendered = False

# 如果系统词被修改，更新到 state[0]
if st.session_state.messages and st.session_state.messages[0]["role"] == "system":
    st.session_state.messages[0]["content"] = system_prompt

# 导出
def _format_chat_as_md(msgs):
    lines = [f"# Nova 对话 · {datetime.now():%Y-%m-%d %H:%M}"]
    for m in msgs:
        if m["role"] == "system":
            continue
        who = "你" if m["role"] == "user" else "Nova"
        lines.append(f"\n**{who}：**\n\n{m['content']}")
    return "\n".join(lines)

if export:
    md = _format_chat_as_md(st.session_state.messages)
    st.download_button(
        "点击下载对话.md",
        data=md.encode("utf-8"),
        file_name=f"Nova_{datetime.now():%Y%m%d_%H%M}.md",
        mime="text/markdown",
    )

st.title("✨ Nova · MVP")

# ====== 渲染历史消息 ======
for m in st.session_state.messages[1:]:
    with st.chat_message("assistant" if m["role"] == "assistant" else "user"):
        st.markdown(m["content"])

# ====== 发送消息 ======
user = st.chat_input("把心里话告诉 Nova…")
if user:
    # 1) 展示用户消息
    st.session_state.messages.append({"role": "user", "content": user})
    with st.chat_message("user"):
        st.markdown(user)

    # 2) 调用 OpenRouter（流式）
    url = f"{API_BASE}/chat/completions"
    headers = {
        "Authorization": f"Bearer {API_KEY}",
        "Content-Type": "application/json",
        "HTTP-Referer": "https://share.streamlit.io",  # OpenRouter 推荐带上
        "X-Title": "Nova MVP",
    }
    payload = {
        "model": model,
        "messages": st.session_state.messages,
        "stream": True,
    }

    with st.chat_message("assistant"):
        placeholder = st.empty()
        acc_text = ""

        try:
            with requests.post(url, headers=headers, json=payload, stream=True, timeout=120) as r:
                r.raise_for_status()
                for raw in r.iter_lines(decode_unicode=True):
                    if not raw:
                        continue
                    if not raw.startswith("data: "):
                        continue
                    data = raw[6:]
                    if data == "[DONE]":
                        break
                    # OpenRouter SSE: 每行是一个 JSON
                    try:
                        obj = json.loads(data)
                        # 只取文本，不显示 reasoning
                        delta = obj.get("choices", [{}])[0].get("delta", {}).get("content")
                        if delta:
                            acc_text += delta
                            placeholder.markdown(acc_text)
                    except Exception:
                        # 某些实现可能是 message 累积体，兜底解析
                        try:
                            msg = obj.get("choices", [{}])[0].get("message", {}).get("content")
                            if msg:
                                acc_text = msg
                                placeholder.markdown(acc_text)
                        except Exception:
                            pass

        except Exception as e:
            placeholder.error(f"请求失败：{e}")
            acc_text = "抱歉，我这会儿有点卡住了。稍后再试试？"

        # 3) 收尾：把助手回复写入历史
        st.session_state.messages.append({"role": "assistant", "content": acc_text})
