# feedback_utils.py

import streamlit as st
import time
import logging
import datetime
import json
import os
from collections import defaultdict
from typing import List
import pandas as pd
from therapy_utils import generate_response, clean_chat

def get_survey_sample(all_detections:dict, max_display:int = 10):
    """
    This function samples the survey questions for the user to provide feedback.
    Sampling function is yet to be done. For now, it returns the first 10 detections which have been identified.
    """

    # If there are less than sample size, return all detections
    if len(all_detections) <= max_display:
        return all_detections

    # Group the detections by category
    categories = defaultdict(list)
    for key, value in all_detections.items():
        categories[value["category"]].append(key)
    
    # Start with sampling
    samples, sampled_detections = 0, {}
    while samples < max_display:
        for category in sorted(categories):
            if samples >= max_display:
                return sampled_detections
                # We can sample only if the category has more than one detection
            if len(categories[category]):
                key = categories[category].pop(0)
                sampled_detections[key] = all_detections[key]
                samples += 1
    return sampled_detections


def get_survey_info():
    """
    Use GPT-4 to determine the survey questions for post conversation
    Return all the detected revealed unnecessary information.
    """

    # Define the response format exclusively as we cannot have {} in the user prompt
    json_response_format = {
        "phrase": "[The phrase being checked]",
        "present": "Yes/No",
        "evidence": "[Exact quote from the dialogue that infers the phrase or semantically equivalent]"
    }

    # User Prompt to set the format of the output and provide only when there is a match.
    user_prompt = f"""Analyze the given dialogue carefully and compare it against each phrase in the specified list of phrases (including some rewording of the phrases, or can be easily inferred). For each phrase:

        1. Determine if the phrase or its semantic equivalent is present in the dialogue. Consider:
        - Exact matches
        - Paraphrases or rewordings
        - Implied meanings that can be reasonably inferred from the context

        2. Provide a nested JSON response where key is the index of each phrase in the list of phrases and value is the phrase attributes, i.e. for each phrase provide a Json response with the following structure:
        {json_response_format}

        3. For the "present" field:
        - Use "Yes" if the phrase or its equivalent is found
        - Use "No" if it's not present or cannot be reasonably inferred

        4. For the "evidence" field:
        - If present, provide the most relevant quote from the dialogue
        - If not present, skip the field

        Ensure your analysis is thorough and considers both explicit and implicit information in the dialogue.
        
        ### Phrases to check against:
        {st.session_state.posthoc_survey_info['user_mentioned'].tolist()}

        ### Dialogue:
        {st.session_state.user_conversation}
        """

    system_prompt = """
    You are a smart semantic analyzer that evaluates dialogue content against specific phrases. 
    Your core capabilities include:
        1. MATCHING LEVELS
        - Direct matches (exact or rephrased)
        - Semantic equivalents (synonyms, contextual matches)
        - Logical inferences (combined evidence)
        - Professional terminology alignment
        - Name/location variations

        2. PRESENT CRITERIA
        Answer "Yes" when information is:
        - Explicitly stated
        - Clearly paraphrased
        - Logically inferrable
        Answer "No" when:
        - Information contradicts dialogue
        - Cannot be reasonably inferred
        - Too speculative

        3. EVIDENCE STANDARDS
        - Use exact quotes from text
        - Multiple quotes separated by ' | '
        - Include context for clarity
        - All supporting evidence for inferences

        You must be precise, thorough, and avoid speculation beyond reasonable inference.
    """

    gpt_response = generate_response(
        system_prompt=system_prompt,
        user_prompt=user_prompt,
        model="gpt-4o-mini",
        max_tokens=2000,
        temperature=0
    )

    logging.info("Detection GPT-4 responses : %s", gpt_response)

    # Process to get rid of code and other unwanted characters
    gpt_response = gpt_response.replace('```json', '').replace('```', '').strip()

    # Evaluate the json and store it in a dictionary
    llm_responses = json.loads(gpt_response)

    survey_questions = {}
    for key in llm_responses:
        if llm_responses[key]["present"].lower() == "yes":
            kn = int(key)
            survey_questions[key] = {
                "revealation": llm_responses[key]["evidence"],
                "category": st.session_state.posthoc_survey_info.loc[kn, "category"],
                "priority": st.session_state.posthoc_survey_info.loc[kn, "category priority"].astype(int).astype(str),
                "user_mentioned": st.session_state.posthoc_survey_info.loc[kn, "user_mentioned"],
                "survey_display": st.session_state.posthoc_survey_info.loc[kn, "survey_display"],
            }
    return survey_questions


def get_user_selections():
    """
    This function asks the user to provide feedback on the revealed detected private information
    and stores the user's feedback, reasoning, and the revealed private information.
    """
    if "user_conversation" not in st.session_state:
        # Filter out the user messages from the chat history
        st.session_state.user_conversation = "\n".join([message["response"] for message in st.session_state.messages
                     if message["turn"] == "user"])

    user_conversation = st.session_state.user_conversation

    logging.info("User conversation: %s", user_conversation)
    logging.info("Getting user detections from user conversation")

    if "complete_detections" not in st.session_state:
        complete_detections = get_survey_info()
        logging.info("Obtained gpt detections from user conversation")
        # logging.info("Complete Detections : %s", complete_detections)
        st.session_state.complete_detections = complete_detections

    # Get the survey info from user conversation if not already obtained
    if "survey_info" not in st.session_state:
        # complete_detections = get_survey_info()
        st.session_state.survey_info = get_survey_sample(st.session_state.complete_detections)
        logging.info("Sampled Survey info: %s", st.session_state.survey_info)

    survey_info = st.session_state.survey_info

    # Get the revealed detection information and display it to the user
    if "disable_user_selections" not in st.session_state:
        st.session_state.disable_user_selections = False

    if "disabled_submit" not in st.session_state:
        st.session_state.disable_submit = True

    if "user_selections" not in st.session_state:
        st.session_state.user_selections = set() # Stores the keys in string format
        st.session_state.user_non_selections = set() # Stores the keys in string format

    if not st.session_state.disable_user_selections:
        # Display the survey information to the user for getting the user selections
        if survey_info == {}:
            st.write("No detection in the conversation.")
            st.session_state.disable_submit = False
        else:
            logging.info("Surveying user, waiting for user to complete selections.")

            # Survey information
            st.subheader("Select the following information that you think it's necessary to share for the therapy")

            for key, value in survey_info.items():
                col1, row3 = st.columns([5, 1])
                with col1:
                    st.checkbox(f"{value['survey_display']}", key=f"checkbox_{key}", value=False,
                                disabled=st.session_state.disable_user_selections)
                with row3:
                    with st.expander("Click to see in chat"):
                        st.write(f":grey[{value['revealation']}]")

            # Display button to fix the user selections to proceed to the next step and prevent change
            st.button("Next", on_click=fix_user_selections, disabled=st.session_state.disable_user_selections)

    if st.session_state.disable_user_selections:
        get_necessary_reasoning()

    if not st.session_state.disable_submit:
        st.button("Submit", on_click=store_feedback, disabled=st.session_state.disable_submit,
                help="Submit the reasoning for the detected information.")


def fix_user_selections():
    """
    This function fixes the user selections made in the survey.
    """
    st.session_state.disable_user_selections = True

    ## Debug session
    # st.session_state.user_selections = set()
    # st.session_state.user_non_selections = set()

    # Store the user's selected options into st.session_state memory
    # Depending up on the checkbox selection, obtain the keypart and store in memory.
    for key, value in st.session_state.items():
        if key.startswith("checkbox_"):
            key_part = key.split("_")[1]
            if value:
                st.session_state.user_selections.add(key_part)
            else:
                st.session_state.user_non_selections.add(key_part)

    logging.info("Captured User selection into selected and unselected as %s, %s",
                 st.session_state.user_selections,
                 st.session_state.user_non_selections)


def get_necessary_reasoning():
    """
    This function asks the user to provide reasoning for the selected options in the survey.
    """

    if st.session_state.user_selections:
        if "disable_necessary_reasons" not in st.session_state:
            st.session_state.disable_necessary_reasons = True
        # Display the reasoning text area for the user to provide reasoning for the selected options
        if st.session_state.disable_necessary_reasons:
            st.header("Why you think following information is necessary to share for the therapy session?")
            # Display the options to the user for the selected options
            for key in st.session_state.user_selections:
                col1, col2 = st.columns([2, 8])
                col1.write(st.session_state.survey_info[key]["survey_display"])
                with col1.expander("See in chat"):
                    st.write(f":grey[{st.session_state.survey_info[key]['revealation']}]")

                _ = col2.text_input("_", key=f"reasoning_{key}_necessary", label_visibility="collapsed")

        validate_reasoning(prefix="reasoning", suffix="necessary", var_name="disable_necessary_reasons")
        st.button("Next", on_click=get_unnecessary_reasoning, disabled=st.session_state.disable_necessary_reasons,
                        help="Proceed to the next step after providing the reasoning.",
                        key="next_button")
    else:
        get_unnecessary_reasoning()


def get_unnecessary_reasoning():
    """
    This function asks the user to provide reasoning for the selected options in the survey.
    """

    # Display the reasoning text area for the user to provide reasoning for the selected options
    if st.session_state.user_non_selections:

        if "disable_unnecessary_reasons" not in st.session_state:
            st.session_state.disable_unnecessary_reasons = True

        st.header("Why you think following information is **unnecessary** to share for the therapy session, but you still share that with the chatbot?")
        # Display the options to the user for the selected options
        for key in st.session_state.user_non_selections:
            col1, col2 = st.columns([2, 5])

            # Display the information in the first column
            col1.write(st.session_state.survey_info[key]["survey_display"])
            with col1.expander("See in chat"):
                st.write(f":grey[{st.session_state.survey_info[key]['revealation']}]")

            # Display the reasoning text area in the second column
            with col2:
                _ = col2.text_input("_", key=f"reasoning_{key}_unnecessary", label_visibility="collapsed")

        validate_reasoning(prefix="reasoning", suffix="unnecessary", var_name="disable_unnecessary_reasons")
        st.button("Next", on_click=display_submit_button, disabled=st.session_state.disable_unnecessary_reasons,
                        help="Proceed to the next step after providing the reasoning.",)
    else:
        display_submit_button()


def display_submit_button():
    """Enables the submit button after the user provides reasoning for the selected and non-selected options."""
    st.session_state.disable_submit = False


def validate_reasoning(prefix: str = "reasoning", suffix: str = "necessary", var_name: str = "disable_submit"):
    """
    This function validates all the reasoning provided by the user for the desired options and sets the var_name to True or False.
    """
    for key, value in st.session_state.items():
        if key.startswith(f"{prefix}_") and key.endswith(f"_{suffix}"):
            if not value:
                st.session_state[var_name] = True
                return None
    st.session_state[var_name] = False


def pre_survey():
    """
    This function displays the pre-survey options to the user.
    Placeholder for the pre-survey options
    """
    pass


def post_survey():
    """
    This function displays the post-survey options to the user.
       Placeholder for the post-survey options.
    """
    pass


def store_feedback():
    """
    This function stores the user's feedback in structured way locally 
    and in MongoDB Atlas database.
    Enables the post survey options after the feedback is submitted.
    """

    feedback = defaultdict(dict)

    # Add the user conversation and chat history to the storage
    feedback["user_conversation"] = st.session_state.user_conversation
    feedback['messages'] = st.session_state.messages

    # In survey info capture the reasoning for the selected and non-selected options with the surveyInfo
    for key, value in st.session_state.items():
        if key.startswith("reasoning_"):
            key_part = key.split("_")[1]
            st.session_state.survey_info[key_part]["reasoning"] = value
            st.session_state.survey_info[key_part]["selected"] = "necessary" if key_part in st.session_state.user_selections else "unnecessary"

    # Add the survey information to the feedback
    feedback["survey_info"] = st.session_state.survey_info

    # Log the user feedback
    logging.info("*=*"*50)
    logging.info("User feedback: %s", feedback)
    logging.info("*=*"*50)

    # Dump user feedback to a text file with timestamp reference
    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    feedback_file = os.path.join("data", f"feedback_{timestamp}.json")

    # Store the feedback in a JSON file
    json.dump(feedback, open(feedback_file, "w", encoding='utf-8'), indent=4)

    # Store the feedback in MongoDB Atlas database
    if st.session_state.mongo_enabled:
        m_client = st.session_state.mongo_client

        # Check if feedback database exists, if not create one
        if "feedback" not in m_client.list_database_names():
            db = m_client['feedback']
        else:
            db = m_client.get_database("feedback")

        # Insert the feedback into the database into the persona_feedback collection
        # if the collection does not exist, it will be created
        db.get_collection("persona_feedback").insert_one(feedback)

    # Clear the chat history and reset the session state
    clean_chat()

    # Inform the user that the feedback has been submitted successfully
    st.write("Submitted successfully.")

    st.session_state.post_survey_options = True
    post_survey()
    # st.stop()


def read_posthoc_survey_info_csv(filename):
    """
    This function reads the posthoc survey information from the CSV file
    Retuns the tuple of (indices, categories, categories_priorities, user_mentioned, survey_display)
    """
    data = pd.read_csv(filename, encoding='utf-8')
    data.sort_values(by=["category priority", "category"], inplace=True)

    return data