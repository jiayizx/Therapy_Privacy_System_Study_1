import streamlit as st
import os
import csv
from webapp.feedback_utils import (read_posthoc_survey_info_csv, get_user_selections)

# Constants
POSTHOC_SURVEY_INFO_FNAME = "posthoc_survey.csv"

def load_survey_info():
    """
    Load the survey info from the CSV file into session state.
    """
    # Load the survey info
    st.session_state.posthoc_survey_info = read_posthoc_survey_info_csv(POSTHOC_SURVEY_INFO_FNAME)

def post_survey_two():
    """ Main function for the post survey part 2 page. """
    # Ensure Prolific ID is available
    if 'prolific_id' not in st.session_state or st.session_state.prolific_id == '':
        st.warning("Please go back to the main page and enter your Prolific ID.")
        st.stop()

    # Ensure the first part of the survey has been completed
    if 'survey_1_completed' not in st.session_state:
        st.warning("Please complete the first part of the survey.")
        st.stop()

    load_survey_info()
    get_user_selections()

    st.rerun()