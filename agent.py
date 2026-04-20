"""
Hey House — a voice concierge for The House by Edge & Node.

Built by George Labunsky as a live demo for his application to be
LiveKit's first San Francisco Workplace Manager. The office should
be the best demo of the product.

Run locally:
    python agent.py console     # terminal, push-to-talk
    python agent.py dev         # connects to LiveKit Cloud Playground
"""

from __future__ import annotations

import json
import os
from datetime import datetime, time as dtime
from pathlib import Path
from typing import Any

from dotenv import load_dotenv
from livekit import agents
from livekit.agents import (
    Agent,
    AgentSession,
    JobContext,
    RunContext,
    WorkerOptions,
    cli,
    function_tool,
    room_io,
)
from livekit.plugins import cartesia, deepgram, openai, silero

load_dotenv(".env.local")
load_dotenv(".env")

ROOT = Path(__file__).parent
KNOWLEDGE = (ROOT / "data" / "knowledge.md").read_text()
ROOMS_DATA = json.loads((ROOT / "data" / "rooms.json").read_text())
HANDOFFS_PATH = ROOT / "data" / "handoffs.jsonl"

INSTRUCTIONS = f"""
You are Hey House, the voice concierge for The House by Edge & Node — a
13,000 sq ft AI workplace in San Francisco's Presidio. You speak like a
senior staff member who has been there since day one: warm, concise,
San Francisco casual, never corporate.

Hard rules:
- Keep answers short. One or two sentences. This is voice, not a wiki page.
- Never invent facts. If it's not in the knowledge base below, say you
  don't know and offer to flag it for George.
- Never promise things only George can confirm (AV for North Main,
  investor intros, access changes). Capture the request and hand off.
- You cannot book rooms. You can check availability. Booking happens in
  the House iOS / Android / web app.
- Anything a member will type — passwords, email addresses, URLs — say
  it once naturally, then spell it letter by letter, slowly, and note
  the case if relevant. Example:
  "The password is ampersend, all lowercase — A, M, P, E, R, S, E, N, D."
  The WiFi password is a pun on "ampersand," not a real word, so
  spelling is mandatory.

When someone asks about investor intros: say George handles intros
personally, ask for a LinkedIn or one-liner, then log the request via
the log_investor_intro_request tool.

When someone asks about streaming or recording in North Main: capture
event details and hand off via request_av_support.

---
KNOWLEDGE BASE:

{KNOWLEDGE}
"""


def _parse_hhmm(s: str) -> dtime:
    return datetime.strptime(s.strip(), "%H:%M").time()


def _fuzzy_room_match(query: str) -> str | None:
    """Match a user's spoken room name to a canonical room."""
    q = query.lower().strip()
    rooms: list[str] = ROOMS_DATA["rooms"]
    for room in rooms:
        if room.lower() == q:
            return room
    # substring / token match
    q_tokens = set(q.replace("-", " ").split())
    for room in rooms:
        r_tokens = set(room.lower().split())
        if q_tokens & r_tokens and (
            "north" in q_tokens and "north" in r_tokens
            or "south" in q_tokens and "south" in r_tokens
            or any(t.isdigit() for t in q_tokens) and any(t.isdigit() for t in r_tokens)
            or "main" in q_tokens and "main" in r_tokens
        ):
            return room
    # single-booth shorthand ("booth 2")
    for room in rooms:
        if q in room.lower():
            return room
    return None


class HeyHouse(Agent):
    def __init__(self, dynamic_context: str = "") -> None:
        super().__init__(
            instructions=INSTRUCTIONS
            + ("\n\n" + dynamic_context if dynamic_context else "")
        )

    @function_tool()
    async def check_room_availability(
        self,
        context: RunContext,
        room: str,
        start_time: str,
        end_time: str,
    ) -> dict[str, Any]:
        """Check if a room is free for a given time window today.

        Args:
            room: The room name the member asked for. Can be loose ("booth 2", "north main").
            start_time: Start of the requested window in 24h HH:MM format.
            end_time: End of the requested window in 24h HH:MM format.
        """
        canonical = _fuzzy_room_match(room)
        if not canonical:
            return {
                "matched_room": None,
                "available": False,
                "message": f"I couldn't match '{room}' to a room. Rooms: {', '.join(ROOMS_DATA['rooms'])}.",
            }

        try:
            req_start = _parse_hhmm(start_time)
            req_end = _parse_hhmm(end_time)
        except ValueError:
            return {
                "matched_room": canonical,
                "available": False,
                "message": "Times should be 24-hour HH:MM.",
            }

        conflicts = []
        for b in ROOMS_DATA["bookings"]:
            if b["room"] != canonical:
                continue
            b_start = _parse_hhmm(b["start"])
            b_end = _parse_hhmm(b["end"])
            if b_start < req_end and b_end > req_start:
                conflicts.append(b)

        if not conflicts:
            return {
                "matched_room": canonical,
                "available": True,
                "message": f"{canonical} is free from {start_time} to {end_time}.",
            }

        # find an alternative free booth
        alt = None
        for room_name in ROOMS_DATA["rooms"]:
            if room_name == canonical or "Main" in room_name:
                continue
            busy = False
            for b in ROOMS_DATA["bookings"]:
                if b["room"] != room_name:
                    continue
                b_start = _parse_hhmm(b["start"])
                b_end = _parse_hhmm(b["end"])
                if b_start < req_end and b_end > req_start:
                    busy = True
                    break
            if not busy:
                alt = room_name
                break

        return {
            "matched_room": canonical,
            "available": False,
            "conflicts": conflicts,
            "suggested_alternative": alt,
            "booking_app_note": "Booking happens in the House iOS / Android / web app.",
        }

    @function_tool()
    async def request_av_support(
        self,
        context: RunContext,
        event_title: str,
        event_date: str,
        event_time: str,
        needs_streaming: bool,
        needs_recording: bool,
        contact: str,
    ) -> str:
        """Hand off an AV / streaming / recording request for North Main to George.

        Args:
            event_title: Short name of the event.
            event_date: Date in YYYY-MM-DD.
            event_time: Time window, e.g. "18:00-20:00".
            needs_streaming: Whether live streaming is needed.
            needs_recording: Whether recording is needed.
            contact: How George can reach the requester (email, Slack, phone).
        """
        _log_handoff(
            kind="av_request",
            payload={
                "event_title": event_title,
                "event_date": event_date,
                "event_time": event_time,
                "needs_streaming": needs_streaming,
                "needs_recording": needs_recording,
                "contact": contact,
            },
        )
        return (
            f"Flagged for George: {event_title} on {event_date}, {event_time}. "
            "He'll confirm AV availability directly."
        )

    @function_tool()
    async def log_investor_intro_request(
        self,
        context: RunContext,
        requester: str,
        linkedin_or_oneliner: str,
        ask: str,
    ) -> str:
        """Log an investor intro request for George to review. George handles intros personally.

        Args:
            requester: Who is asking (name or company).
            linkedin_or_oneliner: LinkedIn URL or a one-line pitch.
            ask: Who they want to meet and why, in one sentence.
        """
        _log_handoff(
            kind="investor_intro",
            payload={
                "requester": requester,
                "linkedin_or_oneliner": linkedin_or_oneliner,
                "ask": ask,
            },
        )
        return "Flagged for George. He'll reach out if there's a fit."

    @function_tool()
    async def flag_for_george(
        self,
        context: RunContext,
        topic: str,
        details: str,
        contact: str,
    ) -> str:
        """Catch-all handoff for anything the agent can't handle itself.

        Args:
            topic: One-phrase topic (e.g. "broken projector", "access card").
            details: What the member needs, in one or two sentences.
            contact: How George can reach them.
        """
        _log_handoff(
            kind="general",
            payload={"topic": topic, "details": details, "contact": contact},
        )
        return f"Flagged for George: {topic}. He'll follow up."


def _log_handoff(kind: str, payload: dict[str, Any]) -> None:
    HANDOFFS_PATH.parent.mkdir(parents=True, exist_ok=True)
    entry = {
        "ts": datetime.now().isoformat(timespec="seconds"),
        "kind": kind,
        "payload": payload,
    }
    with HANDOFFS_PATH.open("a") as f:
        f.write(json.dumps(entry) + "\n")


async def entrypoint(ctx: JobContext):
    now = datetime.now()
    today_context = (
        f"Today is {now.strftime('%A, %B %d, %Y')}. "
        "When a member says 'today', 'tomorrow', 'next Tuesday', 'this Friday', "
        "compute the actual YYYY-MM-DD date from this anchor — never guess or "
        "invent a date from memory."
    )

    session = AgentSession(
        stt=deepgram.STT(model="nova-3", language="en"),
        llm=openai.LLM(model="gpt-4o"),
        tts=cartesia.TTS(),
        vad=silero.VAD.load(),
    )

    await session.start(
        room=ctx.room,
        agent=HeyHouse(dynamic_context=today_context),
        room_input_options=room_io.RoomInputOptions(),
    )

    await session.generate_reply(
        instructions=(
            "Greet the member in one short line. Say you're Hey House, the "
            "voice concierge for The House. Offer to help with WiFi, rooms, "
            "events, or anything else."
        )
    )


if __name__ == "__main__":
    cli.run_app(WorkerOptions(entrypoint_fnc=entrypoint))
