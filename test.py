import streamlit as st

def main():
    st.title("Markdown Test")

    # Test markdown rendering
    st.markdown("# This is a heading")
    st.markdown("## This is a subheading")
    st.markdown("### This is a smaller subheading")
    st.markdown("**Bold text**")
    st.markdown("*Italic text*")
    st.markdown("- Bullet point 1\n- Bullet point 2")
    st.markdown("[Link to Streamlit](https://streamlit.io)")

if __name__ == "__main__":
    main()