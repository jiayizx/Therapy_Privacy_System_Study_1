import streamlit as st
import pandas as pd
import os
import json
import streamlit_survey as ss

def main():
    st.title("AI Chatbot Survey: User Experience and Privacy Feedback")
    st.write("Please indicate to what extent you agree or disagree with the following statements about your experience with the AI chatbot.")

    # Ensure Prolific ID is available
    if 'prolific_id' not in st.session_state or st.session_state.prolific_id == '':
        st.warning("Please go back to the main page and enter your Prolific ID.")
        st.stop()

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
    ]

    response_options = [
        "Strongly Disagree",
        "Disagree",
        "Slightly Disagree",
        "Neutral",
        "Slightly Agree",
        "Agree",
        "Strongly Agree"
    ]

    if "responses_submitted" not in st.session_state:
        st.session_state.responses_submitted = False

    if not st.session_state.responses_submitted:
        survey = ss.StreamlitSurvey()

        for i, statement in enumerate(statements, 1):
            survey.select_slider(
                label=f"Q{i}: {statement}",
                options=response_options,
                id=f"Q{i}"
            )

        submit_button = st.button(label='Submit')

        response = {}
        if submit_button:
            survey_response = survey.to_json()
            survey_response = json.loads(survey_response)  # Parse the JSON string to a dictionary
            prolific_id = st.session_state.get("prolific_id", "unknown")
            response_data = pd.DataFrame({
                "Prolific ID": [prolific_id] * len(statements),
                "Statement": statements,
                "Response": [data["value"] for key, data in survey_response.items()]
            })
            st.success("Thank you for your feedback!")
            st.write(response_data)

            # Save responses to a CSV file
            if not os.path.exists("survey_one_responses.csv"):
                response_data.to_csv("survey_one_responses.csv", index=False)
            else:
                response_data.to_csv("survey_one_responses.csv", mode='a', header=False, index=False)

            # Mark responses as submitted
            st.session_state.responses_submitted = True

    else:
        st.write("You have already submitted your responses. Thank you!")


    if st.session_state.responses_submitted:
        st.session_state.survey_1_completed = True
        if st.button("Part 2: Proceed to Post Survey 2"):
            target_page = "pages/post_survey_2.py"
            st.switch_page(target_page)


if __name__ == "__main__":
    main()
