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

import functions_framework
from utils_bq import run_query, get_chat_response
from utils_ds import search_sample
import vertexai
from configs import (
    PROJECT_ID, 
    BQ_DATASET, 
    BQ_TABLE, 
    LOCATION_ID, 
    DATASTORE_ID, 
    DATASTORE_LOCATION,
    MODEL
)
from vertexai.generative_models import GenerativeModel
from typing import List, Dict
from prompts import (
    BQ_SQL_GENERATION_PROMPT, 
    BQ_RESPONSE_GENERATION_PROMPT, 
    DATASTORE_RESPONSE_PROMPT,
    BQ_GET_COLUMNS_SQL
)
from vertexai.generative_models import ChatSession
import logging

logging.basicConfig(
    level=logging.INFO,  # Set the logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'  # Define the log message format
)

# Create a global chat session to preserve context across requests
chat = None

# Functions-framework --target sql_webhook
@functions_framework.http
def dialogflow_webhook(request):
    global chat
    # Inicializo el modelo
    vertexai.init(project=PROJECT_ID, location=LOCATION_ID)
    model = GenerativeModel(MODEL)

    if chat is None:
        chat = model.start_chat()

    req = request.get_json()
    tag = req['fulfillmentInfo']['tag']

    logging.info(chat)

    # Logica de webhook de bigquery
    if tag == 'bq_webhook':
        return handle_bq_webhook(req, chat)
    elif tag == 'ds_webhook':
        return handle_ds_webhook(req, chat)
    else:
        return {"fulfillment_response": {"messages": [{"text": {"text": ["Invalid webhook tag."]}}]}}

def handle_bq_webhook(req: Dict, chat: ChatSession) -> Dict:
    """Handles requests tagged as 'bq_webhook'.

    Args:
        req: The incoming request dictionary.
        chat: The global ChatSession object.

    Returns:
        Dict: The response dictionary for the webhook.
    """
    user_query = req['text']

    logging.info(user_query)

    # Get column information
    columns_df = get_table_columns()
    if columns_df is None:
        return {"fulfillment_response": {"messages": [{"text": {"text": ["Error fetching column information."]}}]}}

    s_columns = format_columns(columns_df)

    prompt_text = BQ_SQL_GENERATION_PROMPT.format(
            project_id=PROJECT_ID,
            dataset=BQ_DATASET,
            table=BQ_TABLE,
            columns=s_columns,
            user_query=user_query,
        )

    logging.info(prompt_text)

    chat_response = get_chat_response(chat, prompt_text)
    sql_query = extract_sql_query(chat_response)

    logging.info(chat_response)

    try:
        query_results = run_query(sql_query)
        print('SQL query executed successfully.')
    except Exception as e:
        print(f'Error executing SQL query: {e}')
        query_results = "I cannot answer that question based on the available data."

    chat_response = get_chat_response(chat, f"""
        System: 
        ```
        {query_results.to_markdown()}
        ```
        Answer the user's question using this information. Do not generate SQL code.

        User: {user_query}
        AI: 
    """)

    return {"fulfillment_response": {"messages": [{"text": {"text": [chat_response]}}]}}

def handle_ds_webhook(req: Dict, chat: ChatSession) -> Dict:
    """Handles requests tagged as 'ds_webhook'.

    Args:
        req: The incoming request dictionary.
        chat: The global ChatSession object.

    Returns:
        Dict: The response dictionary for the webhook.
    """
    user_query = req['text']

    summary = search_sample(PROJECT_ID, DATASTORE_LOCATION, DATASTORE_ID, user_query).summary.summary_text

    prompt_text = DATASTORE_RESPONSE_PROMPT.format(
            summary=summary,
            user_query=user_query,
        )
    chat_response = get_chat_response(chat, prompt_text)

    return {"fulfillment_response": {"messages": [{"text": {"text": [chat_response]}}]}}

def get_table_columns() -> List:
    """Fetches column information from BigQuery.

    Returns:
        List: A list of column details.
    """
    get_columns_sql = BQ_GET_COLUMNS_SQL.format(
        bq_dataset=BQ_DATASET
    )

    try:
        columns_df = run_query(get_columns_sql)
        columns_df = columns_df[columns_df['column_name'].isin(['BrandName', 'Brand_Desc', 'Category', 'Currancy', 'Product_Name', 'Product_Size', 'SellPrice'])]
        return columns_df

    except Exception as e:
        print(f"Error fetching column information: {e}")
        return None

def format_columns(columns_df) -> str:
    """Formats column information for the prompt.

    Args:
        columns_df: The DataFrame containing column details.

    Returns:
        str: The formatted string of columns.
    """
    return "\n".join(f"- {row['column_name']} ({row['data_type']})" for _, row in columns_df.iterrows())

def extract_sql_query(chat_response: str) -> str:
    """Extracts the SQL query from the chat response.

    Args:
        chat_response: The response from the chat model.

    Returns:
        str: The extracted SQL query.
    """
    # Add logic to reliably extract SQL query from the chat response
    # For example, you can use regular expressions or string manipulation
    # based on how the model formats its output.
    return chat_response.replace('```sql', '').replace('```', '').strip()