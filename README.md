# Hey House

A voice concierge for [The House by Edge & Node](https://thehousesanfrancisco.com) — a 13,000 sq ft AI workplace in San Francisco's Presidio. Built on [LiveKit Agents](https://docs.livekit.io/agents/).

> The office should be the best demo of the product. Agents at the front door. Guest concierge. Conference room booking. Whatever a voice agent can do, the office is a live environment to prove it in.

I run The House. I built this as my live application for LiveKit's first San Francisco Workplace Manager role. It's a working version of the thesis.

## What it does

A voice agent that answers the questions members and guests actually ask at The House:

- **Info** — WiFi, hours, rooms, house rules, AV.
- **Availability** — checks the six bookable rooms against today's calendar, suggests the nearest free alternative if yours is taken.
- **Handoff** — the things only I can decide (AV for North Main, investor intros, anything non-standard) get captured and flagged for me. The agent never promises what it can't deliver.

The investor-intro handler exists because the ask comes up weekly. Teams from a16z, General Catalyst, YC, and Coinbase work out of The House. The agent politely captures the ask and tells the requester I handle intros personally.

## Stack

LiveKit's canonical voice quickstart:

- **STT** — Deepgram (`nova-3`)
- **LLM** — OpenAI (`gpt-4o`)
- **TTS** — Cartesia (`sonic`)
- **VAD** — Silero
- **Transport** — LiveKit Cloud

## Run it locally

```bash
git clone https://github.com/glabun002/hey-house
cd hey-house
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
# fill in the 6 keys in .env
python agent.py console
```

`console` runs the agent in your terminal with push-to-talk. Use `dev` instead to connect to the LiveKit Cloud playground.

## Project layout

```
hey-house/
├── agent.py              # the agent, 4 tools, system prompt
├── data/
│   ├── knowledge.md      # single source of truth for what the agent knows
│   ├── rooms.json        # mock calendar for the 8 rooms
│   └── handoffs.jsonl    # agent-captured requests for George (gitignored)
├── docs/
│   └── loom-script.md    # the 45-second walkthrough
├── .env.example
└── requirements.txt
```

## Why this exists

My cover letter:

> I'm excited about this role specifically because launching LiveKit's first San Francisco office is the same problem I've been solving at The House, except now for the team building the voice infrastructure layer I'm already watching reshape the way we interact with traditional GUIs. Crafting the premier workspace for LiveKit employees is only half of it. The other half is using the space as the product's showroom. The office should be the best demo of the product.

This repo is that, made concrete.

— George Labunsky
