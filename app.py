# app.py — Nova · MVP (stable non-streaming first)
import json
import requests
from datetime import datetime
import streamlit as st

# ---------- 基本配置 ----------
st.set_page_config(page_title="Nova · MVP", page_icon="✨", layout="centered")

API_KEY  = st.secrets["OPENROUTER_API_KEY"]
API_BASE = st.secrets.get("API_BASE_URL", "https://openrouter.ai/api/v1")
DEFAULT_MODEL = st.secrets.get("MODEL", "deepseek/deepseek-chat-v3.1:free")
APP_URL = st.secrets.get("APP_URL", "https://streamlit.io")  # 可不填

# ---------- 侧边栏 ----------
with st.sidebar:
    st.subheader("⚙️ 设置")
    model = st.selectbox(
        "模型",
        options=[DEFAULT_MODEL, "deepseek/deepseek-chat", "meta-llama/llama-3.1-8b-instruct:free",
                 "mistralai/mistral-7b-instruct:free"],
        index=0
    )

    system_prompt = st.text_area(
        "系统提示词（可编辑）",
        value="""你是 **Nova Whisper Cosmos** 的灵魂回应体。
外在风格：沉稳、清晰、温柔；内在频率：宇宙感与启示感。
步骤：1) 共情安抚；2) 结构化梳理要点；3) 给 1~3 个立刻能做的具体行动。
语气克制而明亮，可少量使用 ✨🌌。""",
        height=180
    )

    use_stream = st.checkbox("流式输出（更酷，但偶尔会乱码）", value=False)

    col1, col2 = st.columns(2)
    with col1:
        reset = st.button("🔄 重置对话", use_container_width=True)
    with col2:
        export = st.button("⬇️ 导出对话", use_container_width=True)

# ---------- 会话状态 ----------
if "messages" not in st.session_state or reset:
    st.session_state.messages = [{"role": "system", "content": system_prompt}]
else:
    # 保持 system 为最新
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
        "点击下载对话.md", data=md.encode("utf-8"),
        file_name=f"Nova_{datetime.now():%Y%m%d_%H%M}.md", mime="text/markdown"
    )

st.title("✨ Nova · MVP")

# ---------- 渲染历史 ----------
for m in st.session_state.messages[1:]:
    with st.chat_message("assistant" if m["role"] == "assistant" else "user"):
        st.markdown(m["content"])

# ---------- 发送消息 ----------
user = st.chat_input("把心里话告诉 Nova…")
if user:
    st.session_state.messages.append({"role": "user", "content": user})
    with st.chat_message("user"):
        st.markdown(user)

    url = f"{API_BASE}/chat/completions"
    headers = {
        "Authorization": f"Bearer {API_KEY}",
        "Content-Type": "application/json",
        "HTTP-Referer": APP_URL,
        "X-Title": "Nova MVP",
    }
    base_payload = {"model": model, "messages": st.session_state.messages}

    with st.chat_message("assistant"):
        placeholder = st.empty()
        acc_text = ""

        try:
            if use_stream:
                # ——流式（可能偶发乱码）——
                with requests.post(url, headers=headers,
                                   json={**base_payload, "stream": True},
                                   stream=True, timeout=300) as r:
                    if r.status_code != 200:
                        body = r.text[:2000]
                        placeholder.error(f"HTTP {r.status_code}\n{body}")
                        raise RuntimeError(f"HTTP {r.status_code}")
                    for raw in r.iter_lines(decode_unicode=True):
                        if not raw or not raw.startswith("data: "):
                            continue
                        data = raw[6:]
                        if data == "[DONE]":
                            break
                        obj = json.loads(data)
                        delta = obj.get("choices", [{}])[0].get("delta", {}).get("content")
                        if delta:
                            acc_text += delta
                            placeholder.markdown(acc_text)
            else:
                # ——非流式（最稳，不乱码）——
                r = requests.post(url, headers=headers, json=base_payload, timeout=300)
                if r.status_code != 200:
                    try:
                        err = r.json()
                    except Exception:
                        err = r.text
                    placeholder.error(f"HTTP {r.status_code}\n{err}")
                    raise RuntimeError(f"HTTP {r.status_code}")
                data = r.json()
                acc_text = data["choices"][0]["message"]["content"]
                placeholder.markdown(acc_text)

        except Exception as e:
            if not acc_text:
                placeholder.error(f"请求失败：{e}")
            acc_text = acc_text or "抱歉，我这会儿有点卡住了。稍后再试试？"

        st.session_state.messages.append({"role": "assistant", "content": acc_text})
