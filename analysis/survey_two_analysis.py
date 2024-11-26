import os
import json
import re
import pandas as pd

def process_string_from_delimiter(long_string):
    # Split the string into lines
    lines = long_string.split('\n')

    # Flag to track if we've found the delimiter
    found_delimiter = False

    # List to store processed lines
    processed_lines = []

    # Iterate through lines
    for line in lines:
        # Check if we found the delimiter
        if '------------' in line:
            found_delimiter = True
            continue  # Skip the delimiter line itself

        # If we've found the delimiter, start collecting lines
        if found_delimiter:
            processed_lines.append(line)

    # Join the processed lines back into a string
    result = '\n'.join(processed_lines)
    return result

def main():
    # Get the prolific ids from the chat history files
    prolific_ids = [file.split("_")[-1].split(".")[0] for file in os.listdir("retrieve_data/data") if file.startswith("chat_history") and file.endswith(".json")]

    # Create a dataframe to store the data
    data_df = pd.DataFrame(columns=["PID", "turn", "chat_content", "persuasion_strategy", "detected_info", "disclosure_way", "necessity (y/n)", "justification_init", "justification_coding", "info_disclosed", "disclosure_way"])

    indx = 0
    # For every prolific id
    for prolific_id in prolific_ids:
        print(f"Processing {prolific_id}")
        chat_file = f"chat_history_{prolific_id}.json"
        with open(os.path.join("retrieve_data/data", chat_file), 'r', encoding='utf-8') as f:
            chat_history = json.load(f)

        # Get rid of the unnecessary information
        chat_file_text = process_string_from_delimiter(chat_history)

        # Memory to store the information
        memory = {}

        # Process for the survey two data
        survey_file = f"survey_two_response_{prolific_id}.json"
        if os.path.exists(os.path.join("retrieve_data/data", survey_file)):
            print("Survey two information is present.")
            with open(os.path.join("retrieve_data/data", survey_file), 'r', encoding='utf-8') as f:
                survey_data = json.load(f)

            # Get the detected information
            all_detections = survey_data["all_detections"]
            for key in all_detections:
                # print(key, all_detections[key].keys())
                if "better_evidence" not in all_detections[key]:
                    continue
                # Get the better evidence
                evidence = all_detections[key]["better_evidence"]
                # Using Regex capture the information between the ** and **
                detected_info = re.search(r'\*\*(.*)\*\*', evidence).group(1)

                # If the detected information is not in the memory, add it
                if detected_info not in memory:
                    memory[detected_info] = {}

                # Process this information to get the text that contains the information
                memory[detected_info]['selected'] = all_detections[key].get("selected", False)
                memory[detected_info]['reasoning'] = all_detections[key].get("reasoning", None)
                memory[detected_info]['priority'] = all_detections[key].get("priority", None)
                memory[detected_info]['category'] = all_detections[key].get("category", None)
                memory[detected_info]['survey_display'] = all_detections[key].get("survey_display", None)

        # First line of the chat history will be the iteration number
        lines = chat_file_text.split("\n")

        # Get the information into the dataframe
        while len(lines) > 1:
            turn = (int(lines[0].split(":")[1].strip()) // 2) + 1
            character = "chatbot: " if lines[1].split(":")[1].strip().lower() == "assistant" else "user: "
            character_text = lines[2].split(":")[1].strip()
            persuasion = lines[3].split(":")[1].strip()
            persuasion = persuasion if persuasion.lower() != "none" else None
            data_df.loc[indx, "PID"] = prolific_id
            data_df.loc[indx, "turn"] = turn
            data_df.loc[indx, "chat_content"] = character + "'" + character_text + "'"
            data_df.loc[indx, "persuasion_strategy"] = persuasion

            flag = False
            for key, value in memory.items():
                if key.lower() in character_text.lower():
                    data_df.loc[indx, "PID"] = prolific_id
                    data_df.loc[indx, "turn"] = turn
                    data_df.loc[indx, "chat_content"] = character + "'" + character_text + "'"
                    data_df.loc[indx, "persuasion_strategy"] = persuasion
                    data_df.loc[indx, "detected_info"] = value['survey_display']
                    data_df.loc[indx, "necessity (y/n)"] = value['selected']
                    data_df.loc[indx, "justification_init"] = value['reasoning']
                    indx += 1
                    flag = True
            if not flag:
                indx += 1
            lines = lines[5:]

    os.makedirs("analysis/data", exist_ok=True)
    data_df.to_csv("analysis/data/data.csv", index=False)

if __name__ == "__main__":
    main()
