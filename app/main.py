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
import logging
from typing import Dict
# These libraries are used for interacting with Google Cloud Dialogflow CX
from google.cloud.dialogflowcx_v3beta1.services.agents import AgentsClient
from google.cloud.dialogflowcx_v3beta1.services.sessions import SessionsClient
# These libraries are used for interacting with Telegram
from telegram import Update
from telegram.ext import (
    Application,
    CommandHandler,
    ContextTypes,
    ConversationHandler,
    MessageHandler,
    CallbackContext,
    filters
)
# These libraries are used for interacting with Google Cloud Vertex AI and its Generative Models
import vertexai
from vertexai.generative_models import (
    GenerationConfig,
    GenerativeModel,
    Part,
)
import io
import mimetypes
import base64
# These libraries are used for handling image and audio data
from utils import *
from configs import *
# Set the port for the webhook
PORT = int(os.environ.get("PORT", 8080))

# Initialize Vertex AI with project and location
vertexai.init(project=PROJECT_ID, location=LOCATION_ID)
multimodal_model = GenerativeModel(MODEL)

# Build Telegram application with webhook URL
application = Application.builder().token(TELEGRAM_TOKEN).build()

# Define asynchronous handler functions for different message types
async def handle_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handles incoming text messages and sends a response using Dialogflow.

    Args:
        update: The Telegram Update object containing the message.
        context:  The Telegram Context object.
    """
    telegram_request = update.to_dict()
    response = detect_intent_response(telegram_request, PROJECT_ID, AGENT, LANGUAGE_CODE, LOCATION_ID)
    await update.message.reply_text(response)

async def handle_image(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handles incoming image messages and generates a response using Gemini.
    
    Args:
        update: The Telegram Update object containing the message.
        context:  The Telegram Context object.
    """
    max_retries = 3
    retry_delay = 2

    logging.info("Received image message")

    for attempt in range(max_retries):
        try:
            logging.info(f"Processing image, attempt {attempt + 1}")
            new_file = await context.bot.get_file(update.message.photo[-1].file_id)
            download_url = new_file.file_path
            instruction = update.message.caption

            # Asynchronously download and load the image
            downloaded_image = await load_image_from_url(download_url)

            # Convert the image to bytes
            image_bytes = io.BytesIO()
            downloaded_image.save(image_bytes, format=downloaded_image.format)
            image_bytes = image_bytes.getvalue()

            prompt = "Using the following image, respond to the user's instruction."
            prompt2 = f"Instruction: {instruction}"

            # Get the file extension
            extension = download_url.split('.')[-1]

            # Use mimetypes to guess the MIME type
            mime_type = mimetypes.guess_type(f"image.{extension}")[0]

            # Create a Part object for the image
            image_part = Part.from_data(
                mime_type=mime_type,
                data=image_bytes,
            )

            contents = [
                prompt,
                image_part,
                prompt2
            ]

            response = multimodal_model.generate_content(contents)
            print(type(MAX_RESPONSE_LENGTH))
            # Truncate the response if it exceeds the maximum length
            if int(len(response.text)) > MAX_RESPONSE_LENGTH:
                response.text = response.text[:MAX_RESPONSE_LENGTH] + "...(description truncated)"
            await update.message.reply_text(response.text)
            return # Success, exit the loop

        except Exception as e:
            if "429" in str(e):  # Check for the specific error code
                logging.warning(f"Gemini 429 error, retrying in {retry_delay} seconds...")
                await asyncio.sleep(retry_delay)
            else:
                logging.error(f"Error processing image: {e}")
                await update.message.reply_text("Sorry, there was an error processing your image.")
                return  # Unhandled error, exit the loop

async def handle_video(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handles incoming video messages, prepares them for Gemini, and generates a response.

    This handler downloads the video sent by the user, encodes it to base64, 
    and sends it to the Gemini model along with a prompt based on the user's 
    caption (if provided). If successful, it sends the model's response back 
    to the user. The function includes retry logic for handling potential 
    rate limit errors (HTTP 429) from the Gemini API.

    Args:
        update (Update): The Telegram Update object containing the message.
        context (ContextTypes.DEFAULT_TYPE): The Telegram Context object.
    """
    max_retries = 3
    retry_delay = 2

    logging.info("Received video message")

    for attempt in range(max_retries):
        try:
            logging.info(f"Processing video, attempt {attempt + 1}")
            new_file = await context.bot.get_file(update.message.video.file_id)
            download_url = new_file.file_path
            instruction = update.message.caption
            extension = new_file.file_path.split('.')[-1]

            logging.info(f"Recieve")
            # Download and convert video data (consider optimizing this part)
            async with aiohttp.ClientSession() as session:
                async with session.get(download_url) as resp:
                    video_data = await resp.read()

            logging.info(f"Encoding video data")        
            video_bytes = base64.b64encode(video_data).decode('utf-8') 

            prompt = "Using the following video, respond to the user's instruction."
            prompt2 = f"Instruction: {instruction}"
            
            logging.info(f"Prompting Gemini with {prompt} {prompt2}")

            video = Part.from_data(
                mime_type=f"video/{extension}",
                data=video_bytes,
            )

            contents = [prompt, prompt2, video]

            response = multimodal_model.generate_content(contents)
            if len(response.text) > MAX_RESPONSE_LENGTH:
                response.text = response.text[:MAX_RESPONSE_LENGTH] + "...(description truncated)"
            await update.message.reply_text(response.text)
            return  # Success, exit the loop

        except Exception as e:
            if "429" in str(e):  # Check for the specific error code
                logging.warning(f"Gemini 429 error, retrying in {retry_delay} seconds...")
                await asyncio.sleep(retry_delay)
            else:
                logging.error(f"Error processing video: {e}")
                await update.message.reply_text("Sorry, there was an error processing your video.")
                return  # Unhandled error, exit the loop

    # If the loop completes without success, inform the user
    logging.error(f"Failed to process video after {max_retries} attempts.")
    await update.message.reply_text(
        "Sorry, the service is temporarily unavailable. Please try again later."
    )


async def handle_audio(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handles incoming audio messages, prepares them for Gemini, and generates a response.

    This handler downloads the audio sent by the user, encodes it to base64,
    and sends it to the Gemini model along with a prompt. If successful, it sends 
    the model's response back to the user. The function includes retry logic for 
    handling potential rate limit errors (HTTP 429) from the Gemini API.

    Args:
        update (Update): The Telegram Update object containing the message.
        context (ContextTypes.DEFAULT_TYPE): The Telegram Context object.
    """

    max_retries = 3
    retry_delay = 2
    
    logging.info("Received audio message")

    for attempt in range(max_retries):
        try:        
            logging.info(f"Processing audio, attempt {attempt + 1}")
            # Get the MIME type from the message
            mime_type = update.message.voice.mime_type  

            new_file = await context.bot.get_file(update.message.voice.file_id)
            download_url = new_file.file_path
            instruction = update.message.caption

            # Asynchronously download the audio data
            async with aiohttp.ClientSession() as session:
                async with session.get(download_url) as resp:
                    audio_data = await resp.read()

            # Encode audio data as base64
            audio_bytes = base64.b64encode(audio_data).decode('utf-8')

            prompt = "Responde al audio del usuario"

            # Create a Part object for the audio
            audio_part = Part.from_data(
                mime_type=mime_type,  # Use the extracted MIME type
                data=audio_bytes,
            )

            contents = [prompt, audio_part]

            response = multimodal_model.generate_content(contents)
            await update.message.reply_text(response.text)
            return  # Success, exit the loop

        except Exception as e:
            if "429" in str(e):  # Check for the specific error code
                logging.warning(f"Gemini 429 error, retrying in {retry_delay} seconds...")
                await asyncio.sleep(retry_delay)
            else:
                logging.error(f"Error processing Audio: {e}")
                await update.message.reply_text("Sorry, there was an error processing your Audio.")
                return  # Unhandled error, exit the loop

def main():
    # Configure logging
    logging.basicConfig(
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
    )

    # Add your message handlers
    application.add_handler(MessageHandler(filters.TEXT, handle_text))
    application.add_handler(MessageHandler(filters.VOICE, handle_audio))
    application.add_handler(MessageHandler(filters.PHOTO, handle_image))
    application.add_handler(MessageHandler(filters.VIDEO | filters.VIDEO_NOTE, handle_video))

    application.run_webhook(
    listen="0.0.0.0",
    port=PORT,
    url_path=TELEGRAM_TOKEN,
    webhook_url=WEBHOOK_URL
    )

if __name__ == "__main__":
    main()