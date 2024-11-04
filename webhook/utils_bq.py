# Copyright 2024 Google, LLC. This software is provided as-is, without
# warranty or representation for any use or purpose. Your use of it is
# subject to your agreement with Google.

# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at

#    http://www.apache.org/licenses/LICENSE-2.0

# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import pandas as pd
from configs import BQ_DATASET, BQ_TABLE, PROJECT_ID, LOCATION_ID
from google.cloud import bigquery
import vertexai
from vertexai.generative_models import GenerativeModel, ChatSession

# Initialize Vertex AI
vertexai.init(project=PROJECT_ID, location=LOCATION_ID)
client = bigquery.Client(project=PROJECT_ID)


def run_query(sql: str) -> pd.DataFrame:
    """Executes a SQL query and returns the result as a Pandas DataFrame.

    Args:
        sql (str): The SQL query string to execute.

    Returns:
        pd.DataFrame: The result of the query as a DataFrame. 
                      None if an error occurs during execution.
    """
    try:
        result_query = client.query(sql)
        result_query.result()
    except Exception as e:
        print("Error running the query: {}".format(e))
        return None
    return result_query.to_dataframe()

def get_chat_response(chat: ChatSession, prompt: str) -> str:
    """Sends a prompt to a chat session and returns the text response.

    Args:
        chat (ChatSession): An active chat session object.
        prompt (str): The message or query to send to the chat session.

    Returns:
        str: The text response from the chat session.
    """
    response = chat.send_message(prompt)
    return response.text