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
#### Overview
InsightGenerator is the core service that talks to OpenAI, builds prompts, caches results in Redis, and (for some paths) saves insights to the database. It also powers chat by formatting prompts and tracking context.

#### Responsibilities
- Prompt building for different insight types (campaign performance, optimization, overview; plus domain/whitelist/blacklist).
- OpenAI calls using environment-driven settings from AIConfig.
- Caching insights in Redis to avoid duplicate compute (keyed by campaign + insight type + context hash).
- Persistence of certain insights to AIInsight in the database.
- Chat workflow for user questions with optional campaign context.

#### Key Flows
1. Campaign Insight Generation
generate_campaign_insight(campaign_id, insight_type, context_data)
    - Cache check: compute a stable cache key from (campaign_id, insight_type, context_data) and return if found.
    - Fetch campaign from DB (required).
    - Build prompt via _build_insight_prompt(...) using PromptTemplates.
    - Call OpenAI, receive formatted text.
    - Assemble result object and cache it (TTL from AIConfig).
    - Persist to DB (AIInsight) and return.

2. Domain / Whitelist / Blacklist Insights
    - generate_domain_insight(campaign_id, domain_data)
    - generate_whitelist_insight(campaign_id, whitelist_data)
    - generate_blacklist_insight(campaign_id, blacklist_data)

    Each builds a template-driven prompt (PromptTemplates.DOMAIN_ANALYSIS_PROMPT, etc.), calls OpenAI, and returns a structured payload (with timestamps and the input that was analyzed).
    - Note: These three do not save to DB in this file; they just return the result.

3. Chat  
chat_with_ai(user_id, message, campaign_id=None, context=None)
    - Use or create a ChatContext and add user message.
    - Build a chat prompt with optional campaign metadata (platform, goal, channel).
    - Call OpenAI with a system prompt (PromptTemplates.CHAT_SYSTEM_PROMPT) + the user prompt.
    - Append AI reply to the context and return {response, conversation_id, timestamp, context_summary}.

#### Important Methods
- _build_insight_prompt(insight_type, context_data, campaign)  
Chooses the right template:
    - performance → PERFORMANCE_INSIGHT_PROMPT
    - optimization → OPTIMIZATION_INSIGHT_PROMPT
    - campaign_overview → CAMPAIGN_OVERVIEW_PROMPT
    - otherwise → ValidationError
- _build_chat_prompt(message, context)
    - Wraps the user’s question and (if available) campaign metadata into CHAT_USER_PROMPT.
- _call_openai(prompt, system_prompt=None)  
Sends messages=[{role:system?}, {role:user}] to openai.ChatCompletion.create(...) with:
    - model = AIConfig.OPENAI_MODEL
    - max_tokens = AIConfig.OPENAI_MAX_TOKENS
    - temperature = AIConfig.OPENAI_TEMPERATURE
- Caching helpers
    - _get_cache_key(...) → insight:{campaign_id}:{insight_type}:{md5(context_json)}
    - _get_cached_insight(key) / _cache_insight(key, data)
- Persistence helpers
    - _save_insight_to_db(campaign_id, insight_type, content)
    - CRUD for AIInsight: get_campaign_insights(...), delete_insight(...), clear_campaign_insights(...)

#### Configuration & Dependencies
- Redis: redis.Redis(host='localhost', port=6379, db=1)  
    Used for insight caching. TTL from AIConfig.CACHE_TTL.
- OpenAI: API key and model settings pulled from AIConfig (OPENAI_API_KEY, OPENAI_MODEL, etc.).
- SQLAlchemy Session: Provided at init; used for campaign lookup and saving insights.

#### Notes & Gotchas
- Template placeholders: *.format(**data) requires all fields present. Missing keys in domain_data/whitelist_data/blacklist_data/context_data will raise errors. Consider validating inputs before formatting.
- DB writes: Only generate_campaign_insight(...) saves to DB here. If you expect domain/whitelist/blacklist insights to persist, add save logic for those paths.
- API compatibility: Code uses openai.ChatCompletion.create(...). If you upgrade the OpenAI SDK, you may need to update to the newer chat API.
- Redis config: Host/DB are hardcoded. Consider centralizing via AIConfig/env vars for different environments.

### routes.py
#### Overview
Defines the HTTP API for AI features using FastAPI. Routes are grouped under /ai and secured with get_current_user. Each handler:
- Gets a DB session (get_db)
- Validates the current user
- Delegates work to AIController
- Maps domain errors to HTTP error codes

#### Endpoints
POST /ai/insights/generate → Generate a single campaign insight
- Body: InsightRequest (campaign_id, insight_type, context_data)
- Response: InsightResponse
- Errors: 400 (validation / not found), 500 (unexpected)

POST /ai/insights/domain → Generate insight for one domain
- Body: DomainInsightRequest (campaign_id, domain_data)
- Response: InsightResponse
- Errors: 400, 500

POST /ai/insights/whitelist → Analyze whitelist
- Body: WhitelistInsightRequest (campaign_id, whitelist_data)
- Response: InsightResponse
- Errors: 400, 500

POST /ai/insights/blacklist → Analyze blacklist
- Body: BlacklistInsightRequest (campaign_id, blacklist_data)
- Response: InsightResponse
- Errors: 400, 500

POST /ai/chat → Chat with the AI assistant
- Body: ChatRequest (message, optional campaign_id, optional context_data)
- Response: ChatResponse
- Errors: 400, 500

GET /ai/insights/{campaign_id} → List insights for a campaign
- Query (optional): insight_type
- Response: { campaign_id, insights[], total_insights, insight_types[] }
- Errors: 404 (not found), 500

DELETE /ai/insights/{insight_id} → Delete a single insight
- Response: { "message": "Insight deleted successfully" }
- Errors: 404, 500

DELETE /ai/insights/campaign/{campaign_id} → Clear all insights for a campaign
- Response: { "message": "Campaign insights cleared successfully" }
- Errors: 404, 500

GET /ai/insights/types → Discover available insight types
- Response: { insight_types: [...], descriptions: {...} }

GET /ai/chat/history/{conversation_id} → Fetch chat history
- Response: { conversation_id, messages[], created_at, updated_at }
- Errors: 404, 500

DELETE /ai/chat/history/{conversation_id} → Clear chat history
- Response: { "message": "Chat history cleared successfully" }
- Errors: 404, 500

#### How it’s wired
Dependencies
- get_db → SQLAlchemy Session
- get_current_user → Authenticated user object

Controller
- AIController executes validations, rate limits, caching, and calls the underlying services

Schemas
- Request/response validation via Pydantic models (e.g., InsightRequest, ChatResponse)

#### Notes & Gotchas
- Import path mismatch: from ai_service.controllers import AIController but earlier files define it in ai_service.ai_controller.
    - ➜ Fix: Align the import to the actual module name.
- Error codes consistency: Some routes map NotFoundError to 400 (e.g., generate endpoints), others to 404 (GET/DELETE).
    - ➜ Consider standardizing (typically 404 for missing resources).
- context_data in /chat: Passed into the route but not used by AIController.chat_with_ai downstream.
    - ➜ Either forward it or remove from the schema to avoid confusion.

### schemas.py
#### Overview
Defines the request/response shapes for the AI API using Pydantic. These models validate inputs, document fields, and ensure consistent responses across routes.

#### Requests
InsightRequest
- campaign_id: UUID — target campaign
- insight_type: str — e.g., "performance" | "optimization" | "whitelist" | "blacklist" | "domain" | "campaign_overview"
- context_data: Dict[str, Any] = {} — extra inputs the template needs

DomainInsightRequest
- campaign_id: UUID
- domain_data: Dict[str, Any] — must include fields required by the domain template (e.g., domain, score, etc.)

WhitelistInsightRequest
- campaign_id: UUID
- whitelist_data: Dict[str, Any]

BlacklistInsightRequest
- campaign_id: UUID
- blacklist_data: Dict[str, Any]

ChatRequest
- message: str — 1–1000 chars
- campaign_id: Optional[UUID] — if provided, the AI can tailor answers with campaign metadata
- context_data: Dict[str, Any] = {} — reserved for future context enrichment

BatchInsightRequest
- campaign_id: UUID
- insight_types: List[str] — e.g., ["performance", "optimization"]
- context_data: Dict[str, Any] = {} — shared context for each insight

#### Responses
InsightResponse
- campaign_id: UUID
- insight_type: str
- content: str — AI-generated text
- generated_at: datetime
- Optional enrichments:
    - context_data: Dict[str, Any]
    - domain: str
    - whitelist_data: Dict[str, Any]
    - blacklist_data: Dict[str, Any]

#### Notes
Upstream services return ISO strings for dates/UUIDs; Pydantic auto-parses them into datetime/UUID.

ChatResponse
- response: str — AI reply
- conversation_id: str — "user_id:campaign_id" or "user_id:general"
- timestamp: datetime
- context: Optional[str] — short summary of recent messages

BatchInsightResponse
- campaign_id: UUID
- insights: List[InsightResponse]
- generated_at: datetime
- total_insights: int
- failed_insights: List[str] — any types that failed

InsightSummary
- Compact record for list views:
- insight_id: UUID
- insight_type: str
- content: str
- created_at: datetime
- campaign_id: UUID

CampaignInsightsResponse
- campaign_id: UUID
- insights: List[InsightSummary]
- total_insights: int
- insight_types: List[str] — distinct types present

AIStatusResponse
- service_status: str — "operational" or "unconfigured"
- openai_configured: bool
- cache_enabled: bool
- rate_limit_remaining: Optional[int]
- last_request_time: Optional[datetime]

InsightTypeInfo & InsightTypesResponse
- InsightTypeInfo — per-type docs:
    - type: str
    - description: str
    - required_context: List[str]
    - optional_context: List[str]
- InsightTypesResponse
    - insight_types: List[str]
    - descriptions: Dict[str, str]
    - type_details: List[InsightTypeInfo] = []

ErrorResponse
- error: str — human-readable message
- error_code: Optional[str] — machine-friendly code
- details: Optional[Dict[str, Any]]
- timestamp: datetime — defaults to utcnow()

#### Validation Highlights
- ChatRequest.message must be 1–1000 characters.
- ChatMessage.role matches ^(user|assistant)$.
- Datetime/UUID strings are auto-parsed by Pydantic if formatted correctly.

## auth_service

### __ init __.py
#### Overview
This file turns auth_service into a clean import surface (aka a “barrel”). It re-exports the most-used auth helpers, models, and the FastAPI router so other modules can simply import from auth_service instead of digging through submodules.

#### What it Exports
Token verification
- verify_firebase_token — Validates Firebase ID tokens.

FastAPI dependencies & security
- get_current_user — Requires a valid user; raises if unauthenticated.
- get_current_user_optional — Returns a user if present, otherwise None.
- security — FastAPI HTTPBearer/security scheme used by dependencies.

Pydantic models (auth flows)
- UserCreate — Signup payload shape.
- UserResponse — User object shape returned by the API.
- LoginRequest — Login payload shape.
- LoginResponse — Login response (e.g., tokens).

Router
- auth_router — The FastAPI router that exposes auth endpoints (e.g., login, signup, etc.).

These names are also listed in __ all __, which defines the package’s public API when using from auth_service import * and helps with IDE/autocomplete clarity.

#### Why this Matters
- Ergonomics: Consumers can write from auth_service import get_current_user, auth_router instead of importing from multiple files.
- Encapsulation: Internal structure can change without breaking imports elsewhere, as long as the barrel re-exports stay stable.

#### Notes & Gotchas
- Keep the barrel in sync with actual submodules (firebase_verify.py, dependencies.py, routes.py) so the exports remain valid.
- If you rename or move internal modules, update the re-exports here to avoid import errors across the app.

### dependencies.py
#### Overview
Helpers for authenticating requests in FastAPI using Firebase ID tokens. Exposes:
- Security scheme (HTTPBearer)
- Request models for login/signup
- Response models for returning user info
- Two FastAPI dependencies:
    - get_current_user (requires valid token)
    - get_current_user_optional (intended to be optional)

#### What It Defines
Security
- security = HTTPBearer()
    - Parses the Authorization: Bearer <token> header for each protected route.

Schemas (Pydantic)
- UserCreate: payload for creating a user (firebase_uid, email, name, optional organization_id)
- UserResponse (extends BaseSchema): shape of user data returned by the API
    - Config.from_attributes = True (ORM compatibility)
- LoginRequest: { token: <Firebase ID token> }
- LoginResponse: { user: UserResponse, message: "Login successful" }

Dependencies (FastAPI)
- get_current_user(credentials: HTTPAuthorizationCredentials)
    - Requires a valid Firebase token (via verify_firebase_token)
    - On success: returns user_data (dict) and logs the email
    - On failure: raises AuthenticationError
- get_current_user_optional(credentials: HTTPAuthorizationCredentials)
    - Intended to not fail the request:
        - If token is valid → returns user_data
        - If token invalid/missing → returns None (and logs)

#### How It Works (Request Flow)
1. A route includes Depends(get_current_user) or Depends(get_current_user_optional).
2. HTTPBearer extracts the Bearer token from the header.
3. verify_firebase_token(token) is awaited to validate and decode claims.
4. If valid: a user dict is returned to the route handler; if not: either error (required) or None (optional).

#### Notes & Gotchas
- Optional auth isn’t optional yet: security = HTTPBearer() defaults to auto_error=True, which rejects requests without a token before get_current_user_optional runs.
- Return types: The dependencies return a dict (user_data). If you want typed responses, consider mapping to UserResponse before returning from route handlers.
- Logging: On successful auth, logs User authenticated: <email>; on failures, logs warnings/errors—useful for audit trails.
- Imports: status is imported but not used—safe to remove.
- Error handling: Unexpected exceptions in get_current_user become AuthenticationError("Authentication failed"), which your global handlers should translate into an HTTP error.

### example_usage.py
#### Overview
This file shows example FastAPI endpoints for authentication. It uses the auth dependencies (get_current_user, get_current_user_optional) and returns mock user data. Use it as a template; it does not hit a real database yet.

#### Routes
POST /auth/login → Login with Firebase token
- Body: LoginRequest { token }
- Returns: LoginResponse { user, message }
- Current behavior: Returns mock UserResponse (no DB).
- Real flow (to implement):
    1. Verify Firebase token
    2. Create or fetch user in DB
    3. Return real user data

POST /auth/register → Register a new user
- Body: UserCreate { firebase_uid, email, name, organization_id? }
- Returns: UserResponse
- Current behavior: Returns mock user using request fields.

GET /auth/me → Get current user (auth required)
- Auth: Depends(get_current_user) (must pass a valid Bearer token)
- Returns: UserResponse built from token claims (uid, email, name).

GET /auth/optional → Optional authentication
- Auth: Depends(get_current_user_optional)
- Returns: APIResponse
    - If authenticated → user info
    - If not → data=None, friendly message

POST /auth/verify → Verify token is valid
- Auth: Depends(get_current_user)
- Returns: APIResponse { success: true, data: { verified: true, user_id } }
- Also: Logs the verified email.

#### How It Works (Simple Flow)
1. FastAPI parses the Authorization: Bearer <token> header.
2. get_current_user / get_current_user_optional call verify_firebase_token(...).
3. On success, route handlers receive a current_user dict and return responses using Pydantic models.

#### Notes & Gotchas (Beginner-Friendly)
- Mock data only: login and register return hardcoded users. Replace with real DB reads/writes.
- Optional auth really optional?  
To allow no token on /auth/optional, make sure security = HTTPBearer(auto_error=False) inside auth_service/dependencies.py. Otherwise FastAPI will reject missing tokens before your handler runs.
- Claim names: /auth/me expects current_user['uid'], ['email'], ['name']. Ensure verify_firebase_token returns those exact keys.
- Timestamps/IDs: The example sets ISO strings for created_at/updated_at and fixed IDs. In production, use real DB values (Pydantic will parse ISO timestamps).
- APIResponse shape: Make sure your common.schemas.APIResponse matches the { success, data, message } pattern shown here

### firebase_verify.py
#### Overview
Initializes the Firebase Admin SDK and provides a single helper, verify_firebase_token, which validates a Firebase ID token and returns basic user info. In development, if Firebase isn’t initialized, it falls back to mock user data so the app can still run.

#### What It Does
SDK init (on import)
- Reads a credentials file path from settings.FIREBASE_CREDENTIALS_PATH.
- If present, loads the service account JSON and initializes Firebase Admin.
- Logs success/warnings/errors so you can see whether auth is active.

verify_firebase_token(token: str) -> dict
- (Dev mode) If Firebase isn’t initialized, returns a mock user:
    - { "uid": "dev-user-123", "email": "dev@example.com", "name": "Development User", "email_verified": true }
- Strips a leading "Bearer " prefix if present.
- Validates the token with auth.verify_id_token(...).
- Returns a small dict: { uid, email, name, email_verified }.
- Raises friendly errors for invalid or expired tokens.

#### How It’s Used (Typical Flow)
1. A FastAPI dependency extracts the Bearer token.
2. It calls await verify_firebase_token(token).
3. On success, your route gets a user dict; on failure, the dependency raises an auth error.

#### Configuration
settings.FIREBASE_CREDENTIALS_PATH
- Path to your Firebase service account JSON (e.g., set via env var).
- If missing or "None", Firebase auth is disabled and the dev mock user is returned.

#### Notes & Gotchas 
- Dev fallback: Great for local development, but make sure you provide real credentials in staging/production so tokens are actually verified.
- Bearer prefix: FastAPI’s HTTPAuthorizationCredentials.credentials usually doesn’t include "Bearer "; the code still safely strips it if present.
- Async function, sync call: verify_firebase_token is async but calls a sync function (auth.verify_id_token). It’s fine for most apps; if you expect very high traffic, consider moving verification to a thread pool to avoid blocking the event loop.
- Logging: The code logs init state and errors, but does not log tokens (good for security).
- One-time init: Firebase is initialized at import; if credentials change at runtime, you’ll need to restart the app.

### routes.py
#### Overview
FastAPI routes for real authentication backed by Firebase + your database. These endpoints:
- Verify a Firebase ID token
- Create or fetch a User row
- Return responses wrapped in a common APIResponse
- Base path: /api/v1/auth

#### Endpoints
POST /api/v1/auth/login
- Login with a Firebase token.
- Body: LoginRequest { token }
- Flow:
    1. verify_firebase_token(token) → get { uid, email, name }
    2. Find user by firebase_uid; if missing, create it
    3. Return APIResponse { success, data: UserResponse, message }

GET /api/v1/auth/profile
- Get the current user’s profile (authentication required).
- Auth: Depends(get_current_user)
- Returns: APIResponse { data: UserResponse }

PUT /api/v1/auth/profile
- Update the current user’s name.
- Auth: Depends(get_current_user)
- Params: name: str (currently a query param)
- Returns: APIResponse { data: UserResponse, message }

How It Works (Simple)
- Login
    - Validate token with Firebase
    - Upsert the user in your DB
    - Return normalized UserResponse
- Profile (GET/PUT)
    - Require a valid bearer token
    - Read or update the user record
    - Return UserResponse inside APIResponse

Notes & Gotchas
- Dependency type mismatch:
    - get_current_user (from earlier code) returns a dict of token claims, but these handlers type-hint current_user: User. If it’s actually a dict, UserResponse.model_validate(current_user) will fail.
    - ➜ Fix one of these:
        - Make get_current_user load the ORM User from the DB and return it, or
        - Keep returning a dict, but then fetch the User inside each route using uid, or change the response building to accept dicts.
- PUT body vs query:
    - name: str is currently a query parameter. Most APIs send updates in JSON.
- Unused imports: HTTPException, status aren’t used — safe to remove.
- Duplicate users / race safety:
    - If two logins for the same uid happen at once, you could create duplicates unless there’s a unique index on User.firebase_uid. Add it at the DB level.
- Dev-mode tokens:
    - Your Firebase verifier may return a mock user when credentials aren’t configured. That’s great for local dev, but be sure real environments provide credentials to avoid fake accounts.
- Data defaults:
    - Name is set to the email prefix if Firebase doesn’t provide one — good fallback.

## campaign_service

### controllers.py
#### Overview
CampaignController is the CRUD + workflow layer for campaigns and campaign templates. It:
- Creates/reads/deletes campaign templates
- Creates/reads/updates/deletes campaigns
- Enforces ownership checks
- Tracks status and progress for long-running processing
- Uses SQLAlchemy sessions and raises friendly NotFoundError / ValidationError when something’s off

#### Responsibilities at a Glance
Templates
- create_template – add a new template for the signed-in user
- get_user_templates – list user’s templates (newest first)
- get_template_by_id – fetch a single template (must belong to user)
- delete_template – delete a template (blocked if any campaign uses it)

Campaigns
- create_campaign – create a campaign (optionally linked to a template)
- get_user_campaigns – list campaigns with pagination + optional status filter
- get_campaign_by_id – fetch a single campaign (must belong to user)
- update_campaign_status – move a campaign through statuses; sets completed_at when done
- update_campaign_progress – update processed_records/total_records (supports background tasks)
- set_campaign_file_path – attach a file path (e.g., uploaded CSV)
- delete_campaign – delete if not PROCESSING or COMPLETED

#### Data & Types Used
- Models: Campaign, CampaignTemplate, User
- Schemas: CampaignCreate, CampaignTemplateCreate, CampaignStatus
- Errors: NotFoundError, ValidationError
- IDs: uuid.UUID
- Return for lists: tuple[List[Campaign], int] → (items, total_count)

#### Behavior Notes
- Ownership enforced: Reads and writes always filter by user.id. If not found for the user, a NotFoundError is raised.
- Statuses: When you mark a campaign COMPLETED, completed_at is set to the current UTC time.
- Progress tracking: update_campaign_progress updates counts so the UI can show a progress bar.
- Safe deletions: You can’t delete a campaign that’s already PROCESSING or COMPLETED.

#### Common Flows
Create a Template → Create a Campaign
1. create_template(...)
2. create_campaign(...) (optionally pass template_id)
3. Background processing runs…
4. update_campaign_progress(...) as records are processed
5. update_campaign_status(..., COMPLETED)

List Campaigns (with paging)
- get_user_campaigns(db, user, skip=0, limit=50, status=None)
Returns (campaigns, total) — use total to paginate on the client.

##### Notes & Gotchas (Keep it Simple)
- Template not used in creation (yet):
    - In create_campaign, the code loads the template if template_id is provided but doesn’t apply its settings to the campaign. If templates should prefill fields, add that logic.
- Unique constraints:
    - Consider DB-level unique constraints (e.g., template or campaign names per user) if your product requires it.
- Pagination performance:
    - total = query.count() runs a separate COUNT query; for very large tables, you might want cached counts or keyset pagination.
- Background tasks without user context:
    - update_campaign_progress and set_campaign_file_path support calls without a user (useful for workers). They fall back to fetching by campaign_id.
- Deletion safety:
    - Templates in use by any campaign can’t be deleted (ValidationError), which prevents orphaned references.

### routes.py
#### Overview
Exposes REST endpoints for campaigns and campaign templates. All routes are under /api/v1/campaigns and require authentication via get_current_user. The router delegates business logic to CampaignController and returns results wrapped in a common APIResponse.

#### Endpoints (What each one does)
Templates
- POST /templates → Create a template
    - Body: CampaignTemplateCreate → returns CampaignTemplateResponse
- GET /templates → List my templates
    - Returns List[CampaignTemplateResponse] (newest first)
- GET /templates/{template_id} → Get one template by ID
    - Returns CampaignTemplateResponse (404 if not mine / not found)
- DELETE /templates/{template_id} → Delete a template
    - Fails if the template is used by any campaign

Campaigns
- POST `/` → Create a campaign
    - Body: CampaignCreate → returns CampaignResponse
- GET `/` → List my campaigns (paged)
    - Query: skip (default 0), limit (default 50, max 100), status?
    - Returns CampaignListResponse { campaigns[], total }
- GET /{campaign_id} → Get one campaign by ID
    - Returns CampaignResponse (404 if not mine / not found)
- PUT /{campaign_id}/status → Update campaign status
    - Query: status (required), error_message? → returns updated CampaignResponse
- PUT /{campaign_id}/progress → Update processing progress
    - Query: processed_records (required), total_records? → returns updated CampaignResponse
- DELETE /{campaign_id} → Delete a campaign
    - Only allowed if status is not PROCESSING or COMPLETED

File Uploads
- POST /{campaign_id}/upload → Upload a CSV/Excel for processing
    - File: UploadFile (must end with .csv, .xlsx, or .xls)
    - Saves a placeholder file path on the campaign and returns updated CampaignResponse

#### How it works (in simple terms)
- Auth first: Every handler uses Depends(get_current_user) to ensure the caller is signed in.
- Controller handles logic: The route calls CampaignController methods for ownership checks, CRUD, and status/progress updates.
- Consistent responses: All results are wrapped in APIResponse { success, data, message? }.

#### Models you’ll see
- Requests: CampaignCreate, CampaignTemplateCreate, CampaignStatus (as a query param)
- Responses: CampaignResponse, CampaignTemplateResponse, CampaignListResponse, APIResponse

#### Notes & gotchas
- Import path check: The router imports CampaignController from campaign_service.controllers. If your file is campaign_controller.py, update the import accordingly.
- Query vs JSON bodies: Status/progress updates use query parameters. Many APIs prefer JSON bodies for updates—feel free to add small Pydantic models if you want to switch.
- File checking: Upload validation is by filename extension only. In production, also check MIME type, size limits, and possibly scan for viruses.
- Storage TODO: The upload handler only saves a path string on the campaign. You’ll likely replace this with real storage (e.g., S3/GCS) and a background job to process the file.
- Ownership enforcement: All reads/writes filter by the current user. If an item isn’t yours, you’ll get a 404 (not found) rather than a 403 (forbidden)—that’s by design here.

Errors:
- ValidationError → 400
- NotFoundError → 404
- Unknown issues → 500

#### Mental model
The routes are thin wrappers: they authenticate, parse inputs, call CampaignController, and return standardized responses. All the real rules (ownership, status transitions, deletions) live in the controller—keeping your API layer clean and easy to read.

### schemas.py
#### Overview
Defines the data shapes for campaigns and campaign templates. These are used by your API routes and controllers to validate inputs and format responses (beginner-friendly, predictable JSON).

#### Enums (allowed values)
- CampaignType: trade_desk, pulsepoint
- CampaignGoal: awareness, action
- Channel: ctv, display, video, audio
- AnalysisLevel: domain, supply_vendor
- CampaignStatus: pending, processing, completed, failed

#### Request/Response Models
CampaignTemplateCreate (request)  
Fields:
- name (1–255 chars)
- campaign_type (CampaignType)
- goal (CampaignGoal)
- channel (Channel)
- ctr_sensitivity (bool)
- analysis_level (AnalysisLevel)  

Use when creating a template.

CampaignTemplateResponse (response)
- Extends your BaseSchema (your common response base; e.g., id/timestamps if defined there).
- Fields mirror CampaignTemplateCreate plus:
    - user_id (UUID)

Returned when reading templates.

CampaignCreate (request)
Fields:
- name (required)
- template_id (UUID, optional)

If you don’t pass template_id, you must include all of these:
- campaign_type, goal, channel, ctr_sensitivity, analysis_level

Validation: a model_validator enforces this rule and raises a clear error if any required fields are missing.

CampaignResponse (response)  
Extends BaseSchema. Fields:
- name
- status (CampaignStatus)
- template_id (UUID | null)
- file_path (str | null)
- total_records (int | null)
- processed_records (int | null)
- error_message (str | null)
- completed_at (datetime | null)
- user_id (UUID)

Returned when reading or mutating campaigns.

CampaignListResponse (response)
- campaigns: List[CampaignResponse]
- total: int (for pagination)

#### Notes & gotchas (beginner-friendly)
- Template vs. fields: If template_id is missing, the validator requires all setup fields; this prevents half-configured campaigns.
- Enum safety: Enums keep values consistent across the system (no typos like "TradeDesk" vs "trade_desk").
- BaseSchema: Responses inherit from your common base—keep it consistent (e.g., id, created_at, updated_at) so all responses look alike.

## common

### __init__.py
#### Overview
Makes common easy to import by re-exporting the most-used helpers, base schemas, logging, utilities, and exception types. Instead of importing from several files, other modules can do:
from common import APIResponse, logger, ValidationError — nice and tidy.

#### What It Exports
Schemas
- APIResponse — standard { success, data, message } wrapper
- PaginatedResponse — list results + pagination info
- BaseSchema — shared Pydantic base (e.g., id, timestamps if your project defines them)

Logging
- setup_logging — configure logging for the app
- logger — ready-to-use logger

Utilities
- generate_uuid() — create IDs
- get_current_timestamp() — UTC timestamp
- safe_get(obj, path, default) — read nested values safely
- format_error_message(exc) — normalize error text
- validate_uuid(value) — quick UUID checker

Exceptions
- CaliberException — project base exception
- AuthenticationError, AuthorizationError
- NotFoundError, ValidationError, DatabaseError, ExternalServiceError
- handle_exception — central handler hook

#### Why This Matters
- Cleaner imports across the codebase
- Consistent response shapes, logging, and error handling
- Single source for common helpers, reducing duplication

Keep this barrel in sync with actual module contents (schemas.py, logging.py, utils.py, exceptions.py). If you rename/move things, update the exports here.

### exceptions.py
#### Overview
Defines project-wide error types and a helper to normalize unexpected exceptions. These make your API responses consistent and easier to debug.

#### Exception classes
All extend CaliberException, which itself extends FastAPI’s HTTPException and sets an HTTP status code + message.
- CaliberException(detail, status_code=400)
    - Base class: create custom HTTP errors with a message and status.
- AuthenticationError("Authentication failed") → 401 Unauthorized
    - Use when token/login is invalid.
- AuthorizationError("Access denied") → 403 Forbidden
    - User is authenticated but not allowed to do the action.
- NotFoundError(resource="Resource") → 404 Not Found
    - Say NotFoundError("Campaign") to return "Campaign not found".
- ValidationError(detail="Validation failed") → 422 Unprocessable Entity
    - Use for bad inputs (missing fields, wrong formats, etc.).
- DatabaseError(detail="Database operation failed") → 500 Internal Server Error
    - Wrap DB failures.
- ExternalServiceError(service, detail="External service error") → 503 Service Unavailable
    - For upstream issues (e.g., OpenAI, Firebase): message like "OpenAI: timeout".

#### Helper: handle_exception(error, context=None) -> CaliberException
Converts random Python exceptions into your structured ones:
1. If it’s already a CaliberException → return as-is.
2. ValueError → ValidationError.
3. KeyError → NotFoundError("Required field: <key>").
4. Anything else → generic CaliberException with 500; if context is provided, it’s prefixed in the error message.

Why it’s useful: Central place to translate errors before sending an HTTP response.

#### Notes & tips
- These exceptions are HTTP-aware (carry proper status codes), so FastAPI will render them as JSON errors automatically.
- Use specific exceptions where possible (auth vs. validation) to get the right status code in clients and logs.

### logging.py
#### Overview
Central place to configure logging for the whole app and to provide a ready-to-use project logger.

#### What it does
setup_logging()
- Sets log level based on environment:
    - production → INFO
    - otherwise → DEBUG
- Sets a clean format: time - logger - level - message
- Sends logs to stdout (good for Docker/K8s)
- Quiets noisy libs:
    - sqlalchemy.engine → WARNING
    - urllib3 → WARNING
- logger
    - A named logger you can import anywhere: "caliber"

#### Notes & gotchas
- Call setup_logging() once at startup so the format and levels apply everywhere.
- In production, logs default to INFO. If you need more detail temporarily, set ENVIRONMENT to something else or adjust the level.

### schemas.py
#### Overview
Shared response wrappers and a base schema for models. These keep your API payloads consistent and easy to document.

#### Response Wrappers
BaseResponse  
Generic envelope for API replies.
- success: bool — did the request succeed?
- data: Any | null — main payload (any shape)
- message: str | null — human-friendly note
- errors: List[str] | null — list of error messages (if any)

Use this shape for every endpoint so clients always know where to look.

APIResponse  
Just an alias of BaseResponse. Use it as your standard response model.

PaginatedResponse (extends APIResponse)  
For list endpoints with pages.
- data: List[Any] — the current page of items
- total: int — total items across all pages
- page: int >= 1 — current page number
- per_page: int [1..100] — items per page
- has_next: bool — is there a page after this one?
- has_prev: bool — is there a page before this one?

Tip: Return your items (e.g., CampaignResponse[]) in data, not raw DB rows.

#### Base Model
BaseSchema  
Common fields for DB-backed objects.
- id: UUID
- created_at: datetime
- updated_at: datetime

Config:
- from_attributes = True → lets Pydantic build models directly from ORM objects (SQLAlchemy), not just dicts.

Have your entity responses (e.g., CampaignResponse) inherit from BaseSchema so all objects include id/timestamps automatically.

#### Notes & gotchas
- PaginatedResponse.data is required (not optional like in BaseResponse). Always return a list there.
- from_attributes=True means you can do: UserResponse.model_validate(user_orm_obj) and Pydantic will map fields.
- Keep message short and user-facing; put technical details in logs or errors.

### utils.py
#### Overview
Tiny helpers used across the app for IDs, timestamps, safe dict access, error messages, and UUID checks. They keep code short, readable, and consistent.

#### What each function does
generate_uuid() -> uuid.UUID
- Create a brand-new random UUID.
- Use when: you need an ID for a new record.

get_current_timestamp() -> datetime
- Return the current UTC time as a datetime.
- Use when: you need a created/updated timestamp.

safe_get(data: Dict, key: str, default=None) -> Any
- Safely read data[key] like dict.get, but won’t crash if data isn’t a dict.
- Logs a warning and returns default on problems.

format_error_message(error: Exception, context: str | None = None) -> str
- Turn an exception into a short, readable message, with optional context prefix.

validate_uuid(uuid_string: str) -> bool
- Check if a string is a valid UUID format.

#### Notes & gotchas
- UTC, naive datetimes: get_current_timestamp() returns a naive UTC datetime (no timezone attached). If you need timezone-aware values, wrap with datetime.replace(tzinfo=timezone.utc) or use your ORM’s timezone features.
- safe_get is forgiving: It catches KeyError, AttributeError, and TypeError. If data isn’t a dict (or is None), you’ll still get the default instead of a crash.
- validate_uuid checks format only: It doesn’t check DB existence—just the string format.
- IDs are random: generate_uuid() creates non-sequential IDs (great for uniqueness; not ordered).

## config

### __init__.py
#### Overview
Makes the config package easy to use by re-exporting the most important pieces: application settings and Redis helpers. This way other modules can import from config directly without knowing the internal file layout.

#### What it exports
- settings — Your centralized app configuration (env-driven).
- redis_client — A ready-to-use Redis connection instance.
- get_redis — Helper/factory to obtain a Redis client (useful for DI or testing).

All three are listed in __all__, which defines the package’s public API.

#### Why it matters
- Cleaner imports: from config import settings, redis_client
- Encapsulation: You can refactor internals (settings.py, redis.py) without breaking imports elsewhere.

#### Notes
- Make sure settings reads from environment variables early in app startup so everything gets configured correctly.
- Prefer one shared Redis client per process (what redis_client gives you) to avoid unnecessary connections; use get_redis when you need to control lifecycle (tests, background jobs).

### database.py
#### Overview
Creates a database engine, a session factory, and a FastAPI dependency so each request gets a clean SQLAlchemy session that’s closed after use.

#### What each piece does
- engine = create_engine(settings.DATABASE_URL, pool_pre_ping=True, pool_recycle=300)
    - Connects SQLAlchemy to your DB using the URL from settings.DATABASE_URL (e.g., postgresql+psycopg2://user:pass@host/dbname).
    - pool_pre_ping=True checks connections before using them (prevents “stale connection” errors).
    - pool_recycle=300 (seconds) refreshes connections periodically—handy for cloud DBs that drop idle connections.
- SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    - Factory that creates Session objects bound to the engine.
    - autocommit=False → you control when to commit().
    - autoflush=False → SQL doesn’t auto-flush on every query (you can call flush() or commit() when you’re ready).
- def get_db(): ...
    - A FastAPI dependency that yields a session and always closes it at the end of the request.

    - Usage: db: Session = Depends(get_db)

#### Notes & gotchas 
- Set DATABASE_URL correctly (driver matters):
    - Postgres: postgresql+psycopg2://user:pass@host:5432/db
    - MySQL: mysql+pymysql://user:pass@host:3306/db
- One session per request: don’t share a Session across threads/requests. Always get it via Depends(get_db).
- Transactions: with autocommit=False, changes aren’t saved until you call db.commit(). On errors, call db.rollback().
- Async apps: this is the sync SQLAlchemy setup. If you switch to async, you’ll use create_async_engine, AsyncSession, and async_sessionmaker instead.


### redis.py
#### Overview
Creates a single Redis client for the app using settings.REDIS_URL, and exposes a tiny helper to fetch it. This keeps Redis usage simple and consistent across modules.

#### What it does
- redis_client = redis.from_url(settings.REDIS_URL, decode_responses=True)
    - Builds a pooled client from the URL (e.g., redis://:pass@host:6379/1).
    - decode_responses=True ⇒ you get strings back instead of bytes.
- get_redis() → returns the shared redis_client.

#### Why it matters
- One client, many callers: avoids opening new connections everywhere.
- Centralized config: switch hosts/DBs by changing REDIS_URL—no code changes.

#### Notes & gotchas 
- Set REDIS_URL: e.g., redis://localhost:6379/1 or with password redis://:password@host:6379/0.
- Strings in/out: thanks to decode_responses=True. If you need raw bytes, drop that flag.
- Errors: network issues raise redis.exceptions.ConnectionError—catch where appropriate.
- Time-to-live: use setex(key, ttl, value) or expire(key, seconds) if you want auto-expiring keys.
- Don’t create new clients per request: use this shared one to keep connections healthy and fast.

### settings.py
#### Overview
Central place to read configuration from environment variables (with sensible defaults). Uses:
- python-dotenv to load a local .env file
- pydantic-settings.BaseSettings for typed settings
- A single exported instance: settings = Settings()

#### What it configures (fields & defaults)
Database
- DATABASE_URL → default: postgresql://caliber_user:caliber_pass@localhost:5432/caliber_dev

Redis
- REDIS_URL → default: redis://localhost:6379/0

Firebase
- FIREBASE_CREDENTIALS_PATH → path to Firebase service account JSON

OpenAI
- OPENAI_API_KEY

AWS S3 (optional)
- AWS_ACCESS_KEY_ID
- AWS_SECRET_ACCESS_KEY
- AWS_BUCKET_NAME

Environment & security
- ENVIRONMENT → default: development
- SECRET_KEY → default: your-secret-key-here

API metadata
- API_V1_STR → default: /api/v1
- PROJECT_NAME → default: Caliber

CORS
- BACKEND_CORS_ORIGINS → default: ["http://localhost:3000", "http://localhost:5173"]

#### How it loads values
1. load_dotenv() loads variables from a local .env file into the process environment.
2. Settings() reads from environment variables (or uses the defaults above).
3. You use settings.X anywhere in the code.

#### Notes & gotchas
- One source of truth: Import the instance (settings), not the class.
- Production secrets: Never commit real keys to Git. Set them via environment or your secret manager.
- Driver in DATABASE_URL: For Postgres with psycopg2, use postgresql+psycopg2://....
- CORS origins: For multiple origins via env, consider a JSON list (e.g., ["https://app.example.com","http://localhost:5173"]) and parse if you later read from env.
- Pydantic versions: This pattern works with pydantic-settings. If you upgrade major versions, double-check config class syntax

## db

### migrations/env.py

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


