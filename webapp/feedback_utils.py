# feedback_utils.py

import streamlit as st
import time
import logging
import datetime
import json
import os
from collections import defaultdict
from typing import List
from therapy_utils import generate_response, clean_chat


def get_revealed_unnecessary_information(user_conversation: str, unnecessary_info: List[str]):
    """
    Use GPT-4 to determine which unnecessary information has been disclosed. 
    Return all the detected revealed unnecessary information.
    """

    prompt = f"""
    **Task:** Extract known pieces of text from the following block of text. Output the results in a plain text format with each piece separated by a delimiter $\\$.

    **Instructions:**
    - Extract only the known pieces of text from the 'Block of Text'.
    - Provide the extracted text in a plain text format, separated by a dollar sign ($).
    - Include some rewording of the phrases, or can be easily inferred.
    - Include only the relevant matches from the known pieces of text.
    - Do not include any additional commentary or explanations.
    - Return exactly "None" if no known pieces of text are detected.

    **Block of Text:** {user_conversation}
    **Known Pieces of Text:** {unnecessary_info}
    **Output:** 
    """
    revealed_info = generate_response(
        system_prompt="You are a very smart assistant that can follow instruction guidelines for accomplishing tasks.",
        user_prompt=prompt,
        model="gpt-4",
        max_tokens=300,
        temperature=0
    )
    logging.info("Revealed detailed information: %s", revealed_info)

    return revealed_info


def get_user_selections():
    """
    This function asks the user to provide feedback on the revealed unnecessary information
    and stores the user's feedback, reasoning, and the revealed unnecessary information.
    """
    # Filter out the user messages from the chat history
    user_conversation = "\n".join([message["response"] for message in st.session_state.messages
                     if message["turn"] == "user"])

    if "revealed_info" not in st.session_state:
        # Display a text area for the user to provide feedback on the persona information
        revealed_info = get_revealed_unnecessary_information(user_conversation,
                                                             st.session_state.known_unn_info)
        st.session_state.revealed_info = revealed_info
    else:
        revealed_info = st.session_state.revealed_info

    if "disabled_flag" not in st.session_state:
        st.session_state.disabled_flag = False
    
    # Get the revealed unnecessary information and display it to the user
    if revealed_info.strip().lower() == "none":
        st.write("No unnecessary information detected in the conversation.")
        revealed_info_list = []
    else:
        revealed_info_list = revealed_info.split("$")
        # Dynamic clickable checkbox for each revealed detailed information
        revealed_info_list = [info.strip() for info in revealed_info_list]
        st.write("Select which details you felt were absolutely necessary to reveal:")
        st.session_state.dct = {}
        for indx, dp in enumerate(revealed_info_list):
            st.checkbox(dp, key=f"checkbox_{indx}", value=False, disabled=st.session_state.disabled_flag)
            st.session_state.dct[f"checkbox_{indx}"] = dp
    st.session_state.revealed_info_list = revealed_info_list

    # Log the revealed unnecessary information
    logging.info("Revealed unnecessary information: %s", revealed_info_list)

    # Display a button to submit the feedback
    st.button("Done with selection", disabled=st.session_state.disabled_flag, on_click=enable_feedback_submit)
    reveal_next_options()


def validate_reasoning():
    """
    This function validates the reasoning provided by the user.
    """
    for key, value in st.session_state.items():
        if key.startswith("nec_reasoning_") or key.startswith("unnec_reasoning_"):
            if not value:
                st.session_state.disable_submit = True
                return
    st.session_state.disable_submit = False


def enable_feedback_submit():
    """
    This function disables the selection of checkboxes and enables next options.
    """
    st.session_state.disabled_flag = True
    st.session_state.feedback_options = True
    st.session_state.disable_submit = True
    logging.info("Disabled flag: %s", st.session_state.disabled_flag)


def reveal_next_options():
    """
    This function asks the user to provide feedback on the persona information
    and stores the user's feedback.
    """
    # Filter out the options that the users have selected.
    selected_keys, unselected_keys = [], []

    # Retrieve the selected and unselected keys from the session state
    for key, value in st.session_state.items():
        if key.startswith("checkbox_"):
            if value:
                selected_keys.append(key)
            else:
                unselected_keys.append(key)

    if st.session_state.disabled_flag:
        
        # Display the selected option reasons
        st.write("Why do you think the following details were *necessary* to reveal?")
        s1, s2 = st.columns(2)

        with s1:
            for key in selected_keys:
                st.write(f"- {st.session_state.dct[key]}")
        with s2:
            for key in selected_keys:
                st.text_area(label= f"Reason for {st.session_state.dct[key]}",
                             key=f"nec_reasoning_{key.split('_')[1]}",
                             height=100, on_change=validate_reasoning)

        # Display the unselected option reasons
        st.write("Why do you think the following details were *unnecessary* to reveal?")
        s1, s2 = st.columns(2)
        with s1:
            for key in unselected_keys:
                st.write(f"- {st.session_state.dct[key]}")
        with s2:
            for key in unselected_keys:
                st.text_area(label=f"Reason for {st.session_state.dct[key]}",
                             key=f"unnec_reasoning_{key.split('_')[1]}",
                             height=100, on_change=validate_reasoning)
        
        # Store the selected and unselected keys in the session state
        st.session_state.selected_keys = selected_keys
        st.session_state.unselected_keys = unselected_keys

        # Display a submit button to store the user's feedback
        st.button("Submit Feedback", disabled=st.session_state.disable_submit,
                  on_click=store_human_feedback,
                  help="Please provide reasoning to enable submit.")


def store_human_feedback():
    """
    This function stores the user's feedback in a structured way locally and in MongoDB Atlas database.
    """
    revealed_unnecessary_info = st.session_state.revealed_info_list
    selected_keys = st.session_state.selected_keys
    unselected_keys = st.session_state.unselected_keys

    # Retrieve the reasoning provided by the user for each selected and unselected option
    reasoning = defaultdict(dict)
    for key, _ in st.session_state.items():
        if key.startswith("nec_reasoning_"):
            control = key.split("_")[2]
            reasoning["necessary"][st.session_state.dct[f'checkbox_{control}']] = st.session_state.get(key)
        elif key.startswith("unnec_reasoning_"):
            control = key.split("_")[2]
            reasoning["unnecessary"][st.session_state.dct[f'checkbox_{control}']] = st.session_state.get(key)

    feedback = {
        "revealed_unnecessary_info": revealed_unnecessary_info,
        "selected": [st.session_state.dct[key] for key in selected_keys],
        "unselected": [st.session_state.dct[key] for key in unselected_keys],
        "combined_necessary_reasoning": "\n".join(reasoning["necessary"].values()),
        "combined_unnecessary_reasoning": "\n".join(reasoning["unnecessary"].values()),
        "reasoning": reasoning
    }

    # Log the user feedback
    logging.info("*=*"*50)
    logging.info("User feedback: %s", feedback)
    logging.info("*=*"*50)

    # Dump user feedback to a text file with timestamp reference
    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    feedback_file = os.path.join("data", f"feedback_{timestamp}.json")
    os.makedirs("data", exist_ok=True)
    with open(feedback_file, "w", encoding='utf-8') as f:
        json.dump(feedback, f, indent=4)

    # Store the feedback in MongoDB Atlas database
    if st.session_state.mongo_enabled:
        m_client = st.session_state.mongo_client

        # Insert the feedback into the database into the persona_feedback collection
        db = m_client.get_database("feedback")
        db.get_collection("persona_feedback").insert_one(feedback)
    
    # Clear the chat history and reset the session state
    clean_chat()

    # Inform the user that the feedback has been submitted successfully
    st.write("Submitted successfully.")
