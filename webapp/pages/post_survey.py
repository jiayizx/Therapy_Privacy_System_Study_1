import streamlit as st
from webapp.post_survey_1 import post_survey_one
from webapp.post_survey_2 import post_survey_two
from webapp.post_survey_3 import post_survey_three

def main():
    st.title("Post Survey")

    # Check if the first survey is completed
    if 'survey_1_completed' not in st.session_state:
        post_survey_one()
    elif 'survey_2_completed' not in st.session_state:
        post_survey_two()
    elif 'survey_3_completed' not in st.session_state:
        post_survey_three()
    

if __name__ == "__main__":
    main()
