# CALIBER - Annotations

## Backend

### ai_service

#### chatbot.py
Overview
This file defines a ChatBot class that:

Takes a user’s message and recent chat history.

Sends that information to OpenAI to get a reply.

Updates and optionally saves/loads the conversation using Redis (a fast in-memory database).

Provides functions for clearing, summarizing, and restoring conversations.

Think of it as the “brain + short-term memory” of the website’s chat system.

Key Features
1. Setup (__init__)
Loads configuration from AIConfig (e.g., API keys, model settings).

Connects to Redis for temporary conversation storage.

Sets the openai.api_key if provided.

2. Generate a Response (generate_response)
Builds a list of messages (system prompt + recent history + user’s message).

Calls OpenAI to generate a reply.

Saves both the user message and AI reply to the conversation history.

Returns:

The AI’s response

Conversation ID

Timestamp

A context summary

3. Build Messages (_build_messages)
Creates the message list OpenAI needs.

Adds:

System prompt: a set of rules or a “role” for the AI.
Default: “Caliber,” an AI expert in digital advertising optimization.

Last 10 messages from history (to save on token usage).

Current user message.

4. Call OpenAI (_call_openai)
Sends the message list to OpenAI’s ChatCompletion API.

Returns the AI’s text response.

5. Conversation Tools
get_conversation_summary → Shows conversation ID, number of messages, timestamps, and a summary.

clear_conversation → Empties the conversation history.

save_conversation → Stores conversation in Redis with a 1-hour time limit.

load_conversation → Retrieves a saved conversation from Redis.

Data Flow
Frontend sends a message + existing ChatContext.

generate_response() builds the request and calls OpenAI.

OpenAI returns the assistant’s text.

The conversation history is updated.

Conversation can be saved to Redis for later retrieval.

Glossary
System prompt: Rules/role given to the AI (e.g., “You are Caliber…”).

Context/History: List of past user/assistant messages that give the AI “memory.”

Temperature: Controls creativity (lower = safer/more predictable).

Redis cache: Fast temporary memory for saving chat history.

Notes
Redis settings are hardcoded to localhost, DB 1 — consider moving to configuration for production.

save_conversation() doesn’t store user_id/campaign_id directly, but load_conversation() expects them.

Only the last 10 messages are sent to OpenAI to reduce cost and avoid hitting token limits.

#### config.py

#### controllers.py

#### insight_generator.py

#### routes.py

#### schemas.py

### auth_service

#### __init__.py

#### dependencies.py

#### example_usage.py

#### firebase_verify.py

#### routes.py

### campaign_service

#### controllers.py

#### routes.py

#### schemas.py

### common

#### __init__.py

#### exceptions.py

#### logging.py

#### schemas.py

#### utils.py

### config

#### __init__.py

#### database.py

#### redis.py

#### settings.py

### db

#### migrations

##### env.py

#### __init__.py

#### base.py

#### models.py

### report_service

#### exports.py

#### pdf_generator.py

#### routes.py

#### storage.py

#### uploads.py

### scoring_service

#### config.py

#### controllers.py

#### explain.py

#### normalize.py

#### outliers.py

#### preprocesses.py

#### routes.py

#### schemas.py

#### scoring.py

#### weighting.py

### scripts

#### stat_workers.bat

#### start_workers.sh

### worker

#### __init__.py

#### celery.py

#### tasks.py

### main.py

## Frontend

### pages

#### campaign.jsx

#### dashboard.jsx

#### login.jsx

#### register.jsx

### services

#### api.js

#### firebase.js

### utils

#### authGaurd.js


