# 🌿 Outside Buddy — less screen, more life

**An open-source AI buddy that turns your mood, free time and surroundings into a short,
real-world mission — then tells you to put your phone down.**

Built at Hacktoberfest Hack Day Galway 2026 · Theme: **Touch Grass** · AI: **Gemma 4** (open-weight) · License: MIT

---

## The problem
Students spend their free time scrolling. They *want* to go outside, but when you're bored,
tired or short on time, "go for a walk" is too vague, and generic activity lists don't fit
your mood, budget or the Galway weather.

## Who it's for
- **Students** (starting with University of Galway) with 10–60 spare minutes and a phone in their hand.
- **Parents** who want their teen or uni student off the screen, without nagging or tracking them.

## What's inside
- 🎒 **Student mode:** check in with mood chips, 🎲 *Surprise me*, get a Gemma-planned side quest, phone-away timer, then claim XP
- 🌱 **Levels, streaks and a sticker book:** Seed → Sprout → Sapling → Tree → Forest, 🔥 day streaks, 8 collectible badges
- 🧾 **Touch grass receipt:** a shareable image of every finished quest
- 🏡 **Parent mode:** plan a quest for your teen or the whole family and send it as a friendly WhatsApp message. No tracking, ever.
- 🌍 **Works anywhere:** real nearby places and live weather for any town in the world

## How it works
1. **Check in** — mood, energy, time, budget, alone/friends, vibe.
2. **Gemma 4 plans a mission** grounded in **real nearby places** (OpenStreetMap) and **live weather** (Open-Meteo). Raining? You get a rainy-day plan.
3. **Phone away** — a calm countdown; the app gets out of your way.
4. **Reflect** — 3 quick questions, saved only on your device.
5. **Gets better** — simple rules tune future missions to what you enjoyed.

```
check-in ─► [security layer] ─► Gemma 4 ─► schema + safety check ─► mission card
                 ▲                                   │ fails?
   OSM places + weather (fenced as data)             └─► offline mission (never breaks)
```

## Why open-source AI
- **Gemma 4** is open-weight (Apache 2.0): anyone can inspect, self-host or swap the model.
- Missions run through the Gemini API today; set `GEMMA_MODEL` or point at a local Gemma for fully offline use.
- All code is MIT licensed.

## Security (see [SECURITY.md](SECURITY.md))
Prompt-injection guard · untrusted-data fencing · allow-listed inputs · schema-validated + safety-filtered AI output ·
XSS-safe rendering · parameterised SQL · API key never in code · rate limiting · location rounded to ~1 km · local-only history with one-click delete.

## Run it

```bash
git clone https://github.com/Nivedhaweb/outside-buddy.git
cd outside-buddy
python -m venv venv
venv\Scripts\activate          # Mac/Linux: source venv/bin/activate
pip install -r requirements.txt
copy .env.example .env         # Mac/Linux: cp .env.example .env
# open .env and paste your key from https://aistudio.google.com/apikey
streamlit run app.py
```

No key? It still works with built-in offline missions.

Seeing "Gemma couldn't be reached"? Run `python check_ai.py`. It tells you exactly what's wrong
(bad key, model not available, quota, or network).

## Deploy it (free)
1. Push this repo to GitHub (`.env` is git-ignored, so your key stays private).
2. Go to [share.streamlit.io](https://share.streamlit.io), sign in with GitHub, click **Create app**.
3. Pick the repo, branch `main`, main file `app.py`. In **Advanced settings** choose Python 3.12 and paste:
   ```toml
   GEMINI_API_KEY = "your-key"
   PUBLIC_DEMO = "true"
   ```
4. Click **Deploy**. `PUBLIC_DEMO` gives every visitor their own private history.

## Test it
```bash
pytest
```
24 tests cover injection blocking, unsafe-output blocking, fallbacks, SQL injection and privacy.

## Project structure
```
app.py              Streamlit UI (check-in → mission → phone-away → reflect)
buddy/ai.py         Gemma 4 prompt, call, JSON parse, validation, fallback
buddy/context.py    Nearby places (Overpass) + weather (Open-Meteo) + geocoding
buddy/security.py   Sanitising, injection detection, safety filter, privacy, rate limit
buddy/models.py     Mission schema (Pydantic)
buddy/fallback.py   Offline missions
buddy/storage.py    Local SQLite history, XP, levels, streaks, badges, personalisation
buddy/share.py      Parent invite message + touch grass receipt
check_ai.py         Diagnose your Gemma connection
tests/              pytest suite
```

## Roadmap
- Run Gemma 4 E2B on-device (fully offline, no API)
- Photo proof of "one thing you noticed" using Gemma's vision
- Group missions with friends

## Credits
Map data © OpenStreetMap contributors (ODbL) · Weather by Open-Meteo · Gemma is provided under the Gemma terms of use.
Inspired by the "put your phone away" idea of [LocReminder](https://github.com/zaifears/locreminder).
