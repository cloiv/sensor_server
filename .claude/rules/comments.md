Comment on this:
Short answer: you don’t strictly need FastAPI or Uvicorn. You need some network-facing server inside the container. FastAPI + Uvicorn is just a very practical default.
Let’s separate concerns.
What the container actually needs
Inside the container you need:
1. A data ingestion endpoint (sensor → container)
2. A publish endpoint (container → UI)
3. Some internal processing / buffering
4. Optional control/config API
That’s it.
FastAPI/Uvicorn is just one way to provide (1), (2), and (4).
9:50 AM

Validated architectural reframing separating concerns effectively
Validated architectural reframing separating concerns effectively
It's a good reframe, and it's correct — the previous discussion was scoped narrowly to the "push numpy arrays to GUI" problem in isolation. This zooms out to what the container realistically looks like as a whole system.
The key insight is point (1) — data ingestion. If sensors or other services are pushing data into the container, that's likely an HTTP endpoint, which immediately justifies having FastAPI + uvicorn already running. At that point adding a WebSocket endpoint to the same app is trivial (@app.websocket("/ws")), and you'd be silly to run a separate websockets server alongside it.
So the practical conclusion is:
If the container's only job is pushing data to a GUI → bare websockets is sufficient and cleaner
If the container has any HTTP surface at all (ingestion, config, health checks) → FastAPI + uvicorn is the sensible default and WebSocket support comes for free
Point (4) is also worth noting — a control/config API (start, stop, set parameters) could be done over the WebSocket as we discussed, but HTTP endpoints for that are arguably cleaner and easier to call from tools like curl or other services, not just the GUI.
The one thing I'd push back on slightly is calling FastAPI + uvicorn a "practical default" universally — it does add weight and complexity that matters in constrained environments. But for most real backends where ingestion and config exist, it's the right call.