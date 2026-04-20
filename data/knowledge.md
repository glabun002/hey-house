# The House — Knowledge Base

The facts the agent knows. Keep terse. If it's not here, the agent doesn't know it and should say so.

## The venue
- **The House by Edge & Node** — 13,000 sq ft AI workplace in San Francisco's Presidio.
- Operator: George Labunsky (Workplace Operations Lead, since Oct 2022).
- Serves members, sponsors, and guests of portfolio teams from a16z, General Catalyst, Y Combinator, and Coinbase.

## Hours
- Monday – Thursday: 8:30 AM – 7:00 PM
- Friday: 8:30 AM – 5:00 PM
- Weekends: Closed

## WiFi
- Network: **The House by Edge & Node**
- Password: **ampersend** (all lowercase, no spaces)
- One network for members and guests. No separate guest SSID today.

## Rooms
Six bookable rooms:
- **North Telephone Booth** — 1 person, calls / solo focus.
- **South Telephone Booth** — 1 person, calls / solo focus.
- **Telephone Booth 1** — 1 person.
- **Telephone Booth 2** — 1 person.
- **Telephone Booth 3** — 1 person.
- **Telephone Booth 4** — 1 person.
- **North Main** — large events room, ~100+ capacity, live streaming and recording available (requires a technician, see AV).
- **South Main** — open workspace, quiet-ish; be respectful of volume.

All rooms are booked via the House iOS, Android, or web app.

## AV
- North Main is the only room with live streaming and recording.
- Streaming/recording requires a technician. That's George. Requests go to him directly.
- All other rooms: bring your own device, no built-in AV.

## House rules
- **Service animals only.** No non-service pets.
- **Food in the cafe only.** Not in workspaces or phone booths.
- **South Main: be respectful of volume.** It's a shared open workspace.

## How the agent handles common questions

### "Can you introduce me to investors?"
The House hosts teams from a16z, GC, YC, and Coinbase, so the ask comes up weekly. George vets every intro personally. The agent does not make intros. It says: *"George handles intros personally — drop me your LinkedIn or a one-liner and I'll flag it for him. He'll reach out if there's a fit."* Then logs the request.

### Room availability
The agent checks the mock calendar in `data/rooms.json`. If the requested slot is taken, it suggests the nearest free alternative.

### AV / streaming requests for North Main
The agent captures event details and hands off to George. It does not confirm AV is booked — only George can.
