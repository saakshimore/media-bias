import pandas as pd
import langdetect
import re
from bs4 import BeautifulSoup
import os
import openai
import requests
import base64
import textwrap
import json
from binascii import b2a_base64


def get_completion(prompt, model="gpt-3.5-turbo"):
    messages = [{"role": "user", "content": prompt}]
    response = openai.ChatCompletion.create(
        model=model,
        messages=messages,
        temperature=0, # this is the degree of randomness of the model's output
    )
    return response.choices[0].message["content"]


def read_string(input_string):
    if input_string is None:
        return None
    else:
        try:
            input_string = input_string.replace("'","")
            data = json.loads(input_string)
            return data
        except json.JSONDecodeError:
            print("Invalid JSON string")
            return None

        
key = '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'
openai.api_key = key

# Get the current script's directory
script_directory = os.path.dirname(os.path.abspath(__file__))
# Construct the path to the 'data' folder relative to the script
data_directory = os.path.join(script_directory, 'data')
df = pd.DataFrame()
for filename in os.listdir(data_directory):
    if filename.endswith(".csv"):
        # Construct the full path to the CSV file
        file_path = os.path.join(data_directory, filename)
        # Read the CSV file into a pandas dataframe
        current_dataframe = pd.read_csv(file_path)
        # Concatenate the current dataframe to the master dataframe
        df = pd.concat([df, current_dataframe], ignore_index=True)

        
prompt_folder = os.path.join(script_directory, '..', 'prompt')
text_file_path = os.path.join(prompt_folder, 'prompt_v2.txt')
with open(text_file_path, 'r') as file:
    content = file.read()

a=[]
for index, row in df.iterrows():
    prompt = ##########################################################
    sentiment = get_completion(prompt)
    sentiment = read_string(sentiment)
    print(sentiment)
    a.append(sentiment)
    
result = pd.DataFrame(a)
csv_file_path = 'data/result.csv'
# Write the DataFrame to a CSV file
merged_df.to_csv(csv_file_path, index=False)
        
        
        
        
        
        
        