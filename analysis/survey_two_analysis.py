import os
import json
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

# Get the prolific ids from the chat history files
prolific_ids = [file.split("_")[-1].split(".")[0] for file in os.listdir("retrieve_data/data") if file.startswith("chat_history") and file.endswith(".json")]

# Create a dataframe to store the data
data_df = pd.DataFrame(columns=["PID", "turn", "chat_content", "persuasion_strategy", "detected_info", "disclosure_way", "necessity (y/n)", "justification_init", "justification_coding", "info_disclosed", "disclosure_way"])

indx = 0
# For every prolific id
for prolific_id in prolific_ids:
    chat_file = f"chat_history_{prolific_id}.json"
    with open(os.path.join("retrieve_data/data", chat_file), 'r', encoding='utf-8') as f:
        chat_history = json.load(f)

    chat_file_text = process_string_from_delimiter(chat_history)

    # First line of the chat history will be the iteration number
    lines = chat_file_text.split("\n")

    # Get the information into the dataframe
    while len(lines) > 1:
        iteration = int(lines[0].split(":")[1].strip())
        character = "chatbot: " if lines[1].split(":")[1].strip().lower() == "assistant" else "user: "
        character_text = lines[2].split(":")[1].strip()
        persuasion = lines[3].split(":")[1].strip()
        data_df.loc[indx, "PID"] = prolific_id
        data_df.loc[indx, "turn"] = (iteration // 2) + 1
        data_df.loc[indx, "chat_content"] = character + "'" + character_text + "'"
        data_df.loc[indx, "persuasion_strategy"] = None if persuasion.lower() == "none" else persuasion
        indx += 1
        lines = lines[5:]

data_df.to_csv("retrieve_data/data/info.csv", index=False)
