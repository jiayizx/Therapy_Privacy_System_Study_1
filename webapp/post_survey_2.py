import asyncio
import streamlit as st
import os
import csv
from feedback_utils import (read_posthoc_survey_info_csv, get_user_selections, log_info, get_survey_info)
import threading
from streamlit.runtime.scriptrunner import add_script_run_ctx

# Constants
POSTHOC_SURVEY_INFO_FNAME = "posthoc_survey.csv"

def load_survey_info():
    """
    Load the survey info from the CSV file into session state.
    """
    # Load the survey info
    st.session_state.posthoc_survey_info = read_posthoc_survey_info_csv(POSTHOC_SURVEY_INFO_FNAME)


def prep_survey_two():
    """ Prepare the survey for the second part of the survey. """

    # Filter out the user messages from the chat history
    if "user_conversation" not in st.session_state:
        st.session_state.user_conversation = "\n".join([message["response"] for message in st.session_state.messages
                     if message["turn"] == "user"])
    user_conversation = st.session_state.user_conversation

    # Log the user conversation
    log_info("User conversation: %s", user_conversation)
    log_info("Getting detections from user conversation")

    # Load the detections list
    load_survey_info()

    if "complete_detections" not in st.session_state:
        async def wrapper():
            st.session_state.complete_detections = await get_survey_info()
        
        thread = threading.Thread(target=lambda: asyncio.run(wrapper()))
        add_script_run_ctx(thread)
        thread.start()

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
