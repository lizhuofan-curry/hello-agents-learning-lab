import streamlit as st


def main() -> None:
    st.set_page_config(
        page_title="AutoGen Web Test",
        page_icon="🧪",
        layout="centered",
    )

    st.title("AutoGen Web Test")
    st.write("这是 Engineer 自动生成并经过 Docker 测试的 Streamlit 应用。")
    st.success("Web App 运行成功！")


if __name__ == "__main__":
    main()