import streamlit as st
import os
import csv

# Set page config
st.set_page_config(page_title="Post Survey Part 3")

# Ensure Prolific ID is available
if 'prolific_id' not in st.session_state or st.session_state.prolific_id == '':
    st.warning("Please go back to the main page and enter your Prolific ID.")
    st.stop()

st.title("Post Survey Part 3")

# 1. Age range
if 'age_range' not in st.session_state:
    st.session_state.age_range = "Select your age range"

age_range = st.selectbox(
    "Please select your age range:",
    options=[
        "Select your age range",
        "18-24",
        "25-34",
        "35-44",
        "45-54",
        "55-64",
        "65 or above",
    ],
    index=["Select your age range", "18-24", "25-34", "35-44", "45-54", "55-64", "65 or above"].index(st.session_state.age_range),
    disabled='survey_submitted' in st.session_state and st.session_state.survey_submitted
)

st.session_state.age_range = age_range

# 2. Gender identity
if 'gender_identity' not in st.session_state:
    st.session_state.gender_identity = "Select your gender identity"

gender_identity = st.selectbox(
    "Please select your gender identity:",
    options=[
        "Select your gender identity",
        "Male",
        "Female",
        "Non-binary / Third gender",
        "Prefer not to say",
    ],
    index=["Select your gender identity", "Male", "Female", "Non-binary / Third gender", "Prefer not to say"].index(st.session_state.gender_identity),
    disabled='survey_submitted' in st.session_state and st.session_state.survey_submitted
)

st.session_state.gender_identity = gender_identity

# 3. Highest education (drop-down menu)
if 'highest_education' not in st.session_state:
    st.session_state.highest_education = "Select your highest education"

education_levels = [
    "Select your highest education",
    "Some school, no degree",
    "High school graduate, diploma or the equivalent (e.g. GED)",
    "Some college credit, no degree",
    "Bachelor's degree",
    "Master's degree",
    "Doctorate degree",
    "Prefer not to say",
]

highest_education = st.selectbox(
    "What is your highest level of education?", 
    options=education_levels,
    index=education_levels.index(st.session_state.highest_education),
    disabled='survey_submitted' in st.session_state and st.session_state.survey_submitted
)

st.session_state.highest_education = highest_education

# 4. Prior experience with AI chatbot or therapy
if 'prior_experience' not in st.session_state:
    st.session_state.prior_experience = ""

prior_experience_options = [
    "I've used an AI chatbot for therapy",
    "I've used an AI chatbot, but never for therapy (this is my first time)",
    "I've been to therapy with a human therapist, but not with an AI chatbot",
    "I've neither used an AI chatbot nor been to therapy",
]

prior_experience = st.radio(
    "Select your prior experience with AI chatbot or therapy:",
    options=prior_experience_options,
    index=prior_experience_options.index(st.session_state.prior_experience) if st.session_state.prior_experience in prior_experience_options else 0,
    disabled='survey_submitted' in st.session_state and st.session_state.survey_submitted
)

st.session_state.prior_experience = prior_experience

# Submit button
if st.button("Submit") and not ('survey_submitted' in st.session_state and st.session_state.survey_submitted):
    # Validate that all selections are made
    if age_range == "Select your age range":
        st.error("Please select your age range.")
    elif gender_identity == "Select your gender identity":
        st.error("Please select your gender identity.")
    elif highest_education == "Select your highest education":
        st.error("Please select your highest level of education.")
    else:
        # Collect all responses
        responses = {
            'Prolific ID': st.session_state.prolific_id,
            'Age Range': age_range,
            'Gender Identity': gender_identity,
            'Highest Education': highest_education,
            'Prior Experience': prior_experience,
        }
        # Log the responses to a file

        # Define the log file path
        log_file = 'survey_two_responses.csv'

        # Check if the file exists
        file_exists = os.path.isfile(log_file)

        # Open the file in append mode
        with open(log_file, 'a', newline='', encoding='utf-8') as csvfile:
            fieldnames = ['Prolific ID', 'Age Range', 'Gender Identity', 'Highest Education', 'Prior Experience']
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)

            # Write header only if file does not exist
            if not file_exists:
                writer.writeheader()

            # Write the responses
            writer.writerow(responses)

        st.success("Thank you for completing the survey!")
        st.balloons()
        # Mark responses as submitted
        st.session_state.survey_submitted = True
        st.rerun()


# Optional: Display a message if the survey is already completed
if 'survey_submitted' in st.session_state and st.session_state.survey_submitted:
    st.write("You have already completed the survey. Thank you!")
