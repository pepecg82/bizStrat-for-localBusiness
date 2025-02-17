from main import kickoff
import streamlit as st


st.title("Local Boost")
st.write(
    "Turn local reviews into real-world strategies—get instant insights to outsmart your competition and boost your business today."
)

user_biz_name = st.text_input("Enter a Business Name:")
if st.button("Submit"):
    # Call the function from main.py
    st.write("Creating Strategy Document...")
    result = kickoff(user_biz_name)

    print("---- Strategy Document ----")
    st.write("---- Strategy Document ----")
    st.write(result)
    # ... plus any other logic or Streamlit code


# If you have a function from your main code, you could call it here with `user_input`,
# then display results with st.write(...)
