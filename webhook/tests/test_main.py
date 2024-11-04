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

import sys
sys.path.append('webhook/')
import os 
print(os.getcwd())
from main import dialogflow_webhook
import json
from unittest.mock import MagicMock

def test_handle_bq_webhook():
    request = MagicMock(get_json=lambda: {'fulfillmentInfo': {'tag': 'bq_webhook'}, 'text': 'What is the average price of products?'})
    response = dialogflow_webhook(request)
    print(response)  # Check the structure of the response

def test_handle_ds_webhook():
    request = MagicMock(get_json=lambda: {'fulfillmentInfo': {'tag': 'ds_webhook'}, 'text': 'What is the UI grounding?'})
    response = dialogflow_webhook(request)
    print(response)  # Check the structure of the response

def test_handle_ds_webhook_2():
    request = MagicMock(get_json=lambda: {'fulfillmentInfo': {'tag': 'ds_webhook'}, 'text': 'Which is the most capable gemini model?'})
    response = dialogflow_webhook(request)
    print(response)  # Check the structure of the response

if __name__ == '__main__':
    test_handle_bq_webhook()
    test_handle_ds_webhook()
    test_handle_ds_webhook_2()