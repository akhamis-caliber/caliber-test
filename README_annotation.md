# CALIBER - Annotations

## ai_service

### chatbot.py
#### Overview
This file defines a ChatBot class that:
- Takes a user’s message and recent chat history.
- Sends that information to OpenAI to get a reply.
- Updates and optionally saves/loads the conversation using Redis (a fast in-memory database).
- Provides functions for clearing, summarizing, and restoring conversations.
- Think of it as the “brain + short-term memory” of the website’s chat system.

#### Key Features
1. Setup (__init__)
    -  Loads configuration from AIConfig (e.g., API keys, model settings).
    - Connects to Redis for temporary conversation storage.
    - Sets the openai.api_key if provided.

2. Generate a Response (generate_response)
Builds a list of messages (system prompt + recent history + user’s message).
    - Calls OpenAI to generate a reply.
    - Saves both the user message and AI reply to the conversation history.
    - Returns: The AI’s response, Conversation ID, Timestamp, A context summary

3. Build Messages (_build_messages)
    - Creates the message list OpenAI needs.
    - Adds:
        - System prompt: a set of rules or a “role” for the AI.
        Default: “Caliber,” an AI expert in digital advertising optimization.
        - Last 10 messages from history (to save on token usage).
        - Current user message.

4. Call OpenAI (_call_openai)
    - Sends the message list to OpenAI’s ChatCompletion API.
    - Returns the AI’s text response.

5. Conversation Tools
    - get_conversation_summary → Shows conversation ID, number of messages, timestamps, and a summary.
    - clear_conversation → Empties the conversation history.
    - save_conversation → Stores conversation in Redis with a 1-hour time limit.
    - load_conversation → Retrieves a saved conversation from Redis.

#### Data Flow
- Frontend sends a message + existing ChatContext.
- generate_response() builds the request and calls OpenAI.
- OpenAI returns the assistant’s text.
- The conversation history is updated.
- Conversation can be saved to Redis for later retrieval.

#### Glossary
- System prompt: Rules/role given to the AI (e.g., “You are Caliber…”).
- Context/History: List of past user/assistant messages that give the AI “memory.”
- Temperature: Controls creativity (lower = safer/more predictable).
- Redis cache: Fast temporary memory for saving chat history.

#### Notes
- Redis settings are hardcoded to localhost, DB 1 — consider moving to configuration for production.
- save_conversation() doesn’t store user_id/campaign_id directly, but load_conversation() expects them.
- Only the last 10 messages are sent to OpenAI to reduce cost and avoid hitting token limits.


### config.py
#### Overview
This module centralizes AI settings, prompt templates, insight type constants, and a lightweight ChatContext used to track conversation history. It’s the “settings + templates + context” toolkit that other parts of the backend import.

#### AIConfig — Environment-driven settings
Holds all configuration for the AI service, primarily loaded from environment variables so you can change behavior without editing code.

- OpenAI
    - OPENAI_API_KEY → API key
    - OPENAI_MODEL → model name (default: gpt-4)
    - OPENAI_MAX_TOKENS → max tokens per response (default: 2000)
    - PENAI_TEMPERATURE → creativity level (default: 0.7)

- Cache
    - CACHE_TTL → cache time-to-live in seconds (default: 3600 = 1 hour)
    - CACHE_ENABLED → "true"/"false" (default: true)

- Rate limiting (soft limits)
    - MAX_REQUESTS_PER_MINUTE (default: 60)
    - MAX_REQUESTS_PER_HOUR (default: 1000)
        - Tip: Set these via environment variables in your deployment or .env file to avoid hardcoding secrets and to tune performance.

#### PromptTemplates — Reusable AI prompt strings
Pre-written prompt templates for common tasks. Each template uses {placeholders} that you fill with real data before sending to the model.

- Campaign & Domain Analysis
    - CAMPAIGN_OVERVIEW_PROMPT
        - Summarizes campaign setup, score distribution, top/bottom performers, and metrics, then asks for assessment, strengths/weaknesses, optimizations, risks, and next steps.
    - DOMAIN_ANALYSIS_PROMPT
        - Deep-dive on a single domain: score, quality status, metrics, and whether to whitelist/blacklist.

- List Quality
    - WHITELIST_ANALYSIS_PROMPT
        - Evaluates whitelist quality, characteristics, recommendations, and risks.
    - BLACKLIST_ANALYSIS_PROMPT
        - Evaluates blacklist quality, common issues, recommendations, and potential false positives.

- Chat
    - CHAT_SYSTEM_PROMPT
        - Sets the assistant role/persona for Caliber (explain metrics, provide insights, be clear and actionable).
    - CHAT_USER_PROMPT
        - Wraps a user question plus optional campaign context to guide a helpful response.

- Insights
    - PERFORMANCE_INSIGHT_PROMPT
        - Generates 3–5 key insights for a campaign based on performance metrics and score distribution.
    - OPTIMIZATION_INSIGHT_PROMPT
        - Produces 3–5 specific, actionable optimization recommendations (whitelist/blacklist, bidding, targeting, etc.).  

How to use: prompt = PromptTemplates.CAMPAIGN_OVERVIEW_PROMPT.format(platform=..., goal=..., ...)

#### InsightTypes — String constants for insight categories
A small enum-like class with standard labels:

-  performance, optimization, whitelist, blacklist, domain, campaign_overview
- get_all_types() returns the full list.

Use these to keep downstream logic consistent (e.g., routing, display badges, analytics).

#### ChatContext — Minimal conversation state
Tracks who’s chatting and what’s been said.
- Fields
    - user_id (required)
    - campaign_id (optional)
    - conversation_history (list of {role, content, timestamp} dicts)
    - context_data (free-form dict for extras)

- Methods
    - add_message(role, content)
        - Appends a message (auto-timestamps it in UTC).
    - get_context_summary()
        - Returns a simple text summary of the last 5 messages (or empty string if none).
    - clear_history()
        - Wipes the history.

#### Notes & Gotchas
- Env defaults: Reasonable fallbacks are provided, but production should set real env vars (especially OPENAI_API_KEY).
- Naming alignment: Make sure the rest of your code reads the same variable names as defined here (e.g., OPENAI_MAX_TOKENS, OPENAI_TEMPERATURE). If any other module expects different names (like MAX_TOKENS or TEMPERATURE), align them to avoid config mismatches.
- Context summary vs. full history: get_context_summary() is intentionally brief (last 5 messages). If you need more/less context for the model call, adjust at the call site.

### controllers.py
#### Overview
AIController is the orchestration layer for AI-related operations. It:
- Validates ownership (user ↔ campaign/insight),
- Enforces rate limits (per-minute / per-hour using Redis),
- Delegates generation and CRUD work to InsightGenerator,
- Manages chat contexts in Redis (create, read, update, clear),
- Provides read APIs for previously generated insights and chat history.

#### Responsibilities at a Glance
- Insights
    - generate_campaign_insight(...)
    - generate_domain_insight(...)
    - generate_whitelist_insight(...)
    - generate_blacklist_insight(...)
    - generate_batch_insights(...)
    - get_campaign_insights(...)
    - delete_insight(...)
    - clear_campaign_insights(...)

- Chat
    - chat_with_ai(...)
    - get_chat_history(...)
    - clear_chat_history(...)

- Infra & Limits
    - _check_rate_limit(...) / _update_rate_limit(...)
    - _get_chat_context(...) / _get_chat_context_from_cache(...)
    - _save_chat_context(...) / _clear_chat_context(...)
    - _clear_insight_cache(...) / _clear_campaign_cache(...)
    - get_ai_status(...)

#### How It Works (High-Level Flow)
Generating an insight
1. Verify the campaign belongs to the user.
2. Validate insight type (for single or batch operations).
3. Check rate limit.
4. Call InsightGenerator to do the heavy lifting.
5. Update rate limit counters and return the result.  

Chatting with AI
1. Check rate limit.
2. Build or fetch a chat context (user_id:campaign_id or user_id:general).
3. Delegate to InsightGenerator.chat_with_ai(...).
4. Save updated chat context in Redis with a 1-hour TTL.
5. Update rate limit counters and return the message payload.

##### Key Methods (Beginner-Friendly)
Insights
- generate_campaign_insight(db, campaign_id, insight_type, context_data, user)
    - Validates campaign ownership and insight_type.
    - Calls InsightGenerator.generate_campaign_insight(...).
    - Rate-limited.
- generate_domain_insight(db, campaign_id, domain_data, user)
    - Validates ownership.
    - Calls InsightGenerator.generate_domain_insight(...).
    - Rate-limited.
- generate_whitelist_insight(...) / generate_blacklist_insight(...)
    - Same pattern as above; operate on supplied whitelist/blacklist data.
- generate_batch_insights(db, campaign_id, insight_types, context_data, user)
    - Validates ownership and each insight_type.
    - Rate limit is multiplied by len(insight_types).
    - Loops through types, collecting successes and logging failures.
    - Returns {insights, failed_insights, generated_at, total_insights}.
- get_campaign_insights(db, campaign_id, insight_type=None, user=None)
    - Validates ownership.
    - Queries AIInsight (optionally filtered by insight_type), newest first.
    - Returns a list of {id, insight_type, content, created_at} plus totals.
- delete_insight(db, insight_id, user)
    - Validates ownership by joining AIInsight → Campaign.
    - Delegates delete to InsightGenerator.delete_insight(...).
    - Calls _clear_insight_cache(...) (currently a stub).
- clear_campaign_insights(db, campaign_id, user)
    - Validates ownership.
    - Delegates to InsightGenerator.clear_campaign_insights(...).
    - Clears cache keys with pattern insight:{campaign_id}:*.

Chat
- chat_with_ai(db, user_id, message, campaign_id=None, context_data=None)
    - Enforces rate limit.
    - Gets/creates a ChatContext and delegates to InsightGenerator.chat_with_ai(...).
    - Saves chat context (Redis TTL 1 hour) and updates rate limit.
- get_chat_history(db, conversation_id, user)
    - Ownership check: conversation_id must start with str(user.id).
    - Loads context from cache; returns {conversation_id, messages, created_at, updated_at}.
- clear_chat_history(db, conversation_id, user)
    - Same ownership check; deletes the cached chat context key.

Status & Infra
- get_ai_status()
    - Returns whether the service is “operational” (API key present) or “unconfigured,” plus cache and placeholders for future metrics.

#### Rate Limiting (Redis)
- Keys:
    - Per-minute: rate_limit:{user_id}:minute (expires in 60s)
    - Per-hour: rate_limit:{user_id}:hour (expires in 3600s)
- _check_rate_limit(user_id, multiplier=1):
    - Blocks if current + multiplier exceeds configured thresholds.
- _update_rate_limit(user_id, multiplier=1):
    - Increments both counters and sets/refreshes expirations.

Batch safety: For batch insight generation, multiplier=len(insight_types) prevents overuse.

#### Chat Context (Redis)
- Conversation ID format
    - With campaign: "{user_id}:{campaign_id}"
    - General chat: "{user_id}:general"
- Cache key
    - chat_context:{conversation_id}
- TTL
    - 1 hour (setex with 3600 seconds)

#### Errors You’ll See
- NotFoundError("Campaign") / NotFoundError("Insight")
    - Ownership or existence failed.
- ValidationError(...)
    - Invalid insight type or rate limit exceeded.

#### Notes & Gotchas
- Missing json import: _save_chat_context(...) uses json.dumps(...) but json isn’t imported at the top of the file (it’s only imported inside _get_chat_context_from_cache).
    - ➜ Fix: add import json at the top.
- Cache-clearing stubs: _clear_insight_cache(...) is a placeholder. If you cache insights elsewhere, implement proper invalidation.
- Ownership check for chat history: Uses conversation_id.startswith(str(user.id)). This assumes your conversation IDs always start with the user’s UUID string. Keep the format consistent.
- Hardcoded Redis config: host='localhost', db=1 appears in multiple methods. Consider centralizing via AIConfig/env vars.

### insight_generator.py

### routes.py

### schemas.py

## auth_service

### __init__.py

### dependencies.py

### example_usage.py

### firebase_verify.py

### routes.py

## campaign_service

### controllers.py

### routes.py

### schemas.py

## common

### __init__.py

### exceptions.py

### logging.py

### schemas.py

### utils.py

## config

### __init__.py

### database.py

### redis.py

### settings.py

## db

### migrations

#### env.py

### __init__.py

### base.py

### models.py

## report_service

### exports.py

### pdf_generator.py

### routes.py

### storage.py

### uploads.py

## scoring_service

### config.py

### controllers.py

### explain.py

### normalize.py

### outliers.py

### preprocesses.py

### routes.py

### schemas.py

### scoring.py

### weighting.py

## scripts

### stat_workers.bat

### start_workers.sh

## worker

### __init__.py

### celery.py

### tasks.py

## main.py


