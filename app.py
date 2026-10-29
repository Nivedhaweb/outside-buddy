"""Outside Buddy — your side quest is outside.

Run:  streamlit run app.py
"""

from __future__ import annotations

import html
import os
import random
import tempfile
import time
import uuid

import streamlit as st
from dotenv import load_dotenv

from buddy import storage
from buddy.ai import Result, _api_key, generate_mission
from buddy.context import DEFAULT_PLACE, build_context, geocode
from buddy.security import ALLOWED, RateLimiter, coarsen
from buddy.share import FACES, invite_text, receipt_svg, svg_data_uri, whatsapp_link

load_dotenv()
st.set_page_config(page_title="Outside Buddy", page_icon="🌿", layout="centered")

# ---------- design tokens: sticker pack on a blue-sky day ----------
# ink #18233D · sky #E4F1FF · grass #22B07D · sun #FFD23F · bubblegum #FF8FB1 · lilac #C9B8FF
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Bricolage+Grotesque:opsz,wght@12..96,600;12..96,800&family=Figtree:wght@400;600;700&display=swap');
:root { --ink:#18233D; --sky:#E4F1FF; --grass:#22B07D; --sun:#FFD23F; --gum:#FF8FB1;
        --lilac:#C9B8FF; --paper:#FFFFFF; --pop: 4px 4px 0 var(--ink); }
.stApp { background: var(--sky); color: var(--ink); }
.stApp :is(p, li, label, input, textarea, button, summary) { font-family: 'Figtree', system-ui, sans-serif; }
[data-testid="stIconMaterial"] { font-family: 'Material Symbols Rounded' !important; }
h1, h2, h3, .display { font-family: 'Bricolage Grotesque', system-ui, sans-serif !important; color: var(--ink); }
.block-container { max-width: 700px; padding-top: 1.2rem; padding-bottom: 5rem; }
#MainMenu, footer, [data-testid="stToolbar"] { visibility: hidden; }

/* stickers */
.sticker { background: var(--paper); border: 2.5px solid var(--ink); border-radius: 22px;
           box-shadow: var(--pop); padding: 1.3rem 1.4rem; margin: .4rem 0 1.1rem; }
.tilt-l { transform: rotate(-1.2deg); } .tilt-r { transform: rotate(1.4deg); }

/* hero */
.hero { position: relative; overflow: hidden; background: var(--grass); color: #fff; }
.hero h1 { color: #fff; font-size: clamp(2.4rem, 8vw, 3.8rem); font-weight: 800; line-height: .95;
           letter-spacing: -.03em; margin: 0 0 .6rem; max-width: 12ch; }
.hero p { color: #fff; margin: 0; max-width: 34ch; font-size: 1.05rem; line-height: 1.45; }
.hero .blob { position: absolute; right: -18px; top: -18px; font-size: 7.5rem; transform: rotate(12deg);
              filter: drop-shadow(4px 4px 0 var(--ink)); }
.badge-sun { display: inline-block; background: var(--sun); color: var(--ink); border: 2px solid var(--ink);
             border-radius: 999px; padding: .15rem .7rem; font-weight: 700; font-size: .85rem;
             margin-bottom: .8rem; transform: rotate(-2deg); }

/* player card */
.player { display: grid; grid-template-columns: auto 1fr auto; gap: .9rem; align-items: center; }
.player .lvl { font-size: 2.4rem; width: 62px; height: 62px; display: grid; place-items: center;
               background: var(--sun); border: 2.5px solid var(--ink); border-radius: 18px; }
.player .name { font-family: 'Bricolage Grotesque', sans-serif; font-weight: 800; font-size: 1.25rem; }
.bar { height: 14px; border: 2px solid var(--ink); border-radius: 999px; background: var(--sky); overflow: hidden;
       margin-top: .35rem; }
.bar > div { height: 100%; background: var(--grass); border-right: 2px solid var(--ink); }
.small { font-size: .85rem; opacity: .75; }
.streak { text-align: center; font-family: 'Bricolage Grotesque', sans-serif; font-weight: 800;
          font-size: 1.6rem; line-height: 1; }
.streak span { display: block; font-family: 'Figtree', sans-serif; font-size: .75rem; font-weight: 600; opacity: .7; }

/* sticker book */
.book { display: grid; grid-template-columns: repeat(4, 1fr); gap: .6rem; }
.stk { text-align: center; padding: .6rem .3rem; border: 2px solid var(--ink); border-radius: 16px;
       background: var(--lilac); font-size: .78rem; font-weight: 700; line-height: 1.2; }
.stk b { display: block; font-size: 1.8rem; margin-bottom: .2rem; }
.stk.locked { background: #F1F4F8; border-style: dashed; opacity: .55; filter: grayscale(1); }

/* form + inputs */
[data-testid="stForm"] { background: var(--paper); border: 2.5px solid var(--ink) !important;
                         border-radius: 22px; box-shadow: var(--pop); padding: 1.2rem 1.3rem; }
[data-testid="stWidgetLabel"] p { font-weight: 700; font-size: 1rem; color: var(--ink); }
[data-baseweb="input"] { border-radius: 14px; border: 2px solid var(--ink) !important; }
[data-testid="stButtonGroup"] button { border-radius: 999px !important; border: 2px solid var(--ink) !important;
                                        background: var(--paper) !important; color: var(--ink) !important; }
[data-testid="stButtonGroup"] button[aria-checked="true"],
[data-testid="stButtonGroup"] button[kind$="Active"] { background: var(--ink) !important; color: #fff !important; }
[data-testid="stButtonGroup"] button[aria-checked="true"] p,
[data-testid="stButtonGroup"] button[kind$="Active"] p { color: #fff !important; }

/* buttons */
.stButton > button, .stDownloadButton > button, .stLinkButton > a,
[data-testid="stFormSubmitButton"] > button {
  border-radius: 999px; border: 2.5px solid var(--ink) !important; font-weight: 700; min-height: 3rem;
  box-shadow: 3px 3px 0 var(--ink); background: var(--paper); color: var(--ink) !important;
  transition: transform .08s, box-shadow .08s; }
.stButton > button:active, [data-testid="stFormSubmitButton"] > button:active,
.stDownloadButton > button:active, .stLinkButton > a:active { transform: translate(3px, 3px); box-shadow: none; }
button[kind="primary"], button[kind="primaryFormSubmit"] { background: var(--sun) !important; font-size: 1.05rem; }
button:focus-visible, a:focus-visible { outline: 3px solid var(--gum) !important; outline-offset: 3px; }

/* quest card */
.quest h2 { font-size: clamp(1.9rem, 6vw, 2.6rem); font-weight: 800; line-height: 1; letter-spacing: -.02em;
            margin: .5rem 0 .5rem; }
.tags { display: flex; flex-wrap: wrap; gap: .4rem; }
.tag { font-size: .82rem; font-weight: 700; padding: .2rem .7rem; border-radius: 999px;
       border: 2px solid var(--ink); background: var(--paper); }
.tag.ai { background: var(--lilac); } .tag.wx { background: var(--sky); } .tag.t { background: var(--sun); }
.goal { font-size: 1.08rem; line-height: 1.45; margin: 0 0 .8rem; }
.where { display: inline-block; background: var(--gum); border: 2px solid var(--ink); border-radius: 12px;
         padding: .3rem .7rem; font-weight: 700; margin-bottom: 1rem; transform: rotate(-1deg); }
ol.steps { list-style: none; counter-reset: s; padding: 0; margin: 0 0 1rem; }
ol.steps li { counter-increment: s; display: grid; grid-template-columns: 2rem 1fr; gap: .6rem;
              align-items: start; padding: .35rem 0; line-height: 1.4; }
ol.steps li::before { content: counter(s); width: 2rem; height: 2rem; border-radius: 50%; background: var(--grass);
                      color: #fff; border: 2px solid var(--ink); display: grid; place-items: center;
                      font-weight: 800; font-family: 'Bricolage Grotesque', sans-serif; }
.side { background: var(--sky); border: 2px dashed var(--ink); border-radius: 16px; padding: .8rem 1rem;
        margin-bottom: .8rem; }
.side b { display: block; margin-bottom: .3rem; }
.side ul { margin: 0; padding-left: 0; list-style: none; }
.side li::before { content: "👀 "; }
.rain { margin: 0 0 .6rem; } .safety { font-size: .88rem; opacity: .75; margin: 0; }

/* parent */
.parent { background: var(--lilac); }
.why { display: grid; grid-template-columns: repeat(3, 1fr); gap: .6rem; margin-top: .9rem; }
.why div { background: var(--paper); border: 2px solid var(--ink); border-radius: 14px; padding: .6rem;
           font-size: .85rem; line-height: 1.3; }
.why b { display: block; font-size: 1.3rem; }

/* done */
.xp { font-family: 'Bricolage Grotesque', sans-serif; font-weight: 800; font-size: clamp(3.4rem, 14vw, 5.5rem);
      line-height: .9; color: var(--ink); animation: pop .5s cubic-bezier(.2, 1.6, .4, 1) both; }
@keyframes pop { from { transform: scale(.4) rotate(-8deg); opacity: 0; } to { transform: none; opacity: 1; } }
.receipt img { width: 100%; max-width: 360px; display: block; margin: 0 auto; transform: rotate(1.5deg);
               filter: drop-shadow(5px 5px 0 rgba(24,35,61,.9)); }

[data-testid="stSidebar"] { background: var(--paper); border-right: 2.5px solid var(--ink); }
[data-testid="stAlert"] { border: 2px solid var(--ink); border-radius: 16px; }
@media (prefers-reduced-motion: reduce) { * { animation: none !important; transition: none !important; } }
@media (max-width: 560px) { .book { grid-template-columns: repeat(2, 1fr); } .why { grid-template-columns: 1fr; }
  .hero .blob { font-size: 5rem; } }
</style>
""", unsafe_allow_html=True)

e = html.escape  # anything from the AI or a third party is escaped before it is rendered

# ---------- session state ----------
ss = st.session_state
for k, v in {"stage": "checkin", "limiter": RateLimiter(max_calls=5, window_s=60), "result": None,
             "prefs": None, "started_at": None, "place": DEFAULT_PLACE, "last": None,
             "mode": "🎒 I'm a student", "in_mood": "Bored", "in_energy": "Medium", "in_minutes": 20,
             "in_vibe": "Relaxing", "in_company": "Alone", "in_budget": "Free",
             "p_who": "My teen", "p_minutes": 20, "p_vibe": "Fun"}.items():
    ss.setdefault(k, v)

def _public_demo() -> bool:
    """On a shared host (e.g. Streamlit Cloud) set PUBLIC_DEMO = true in secrets."""
    flag = os.environ.get("PUBLIC_DEMO", "")
    if not flag:
        try:
            flag = str(st.secrets.get("PUBLIC_DEMO", ""))
        except Exception:
            flag = ""
    return flag.lower() in ("1", "true", "yes")


# Running on your own computer: one history file for you.
# Public demo: each visitor gets a private, throwaway history (random id, temp folder),
# so nobody can see anyone else's missions.
if _public_demo():
    ss.setdefault("db_path", os.path.join(tempfile.gettempdir(), "outside-buddy",
                                          f"{uuid.uuid4().hex}.db"))
    DB = ss.db_path
else:
    DB = None   # -> data/history.db

MOOD_ICON = {"Bored": "😐", "Stressed": "😵‍💫", "Tired": "🥱", "Restless": "⚡", "Happy": "😎", "Lonely": "🫠"}
VIBE_ICON = {"Relaxing": "🧘", "Fun": "🎉", "Creative": "🎨", "Social": "💬", "Active": "🏃"}
BUDGET_LABEL = {"Free": "€0 / ₹0", "A little": "A little (bus, snack)", "Happy to spend": "Happy to spend"}
PARENT_WHO = {"My teen": "Alone", "My uni student": "Alone", "The whole family": "With family"}
LOADING = ["Asking Gemma nicely…", "Scouting the area…", "Checking if it's raining (it's probably raining)…",
           "Finding grass to touch…", "Drawing you a side quest…"]


@st.cache_data(ttl=600, show_spinner=False)
def cached_context(name: str, lat: float, lon: float):
    return build_context(name, lat, lon)


def show(markup: str):
    """Render our own HTML. Lines are de-indented so Markdown can't turn them into code blocks."""
    st.markdown("\n".join(line.strip() for line in markup.splitlines() if line.strip()),
                unsafe_allow_html=True)


def go(stage: str):
    ss.stage = stage
    st.rerun()


def surprise():
    for key in ("mood", "energy", "minutes", "vibe", "company"):
        ss[f"in_{key}"] = random.choice(ALLOWED[key])
    ss.in_minutes = random.choice([10, 20, 30])


def resolve_place(where: str):
    if where.strip() and where.strip() != ss.place[0]:
        found = geocode(where)
        if found:
            ss.place = found
        else:
            st.info(f"Couldn't find “{e(where)}”, so I used {e(ss.place[0])}. "
                    "Add the city or country, like “Marina Beach, Chennai”.")
    name, lat, lon = ss.place
    clat, clon = coarsen(lat, lon, 3)
    return cached_context(name, clat, clon)


def player_stats():
    rows = storage.history(500, path=DB)
    xp = storage.total_xp(rows)
    return rows, storage.level_for(xp), storage.streak(rows), storage.earned_badges(rows)


# ---------- sidebar ----------
with st.sidebar:
    st.markdown("<h3 class='display' style='margin:0'>Outside Buddy 🌿</h3>", unsafe_allow_html=True)
    st.caption("Your side quest is outside.")
    with st.expander("🛡️ Security and privacy", expanded=False):
        st.markdown(f"""
- **AI:** Gemma 4, {'connected' if _api_key() else 'no key set, so offline missions are used'}
- Choices are checked again on the server
- Notes are cleaned and checked for prompt injection
- Map and weather data is treated as data, never as instructions
- Every AI mission passes a schema check and a safety filter
- Location is rounded to about 1 km and never saved
- No tracking: parents send invites, they can't see where you are
- History stays on this device
- Limit: 5 missions a minute
""")
    with st.expander("📜 Past missions"):
        rows = storage.history(10, path=DB)
        if not rows:
            st.caption("No missions yet.")
        for r in rows:
            st.markdown(f"{'✅' if r['completed'] else '⏭️'} **{e(r['title'])}**  \n"
                        f"<span class='small'>{e(str(r['vibe']))}, {r['minutes']} min</span>",
                        unsafe_allow_html=True)
        if rows and st.button("Delete my history"):
            storage.delete_all(path=DB)
            st.toast("History deleted")
            st.rerun()


# ---------- 1. home ----------
def home():
    st.segmented_control("mode", ["🎒 I'm a student", "🏡 I'm a parent"], key="mode",
                         label_visibility="collapsed")
    if (ss.mode or "").endswith("parent"):
        parent_home()
    else:
        student_home()


def student_home():
    rows, lvl, streak_days, badges = player_stats()
    show("""
<div class="sticker hero tilt-l">
  <div class="blob" aria-hidden="true">🌿</div>
  <div class="badge-sun">touch grass, but make it a game</div>
  <h1>Your side quest is outside.</h1>
  <p>Tell us your mood and how long you've got. Gemma plans a mini mission around real places near you.
  Phone goes in your pocket. You level up.</p>
</div>""")

    nxt = (f"{lvl['next_xp'] - lvl['xp']} XP to {lvl['next_name']}" if lvl["next_name"]
           else "Max level. Legend.")
    show(f"""
<div class="sticker player">
  <div class="lvl" aria-hidden="true">{lvl['icon']}</div>
  <div><div class="name">{lvl['name']} · {lvl['xp']} XP</div>
    <div class="bar" role="progressbar" aria-valuenow="{int(lvl['progress'] * 100)}" aria-valuemin="0"
      aria-valuemax="100"><div style="width:{max(4, int(lvl['progress'] * 100))}%"></div></div>
    <div class="small">{nxt}</div></div>
  <div class="streak">{streak_days}🔥<span>day streak</span></div>
</div>""")

    with st.expander(f"🗂️ Sticker book · {len(badges)}/{len(storage.BADGES)} collected"):
        cells = "".join(
            f"<div class='stk{'' if key in badges else ' locked'}' title='{e(how)}'><b>{icon}</b>{e(name)}"
            f"<div class='small'>{e(how)}</div></div>"
            for key, icon, name, how in storage.BADGES)
        show(f"<div class='book'>{cells}</div>")

    c1, c2 = st.columns([3, 2])
    c1.markdown("### Check in")
    c2.button("🎲 Surprise me", on_click=surprise, use_container_width=True)

    with st.form("checkin", border=False):
        mood = st.pills("How are you feeling?", ALLOWED["mood"], key="in_mood",
                        format_func=lambda m: f"{MOOD_ICON.get(m, '')} {m}")
        energy = st.pills("Battery level", ALLOWED["energy"], key="in_energy",
                          format_func=lambda x: {"Low": "🪫 Low", "Medium": "🔋 Medium", "High": "⚡ High"}[x])
        minutes = st.pills("Time you've got", ALLOWED["minutes"], key="in_minutes",
                           format_func=lambda m: f"{m} min")
        vibe = st.pills("Vibe", ALLOWED["vibe"], key="in_vibe",
                        format_func=lambda v: f"{VIBE_ICON.get(v, '')} {v}")
        company = st.pills("Who's coming", ALLOWED["company"], key="in_company",
                           format_func=lambda c: {"Alone": "🙋 Just me", "With friends": "👯 Friends",
                                                  "With family": "🏡 Family"}[c])
        budget = st.pills("Budget", ALLOWED["budget"], key="in_budget",
                          format_func=lambda b: BUDGET_LABEL.get(b, b))
        where = st.text_input("📍 Where are you?", value=ss.place[0], max_chars=80,
                              help="Any town, street or landmark, anywhere. Add the city or country "
                                   "for best results. Only an approximate area is used.")
        extra = st.text_input("Anything I should know? (optional)", max_chars=200,
                              placeholder="Sore knee, keep it flat")
        submitted = st.form_submit_button("Unlock my side quest 🌿", type="primary",
                                          use_container_width=True)

    if submitted:
        prefs = dict(mood=mood or "Bored", energy=energy or "Medium", minutes=minutes or 20,
                     budget=budget or "Free", company=company or "Alone", vibe=vibe or "Relaxing")
        plan(prefs, where, extra)


def parent_home():
    show("""
<div class="sticker hero parent tilt-r" style="color:var(--ink)">
  <div class="blob" aria-hidden="true">💌</div>
  <div class="badge-sun">for parents</div>
  <h1 style="color:var(--ink)">Send a side quest, not a lecture.</h1>
  <p style="color:var(--ink)">Pick how long and what kind of fun. Outside Buddy plans a mission near them,
  and gives you a friendly message to send. No nagging, no tracking.</p>
  <div class="why">
    <div><b>💬</b>An invite, not a screen-time fight</div>
    <div><b>🔒</b>No location tracking. They share what they spotted, if they want</div>
    <div><b>🏡</b>Or do it together as a family</div>
  </div>
</div>""")
    with st.form("parent", border=False):
        who = st.pills("Who's it for?", list(PARENT_WHO), key="p_who")
        minutes = st.pills("How long?", ALLOWED["minutes"], key="p_minutes", format_func=lambda m: f"{m} min")
        vibe = st.pills("What kind?", ALLOWED["vibe"], key="p_vibe",
                        format_func=lambda v: f"{VIBE_ICON.get(v, '')} {v}")
        where = st.text_input("📍 Where are they?", value=ss.place[0], max_chars=80,
                              help="A town or neighbourhood is enough.")
        submitted = st.form_submit_button("Plan a side quest 💌", type="primary", use_container_width=True)
    if submitted:
        who = who or "My teen"
        prefs = dict(mood="Bored", energy="Medium", minutes=minutes or 20, budget="Free",
                     company=PARENT_WHO[who], vibe=vibe or "Fun")
        plan(prefs, where, "")


def plan(prefs: dict, where: str, extra: str):
    if not ss.limiter.allow():
        st.warning(f"That's 5 missions in a minute. Try again in {ss.limiter.retry_after()} seconds.")
        return
    with st.spinner(random.choice(LOADING)):
        ctx = resolve_place(where)
        result = generate_mission(prefs, ctx, extra, storage.preference_hint(path=DB))
    ss.prefs, ss.result, ss.ctx = prefs, result, ctx
    go("mission")


# ---------- 2. quest card ----------
def quest_card():
    result: Result = ss.result
    m, ctx = result.mission, ss.ctx
    for n in result.notes:
        st.info(n)
    src = "<span class='tag ai'>✨ Gemma 4</span>" if m.source == "gemma" else "<span class='tag'>📦 Offline</span>"
    steps = "".join(f"<li><span>{e(s)}</span></li>" for s in m.steps)
    side = "".join(f"<li>{e(o)}</li>" for o in m.observe)
    rain = f"<p class='rain'>☔ <b>If it's wet:</b> {e(m.rainy_plan)}</p>" if m.rainy_plan else ""
    show(f"""
<div class="sticker quest">
  <div class="tags">{src}<span class="tag t">⏱ {m.duration_min} min</span>
    <span class="tag wx">🌦 {e(ctx.weather.summary())}</span><span class="tag">📍 {e(ctx.place_name)}</span></div>
  <h2>{e(m.title)}</h2>
  <p class="goal">{e(m.goal)}</p>
  <div class="where">📍 {e(m.where)}</div>
  <ol class="steps">{steps}</ol>
  <div class="side"><b>Side quests: spot these for bonus XP</b><ul>{side}</ul></div>
  {rain}
  <p class="safety">🦺 {e(m.safety)}</p>
</div>""")

    parent = (ss.mode or "").endswith("parent")
    if parent:
        together = ss.prefs["company"] == "With family"
        msg = invite_text(m, together)
        st.markdown("#### Send it 💌")
        st.code(msg, language=None, wrap_lines=True)
        c1, c2 = st.columns(2)
        c1.link_button("Send on WhatsApp", whatsapp_link(msg), use_container_width=True)
        if c2.button("Do it together now", use_container_width=True):
            ss.started_at = time.time()
            go("outside")
        st.caption("Tip: hover the message and click the copy icon to paste it anywhere.")
    else:
        if st.button("Accept quest & start timer 🌿", type="primary", use_container_width=True):
            ss.started_at = time.time()
            go("outside")

    text = (f"{m.title}\n\n{m.goal}\nWhere: {m.where}\n\n"
            + "\n".join(f"{i}. {s}" for i, s in enumerate(m.steps, 1))
            + "\n\nSpot these:\n" + "\n".join(f"- {o}" for o in m.observe)
            + (f"\n\nIf it's wet: {m.rainy_plan}" if m.rainy_plan else "") + f"\n\nSafety: {m.safety}\n")
    c1, c2 = st.columns(2)
    c1.download_button("Save quest", text, file_name="side-quest.txt", use_container_width=True)
    if c2.button("🔁 Reroll", use_container_width=True):
        go("checkin")


# ---------- 3. phone-away ----------
def outside():
    m = ss.result.mission
    end_ms = int((ss.started_at + m.duration_min * 60) * 1000)
    # Our own static HTML + one number only — no AI text inside the iframe.
    timer_html = f"""
<link href="https://fonts.googleapis.com/css2?family=Bricolage+Grotesque:opsz,wght@12..96,800&family=Figtree:wght@600&display=swap" rel="stylesheet">
<style>body{{margin:0;padding:4px 8px 10px 4px}}
 .box{{font-family:'Figtree',system-ui,sans-serif;text-align:center;padding:26px 16px;border-radius:24px;
   background:#18233D;color:#E4F1FF;border:3px solid #18233D;box-shadow:6px 6px 0 #22B07D}}
 #t{{font-family:'Bricolage Grotesque',system-ui,sans-serif;font-size:clamp(60px,18vw,104px);font-weight:800;
   letter-spacing:-.03em;color:#FFD23F;margin:4px 0;font-variant-numeric:tabular-nums}}
 .ring{{height:12px;border-radius:99px;background:#2b3a5c;overflow:hidden;margin:10px auto 0;max-width:420px}}
 .ring div{{height:100%;background:#22B07D;width:0}}</style>
<div class="box"><div>📵 phone in pocket. touching grass for</div>
<div id="t">--:--</div><div id="s">you got this</div><div class="ring"><div id="p"></div></div></div>
<script>
  const end = {end_ms}, total = {m.duration_min * 60};
  const lines = ["you got this", "look up 👀", "main character walk", "breathe in, breathe out", "almost there"];
  function tick() {{
    const s = Math.max(0, Math.round((end - Date.now())/1000));
    document.getElementById('p').style.width = (100 - s / total * 100) + '%';
    if (s === 0) {{ document.getElementById('t').textContent = "DONE 🎉";
                   document.getElementById('s').textContent = "come back and claim your XP"; return; }}
    document.getElementById('t').textContent = String(Math.floor(s/60)).padStart(2,'0') + ':' + String(s%60).padStart(2,'0');
    if (s % 60 === 0) document.getElementById('s').textContent = lines[Math.floor(Math.random()*lines.length)];
    setTimeout(tick, 1000);
  }}
  tick();
</script>"""
    st.markdown(f"<h2 style='margin:.2rem 0 .8rem'>{e(m.title)}</h2>", unsafe_allow_html=True)
    if hasattr(st, "iframe"):
        st.iframe(timer_html, height=270)
    else:  # older Streamlit
        import streamlit.components.v1 as components
        components.html(timer_html, height=270)
    st.markdown(f"📍 **{e(m.where)}**")
    with st.expander("Forgot a step? Peek here (then pocket the phone)"):
        for i, s in enumerate(m.steps, 1):
            st.markdown(f"{i}. {e(s)}")
    if st.button("I'm back, claim my XP ✨", type="primary", use_container_width=True):
        go("reflect")


# ---------- 4. reflect ----------
def reflect():
    m, p = ss.result.mission, ss.prefs
    st.markdown("<h2 style='margin:.2rem 0 .2rem'>Welcome back 👋</h2>"
                "<p class='small'>Quick debrief. Takes 10 seconds.</p>", unsafe_allow_html=True)
    with st.form("reflect"):
        done_it = st.pills("Did you do it?", ["✅ Yes", "🤏 Partly", "❌ Nope"], default="✅ Yes")
        st.markdown("**What did you spot?** (+5 XP each)")
        spotted = sum(st.checkbox(o, key=f"spot_{i}") for i, o in enumerate(m.observe))
        feeling = st.select_slider("Vibe check, now?", [1, 2, 3, 4, 5], value=4,
                                   format_func=lambda v: FACES[v - 1])
        again = st.pills("Run it back sometime?", ["Yes", "No"], default="Yes")
        st.text_area("Best moment (just for you, never saved)", max_chars=300)
        if st.form_submit_button("Claim XP ✨", type="primary", use_container_width=True):
            rows_before = storage.history(500, path=DB)
            badges_before = storage.earned_badges(rows_before)
            completed = (done_it or "✅ Yes") != "❌ Nope"
            storage.save_result(m.title, p["mood"], p["vibe"], p["company"], m.duration_min,
                                completed, feeling, (again or "Yes") == "Yes",
                                spotted=spotted, wet=ss.ctx.weather.wet, path=DB)
            rows, lvl, streak_days, badges = player_stats()
            ss.last = dict(xp=storage.mission_xp(m.duration_min, completed, spotted), spotted=spotted,
                           feeling=feeling, lvl=lvl, streak=streak_days,
                           new_badges=badges - badges_before,
                           levelled_up=storage.level_for(storage.total_xp(rows_before))["name"] != lvl["name"])
            go("done")


def done():
    m, last = ss.result.mission, ss.last
    lvl = last["lvl"]
    st.balloons()
    lvl_line = (f"Level up! You're now a <b>{lvl['icon']} {lvl['name']}</b>." if last["levelled_up"]
                else f"{lvl['icon']} {lvl['name']} · {lvl['xp']} XP total")
    show(f"""
<div class="sticker tilt-l" style="text-align:center">
  <div class="xp">+{last['xp']} XP</div>
  <p style="margin:.6rem 0 .4rem;font-size:1.05rem">{lvl_line}</p>
  <div class="bar" style="max-width:360px;margin:0 auto"><div style="width:{max(4, int(lvl['progress'] * 100))}%"></div></div>
  <p class="small" style="margin-top:.4rem">{last['streak']} day streak 🔥</p>
</div>""")
    if last["new_badges"]:
        cells = "".join(f"<div class='stk'><b>{icon}</b>{e(name)}</div>"
                        for key, icon, name, _ in storage.BADGES if key in last["new_badges"])
        st.markdown("### New sticker unlocked!")
        show(f"<div class='book'>{cells}</div>")

    svg = receipt_svg(m, last["spotted"], len(m.observe), last["feeling"], last["xp"],
                      f"{lvl['name']}", last["streak"])
    st.markdown("### Your touch grass receipt 🧾")
    show(f"<div class='receipt'><img alt='Touch grass receipt' src='{svg_data_uri(svg)}'></div>")
    c1, c2 = st.columns(2)
    c1.download_button("Download receipt", svg, file_name="touch-grass-receipt.svg",
                       mime="image/svg+xml", use_container_width=True)
    if c2.button("Next quest 🌿", type="primary", use_container_width=True):
        go("checkin")


{"checkin": home, "mission": quest_card, "outside": outside,
 "reflect": reflect, "done": done}[ss.stage]()
