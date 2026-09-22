import streamlit as st

st.set_page_config(
    page_title="Docker Streamlit Test",
    page_icon="🐳"
)

st.title("🐳 Docker Streamlit 测试")

st.write("如果你能看到这个页面，说明 Streamlit 已经成功运行在 Docker 容器中。")

st.success("Docker + Streamlit 运行成功！")