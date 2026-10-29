"""Offline missions — used when the AI is unavailable, rate-limited,
returns invalid JSON, or fails the safety check. The demo never breaks."""

from __future__ import annotations

import random

from .models import Mission

_TEMPLATES = {
    "Relaxing": dict(
        title="The {m}-Minute Reset",
        goal="Slow down, breathe and notice the world around you without a screen.",
        steps=["Walk somewhere green or open, at an easy pace.",
               "Find a spot to sit or stand still for five minutes.",
               "Take ten slow breaths and just listen.",
               "Walk back by a different route."],
        observe=["Three sounds you'd normally tune out", "The colour that stands out most",
                 "How the air smells right now"],
    ),
    "Fun": dict(
        title="The Hidden Details Challenge",
        goal="Find small details that most people walk straight past.",
        steps=["Head to a nearby public space.", "Hunt for three overlooked details.",
               "Give each one a made-up backstory.", "Pick a winner on the way back."],
        observe=["Something old hiding in plain sight", "A pattern or texture you like",
                 "Something that made you smile"],
    ),
    "Creative": dict(
        title="Pocket Notebook Walk",
        goal="Collect material for something creative using only your eyes and memory.",
        steps=["Walk to a nearby open space.", "Choose one theme: circles, red, or doors.",
               "Collect five examples of your theme.", "Back home, sketch or describe your favourite."],
        observe=["Your best example of the theme", "An unexpected shape", "A good title for this walk"],
    ),
    "Social": dict(
        title="Say Hello Loop",
        goal="Have small, friendly moments with the world around you.",
        steps=["Walk a short loop through a busy public area.",
               "Say thanks or hello to someone at a shop or café.",
               "If with friends, each person picks the next turn.",
               "End somewhere you can sit together for a minute."],
        observe=["The friendliest moment", "Something you'd recommend to a friend",
                 "A place you want to come back to"],
    ),
    "Active": dict(
        title="Landmark Dash",
        goal="Get your heart rate up with a mini route to a landmark and back.",
        steps=["Pick the nearby landmark as your target.", "Walk briskly there.",
               "Do one lap of it at an easy jog or fast walk.", "Cool down with a slow walk back."],
        observe=["How your body feels halfway", "The best view on the route",
                 "Something you've never noticed before"],
    ),
}


def offline_mission(vibe: str, minutes: int, company: str, wet: bool,
                    nearby: list[str] | None = None) -> Mission:
    t = _TEMPLATES.get(vibe, _TEMPLATES["Relaxing"])
    where = random.choice(nearby[:3]) if nearby else "A nearby park or public square"
    steps = list(t["steps"])
    if company == "With friends":
        steps[-1] += " Compare notes with your friends."
    elif company == "With family":
        steps[-1] += " Everyone shares their favourite find."
    return Mission(
        title=t["title"].format(m=minutes),
        goal=t["goal"],
        steps=steps,
        observe=list(t["observe"]),
        duration_min=minutes,
        where=where,
        safety="Stay in public, well-lit places, keep to paths, and tell someone where you're going.",
        rainy_plan=("It's wet — take a jacket and shorten the route, or do it under a covered "
                    "walkway or at a library window.") if wet else "",
        source="offline",
    )
