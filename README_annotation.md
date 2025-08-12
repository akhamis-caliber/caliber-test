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

### __ init __.py
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
#### Overview
Alembic’s environment script. It connects your SQLAlchemy models to Alembic so you can:
- Autogenerate migration files from model changes
- Run migrations against your database (online) or emit SQL (offline)

####What it does
Loads app config & models
- Adds project paths to sys.path so imports work
- Reads the DB URL from settings.DATABASE_URL
- Imports your app’s SQLAlchemy Base (backend.db.base.Base) so Alembic “sees” all tables

Configures Alembic
- Sets sqlalchemy.url at runtime (no hardcoded DSN in alembic.ini)
- Applies logging from the Alembic config file if present

Targets metadata
- target_metadata = Base.metadata → used for --autogenerate

Runs migrations
- Offline mode: generates SQL with bound literals (no DB connection)
- Online mode: creates an engine and executes migrations (uses NullPool)

#### Tips & gotchas
Models must be imported into Base
- If --autogenerate creates empty migrations, ensure all model modules are imported by backend.db.base so they’re included in Base.metadata.

Environment decides the DB
- settings.DATABASE_URL controls which database you migrate (dev/staging/prod). Double-check your .env before running upgrade.

Path tweaks
- The sys.path.append(...) lines make imports work when running Alembic from the repo root. If your layout changes, update these paths or set PYTHONPATH.

Offline vs. online
- Use offline to review SQL safely in CI or code review.
- Use online to actually apply changes.

Logging
- If alembic.ini sets logging, this script loads it—handy for debugging migration issues.

#### Mental model
migrations/env.py is Alembic’s bridge to your app: it knows where your DB is (from settings), what the schema should be (your Base.metadata), and how to run changes (offline/online).

### migrations/script.py.mako
#### What this file is
This is the template Alembic uses to create each new migration file. Alembic fills in the ${...} placeholders and writes a new file like migrations/versions/<timestamp>_<slug>.py.

#### What gets filled in
At the top, Alembic injects metadata:
- """${message} ... Create Date: ${create_date} — the docstring header (your message + timestamp).
- revision = ${repr(up_revision)} — unique ID for this migration.
- down_revision = ${repr(down_revision)} — the previous migration it builds on.
- branch_labels / depends_on — advanced features for branching or cross-migration deps (often None).
- ${imports} — any extra imports autogenerate needs (e.g., for enums).

The ${...} syntax is from Alembic’s Mako templating; Alembic replaces these when generating a migration.

#### The important parts you edit
- upgrade(): put schema changes that move the DB forward (create table/column/index, etc.).
- downgrade(): put the reverse of those changes so you can roll back.

You’ll use:
- op — Alembic’s “operations” API (schema changes).
- sa — SQLAlchemy types and helpers (e.g., sa.String, sa.Integer, sa.ForeignKey).

#### How autogenerate fits in
If you run --autogenerate, Alembic diff-scans your Base.metadata (your SQLAlchemy models) and tries to fill ${upgrades}/${downgrades} for you. Always review the generated operations and adjust as needed (especially defaults, constraints, and data migrations).

#### Tips & gotchas
- Don’t change revision/down_revision by hand; they define the migration graph.
- Always write a matching downgrade() so you can roll back.
- Non-nullable columns on existing tables need a server_default or a data backfill step before making them non-null.
- Data migrations (e.g., backfilling a new column) can be done inside upgrade() using op.execute(...) with raw SQL.
- If autogenerate misses something, it’s normal—add/adjust operations manually.

#### TL;DR
This template produces each migration file. You’ll mostly edit the upgrade() and downgrade() functions using op and sa to describe how the schema should change forward and backward.

### __ init __.py
#### Overview
Makes the db package easy to use and ensures all SQLAlchemy models are loaded when the package is imported.

#### What it does
- from .base import Base, BaseModel
Exposes your SQLAlchemy Base (for metadata/migrations) and a project BaseModel (if you have one).
- from .models import *
Imports all model classes so they register with Base.metadata (important for Alembic autogenerate).
- __ all __ = ['Base', 'BaseModel']
Controls what’s exported on from db import * (keeps the public surface minimal).

#### Why it matters
- Migrations work: Importing db guarantees every model is imported, so Alembic “sees” all tables.
- Cleaner imports: Other modules can do from db import Base and pass it to tooling.

#### Notes & gotchas 
- __ all __ only affects import *: Explicit imports like from db import Campaign still work.
- Wildcard import cost: from .models import * loads every model on package import—great for migrations, but be mindful of import-time side effects.
- Avoid circular imports: Keep model modules lightweight and avoid importing app code back into db to prevent cycles.

### base.py
#### Overview
Defines the SQLAlchemy base your models inherit from and a shared BaseModel with common fields. This keeps every table consistent (UUID id + timestamps) with minimal boilerplate.

#### What’s inside
Base = declarative_base()
- The foundation for all ORM models. SQLAlchemy uses this to track tables/columns.

class BaseModel(Base): (abstract)  
- A reusable base with:
    - id → UUID primary key (postgresql.UUID, generated via uuid.uuid4)
    - created_at → set to UTC now when the row is created
    - updated_at → set to UTC now on create and auto-updates on change (onupdate=datetime.utcnow)

Marked __abstract__ = True so SQLAlchemy doesn’t create a basemodel table.

#### How to use it
Create your models by inheriting BaseModel

Now campaign automatically has:
- id (UUID primary key)
- created_at
- updated_at
- plus your own columns (like name)

#### Tips & gotchas
- Postgres-specific UUID: UUID(as_uuid=True) uses the Postgres type. Make sure your DATABASE_URL uses a Postgres driver (e.g., postgresql+psycopg2://...).
- Naive UTC datetimes: datetime.utcnow() is timezone-naive. If you want timezone-aware timestamps, switch to DateTime(timezone=True) and store timezone.utc values.
- App-side defaults: These defaults are applied by SQLAlchemy, not by the database. If rows are inserted outside the app (raw SQL, another service), set DB-level defaults too (e.g., server defaults or triggers) if needed.
- Auto-update works on ORM flush/commit: updated_at changes when SQLAlchemy detects column changes and flushes. Pure read operations won’t alter it.
- SQLAlchemy 2.x import: Prefer from sqlalchemy.orm import declarative_base (the ext.declarative import is legacy).
- Migrations: Ensure Alembic can see your models (e.g., import them in db/__init__.py) so autogenerate picks up the tables.

### models.py
#### Overview
SQLAlchemy ORM models for the app. All models inherit from BaseModel, so they automatically have:
- id: UUID (primary key)
- created_at: datetime
- updated_at: datetime

PostgreSQL-specific types used: UUID, JSON, DECIMAL. Relationships are declared with relationship() and back_populates for easy navigation between records.

#### Organization
Table: organizations  
Fields
- name: str (required)

Relationships
- users: List[User] — all users in the org

Use it for: grouping users by company/account.

#### User
Table: users  
Fields
- firebase_uid: str (unique, required) — maps to Firebase account
- email: str (unique, required)
- name: str (required)
- organization_id: UUID | null → FK → organizations.id

Relationships
- organization: Organization
- campaigns: List[Campaign]
- templates: List[CampaignTemplate]
- file_uploads: List[FileUpload]

Notes
- Unique constraints on firebase_uid and email prevent duplicates.

#### CampaignTemplate
Table: campaign_templates  
Fields
- user_id: UUID (required) → FK → users.id
- name: str (required)
- campaign_type: str — e.g., "trade_desk", "pulsepoint"
- goal: str — e.g., "awareness", "action"
- channel: str — e.g., "ctv", "display", "video", "audio"
- ctr_sensitivity: bool (required)
- analysis_level: str — "domain" or "supply_vendor"

Relationships
- user: User
- campaigns: List[Campaign] — campaigns created from this template

Use it for: reusable default settings when creating campaigns.

#### Campaign
Table: campaigns  
Fields
- user_id: UUID (required) → FK → users.id
- template_id: UUID | null → FK → campaign_templates.id
- name: str (required)
- status: str (default "pending") — "pending" | "processing" | "completed" | "failed"
- file_path: str | null — source data file location
- results_path: str | null — processed results location
- total_records: int | null
- processed_records: int | null
- error_message: text | null
- completed_at: datetime | null

Scoring & processing snapshots (JSON)
- scoring_platform: str | null — "trade_desk" / "pulsepoint"
- scoring_config_snapshot: JSON | null — config used to score at the time
- data_quality_report: JSON | null — validation outcomes
- column_mapping_used: JSON | null — how columns were interpreted

Relationships
- user: User
- template: CampaignTemplate
- results: List[ScoringResult]
- insights: List[AIInsight]
- file_uploads: List[FileUpload]

Use it for: the main entity representing a scoring run and its lifecycle.

#### ScoringResult
Table: scoring_results  
Fields
- campaign_id: UUID (required, indexed) → FK → campaigns.id
- domain: str (required, indexed)
- impressions: int (required)
- ctr: DECIMAL(10,6) (required)
- conversions: int (required)
- total_spend: DECIMAL(12,2) (required)

Optional/raw metrics (JSON)
- raw_metrics: JSON | null — original platform fields
- normalized_metrics: JSON | null — normalized values (0–100)

Calculated metrics
- cpm: DECIMAL(10,2) | null
- conversion_rate: DECIMAL(10,6) | null
- cost_per_conversion: DECIMAL(10,2) | null

Scoring details
- score: int (0–100, required)
- score_breakdown: JSON | null
- normalization_stats: JSON | null
- scoring_config_used: JSON | null

Quality
- status: str (required, indexed) — "good" | "moderate" | "poor"
- percentile_rank: int | null
- quality_flags: JSON | null

Relationships
- campaign: Campaign

Use it for: per-domain (or row-level) scored outcomes that feed insights and lists.

#### AIInsight
Table: ai_insights  
Fields
- campaign_id: UUID (required) → FK → campaigns.id
- insight_type: str — e.g., "performance", "optimization", "domain", etc.
- content: text — AI-generated narrative

Relationships
- campaign: Campaign

Use it for: storing AI summaries/recommendations tied to a campaign.

#### FileUpload
Table: file_uploads  
Fields
- user_id: UUID (required) → FK → users.id
- campaign_id: UUID | null → FK → campaigns.id
- filename: str (required)
- file_path: str (required)
- file_size: int (required, bytes)
- upload_date: datetime (required)
- status: str (default "uploaded") — "uploaded" | "assigned" | "processed"

Relationships
- user: User
- campaign: Campaign

Use it for: tracking uploads and associating them with campaigns when assigned.

#### Notes & gotchas
- Strings instead of enums: Many fields (e.g., status, campaign_type) are plain String. Keep values in sync with your Pydantic enums in campaign_service/schemas.py to avoid typos.
- Indexes present: ScoringResult.campaign_id, domain, and status are indexed for faster filtering.
- DECIMAL vs float: DECIMAL stores precise values (good for money/ratios). Convert carefully when doing math in Python.
- JSON snapshots: Useful for auditability; they capture the exact config/data used during a run.
- No cascade rules specified: Deleting a User/Campaign won’t automatically delete children unless you add ondelete/cascade options. Consider your desired behavior.
- Timestamps are naive UTC: Match how you display/parse datetimes on the API side.
- Constraints you might add later: unique keys (e.g., per-campaign (domain)), foreign key ondelete, and check constraints for allowed statuses.

## report_service

### exports.py
#### What this file does
ExportService turns campaign data into CSV or JSON so you can download it or feed it to other tools. It:
- Checks that the campaign belongs to the current user (where appropriate)
- Pulls results/metrics from ScoringController
- Adds helpful metadata (campaign name, channel, export date)
- Returns bytes for CSV downloads or dicts for JSON APIs

Construct it once with a DB session: svc = ExportService(db).

#### Main methods you’ll call
export_scoring_results_csv(campaign_id, user, filters=None) -> bytes  
- Exports all scored rows (e.g., per-domain) for a completed campaign.
    - Validates ownership and that status is completed
    - Pulls results via ScoringController.get_scoring_results(...)
    - Adds campaign metadata + export timestamp
    - Returns a CSV as bytes (ready to send in a response)

- CSV column order (when present):  
    - campaign_name, campaign_type, goal, channel, domain, score, quality_status, percentile_rank, impressions, spend, cpm, ctr, conversions, conversion_rate, raw_metrics, normalized_metrics, score_breakdown, quality_flags, export_date
    - Only columns that actually exist are included, so the CSV won’t crash if a field is missing.

export_whitelist_csv(campaign_id, user, min_impressions=250) -> bytes
- Builds a whitelist from your results and exports it as CSV.
    - Uses ScoringController.generate_optimization_list(..., list_type="whitelist")
    - One row per domain + campaign metadata and thresholds
- Columns (typical):
    - domain, list_type, campaign_name, campaign_type, goal, channel, min_impressions, average_score, total_impressions, export_date

export_blacklist_csv(campaign_id, user, min_impressions=250) -> bytes
- Same as whitelist export, but for blacklists.

export_campaign_summary_csv(campaign_id, user) -> bytes
- Exports a one-row summary with key totals and averages:
    - Reads ScoringController.get_campaign_summary(...)
    - Fields like totals, average score/CPM, score distribution, etc.

export_optimization_lists_csv(campaign_id, user, min_impressions=250) -> bytes
- Exports whitelist and blacklist together in one CSV.
    - Two sections combined into one DataFrame
    - Each row labeled with list_type = whitelist or blacklist

generate_whitelist_json(campaign_id, user, min_impressions=250) -> dict
- JSON-friendly version of the whitelist export for APIs.
- Includes:
    - domains list
    - criteria used (min impressions, counts)
    - metrics (average score, total impressions)
    - campaign metadata + timestamp

generate_blacklist_json(campaign_id, user, min_impressions=250) -> dict
- JSON-friendly blacklist. Same shape as whitelist JSON.

export_campaign_data_json(campaign_id, user, include_results=True, include_insights=False) -> dict
- Full campaign export in JSON:
    - Campaign metadata (status, timestamps, scoring config snapshot, data quality report)
    - Optionally scoring_results (if completed)
    - Always a campaign_summary (if completed)
    - Optionally ai_insights (see note below)

#### Mental model
Think of ExportService as a formatting layer:
- ScoringController fetches/derives the data.
- ExportService reshapes that data and adds metadata + timestamps, then returns it as CSV bytes or JSON dicts ready for API responses or downloads.

### pdf_generator.py
#### What this does
PDFReportGenerator creates a multi-section PDF for a completed campaign (using ReportLab). It:
- Verifies the campaign belongs to the current user and is completed
- Pulls summaries and results from ScoringController
- Lays out a clean report: title page → executive summary → overview → metrics → charts → detailed table → recommendations → appendix
- Returns the PDF as bytes (ready to send as a download)

#### What’s inside the report (sections)
Title page
- Big title with the campaign name
- Key facts table: platform, goal, channel, status, created date, “report generated” timestamp

Executive summary
- Pulls summary via ScoringController.get_campaign_summary(...)
- Shows overall performance level (Excellent/Good/Moderate/Poor), totals, and quick “Key Insights” bullets

Campaign overview
- High-level metrics table: impressions, spend, average CPM, campaign score, total domains, processing date

Performance metrics
- Computes averages/medians/ranges for score, CTR, CPM, volume (from get_scoring_results(...))
- Simple table with descriptions for each metric

Charts (optional)
- Score distribution pie chart
- Top 10 Domains table (rank, domain, score, impressions, CTR, CPM)

Detailed results (optional)
- First 50 rows of results (Domain, Score, Status, Impressions, CTR, CPM)
- Notes if there are more than 50 rows total

Optimization recommendations
- Auto-generates whitelist and blacklist snapshots via generate_optimization_list(...)
- Summaries (counts, average score, impressions) plus action guidance

Appendix
- Scoring methodology (what factors affect the score)
- Data quality notes (if present on the campaign)

#### Inputs & outputs
Input params
- campaign_id: str — target campaign
- user: User — used for ownership check
- include_charts: bool — add pie chart + top domains table
- include_details: bool — add first 50 detailed rows

Output
- bytes — the generated PDF document

#### Styling & layout (what ReportLab styles do)
- Custom styles for Title, Section headers, Subsection headers, Metric lines, and Summary bullets
- Tables with grid lines, light grey headers, and consistent font sizes

#### Mental model
This class is a presentation layer: it fetches (via ScoringController), summarizes, and formats campaign performance into a client-ready PDF your stakeholders can read without touching the app.


### routes.py
#### What this file does 
Defines all the report-related API endpoints (FastAPI router at /reports). It lets users:
- Upload CSV/Excel files and tie them to campaigns
- List / inspect / preview / validate uploaded files
- Export campaign outputs (results, whitelist, blacklist, summary) as CSV or JSON
- Download a polished PDF report of a completed campaign

#### Key endpoints at a glance
Uploads
- POST /reports/upload
    - Upload a .csv, .xlsx, or .xls (≤ 50 MB). Stores the file, creates a DB record via FileUploadService, and (optionally) associates it with a campaign.
- GET /reports/files
    - Paginated list of the current user’s uploaded files.
- GET /reports/files/{file_id}
    - Details for a single uploaded file.
- GET /reports/files/{file_id}/preview?rows=10
    - Reads the first N rows (via pandas) to preview columns and sample data.
- GET /reports/files/{file_id}/validate
    - Loads the file into a DataFrame and runs FileUploadService.validate_file_structure to report schema/quality findings.
- DELETE /reports/files/{file_id}
    - Delete the uploaded file and its record.
- POST /reports/files/{file_id}/assign-campaign
    - Link an uploaded file to a specific campaign_id.

Exports (CSV/JSON)
- GET /reports/export/campaigns/{campaign_id}/results/csv
    - CSV of scoring results. Optional filters:
        - quality_status (good|moderate|poor) · min_score · max_score · min_impressions.
- GET /reports/export/campaigns/{campaign_id}/whitelist/csv
    - CSV domains recommended for whitelist; tweak with min_impressions.
- GET /reports/export/campaigns/{campaign_id}/blacklist/csv
    - CSV domains recommended for blacklist.
- GET /reports/export/campaigns/{campaign_id}/summary/csv
    - One-row campaign summary CSV (totals/averages).
- GET /reports/export/campaigns/{campaign_id}/optimization-lists/csv
    - Combined whitelist + blacklist in one CSV.
- GET /reports/export/campaigns/{campaign_id}/whitelist/json
    - JSON-formatted whitelist (domains, criteria, metrics).
- GET /reports/export/campaigns/{campaign_id}/blacklist/json
    - JSON-formatted blacklist.
- GET /reports/export/campaigns/{campaign_id}/data/json?include_results=true&include_insights=false
    - Full campaign export in JSON (metadata, optional results, summary, optional AI insights).

PDF
- GET /reports/reports/campaigns/{campaign_id}/pdf?include_charts=true&include_details=true
    - Generates a multi-section PDF via PDFReportGenerator (title, summary, charts, top domains, details, recommendations, appendix).

#### How it works behind the scenes
Auth & DB
- Every route uses get_current_user (Firebase-backed auth) and a per-request SQLAlchemy session via get_db.

Storage & uploads
- Uses report_service.storage.file_storage to save/read raw bytes and FileUploadService (create records, list files, validate schema, deletion, assignment).

Exports & PDF
- Hands off heavy lifting to:
    - ExportService (CSV/JSON shaping for results, lists, summaries, full campaign data)
    - PDFReportGenerator (layout + charts using ReportLab)

Download responses
- CSV/PDF routes return a Response with proper Content-Disposition so the browser downloads a file.

#### Inputs & outputs
Upload
- Input: form-data file, optional campaign_id (UUID)
- Output: { upload_id, filename, file_path, file_size, campaign_id, status }

Preview
- Input: file_id, optional rows (default 10)
- Output: { columns: [...], rows: [...], total_rows, file_info: {...} }

Exports
- CSV routes return file bytes with text/csv
- JSON routes return structured dicts (domains, criteria, metrics, etc.)

PDF
- Returns PDF bytes with application/pdf

#### Validations & errors you’ll see
- File checks: extension must be .csv/.xlsx/.xls, size ≤ 50 MB
- Ownership: many routes confirm the file/campaign belongs to the current user
- Campaign status: export/PDF routes generally require completed campaigns
- Errors raised: ValidationError, NotFoundError mapped to HTTPException with appropriate codes; unknown errors → 500

#### Notes, gotchas, and small improvements
- Memory use: Upload & preview read entire file into memory (await file.read() / pd.read_*). For very large files, consider streaming, chunking, or server-side preprocessing.
- Extension vs content: The check uses filename extension only. If you need stricter validation, sniff content (e.g., try pd.read_* with error handling).
- Model fields: Some exports/PDF sections reference campaign.campaign_type/goal/channel. Ensure those exist on Campaign or pull them from the linked CampaignTemplate / snapshot.
- Filter names: Results CSV filter expects keys like quality_status, min_score, max_score, min_impressions. Make sure your ScoringController.get_scoring_results supports the same names.
- Response models: Most endpoints return plain dicts for convenience; only DELETE /files/{file_id} uses BaseResponse. If you want stricter OpenAPI docs, wrap others with APIResponse too.
- Imports inside functions: The code imports fastapi.responses.Response inside each route to build download responses. That’s fine, but you can import it once at the top for clarity.

#### Mental model
This router is the front door for anything file/report related:
- Upload → Preview/Validate → Assign to campaign
- After scoring completes → Export CSV/JSON or download a PDF to share with stakeholders.

### storage.py
#### What this does
A tiny helper class (FileStorage) that saves, reads, lists, and deletes files on the server’s disk. It also creates temporary files and cleans them up later. A single, ready-to-use instance file_storage is created at the bottom.

#### How it’s organized
FileStorage(base_path="storage")
- Creates a storage/ folder (if missing) and does all file operations inside it.

save_file(file_content, filename, subdirectory="") -> str
- Saves raw bytes to disk and returns the full file path.
- Tip: Pass a unique filename (e.g., prepend a UUID) to avoid collisions.

get_file_path(filename, subdirectory="") -> Optional[str]
- Returns the full path if that file exists; otherwise None.

delete_file(filename, subdirectory="") -> bool
- Deletes the file and returns True if it existed.

list_files(subdirectory="") -> list[str]
- Lists all files in a subfolder (no recursion).

read_file(file_path) -> bytes
- Reads a file (by full path) and returns its bytes. Raises FileNotFoundError if missing.

create_temp_file(suffix="", prefix="caliber_") -> str
- Makes a temp file in storage/ and returns its path (you can write to it later).

cleanup_temp_files(max_age_hours=24)
- Deletes temp files in storage/ whose names start with caliber_ and are older than max_age_hours.

file_storage = FileStorage()
- A global instance you can import and use everywhere.

#### Notes & gotchas
- Local disk only: This stores files on the app server’s filesystem. For cloud deployments, you’ll likely swap this out for S3/GCS/Azure Blob logic with the same method names.
- Use unique names: save_file will overwrite if filename already exists. Generate a unique name (e.g., f"{uuid4()}_{original}") before saving.
- Subdirectories are allowed: save_file(..., subdirectory="uploads") writes to storage/uploads/. The method creates the subfolder if needed.
- Sanitize filenames: If filenames come from users, consider stripping weird characters to avoid path issues (e.g., "../"). Right now the code joins paths naively.
- Temp cleanup relies on name prefix: Only files starting with caliber_ are considered “temp” for cleanup.
- Binary mode: All reads/writes are in bytes—great for CSV/Excel/PDF uploads and downloads.
- Logging: Saves and deletions are logged via the module logger.

### uploads.py
#### What this does
FileUploadService is the database-facing helper for uploaded files. It:
- creates a record when a user uploads a file,
- lists and fetches file metadata,
- does a light schema/quality check on the file contents,
- assigns a file to a campaign,
- and deletes the file’s DB record.

It does not move bytes on disk/cloud—that’s handled by report_service/storage.py. This class manages the database rows about those files.

#### How it’s used in the app
- The /reports/upload route saves the raw file via file_storage.save_file(...), then calls create_upload_record(...) here to persist metadata (filename, path, size, etc.).
- /reports/files/... routes use get_user_files(...) and get_file_info(...).
- /reports/files/{id}/validate loads the file into a pandas DataFrame and calls validate_file_structure(...).
- /reports/files/{id}/assign-campaign calls assign_file_to_campaign(...).

#### Key methods you’ll call
create_upload_record(user_id, filename, file_path, file_size, campaign_id=None) -> FileUpload
- Makes a file_uploads row (status=uploaded) with timestamps.

get_file_info(file_id, user_id) -> dict
- Returns a safe dict of the file’s metadata (only if it belongs to the user).

get_user_files(user_id, page=1, per_page=20) -> list[dict]
- Simple pagination (offset/limit). Returns the user’s recent uploads.

validate_file_structure(df: pd.DataFrame) -> dict
- Quick checks on the loaded file:
    - Required columns (currently "impressions", "ctr")
    - Empty file
    - Many columns (warn)
    - Duplicate column names (warn)
    - Missing values in impressions (warn)

delete_file(file_id, user_id) -> None
- Deletes the DB record for the file. (Note: file removal from storage is currently commented out—see “Gotchas”.)

assign_file_to_campaign(file_id, campaign_id, user_id) -> dict
- Ownership checks (file + campaign must belong to the user), sets campaign_id on the upload record, marks status=assigned.

get_campaign_files(campaign_id, user_id) -> list[dict]
- Returns files tied to that user’s campaign.

#### Errors you might see
- NotFoundError("File upload record") — wrong file_id or not your file
- NotFoundError("Campaign") — wrong campaign_id or not your campaign
- ValidationError(...) — from higher-level routes (e.g., bad inputs)

#### Mental model
Think of FileUploadService as the file registry in your database: who uploaded which file, where it lives on disk, and which campaign (if any) it belongs to—plus a quick sanity check on structure before you process it further.


## scoring_service

### config.py
#### What this file does
Central place to define how we score performance for different ad setups (Trade Desk vs PulsePoint, Display vs CTV vs Video/Audio, Awareness vs Action).  
It also lists which columns are required for each setup and a mapping to normalize messy CSV headers into standard names.

#### Key pieces
Enums
- ScoringPlatform: trade_desk, pulsepoint
- CampaignGoal: awareness, action
- Channel: ctv, display, video, audio

Dataclasses
- MetricConfig: one metric in the score
    - name: the standardized metric name (e.g., "ctr", "cpm")
    - weight: importance (0–1). All weights in a config add up to 1
    - is_higher_better: True if higher values are good (CTR), False if lower is good (CPM)
    - required: keep as True unless you want optional metrics
- ScoringConfig: a full recipe for scoring
    - platform, goal, channel, ctr_sensitivity, analysis_level ("domain" or "supply_vendor")
    - metrics: List[MetricConfig]
    - required_fields: List[str] — raw column names we expect to see in the upload

ScoringConfigManager
- Factory methods that return ready-to-use configs for common combos, like:
    - get_trade_desk_display_awareness(ctr_sensitivity: bool)
    - get_trade_desk_display_action()
    - get_trade_desk_ctv() (uses analysis_level="supply_vendor")
    - get_trade_desk_video_audio() (shared for video/audio)
    - get_pulsepoint_display_awareness() / ..._action() / get_pulsepoint_video()
- get_config(platform, goal, channel, ctr_sensitivity=False) picks the right one for you or raises an error if unsupported

COLUMN_MAPPINGS
- Dictionary that maps many possible header variations (e.g., "Spend", "Total Cost") to a single standard key (e.g., "advertiser_cost").
- Use this to rename columns from user files before scoring.

#### How scoring configs are picked
CTR sensitivity only affects Trade Desk Display Awareness:
- With sensitivity: CTR gets more weight, CPM a bit less.
- Without: more balanced weights.

Analysis level
- Most configs score at the domain level
- CTV scores at supply_vendor level

#### Common metric names used here
- Display (Trade Desk): cpm (lower is better), ias_display_fully_in_view_1s_rate, ctr, ad_load_xl_rate (lower), ad_refresh_below_15s_rate (lower)
- Action (Trade Desk): adds conversion_rate weight
- CTV (Trade Desk): tv_quality_index_rate, unique_id_ratio (both higher is better)
- Video/Audio (Trade Desk): sampled_in_view_rate, player_completion_rate, player_errors_rate (lower), player_mute_rate (lower), plus cpm
- PulsePoint: ecpm (lower), ctr, conversion_rate, completion_rate (for video)

All configs’ weights sum to 1.0.

#### Required fields (raw upload expectations)
Each config includes required_fields with the exact vendor column names we expect (e.g., "IAS Display Fully In View 1 Second Rate").  
If your upload has different headers, use COLUMN_MAPPINGS to translate first.

#### Tips & gotchas
Name mismatches you’ll want to handle in preprocessing
- Some metrics end with "_rate" in configs but the raw columns don’t (e.g., player_errors_rate vs "Player Errors"). You may need to compute a rate from counts or normalize names consistently.
- CTV uses tv_quality_index_rate and unique_id_ratio, while mappings list "TV Quality Index" and "Unique IDs". Again, compute/normalize as needed.

Video vs Audio
- get_trade_desk_video_audio() returns a single config (internally marked Channel.VIDEO). If you ingest audio, treat it the same scoring-wise, or split later if you need different weights.

Strictness
- get_config(...) raises a ValueError for unsupported combinations—this is intentional to catch misconfigurations early.

Why required_fields use vendor names
- They reflect exact headers you’ll see from the export source. The app should normalize to standard keys using COLUMN_MAPPINGS, then compute metrics from those.

#### Mental model
This module is the source of truth for what matters in scoring (which metrics, how important, direction), plus the glue to reconcile messy CSV headers into clean, standardized metric names.

### controllers.py
#### What this file does
ScoringController is the “traffic cop” that takes an uploaded campaign file and walks it through all the steps to produce scores and insights. It:
1. loads your data file,
2. cleans and normalizes it,
3. calculates a quality score per domain/supply vendor,
4. saves results to the database, and
5. serves endpoints that read back results, progress, whitelists/blacklists, and a campaign summary.

#### The big picture flow
1. start_scoring_process(...)
    - Checks you own the campaign and that a file is uploaded.
    - Picks the right scoring recipe (Trade Desk vs PulsePoint, etc.).
    - Saves a snapshot of the scoring config used.
    - Kicks off the main pipeline (_process_scoring) and returns a quick “started” response with an estimated finish time.
2. _process_scoring(...) (main pipeline)
    - Loads the CSV/Excel from disk.
    - Preprocesses it (clean/rename/validate).
    - Normalizes metrics to 0–100 style scales.
    - Scores each row using configured metric weights.
    - Flags outliers (data points that look off).
    - Saves per-row results into scoring_results and campaign-level metrics into the campaign row.
    - Marks the campaign as completed.
3. Reads & summaries for the UI / API
    - get_scoring_progress(...) — how far along the job is.
    - get_scoring_results(...) — paginated table of domains with metrics and scores (supports filters & sorting).
    - generate_optimization_list(...) — returns a whitelist (top 25%) or blacklist (bottom 25%) of domains, optionally requiring a minimum number of impressions.
    - get_campaign_summary(...) — totals, averages, score distribution, top/bottom performers, CPM, impressions, plus the campaign-level score.

#### Key methods
start_scoring_process(db, campaign_id, user) -> dict
- Starts processing

get_scoring_results(db, campaign_id, user, page=1, per_page=50, sort_by="score", sort_direction="desc", filters=None) -> dict
- Returns paginated rows

generate_optimization_list(db, campaign_id, user, list_type, min_impressions=250) -> dict
- list_type is "whitelist" or "blacklist". Picks the top 25% (whitelist) or bottom 25% (blacklist) by score after filtering for min_impressions.
- Returns the chosen domains + summary metrics.

get_campaign_summary(db, campaign_id, user) -> dict
- Totals (domains/impressions/spend), average score, score buckets (good/moderate/poor), top/bottom performers, CPM, and campaign-level score.

#### Data it reads/writes
Reads:
- The uploaded file from disk (campaign.file_path)
- campaigns table (to get settings/ownership)

Writes:
- scoring_results table — one row per domain/supply vendor
- campaigns table — status, totals, processing metadata, and a snapshot of the scoring config

#### Behind-the-scenes helpers it calls
- ScoringConfigManager.get_config(...) — picks the recipe (which metrics, weights, directions).
- DataPreprocessor — cleans/standardizes columns and validates.
- DataNormalizer — normalizes metric values to comparable scales.
- ScoringEngine — computes the weighted score.
- OutlierDetector — flags odd data points for review.

(These classes live in scoring_service.preprocess, scoring_service.normalize, and scoring_service.scoring.)

#### Mental model
This controller is the orchestrator. It doesn’t invent scores itself; it just runs the steps in order, persists data, and gives clean endpoints for the frontend to show progress, tables, and summaries.

### explain.py
#### What this file does
The ExplainabilityEngine is a helper that looks at your scored data and answers:
- Which metrics mattered most overall?
- Why did this single domain get its score?
- What changed between two time periods, and which metrics caused it?

It does this with three simple techniques:
- SHAP (model-agnostic feature impact scores)
- Feature importance (from a quick Random Forest model)
- Correlation (straightforward stat relationships)

#### Where it fits
After you’ve produced per-domain scores (via the scoring pipeline), this module is used to interpret those scores for dashboards, tooltips, reports, and “why” explanations.

#### Key methods you’ll call
explain_score(data, scores, feature_columns, method="shap") -> dict
- Explains scores across the entire dataset.
- Inputs:
    - data — DataFrame with all your metrics (one row per domain/vendor).
    - scores — Series of final scores for those rows.
    - feature_columns — Which columns to consider as drivers.
    - method — "shap", "feature_importance", or "correlation".
- Output: A dict with top features and a short human-readable explanation.

explain_domain_score(domain_data, domain_score, feature_columns) -> dict
- Explains a single domain’s score.
- Inputs: One-row DataFrame for a domain, its score, and the metric columns.
- Output: The biggest contributing factors, a sentence explaining them, and a basic confidence score.

explain_score_changes(before_data, after_data, before_scores, after_scores, feature_columns) -> dict
- Explains what changed between two periods.
- Inputs: Two datasets + their scores and the metric columns to compare.
- Output: Per-metric changes, top change drivers, and a summary sentence.

#### What you get back
Each method returns a JSON-friendly dict with items like:
- top_features — pairs like ("ctr", 0.31) showing most impactful metrics
- explanation — one or two sentences in plain English
- feature_importance / correlations / shap_values — details for charts
- For domain explanations: feature_contributions, confidence

#### How it works (high level)
- SHAP path: trains a small RandomForestRegressor on your feature_columns → computes SHAP values → averages absolute SHAP values to rank features → generates a short explanation.
- Feature importance path: uses the model’s built-in importances to rank metrics.
- Correlation path: computes simple correlations between each metric and the score.

Note: The Random Forest is used only as a lightweight explainer model here (not for the final scoring).

#### Data it expects
- data must contain every column listed in feature_columns. Missing values are filled with 0 for modeling.
- scores must align row-for-row with data.
- For a single domain, pass a one-row DataFrame to explain_domain_score.

### normalize.py
#### What this file does
DataNormalizer converts different metrics (like CTR, CPM, Viewability, etc.) into the same 0–100 scale so they’re easy to combine later when calculating a final score. It uses simple min–max normalization and respects whether a metric is “higher is better” (e.g., CTR) or “lower is better” (e.g., CPM).

#### Where it fits
After raw data is cleaned, this step standardizes each metric so the scoring engine can weight and sum them fairly.

#### Key class & methods
DataNormalizer(config)
- Takes a ScoringConfig (which lists which metrics to normalize and whether higher values are better).

normalize_data(df) -> (df_normalized, stats)
- For every metric in the config:
    - Creates a new column named <metric>_normalized with values from 0 to 100.
    - Returns:
        - df_normalized: your original DataFrame plus the new *_normalized columns
        - stats: per-metric min/max/count and the is_higher_better flag (helpful for audits)

get_normalization_report() -> dict
- A handy summary of which metrics were normalized, what stats were used, and which scoring config was applied.

#### How normalization works
- Min–max scaling:
    - If higher is better: score = (value - min) / (max - min) * 100
    - If lower is better: score = (max - value) / (max - min) * 100
- Missing/invalid values → normalized to 0
- All values identical (no variation) → assigns a neutral 50 for that metric
- Values are clipped to the [0, 100] range

#### Inputs & outputs
Input:
- A DataFrame with raw metric columns (e.g., ctr, cpm, viewability) and a ScoringConfig that says:
    - metric name
    - weight (used later by scoring, not here)
    - is_higher_better (used here)

Output:
- DataFrame with new columns like ctr_normalized, cpm_normalized, etc.
- A dict of normalization stats

#### Edge cases handled
- Metric column missing → logs a warning and skips it
- All values the same → returns 50 to avoid divide-by-zero and bias
- NaN/inf values → treated as invalid; normalized result becomes 0

### outliers.py
#### What this file does
OutlierDetector helps you spot, review, and fix outliers in your dataset before (or after) scoring. It supports several detection methods (ML-based and statistical), plus utilities to drop, cap, or winsorize those outliers and to summarize what’s going on.

#### Where it fits
Use this after you’ve assembled your modeling table (raw or normalized metrics) and before you finalize scores or reports. It’s especially helpful to reduce the impact of extreme CPM/CTR values, mis-logged impressions, etc.

#### Core methods (what you’ll actually call)
detect_outliers(data, method="isolation_forest", columns=None, contamination=0.1) → dict
- Finds unusual rows.
    - columns: which numeric columns to consider (defaults to all numeric).
    - method:
        - "isolation_forest" (good default),
        - "local_outlier_factor",
        - "elliptic_envelope",
        - "zscore",
        - "iqr",
        - "combined" (union of several methods).

remove_outliers(data, outlier_indices, method="drop") → DataFrame
- Applies your chosen handling strategy:
    - "drop": remove those rows
    - "cap": clip all numeric cols to [p1, p99]
    - "winsorize": shrink tails (default 5% each side)

analyze_outliers(data, outlier_indices, columns=None) → dict
- Quick diagnostics: how many outliers, % of dataset, per-column means/stds for outliers vs. normal rows, and a severity summary.

get_outlier_recommendations(outlier_analysis, data_shape) → list[str]
- Human-readable advice (e.g., “cap column X” or “investigate data quality”).

#### Method cheat-sheet
Isolation Forest ("isolation_forest")
- Robust, model-based; good general default. Tune with contamination.

Local Outlier Factor ("local_outlier_factor")
- Density-based; highlights points isolated from local neighbors.

Elliptic Envelope ("elliptic_envelope")
- Assumes roughly Gaussian data; fits an ellipsoid; sensitive to non-Gaussian shapes.

Z-score ("zscore")
- Simple per-column |z| > 3 rule; fast, easy, can miss multivariate issues.

IQR ("iqr")
- Per-column whiskers rule (1.5×IQR); robust to non-normal distributions.

Combined ("combined")
- Union of Isolation Forest, LOF, and Z-score to catch different patterns.

#### Outputs you can rely on
- Indices of outlier rows (outlier_indices) you can drop, cap, or tag.
- Counts/percentages to understand scope.
- Per-column analysis (means/stds for outliers vs non-outliers).
- Severity tag (minimal/low/moderate/high) and practical recommendations.

#### When to use which handling method
- Drop: when outliers are likely bad rows (parse errors, duplicates).
- Cap: when extremes are real but too influential (e.g., CPM spikes).
- Winsorize: when you need smooth tails for modeling without hard clipping.

### preprocesses.py
#### What this file does
DataPreprocessor turns a messy export (CSV/XLSX) into a clean, standardized DataFrame the rest of your pipeline can safely use. It:
1. normalizes column names
2. maps many possible header variants to your standard names (like impressions, ctr)
3. checks required fields
4. drops “Totals/Grand total” rows
5. fixes data types
6. computes derived metrics (e.g., CPM, CTR)
7. aggregates when needed (PulsePoint domain rollup)
8. filters low-volume rows
9. records any data quality issues it finds.

#### The pipeline steps
1. Clean headers: trims whitespace and removes prefixes like TTD_, PulsePoint_, Report_.
2. Map headers: uses COLUMN_MAPPINGS to rename many possible source names to a single standard (e.g., “Advertiser Cost” → advertiser_cost).
3. Validate requireds: checks that the columns needed by your config exist (see “gotchas” below re: derived fields).
4. Drop aggregates: removes “total / grand total / [tail aggregate] / summary …” rows.
5. Fix data types: numeric coercion, convert percentages (0–100 → 0–1), drop rows with missing critical keys (like impressions or the dimension column).
6. Derived metrics (adds when missing):
    - cpm / ecpm from spend ÷ impressions × 1000
    -ctr from clicks ÷ impressions
    - conversion_rate from conversions ÷ impressions
    - Trade Desk-specific rates (e.g., ad_load_xl_rate, player_errors_rate, etc.)
7. PulsePoint aggregation: groups by domain and recomputes sums and weighted averages.
8. Volume filter: drops rows below a minimum impression threshold (and a % of total for PulsePoint).
9. Quality checks: flags negatives in counts, invalid %s, extremely high CPMs.
    - process_file returns (df_processed, processing_report) with:
        - column_mapping: original → standard names used
        - data_quality_issues: human-readable warnings
        - final_rows, excluded_rows, and derived_metrics

### routes.py
#### What this file does
exposes scoring endpoints your frontend can call:
- start a scoring job for a campaign
- check progress
- fetch results (with paging/filters/sorting)
- get a campaign summary
- build whitelist/blacklist (or fetch each directly)

auth runs via get_current_user.

#### What Each Endpoint Does
- Auth: all routes require a logged-in user; the campaign must belong to that user.

POST /scoring/start
- What it does: kicks off the scoring pipeline for a campaign that already has a data file attached.
- Body: campaign_id (UUID).
- Returns: { status: "started", estimated_completion: ISO time, config_used: {...} }
- Common errors:
    - 400 if no file is attached or input invalid
    - 404 if campaign not found (or not yours)

GET /scoring/progress/{campaign_id}
- What it does: tells you how far the scoring job has gotten.
- Returns:
    - status (pending|processing|completed|failed)
    - progress_percentage (0–100)
    - estimated_completion (when still processing)
    - error_message (only if failed)

GET /scoring/results/{campaign_id}
- What it does: paginated table of scored rows.
- Query params (most used):
    - page (default 1), per_page (1–100)
    - sort_by (score|impressions|ctr|conversion_rate|percentile_rank)
    - sort_direction (asc|desc)
    - Filters: quality_status (good|moderate|poor), min_score, max_score, min_impressions
- Returns:
    - results: each row includes domain, impressions, spend, cpm, ctr, conversions, conversion_rate, score, percentile_rank, quality_status, plus raw_metrics, normalized_metrics, score_breakdown, quality_flags
    - pagination: { page, per_page, total, pages }
- Common errors:
    - 400 if scoring isn’t complete yet
    - 404 if campaign not found

GET /scoring/summary/{campaign_id}
- What it does: one-page overview.
- Returns: totals and averages (impressions, spend, average CPM), score distribution (good/moderate/poor), top/bottom performers, and the campaign-level score.

POST /scoring/optimization-list
- What it does: builds a whitelist (top performers) or blacklist (bottom performers).
- Body:
    - campaign_id (UUID)
    - list_type (whitelist or blacklist)
    - min_impressions (default 250)
- How it selects: after filtering by min_impressions, it takes the top 25% for whitelist or bottom 25% for blacklist (by score).
Returns: domains + summary (selected_count, total_impressions, average_score).
- Shortcuts:
    - GET /scoring/whitelist/{campaign_id}?min_impressions=250
    - GET /scoring/blacklist/{campaign_id}?min_impressions=250

#### Typical Flow
1. Upload + attach file to campaign
2. POST /scoring/start
3. Poll GET /scoring/progress/{id} until completed
4. Read data: GET /scoring/results/{id} (use filters/sort for UI tables)
5. Summarize: GET /scoring/summary/{id}
6. Action lists: GET /scoring/whitelist/{id} or GET /scoring/blacklist/{id}


### schemas.py
#### What this file is
These Pydantic models describe the shape of the data our scoring endpoints send and receive. Think of them as the contract between the backend and the frontend for anything related to running a campaign score, tracking progress, getting results, and building whitelist/blacklist recommendations.

Purpose: Defines all request/response shapes for scoring: starting a run, tracking progress, fetching results, and generating whitelist/blacklist recommendations. Helps keep the API responses predictable and documented.

#### Models at a glance
ScoringRequest
- Used by: POST /scoring/start
- What it represents: “Please start scoring this campaign.”
    - campaign_id (UUID): which campaign to process.
    - file_path (str): Currently ignored by the endpoint (we use the file already attached to the campaign).
    - force_reprocess (bool): reserved for later; not used now.

Tip: Make sure the campaign already has an uploaded/assigned file before calling start.

ScoringProgress
- Used by: GET /scoring/progress/{campaign_id}
- What it represents: “How far along is the scoring?”
    - campaign_id (UUID)
    - status (str): one of pending | processing | completed | failed
    - progress_percentage (int): 0–100
    - current_step (str): Schema expects this, but the API doesn’t return it yet
    - total_records (int?), processed_records (int?)
    - estimated_completion (datetime?)
    - error_message (str?): present if failed

ScoringResultSummary
- Intended to be an at-a-glance summary of a finished run.
    - campaign_id (UUID)
    - total_domains (int)
    - average_score (float) — 0–100
    - score_distribution (dict) — counts in good/moderate/poor
    - top_performers, bottom_performers (lists)
    - data_quality_issues (list)
    - processing_time_seconds (float)

DomainScore
- One row in the scored results table.
    - domain (str) — (or supply vendor for some CTV cases)
    - impressions (int), spend (float), cpm (float)
    - ctr (float) — as a decimal (e.g., 0.034 = 3.4%)
    - conversions (int), conversion_rate (float) — decimal
    - score (float) — 0–100
    - percentile_rank (int)
    - quality_status (str) — good | moderate | poor
    - score_breakdown (dict)

ScoringResultsResponse
- Intended “rich” response when fetching results.
    - campaign_id (UUID)
    - results (List[DomainScore])
    - summary (ScoringResultSummary)
    - normalization_stats (dict) — min/max, etc.
    - scoring_config (dict) — the weights/settings used

WhitelistBlacklistRequest
- Used by: POST /scoring/optimization-list
- What it represents: “Give me a whitelist or blacklist.”
    - campaign_id (UUID)
    - list_type (str): whitelist or blacklist
    - min_impressions (int): default 250; rows below this volume are ignored

OptimizationListResponse
- Returned by: POST /scoring/optimization-list (also by GET /scoring/whitelist/{id} and /scoring/blacklist/{id})
    - list_type (str) — whitelist or blacklist
    - campaign_id (UUID)
    - domains (list[str]) — selected domains
    - criteria_used (dict) — thresholds and counts used
    - total_impressions (int) — across selected domains
    - average_score (float)
- How the lists are chosen: After filtering to min_impressions, whitelist = top 25% by score; blacklist = bottom 25% by score.

### scoring.py
#### What this file does
This file turns cleaned campaign data into a single quality score (0–100) per domain (or supply vendor). It also tags each row as good / moderate / poor, and can spit out whitelists (top 25%) and blacklists (bottom 25%). There’s also a small helper that flags outliers in the data.

Purpose: Applies weighted math to normalized metrics to produce a 0–100 quality score per domain, ranks and labels performance, and generates whitelist/blacklist recommendations—with a simple outlier flagger for sanity checks.

#### How the scoring works (step by step)
1. Inputs it expects
    - A DataFrame where each metric already has a normalized version on a 0–100 scale (e.g. ctr_normalized, cpm_normalized).
        - These normalized columns are created earlier by the DataNormalizer step.
    - A ScoringConfig that lists which metrics to use and their weights (e.g., CTR weight 0.3, CPM weight 0.15, etc.).
2. Weighted score per row
    - For each metric in the config, it reads the row’s *_normalized value and multiplies it by the metric’s weight.
    - Adds everything up, divides by the total weight, and scales to 0–100.
    - Puts the result in coegi_inventory_quality_score.
    - Also stores a breakdown per metric (normalized value, weight, and its contribution) in score_breakdown.
3. Percentile rank & quality label
    - Calculates where each row’s score sits relative to all others (0–100th percentile).
    - Labels each row:
        - good if percentile ≥ 75
        - moderate if 25 ≤ percentile < 75
        - poor if percentile < 25
4. Stats for the whole file
    - Returns a bundle of summary stats: mean/median/std of scores, min/max, quartiles, the quality label counts, and the metric weights used.

#### Extra helpers you get
Whitelist generator
- Filters to rows with at least 250 impressions, then takes the top 25% by score.

Blacklist generator
- Same 250-impression filter, then takes the bottom 25% by score.

Campaign-level score
- Calculates an impression-weighted average score for the whole campaign, plus totals (impressions, spend), average CPM, and the top/bottom 5 performers.

Simple Outlier Detector (IQR method)
- Looks at each numeric metric column and flags rows that sit well outside the typical range. Adds:
    - outlier_flags: list of which metrics were outliers for that row
    - is_outlier: true/false

#### Where this fits in the pipeline
- Before this: Data is cleaned/mapped (DataPreprocessor) and normalized to 0–100 (DataNormalizer).
- Here: We apply weights, compute the final quality score, tag quality status, and prepare whitelists/blacklists.
- After this: Results are saved to the database and exposed by the scoring API endpoints.

#### What it returns (in plain terms)
- A new DataFrame with added columns:
    - coegi_inventory_quality_score (0–100)
    - score_breakdown (per-metric contributions)
    - percentile_rank (0–100)
    - quality_status (good | moderate | poor)
    - (optionally) outlier_flags, is_outlier if you run the outlier detector
- A scoring_stats dictionary with summary numbers and the config used.


### weighting.py
#### What this file does
This module helps you figure out how important each metric should be (its “weight”) and then build a single weighted score from many features. You can:
- Calculate weights from data using different methods (equal, correlation, mutual info, F-score, variance, or your own).
- Apply those weights to your dataset.
- Combine into one score per row (simple weighted sum).
- Try simple “optimizers” to search for better weight combinations.

Think of it as a helper to set or learn the weights that the main Scoring Engine will use.

Purpose: Learns metric weights from data (or uses your custom ones) and builds a single weighted score per row; includes simple search methods to tune those weights.

#### When you’d use it
- You don’t know the best weights for metrics like CTR, CPM, etc.
- You have a target outcome (e.g., conversions, revenue, or any “ground truth” you care about) and want to learn which features matter most.
- You want a fast baseline before hand-crafting weights.

#### Core pieces
1. Calculating weights  
    - Call calculate_weights(data, target, method=...). Supported methods:
        - equal — gives every feature the same weight.
        - correlation — higher absolute correlation with the target → higher weight.
        - mutual_info — uses mutual information (captures non-linear relationships).
        - f_score — uses F-regression (linear model signal strength).
        - variance — features with more spread (variance) get higher weight.
        - custom — you pass your own {feature: weight} mapping.
    - All weights are normalized to sum to 1.
    - Returns a dict with:
        - weights (normalized),
        - raw_weights,
        - feature_importance (sorted list),
        - summary (quick stats about the weights).
2. Applying weights
    - apply_weights(data, weights) multiplies each feature column by its weight and returns a new DataFrame.
    - get_weighted_score(...) then adds them up to produce a single weighted score per row.
3. “Optimizing” weights
    - optimize_weights(..., method=...) tries to find better weights by measuring correlation between the weighted score and your target:
        - grid_search — sweeps a few values (mainly for the first two features) and splits the rest evenly.
        - genetic — toy genetic algorithm (random init, crossover, mutation, normalize).
        - bayesian — simplified random/Bayesian-style trials.
    - These are lightweight heuristics, good for exploration—not production-grade hyper-parameter tuning.

#### Inputs & outputs
Inputs:
- data: a pandas DataFrame (ideally numeric feature columns, cleaned/normalized beforehand).
- target: a Series you want to predict/align with (e.g., conversions).

Outputs:
- Learned weights per feature (sum to 1).
- Optional weighted score per row (a single number you can rank by).

#### Where this fits in the pipeline
- Before scoring: Use WeightingEngine to learn or set good metric weights from historical data.
- Then scoring: Pass those weights (or a config that contains them) into the ScoringEngine to compute final 0–100 quality scores.

## scripts

### stat_workers.bat
#### What this script does
This Windows .bat file starts all the background services your app needs to process jobs:
- Celery workers for two kinds of tasks:
    - scoring (heavy data work)
    - maintenance/exports/monitoring (lighter tasks)
- Celery Beat (the scheduler for periodic jobs)
- Flower (a web dashboard to watch Celery in real time)

It also checks that Redis is running first, and it writes logs to a local logs/ folder.

#### Step-by-step
1. Verify Redis is up
    - Runs redis-cli ping.
    - If Redis isn’t running, the script stops and tells you to start Redis.
2. Create a logs folder
    - Ensures logs/ exists so services can write log files there.
3. Start the scoring workers
    - celery -A worker.celery worker ... --queues=scoring --concurrency=2
    - Listens only to the scoring queue.
    - Uses 2 worker processes for parallelism.
    - Logs to logs/celery_scoring.log.
4. Start the maintenance workers
    - celery -A worker.celery worker ... --queues=maintenance,exports,monitoring --concurrency=1
    - Listens to maintenance, exports, and monitoring queues.
    - Uses 1 worker process (safer for non-heavy tasks).
    - Logs to logs/celery_maintenance.log.
5. Start the scheduler (Beat)
    - celery -A worker.celery beat
    - Triggers scheduled/recurring jobs (e.g., hourly cleanups).
    - Logs to logs/celery_beat.log.
6. Start Flower (monitoring UI)
    - celery -A worker.celery flower --port=5555
    - Visit http://localhost:5555 to see task queues, running jobs, failures, etc.
    - Logs to logs/celery_flower.log.

Note on --hostname=scoring@%%h: the %%h escapes to %h so Celery can substitute your machine’s hostname. That’s normal on Windows .bat files.

#### Prerequisites
- Redis installed and running (and redis-cli in your PATH).
- Your Python environment has Celery and your project installed.
- The Celery app path -A worker.celery matches your codebase (i.e., you have a worker/__init__.py that exposes a celery app).

### start_workers.sh
#### What it is:
A one-stop script to start, stop, restart, check, and view logs for all Celery services used by the app on Linux/macOS.

#### Why it exists:
Your backend processes data in the background. This script makes it easy to run all the moving parts:
- Celery scoring worker (heavy data work)
- Celery maintenance/exports/monitoring worker (support tasks)
- Celery Beat (scheduler for recurring jobs)
- Flower (web dashboard to monitor Celery)

#### What it does
- Checks Redis is up first (fails fast if not).
- Creates a logs/ folder for log files.
- Starts each service in the background (detached) and writes a PID file to /tmp for clean shutdowns:
    - scoring worker → /tmp/celery_scoring.pid, logs → logs/celery_scoring.log
    - maintenance,exports,monitoring worker → /tmp/celery_maintenance.pid, logs → logs/celery_maintenance.log
    - beat (scheduler) → /tmp/celery_beat.pid, logs → logs/celery_beat.log
    - flower (dashboard on port 5555) → /tmp/celery_flower.pid, logs → logs/celery_flower.log
- Stops services by reading those PID files (and force-kills anything left over).
- Checks status by verifying each PID is alive.
- Streams logs with tail -f for any component.
- Uses colored output to make messages easy to scan.

#### Prerequisites
- Redis running and redis-cli available.
- Python environment with Celery and your project installed.
- The Celery app path -A worker.celery matches your codebase (there’s a worker package exposing a celery app).

#### What each function does (quick map)
- check_redis → Ensures Redis responds to PING.
- start_scoring_workers → Celery worker for scoring queue, 2 concurrent processes.
- start_maintenance_workers → Celery worker for maintenance,exports,monitoring queues, 1 process.
- start_scheduler → Celery Beat for scheduled jobs.
- start_flower → Flower monitoring UI on port 5555.
- stop_workers → Gracefully stops all via PID files; force-kills leftovers.
- check_status → Prints which services are RUNNING vs NOT RUNNING.
- show_logs → Streams the chosen log file with tail -f.
- create_logs_dir → Makes the logs/ directory if missing.

## worker

### __init__.py
#### What this file is:
A tiny “package initializer” that makes the worker folder act like a Python package and exposes the key objects your background system needs.

#### Purpose:
When other parts of the app (or Celery itself) import worker, this file ensures two things happen:
1. The Celery app gets loaded (celery_app), so workers know how to connect to Redis/broker and what settings to use.
2. All task functions are registered (by importing tasks). Celery only “sees” tasks if their module is imported at startup.

#### Whats Inside
- celery_app: Your configured Celery application (broker URL, result backend, queues, etc.).
- tasks: The module where the actual background jobs (e.g., campaign scoring, exports, cleanups) live. Importing it at package import time registers all @celery_app.task functions.

#### Why it matters
- Celery must discover tasks: If the tasks module isn’t imported, Celery won’t find any jobs to execute. This __init__.py guarantees they’re pulled in when worker is imported.

- Simple imports elsewhere: Other code can do from worker import celery_app without knowing the internal file layout.

#### How it’s used in your project
Your start scripts run workers like:
- Linux/macOS: celery -A worker.celery worker ...
- Windows: celery -A worker.celery worker ...

Those commands load worker/celery.py (the app config). Separately, importing worker (or explicitly importing worker.tasks) ensures Celery registers tasks. Keeping this __init__.py makes both flows straightforward.

### celery.py
#### What this file does:
It creates and configures the Celery background worker for the project. This is the “control room” that tells workers where to get jobs (Redis), what queues exist, how to run tasks, and which tasks run on a schedule.

This file wires up Celery: it connects to Redis, finds your tasks, decides which queue they belong to, enforces timeouts/rate limits, and schedules recurring jobs.

#### Why this exists
- To connect Celery to Redis (as both the message broker and result store).
- To register your task module (worker.tasks) so Celery can find your @tasks.
- To route each task to the right queue (e.g., scoring, maintenance, exports).
- To set timeouts, retries, logging, and rate limits so jobs behave nicely in production.
- To define scheduled/recurring jobs (via Celery Beat).

#### Key settings
Broker / Backend:
- Uses settings.REDIS_URL for both.
- Think: “All tasks go through Redis, and results are stored there too.”

Task formats:
- Tasks and results are sent as JSON.

Time limits:
- Hard limit: 30 minutes (task_time_limit)
- Soft limit: 25 minutes (task_soft_time_limit) → task gets a warning to wrap up.

Reliability:
- task_track_started=True → you can see when tasks move from “queued” to “running”.
- task_acks_late=True → don’t mark a task “done” until it actually finishes (safer if a worker dies mid-task).
- worker_prefetch_multiplier=1 → each worker grabs one task at a time (fairer when tasks take different time).
- worker_max_tasks_per_child=1000 → recycle worker processes periodically to avoid memory leaks.

Retries & rate limits:
- Default retry delay: 60s, max 3 tries.
- Per-task rate limits like '10/m' so heavy tasks don’t overwhelm the system.

Logging:
- Custom log formats so you can see timestamps, task names, and IDs in logs.

#### Scheduled (recurring) jobs — Celery Beat
These run automatically on a timer:
- Daily: cleanup_old_files_task (queue: maintenance)
- Every 4 hours: cleanup_old_exports (queue: maintenance)
- Every 5 minutes: health_check (queue: monitoring)
- Hourly: update_campaign_statistics (queue: maintenance)

Requires the beat scheduler process to be running (your start scripts do this).

Failure handling
- task_failure_handler: A generic task that logs failures (task id, error, traceback).

Useful for alerting/monitoring or custom on-failure actions.

### tasks.py
#### What this file is:
A collection of long-running “background jobs” (Celery tasks) that handle heavy lifting away from the web request. Things like scoring campaigns, generating exports, cleaning old files, and posting health checks happen here.

This file defines the actual background jobs (scoring, exports, cleanup, health, stats, notifications) that Celery workers run, complete with progress updates, retries, and scheduled housekeeping.

#### How it works at a high level:
- Connects to the database using a local session factory.
- Each function decorated with @celery_app.task becomes a runnable job.
- Tasks can report progress back to Celery (self.update_state(...)) so the UI can show a percent complete.
- If something fails, tasks can retry automatically with a delay (exponential backoff in some cases).

#### Key tasks
process_campaign_scoring(campaign_id_str, user_id_str)
- Purpose: Runs the full scoring pipeline for a campaign file a user uploaded.
- What it does:
    1. Loads the user and campaign from the DB.
    2. Marks the campaign as “processing”.
    3. Builds the scoring configuration (platform/goal/channel).
    4. Calls the main scoring pipeline (ScoringController._process_scoring) which:
        - reads the file, cleans & normalizes data, computes scores, saves results
    5. Updates progress along the way and finally marks the campaign “completed”.
- Progress updates: initializing → loading_data → preprocessing → finalizing → completed.
- Error handling: On failure, marks the campaign “failed”, saves the error, and retries up to 3 times with exponential backoff.

generate_export(campaign_id_str, user_id_str, export_format, include_insights=True, filters=None)
- Purpose: Creates downloadable exports for a campaign (CSV or PDF) in the background.
- What it does:
    1. Verifies the campaign belongs to the user.
    2. For CSV: calls an export helper to build the file bytes.
        - For PDF: builds a compiled report (charts/tables).
    3. Saves the file to storage and returns the saved path/filename/size.
- Progress updates: 25% (generating) → 75% (saving) → 100% (done).
- Retries: Up to 2 retries on failure.

cleanup_old_exports()
- Purpose: Deletes export files older than 24 hours to save disk space.
- Schedule: runs every 4 hours (configured in celery.py beat schedule).
- What it does: Walks the storage/ folder, removes stale export files, and logs how many bytes were freed.

health_check()
- Purpose: Quick heartbeat for monitoring.
- What it checks:
    - Database: can we query a table?
    - Redis: can we ping it?
    - Storage: does the storage directory exist?
- Output: A simple JSON status (healthy/degraded/failed) with timestamps.

update_campaign_statistics()
- Purpose: Computes roll-up stats (counts, averages) for dashboards.
- What it does:
    - Counts campaigns by status, total users, total scored rows, average score.
    - Caches the result in Redis for quick reads.
- Schedule: runs hourly.

send_completion_notification(campaign_id_str, user_email)
- Purpose: Fire-and-forget “your scoring is done” notification.
- What it does: (placeholder) logs an entry and drops a message in Redis so the UI can show a notification.
- Note: In a real system you’d plug this into email/SMS/Slack here.

generate_optimization_lists_task(campaign_id, user_id)
- Purpose: Builds a whitelist (top performers) and blacklist (bottom performers) for a campaign.
- What it does: Calls the scoring controller to fetch results and slice the top/bottom 25% with a minimum-impressions filter.

cleanup_old_files_task()
- Purpose: Cleans up stale uploads (e.g., files older than 30 days that were never attached to a campaign).
- What it does: Removes database records (and, when implemented, the file itself) for unassigned uploads and reports how many were deleted.

validate_file_task(file_id, user_id)
- Purpose: Runs a schema check on an uploaded file in the background so the UI stays snappy.
- What it does:
    - Loads the file content from storage.
    - Parses as CSV/Excel.
    - Runs validations (columns present, row counts, warnings).
    - Returns a structured validation report.

#### Where this fits in the system
- Web API receives a request → queues a Celery task (one of the above).
- Workers (launched by your start scripts) pick up tasks from Redis and run them.
- Progress/Results can be read back by the API and shown in the UI.
- Beat scheduler triggers recurring housekeeping tasks (cleanup, health, stats).

#### Operational notes
- You’ll need Redis running (as the queue) and workers listening on the expected queues (scoring, exports, maintenance, monitoring, notifications).
- Tasks can retry after failures — that’s normal when working with files or external services.
- Long tasks report progress so users aren’t left guessing.
- Housekeeping tasks help keep storage small and dashboards fast.

## Dockerfile
### Purpose:
Defines a repeatable recipe to package and run the backend API in a lightweight Linux container.

Builds a minimal Python 3.11 container, installs system & Python dependencies, copies the app, runs it as a non-root user with Uvicorn on port 8000, and includes a simple HTTP healthcheck.

### What each section does
- Base image: FROM python:3.11-slim → small Python 3.11 image to build on.
- Workdir: WORKDIR /app → sets the folder everything runs from inside the container.
- Env flags:
    - PYTHONDONTWRITEBYTECODE=1 → don’t create .pyc files.
    - PYTHONUNBUFFERED=1 → show logs immediately (no buffering).
- System deps: apt-get install ... gcc postgresql-client → tools needed to compile some Python packages and talk to Postgres from the shell.
- Python deps: copies requirements.txt then pip install -r requirements.txt → installs your app’s Python libraries.
- App code: COPY . . → brings your backend code into the image.
- Security: creates non-root user appuser and switches to it.
- Port: EXPOSE 8000 → documents the port the app listens on.
- Healthcheck: periodically calls http://localhost:8000/health to mark the container healthy/unhealthy.
- Start command: runs uvicorn main:app on 0.0.0.0:8000.

## main.py
### Purpose:
Boots the API server, wires in all feature areas (auth, campaigns, scoring, reports, AI), and adds a couple of simple health/check routes.

Central app file that configures logging, docs, security middleware, plugs in all feature routers, and exposes simple root/health endpoints for the Caliber API.

### What it sets up
- Logging: Calls setup_logging() so all services share consistent, formatted logs.
- FastAPI app config: Human-readable title/description/version and built-in docs at:
    - Swagger UI → /docs
    - ReDoc → /redoc
- CORS (browser access): Lets your frontend (e.g., http://localhost:3000/5173) call this API from the browser.
    - Change allow_origins when you deploy to your real domain(s).
- Trusted hosts (security): Blocks requests with unexpected Host headers. Allowed: localhost, 127.0.0.1, and any *.caliber.ai domain.
    - Update allowed_hosts to match your production hostname(s).
- Routers (feature modules): Plugs in the route groups from other parts of the app:
    - auth_service.routes
    - campaign_service.routes
    - scoring_service.routes
    - report_service.routes
    - ai_service.routes

### Built-in lightweight routes
- GET / → returns { "message": "Caliber API is running" } (quick sanity check).
- GET /health → returns { "status": "healthy" } (used by container/orchestrator health checks).

### Local development
- If you run this file directly, it starts Uvicorn on 0.0.0.0:8000 with reload=True for auto-restart on code changes.

### How to extend it
- Add a new area? Create a router in your module and call app.include_router(your_router) here.
- New frontend domain? Add it to allow_origins.
- New deployment host? Add it to allowed_hosts.

