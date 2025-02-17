from main import kickoff
import streamlit as st


st.title("Local Business AI")
st.write("Hello, world! This is a simple Streamlit front-end.")

user_biz_name = st.text_input("Enter a Business Name:")
if st.button("Submit"):
    # Call the function from main.py
    st.write("Creating Report...")
    result = kickoff(user_biz_name)

    print("---- Final Output ----")
    st.write("---- Final Output ----")
    st.write(result)
    # ... plus any other logic or Streamlit code


# If you have a function from your main code, you could call it here with `user_input`,
# then display results with st.write(...)
