import streamlit as st
import requests

st.set_page_config(page_title="Nova", page_icon="✨", layout="centered")
st.title("✨ Nova · MVP")

# 从 Streamlit Secrets 里读配置
API_KEY  = st.secrets["OPENROUTER_API_KEY"]         # 必填：sk-or-xxxx
API_BASE = st.secrets.get("API_BASE_URL", "https://openrouter.ai/api/v1")
MODEL    = st.secrets.get("MODEL", "deepseek/deepseek-chat-v3.1:free")

if "messages" not in st.session_state:
    st.session_state.messages = [
        {"role": "system",
         "content": "你是Nova，语气温柔但清醒，先共情、再结构化梳理、给可执行的小步骤。"}
    ]

# 展示历史消息
for m in st.session_state.messages[1:]:
    with st.chat_message("assistant" if m["role"]=="assistant" else "user"):
        st.markdown(m["content"])

user = st.chat_input("把心里话告诉 Nova…")
if user:
    st.session_state.messages.append({"role":"user","content":user})
    with st.chat_message("user"): st.markdown(user)

    # 请求 OpenRouter（DeepSeek）
    url = f"{API_BASE}/chat/completions"
    headers = {
        "Authorization": f"Bearer {API_KEY}",
        "Content-Type": "application/json",
        # 建议加上下面两行（OpenRouter 推荐）
        "HTTP-Referer": "https://share.streamlit.io",
        "X-Title": "Nova MVP",
    }
    payload = {
        "model": MODEL,
        "messages": st.session_state.messages,
        "stream": False  # 不用流式，简单稳定
    }

    try:
        r = requests.post(url, headers=headers, json=payload, timeout=60)
        r.raise_for_status()
        data = r.json()

        # ✅ 只取文本，不展示 reasoning 字段
        content = data["choices"][0]["message"]["content"]
        with st.chat_message("assistant"): st.markdown(content)
        st.session_state.messages.append({"role":"assistant","content":content})

    except Exception as e:
        with st.chat_message("assistant"):
            st.error(f"请求失败：{e}")
