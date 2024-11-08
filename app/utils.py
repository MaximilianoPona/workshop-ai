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

import asyncio
import telegram
import requests
import soundfile as sf
import io
import aiohttp

import logging
from typing import Dict
from google.cloud.dialogflowcx_v3beta1.services.agents import AgentsClient
from google.cloud.dialogflowcx_v3beta1.services.sessions import SessionsClient
from google.cloud.dialogflowcx_v3beta1.types import session, audio_config

from telegram import ReplyKeyboardMarkup, ReplyKeyboardRemove, Update
from telegram.ext import (
    Application,
    CommandHandler,
    ContextTypes,
    ConversationHandler,
    MessageHandler,
    CallbackContext,
    filters
)

# Initialize Vertex AI
import vertexai
from vertexai.generative_models import (
    GenerationConfig,
    GenerativeModel,
    Part,
)

from PIL import Image 

import http.client
import typing
import urllib.request
import base64

def get_image_bytes_from_url(image_url: str) -> bytes:
    """Downloads image data from a URL and returns it as bytes.

    Args:
        image_url: The URL of the image.

    Returns:
        bytes: The raw image data in bytes format.
    """
    with urllib.request.urlopen(image_url) as response:
        response = typing.cast(http.client.HTTPResponse, response)
        image_bytes = response.read()
    return image_bytes

async def load_image_from_url(url):
    """Asynchronously loads an image from a URL."""
    async with aiohttp.ClientSession() as session:
        async with session.get(url) as resp:
            image_data = await resp.read()
    image = Image.open(io.BytesIO(image_data))
    return image

def download_video(url, filename):
    """Downloads the video from the provided URL and saves it locally.

    Args:
        url (str): The URL of the video to download.
        filename (str): The desired filename for the downloaded video.
    """

    try:
        response = requests.get(url, stream=True)
        response.raise_for_status()

        with open(filename, 'wb') as file:
            for chunk in response.iter_content(1024):
                file.write(chunk)

        print(f"Video downloaded successfully as '{filename}'")

    except requests.exceptions.RequestException as error:
        print(f"Video download failed: {error}")

def video_to_base64(video_path: str) -> str:
    """Encodes a video file into a base64 string.

    Args:
        video_path: The path to the video file.

    Returns:
        str: The base64-encoded representation of the video.
    """
    with open(video_path, "rb") as video_file:
        encoded_string = base64.b64encode(video_file.read())
    return encoded_string.decode('utf-8')


def detect_intent_audio(telegram_request: dict, agent: str, 
                        audio_file: str, language_code: str, 
                        location_id: str, sample_rate: int) -> str:
    """Processes a Telegram voice message, detects intent using Dialogflow, and returns a response.

    Args:
        telegram_request: Dictionary containing the Telegram user request.
        agent: Dialogflow agent ID.
        audio_file: Path to the audio file.
        language_code: Language code for Dialogflow.
        location_id: Location ID for Dialogflow.
        sample_rate: Sample rate of the audio file.

    Returns:
        str: The response text generated by Dialogflow.
    """

    session_id = telegram_request['message']['chat']['id']
    session_path = f"{agent}/sessions/{session_id}"
    client_options = None
    agent_components = AgentsClient.parse_agent_path(agent)
    if location_id != "global":
        api_endpoint = f"{location_id}-dialogflow.googleapis.com:443"
        print(f"API Endpoint: {api_endpoint}\n")
        client_options = {"api_endpoint": api_endpoint}
    session_client = SessionsClient(client_options=client_options)

    input_audio_config = audio_config.InputAudioConfig(
        audio_encoding=audio_config.AudioEncoding.AUDIO_ENCODING_LINEAR_16,
        sample_rate_hertz=samplerate,
    )

    with open(audio_file_path, "rb") as audio_file:
        input_audio = audio_file.read()
        print("the audio was read successfully")

    audio_input = session.AudioInput(config=input_audio_config, audio=input_audio)
    query_input = session.QueryInput(audio=audio_input, language_code=language_code)
    request = session.DetectIntentRequest(session=session_path, query_input=query_input)
    
    response = session_client.detect_intent(request=request)
    response_messages = [
        " ".join(msg.text.text) for msg in response.query_result.response_messages
    ]

    print(f"Response text: {' '.join(response_messages)}\n")

    return ' '.join(response_messages)

def detect_intent_response(telegram_request: dict, 
                            project_id: str, agent: str, 
                            language_code: str, location_id: str) -> str:
    """Processes a Telegram request and returns a response using Dialogflow.

    Args:
        telegram_request: Dictionary containing the Telegram user request.
        project_id: Google Cloud Project ID.
        agent: Dialogflow agent ID.
        language_code: Language code for Dialogflow.
        location_id: Location ID for Dialogflow. 

    Returns:
        str: The response text generated by Dialogflow.
    """

    session_id = telegram_request['message']['chat']['id']
    session_path = f"{agent}/sessions/{session_id}"
    texts = [telegram_request['message']['text']]
    client_options = None
    agent_components = AgentsClient.parse_agent_path(agent)
    if location_id != "global":
        api_endpoint = f"{location_id}-dialogflow.googleapis.com:443"
        print(f"API Endpoint: {api_endpoint}\n")
        client_options = {"api_endpoint": api_endpoint}
    session_client = SessionsClient(client_options=client_options)
    
    for text in texts:  
        text_input = session.TextInput(text=text)
        query_input = session.QueryInput(text=text_input, language_code=language_code)
        request = session.DetectIntentRequest(
            session=session_path, query_input=query_input
        )
        response = session_client.detect_intent(request=request)
        
        response_messages = [
            " ".join(msg.text.text) for msg in response.query_result.response_messages
        ]
    
    return ' '.join(response_messages)