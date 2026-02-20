High Level Overview: Setup a tutorial on how to use FastAPI + uvicorn in a python backend to receive numpy data and to send numpy data.

The possible setups are client A -> Host B -> Container C and Client = Host B -> Container C.

Client:
- Create a dummy client that lets you select a numpy file and sends it to the backend.
- The dummy client must be capable of receiving data from the backend. That includes numpy data streamed for plotting.
- The dummy client must be able to tell the backend to start/stop streaming.


Backend:
- The backend must be able to stop streaming data upon the clients request.
- The backend must be able to receive data from the client, including numpy data.
