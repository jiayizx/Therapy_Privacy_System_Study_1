import streamlit as st
import pandas as pd
import os
import json
import streamlit_survey as ss
from firebase_admin import firestore
import time
import logging

# Assuming Firebase setup has already been initialized

def save_survey_response_to_firebase(prolific_id, survey_data):
    """Save the survey responses to Firebase Firestore."""
    if "firestore_db" not in st.session_state:
        logging.error("Firestore DB not set up. Please initialize Firebase first.")
        return

    db = st.session_state.firestore_db
    document_name = f"survey_one_{prolific_id}_{int(time.time())}"  # Create a unique document name using prolific_id and timestamp

    # Prepare the data to be saved
    survey_document = {
        "prolific_id": prolific_id,
        "survey_data": survey_data,
        "timestamp": firestore.SERVER_TIMESTAMP,  # Automatically set the timestamp in Firestore
    }

    try:
        # Save the survey document to the Firestore collection named "survey_one_responses"
        db.collection("group_one_survey_one_responses").document(document_name).set(survey_document)
        logging.info("Survey Part 1 response successfully saved to Firebase Firestore.")
    except Exception as e:
        logging.error(f"Failed to save survey response to Firebase Firestore: {e}")


def post_survey_one():
    st.write("### Survey Part 1: How's your experience with the AI chatbot?")
    st.write("Here are some experience-related statements. To what extent do you agree or disagree with each statement?")

    # Ensure Prolific ID is available
    if 'prolific_id' not in st.session_state or st.session_state.prolific_id == '':
        st.warning("Please go back to the main page and enter your Prolific ID.")
        st.stop()

    if st.session_state.phase != "post_survey":
        st.warning("Please complete the chat session before proceeding to the survey.")
        st.stop()

    
    # Survey statements
    statements = [
        "I trust this AI chatbot to be reliable.",
        "I do not feel totally safe providing personal private information over this chatbot.",
        "I think this AI chatbot is persuasive.",
        "I enjoyed the therapy session.",
        "This chatbot demonstrates empathy during interactions.",
        "I feel understood when I talk to this chatbot.",
        "The AI chatbot's responses are appropriate for my needs.",
        "I am comfortable using this chatbot for sensitive discussions.",
        "This chatbot respects my privacy.",
        "I believe the chatbot provides helpful recommendations.",
        "I feel the chatbot has a human-like understanding of my concerns."
        "I enjoyed the therapy session.",
        "I trust this AI chatbot to be reliable.",
        "I think this AI chatbot is persuasive.",
        "I do not feel totally safe providing personal private information over this chatbot.",
        "I can understand what Alex was going through recently.",
        "I recognize Alex's situation.",
        "I can see Alex's point of view.",
        "Alex's reactions to the situation are understandable.",
        "Alex's emotions are genuine.",
        "I was in a similar emotional state as Alex when chatting with the AI therapist.",
        "I experienced the same emotions as Alex when chatting with the AI therapist.",
        "I can feel Alex's emotions."
    ]

    # Add a placeholder option at the beginning
    response_options = [
        "Select an option",  # Placeholder
        "Disagree",
        "Slightly Disagree",
        "Neutral",
        "Slightly Agree",
        "Agree",
    ]

    # Initialize survey responses in session state if not already present
    if "survey_response" not in st.session_state:
        st.session_state.survey_response = {f"Q{i}": "Select an option" for i in range(1, len(statements) + 1)}

    # Check if responses have already been submitted
    if "responses_submitted" in st.session_state and st.session_state.responses_submitted:
        st.write("You have already submitted your responses. Thank you!")
        return  # Exit the function to prevent further execution

    if not st.session_state.get("survey_1_completed", False):
        # Loop through each question and store response in session state
        for i, statement in enumerate(statements, 1):
            question_key = f"Q{i}"  # Unique key for each question
            # Render the selectbox and update the session state on change
            st.session_state.survey_response[question_key] = st.selectbox(
                label=f"**Q{i}: {statement}**",
                options=response_options,
                index=response_options.index(st.session_state.survey_response[question_key]),
                key=question_key  # Use unique keys for each selectbox
            )

        # Submit button to save responses
         # Submit is misleading, change to Next
        submit_button = st.button(label='Next', key='survey_1_submit_button')

    if submit_button:
        # Check if any question still has the placeholder selection
        if "Select an option" in st.session_state.survey_response.values():
            st.warning("Please select an option for each question before submitting.")
            return

        prolific_id = st.session_state.get("prolific_id", "unknown")

        # Prepare survey data for storage
        survey_data = []
        for key, response in st.session_state.survey_response.items():
            survey_data.append({
                "question_id": key,
                "statement": statements[int(key[1:]) - 1],
                "response": response
            })

        # Store the responses in Firebase
        save_survey_response_to_firebase(prolific_id, survey_data)
        # Mark responses as submitted and disable further edits
        st.session_state.responses_submitted = True
        st.session_state.survey_1_completed = True
        st.rerun()  # Rerun the script to display the completion message