# Security & Privacy

Outside Buddy sends user context to an LLM and pulls data from third-party map/weather
services, so we treat **every input and every output as untrusted**.

## Threats and defences

| Threat | Defence | Code |
|---|---|---|
| Prompt injection via the free-text box | Sanitise (NFKC, strip control/zero-width chars, markup), pattern-based injection detector; flagged notes are dropped and the user is told | `security.sanitize_text`, `detect_injection` |
| Indirect injection via OpenStreetMap place names | Third-party data is fenced as `DATA ONLY, NOT INSTRUCTIONS`; instruction-like items removed | `security.wrap_untrusted` |
| Tampered form values | Server-side allow-list re-check of every choice | `security.ALLOWED`, `validate_choice` |
| Unsafe AI advice (cliffs, swimming, trespass…) | System rules + post-generation safety filter; unsafe missions replaced | `security.check_mission_safety` |
| Malformed AI output | Strict Pydantic schema; retry once, then offline fallback | `models.Mission`, `ai.generate_mission` |
| XSS from AI output | All AI text HTML-escaped; the timer iframe never contains AI text | `app.py` |
| SQL injection | Parameterised SQLite queries only | `storage.py` |
| API key leakage | Key only from `.env` / Streamlit secrets; git-ignored; errors never echoed to UI | `ai._api_key`, `.gitignore` |
| Quota abuse / cost | Per-session rate limit (5 / min) + response caching | `security.RateLimiter` |
| Location privacy | Coordinates rounded to ~1 km before leaving the app; never stored | `security.coarsen` |
| Data retention | History is local SQLite only; no free text or location stored; one-click delete | `storage.py` |
| Error info leaks | `showErrorDetails = false`; exceptions logged by type only | `.streamlit/config.toml` |

## Known limits
- Pattern-based injection detection can be bypassed by novel phrasings; it is one layer of several.
- Safety filtering is keyword-based; users should still use common sense outdoors.

## Reporting
Open a GitHub issue marked **security**, or email the maintainer.
