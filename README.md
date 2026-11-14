# Smallest AI – API Testing

This repository contains API testing work performed as part of the Smallest AI engineering trial. The focus was on testing REST and WebSocket TTS APIs, validating expected behavior, and documenting observations.

## Repository Structure

```text
Smallest.ai-QA/
├── concurrency_results.json
├── concurrency_test.py
├── screenshots/
└── README.md
```

## Testing Coverage

### REST API Testing
- Authentication: valid, invalid, and missing API keys.
- Input validation: empty text, missing fields, invalid voice IDs, and unsupported parameters.
- Boundary testing: text length, speed, and sample rate.
- Response status codes, error messages, and response headers.

### WebSocket API Testing
- Connection and handshake.
- Audio streaming and completion events.
- Multiple sequential requests.
- Invalid input handling and recovery.
- Ping/pong keepalive.
- Default and custom idle timeouts.
- Multi-part streaming.
- Word timestamps.
- Context lifecycle.
- Concurrent requests across separate WebSocket connections.

## Tools Used

- Postman – Manual REST and WebSocket API testing.
- Python – Controlled WebSocket concurrency testing.
- `asyncio` and `websockets` – Asynchronous WebSocket communication.

## Concurrency Test

A Python script was used to test two separate WebSocket connections under a controlled scenario. The second TTS request was sent while the first request was still streaming.

Both requests were accepted and completed successfully, despite the documented account-wide limit of one active TTS request.

The raw execution output is available in `concurrency_results.json`.

## Screenshots

The `screenshots/` directory contains selected screenshots from the manual Postman testing, demonstrating REST responses, validation behavior, and WebSocket interactions.

## Running the Concurrency Test

Install the required dependencies:

```bash
pip install websockets python-dotenv
```

Create a `.env` file in the project root:

```env
API_KEY=your_api_key
```

Run the script:

```bash
python concurrency_test.py
```

Do not commit the `.env` file or expose API credentials.

## Notes

- Testing was performed using my own Smallest AI account.
- Tests were limited to controlled requests.
- No large-scale load or stress testing was performed.
- Findings represent observed behavior during testing and are not claims about all production conditions.