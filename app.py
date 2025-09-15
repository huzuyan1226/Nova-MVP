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
