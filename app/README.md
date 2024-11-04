# Telegram Integration for Dialogflow CX

This document outlines the process of integrating a Telegram bot with Dialogflow CX, leveraging Google Cloud services like Cloud Run, Datastore, and BigQuery.

## Architecture

The following diagram illustrates the high-level architecture of the integration:

![Architecture](/images/telegrambot.png)

## Prerequisites

- A GCP project with billing enabled.
- A Telegram account.
- Basic familiarity with Dialogflow CX, Cloud Run, Datastore, and BigQuery.

## Setup

### 1. GCP Project Setup

- Create a new project in Google Cloud Platform (GCP).
- Enable the following APIs:
    - Dialogflow CX API
    - Cloud Run API
    - Cloud Build API
    - Datastore API
    - BigQuery API

### 2.  Environment Variables

- Create a `.env` file in the `webhook` directory to store your environment variables. Use the provided `.env_template` file as a reference.
- Populate the `.env` file with the following:

    **GCP Project:**
    ```
    PROJECT_ID = 'your-gcp-project-id'
    LOCATION_ID = 'your-location' 
    ```

    **Dialogflow:**
    ```
    AGENT_ID = 'your-dialogflow-agent-id'
    LANGUAGE_CODE = 'your-agent-language-code'
    ```

    **Telegram:**
    ```
    TELEGRAM_TOKEN = 'your-telegram-token-id'
    MAX_RESPONSE_LENGTH = 3500
    ```

    **Cloud Run:**
    ```
    WEBHOOK_URL = f'your-cloud-run-url/{TELEGRAM_TOKEN}' 
    ```

    **Bigquery:**
    ```
    BQ_DATASET = "your-bigquery-dataset"
    BQ_TABLE = "your-bigquery-table"
    BQ_LOCATION = 'your-bigquery-location'
    ```

    **Datastore:**
    ```
    DATASTORE_ID = 'your-datastore-id'
    DATASTORE_LOCATION = 'your-datastore-location'
    ```

    **Gemini Model:**
    ```
    MODEL = 'your-gemini-model'
    ```

### 3. Datastore Setup

- **Create a Datastore bucket:**
    - Navigate to Cloud Storage > Buckets > Create.
    - Upload your files (`.pdf`, `.html`, `.txt`, etc.) to the bucket. You can find example files in the `papers` folder.

- **Create a Datastore index:**
    - Go to Agent Builder.
    - Enable the Datastore API.
    - Create a Search app.
    - Create the Datastore index:
        - Select "Create datastore".
        - Choose "Cloud Storage".
        - Select your GCS bucket folder.
        - Set the frequency for updates.
        - Click "Create".
        - Select the newly created datastore.
        - Click "Create" again.
    - **Note:** In options, you can choose the parser. Using Layout Parser is recommended for PDFs with images and tables.
    - The build process may take around 15 minutes. Wait for it to complete.

    ![Datastore Import](/images/datastore_import.png)

- Copy the Datastore ID and location into your `.env` file.


### 4. BigQuery Setup

- Enable the BigQuery API.
- Create a new dataset.
- Create a new table.
- Select the upload option.
- Import data into the BigQuery table. You can use the `.csv` file in the `catalog` folder, or your own data.
- If you use the provided `.csv` file select the infer schema checkbox.
- **Important:** Ensure this step is completed before deploying to Cloud Run.

### 5. Create Webhooks

- Enable Cloud Run API and Cloud Build API.
- Navigate to the `webhook` folder.
- Authenticate with a GCP account that has the necessary permissions for deployment (refer to the `roles.png` image for required roles).
- Deploy the webhooks to Cloud Run using the following `gcloud` command:
**Note:** Make sure to create and complete the .env file inside the `webhook` folder.

```bash
gcloud functions deploy YOUR_FUNCTION_NAME \
--gen2 \
--project YOUR_PROJECT_ID \
--region=YOUR_REGION \
--runtime=python310 \
--entry-point=YOUR_CODE_ENTRYPOINT \
--memory=1GiB \
--min-instances=1 \
--trigger-http
```

### 6. Dialogflow CX Setup

- Go to the Dialogflow CX console.
- Enable the Dialogflow API.
- Create a new agent:
    - Select "Build your own".
    - Configure the agent name, location, time zone, and language.
- Import the provided agent:
    - Download `agent/exported_agent_telegram-bot.blob`.
    - Go to "View all agents".
    - Select the three dots next to your agent and click "Restore".
    - Upload the `exported_agent_telegram-bot.blob` file.
    - Click "Restore".
- Configure the webhook:
    - Go to `Manage` > `Webhooks`.
    - Select `webhook` and change the url.
- Attach the webhook to the user intention in Dialogflow:
    - Copy your Cloud Run function URL.
    - **Step 1:**
        - Go to the `consulta_datos` flow.
        - Navigate to the `bq-reply-to-user` page.
        - In Entry fulfillment, edit the webhook settings:
            - `consulta_datos` > `bq-reply-to-user` > Edit fulfillment > Webhook settings > Create new webhook.
        - Set the timeout to 30 seconds and paste your webhook URL.
    - **Step 2:**
        - Go to the `paper-datastore` flow.
        - Navigate to the `reply-to-user` page.
        - Edit fulfillment and select the webhook you created in Step 1.

### 7. Telegram Bot Setup

- Set up a Telegram account.
- Create a new Telegram bot using BotFather.
- Copy the bot token and paste it into the `TELEGRAM_TOKEN` variable in your `.env` file.

### 8. Deploy the Cloud Run App

- Complete the `.env` file in the `app` directory.
- Move to the `app` directory.
- Build the Docker image:

```bash
gcloud builds submit --tag gcr.io/your-project-id/image-name
```

- Deploy to Cloud Run:

```bash
gcloud run deploy --image gcr.io/workshop-ai-community/workshop-image \
  --service-account your-service-account \
  --memory 2Gi \
  --port 8080 \
  --allow-unauthenticated \
  --min-instances 1 
```

- Retrieve the Cloud Run URL and update the WEBHOOK_URL variable in your .env file.
- You need to repeat the build and deploy process after updating the WEBHOOK_URL.

### Additional Notes

- Ensure that your Cloud Run service account has the necessary permissions to access other GCP services (e.g., Datastore, BigQuery).
- Consider implementing error handling and logging for improved debugging and monitoring.
- Refer to the official documentation for Dialogflow CX, Cloud Run, Datastore, and BigQuery for more detailed information.