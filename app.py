import streamlit as st, requests, time

st.set_page_config(page_title="Nova", page_icon="✨", layout="centered")
st.title("✨ Nova · 心灵对话 MVP")

API_KEY = st.secrets["OPENROUTER_API_KEY"]
API_BASE = st.secrets.get("API_BASE_URL", "https://openrouter.ai/api/v1")
MODEL    = st.secrets.get("MODEL", "deepseek/deepseek-chat-v3.1:free")

if "messages" not in st.session_state:
    st.session_state.messages = [{"role":"system","content":"你是Nova，语气温柔但清醒，擅长共情+结构化建议。"}]

for m in st.session_state.messages:
    with st.chat_message("assistant" if m["role"]=="assistant" else "user"):
        st.markdown(m["content"])

user = st.chat_input("把心里话告诉 Nova…")
if user:
    st.session_state.messages.append({"role":"user","content":user})
    with st.chat_message("user"): st.markdown(user)
    with st.chat_message("assistant"):
        box = st.empty(); text=""
        headers={"Authorization":f"Bearer {API_KEY}","Content-Type":"application/json","HTTP-Referer":"https://share.streamlit.io","X-Title":"Nova"}
        payload={"model":MODEL,"messages":st.session_state.messages,"stream":True}
        with requests.post(f"{API_BASE}/chat/completions",headers=headers,json=payload,stream=True) as r:
            r.raise_for_status()
            for line in r.iter_lines():
                if not line or not line.startswith(b"data: "): continue
                data=line[6:]
                if data==b"[DONE]": break
                s=data.decode("utf-8")
                # 粗暴解析增量（够用就好）
                if '"content":' in s:
                    chunk=s.split('"content":')[-1].split('}')[0].strip().strip('"')
                    if chunk and chunk!="null":
                        text+=chunk; box.markdown(text)
                        time.sleep(0.002)
        st.session_state.messages.append({"role":"assistant","content":text})
