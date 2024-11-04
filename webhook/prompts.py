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

BQ_SQL_GENERATION_PROMPT = """
You are a SQL expert. Write a SQL command to answer the user's question based on the context given.

<instructions>
- Pay attention to the columns names.
- Pay attention to the project id.
- Pay attention to the dataset and table name.
- Use only a column or a table name if you are possitive that exists.
- Provide only the sql code ready to be run in bigquery.
- If the information to answer the user question is not in the table, reply that you cannot answer that question.
</instructions>

<context>
Project ID: {project_id}
Dataset: {dataset}
Table: {table}
Columns: 
{columns}

User question: {user_query}
</context>

SQL:
"""

BQ_RESPONSE_GENERATION_PROMPT = """
System: {query_results}

Responde la pregunta del usuario en español usando esta información. Evita generar codigo SQL.

User: {user_query}

AI: 
"""

DATASTORE_RESPONSE_PROMPT = """
Sos un agente llamado GCPBot necesito que respondas basado en esta informacion la pregunta de mi usuario, basada en esta informacion:\n

<information>
{summary}
</information>

User: {user_query}
AI: 
"""

BQ_GET_COLUMNS_SQL = """
        SELECT
            TABLE_CATALOG as project_id, TABLE_SCHEMA as owner, TABLE_NAME as table_name, COLUMN_NAME as column_name,
            IS_NULLABLE as is_nullable, DATA_TYPE as data_type, COLUMN_DEFAULT as column_default, ROUNDING_MODE as rounding_mode
        FROM
            {bq_dataset}.INFORMATION_SCHEMA.COLUMNS
        ORDER BY
            project_id, owner, table_name, column_name;
"""