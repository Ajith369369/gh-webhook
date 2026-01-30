# gh-webhook

Flask-based GitHub webhook receiver that stores events in MongoDB and provides a real-time UI for monitoring repository activity.

## Features

- Receives GitHub webhook events (push, pull_request, merge)
- Stores events in MongoDB with normalized schema
- Real-time UI that polls for new events every 15 seconds
- Clean, enterprise-grade code with proper documentation
- Handles UTC timestamps correctly (ISO 8601 format)

## Setup Instructions

### Prerequisites

- Python 3.7 or higher
- MongoDB installed and running (default: `mongodb://localhost:27017`)
- Virtual environment (recommended)

### Installation

1. **Create a virtual environment:**

```bash
pip install virtualenv
virtualenv venv
```

2. **Activate the virtual environment:**

**Windows:**

```bash
venv\Scripts\activate
```

**Linux/Mac:**

```bash
source venv/bin/activate
```

3. **Install dependencies:**

```bash
pip install -r requirements.txt
```

4. **Configure environment variables:**

Only **MONGO_URI** is required. Copy `.env.example` to `.env` and set your MongoDB connection string:

```bash
cp .env.example .env
# Edit .env and set MONGO_URI (e.g. your Atlas connection string or mongodb://localhost:27017/github_webhook)
```

**Required:**
- **MONGO_URI** – MongoDB connection string (e.g. Atlas URI or `mongodb://localhost:27017/github_webhook`). You must set this for a remote DB; if unset, the app falls back to `mongodb://localhost:27017/github_webhook` for local MongoDB.

**Optional (have defaults):**
- **SECRET_KEY** – Flask secret key. Default: `dev-secret-key-change-in-production`. Set a strong value in production.
- **FLASK_DEBUG** – Enable Flask debug mode. Default: `False`. Set to `true` (lowercase) to enable.

5. **Run the Flask application:**

```bash
python run.py
```

The application will start on `http://127.0.0.1:5000`

**Note:** For production, use a production WSGI server like Gunicorn:

```bash
gunicorn -w 4 -b 0.0.0.0:5000 run:app
```

## MongoDB Configuration

### Database Schema

Events are stored in the `events` collection with the following schema:

```javascript
{
    "_id": ObjectId,              // MongoDB default ID
    "request_id": String,          // Git commit hash or PR ID
    "author": String,              // GitHub username
    "action": String,              // Enum: "PUSH", "PULL_REQUEST", "MERGE"
    "from_branch": String,         // Source branch name
    "to_branch": String,           // Target branch name
    "timestamp": String            // ISO 8601 UTC timestamp string
}
```

### Example Document

```json
{
  "request_id": "a1b2c3d",
  "author": "travis",
  "action": "PUSH",
  "from_branch": "staging",
  "to_branch": "staging",
  "timestamp": "2021-04-01T21:30:00Z"
}
```

## API Endpoints

### Webhook Receiver

**Endpoint:** `POST /webhook/github`

Receives GitHub webhook events and stores them in MongoDB.

**Headers:**

- `X-GitHub-Event`: GitHub event type (push, pull_request, etc.)

**Response:**

```json
{
  "message": "Event stored successfully",
  "event": {
    "request_id": "a1b2c3d",
    "author": "travis",
    "action": "PUSH",
    "from_branch": "staging",
    "to_branch": "staging",
    "timestamp": "2021-04-01T21:30:00Z"
  }
}
```

### Polling API

**Endpoint:** `GET /webhook/events?since=<ISO_TIMESTAMP>`

Retrieves events newer than the specified timestamp.

**Query Parameters:**

- `since` (optional): ISO 8601 formatted UTC timestamp string

**Response:**

```json
[
  {
    "request_id": "a1b2c3d",
    "author": "travis",
    "action": "PUSH",
    "from_branch": "staging",
    "to_branch": "staging",
    "timestamp": "2021-04-01T21:30:00Z"
  }
]
```

### UI

**Endpoint:** `GET /`

Serves the main UI page that displays webhook events in real-time.

## How Polling Works

The UI polls the backend API every **15 seconds** to fetch new events:

1. On initial load, all events are fetched
2. The `lastSeenTimestamp` is stored in browser memory
3. Subsequent polls send the `since` parameter with the last seen timestamp
4. Only new events (timestamp > lastSeenTimestamp) are returned
5. New events are appended to the UI without re-rendering old ones

This ensures:

- No duplicate entries
- Efficient data transfer
- Real-time updates without page refresh

## Event Format Display

Events are displayed in the following formats:

### Push Event

```
"Travis" pushed to "staging" on 1st April 2021 - 9:30 PM UTC
```

### Pull Request Event

```
"Travis" submitted a pull request from "staging" to "master" on 1st April 2021 - 9:00 AM UTC
```

### Merge Event

```
"Travis" merged branch "dev" to "master" on 2nd April 2021 - 12:00 PM UTC
```

## GitHub Webhook Configuration

To receive events from your `gh-action` repository:

1. Go to your GitHub repository settings
2. Navigate to "Webhooks"
3. Click "Add webhook"
4. Set the payload URL to: `http://your-server:5000/webhook/github`
5. Set content type to: `application/json`
6. Select events: `push`, `pull_request`
7. Save the webhook

**Note:** For local development, use a tunneling tool to expose your local server. Here are two popular options:

#### Option 1: Using Pinggy (No download required)

[Pinggy](https://pinggy.io/) is a free tunneling service that uses SSH and doesn't require downloading any binaries. It provides both HTTP and HTTPS URLs automatically.

**Windows PowerShell:**
```powershell
ssh -p 443 -R0:127.0.0.1:5000 -L4300:127.0.0.1:4300 qr@free.pinggy.io
```

**Windows Command Prompt:**
```cmd
ssh -p 443 -R0:127.0.0.1:5000 -L4300:127.0.0.1:4300 qr@free.pinggy.io
```

**Linux/Mac:**
```bash
ssh -p 443 -R0:localhost:5000 -L4300:localhost:4300 qr@free.pinggy.io
```

**Important Notes:**
- When prompted for a password, just press Enter (blank password is fine)
- Pinggy will display two URLs: HTTP and HTTPS - **always use the HTTPS URL** for GitHub webhooks
- Your tunnel will expire in 60 minutes on the free tier (upgrade to Pinggy Pro for persistent URLs)
- Use `127.0.0.1` instead of `localhost` on Windows to avoid connection issues

**Troubleshooting SSH Permissions Error:**

If you encounter the error: `Bad owner or permissions on C:\\Users\\USERNAME/.ssh/config`

**Quick Fix (Recommended):**
Add `-F NUL` to ignore the SSH config file:
```powershell
ssh -F NUL -p 443 -R0:127.0.0.1:5000 -L4300:127.0.0.1:4300 qr@free.pinggy.io
```

**Alternative Fix:**
Temporarily rename your SSH config file:
```powershell
# Backup and rename the config file
Rename-Item $env:USERPROFILE\.ssh\config $env:USERPROFILE\.ssh\config.backup

# After using Pinggy, restore it if needed:
# Rename-Item $env:USERPROFILE\.ssh\config.backup $env:USERPROFILE\.ssh\config
```

**Example Pinggy Output:**
```
http://qledd-59-182-184-44.a.free.pinggy.link
https://qledd-59-182-184-44.a.free.pinggy.link
```

Use the HTTPS URL in your GitHub webhook configuration:
- Payload URL: `https://your-pinggy-url.a.free.pinggy.link/webhook/github`

#### Option 2: Using ngrok

Alternatively, you can use [ngrok](https://ngrok.com/):

```bash
ngrok http 5000
```

Then use the ngrok HTTPS URL in your webhook configuration.

## Project Structure

```
gh-webhook/
├── .gitignore
├── README.md
├── requirements.txt
├── run.py
├── config.py
│
├── app/
│   ├── __init__.py          # Flask app factory
│   ├── extensions.py        # MongoDB extension
│   │
│   ├── webhook/
│   │   ├── __init__.py
│   │   └── routes.py        # Webhook and polling endpoints
│   │
│   ├── models/
│   │   └── event_model.py   # Event data model
│   │
│   └── services/
│       └── github_parser.py # GitHub payload parser
│
├── templates/
│   └── index.html           # Main UI page
│
└── static/
    └── poll.js              # Polling JavaScript
```

## Code Quality

This project follows enterprise-grade engineering practices:

- ✅ Proper indentation (PEP8)
- ✅ Clear function-level docstrings
- ✅ Inline comments for non-trivial logic
- ✅ Meaningful variable and function names
- ✅ Consistent folder structure
- ✅ Proper error handling
- ✅ UTC timestamp handling
- ✅ Clean separation of concerns

## Environment Variables

**Required:**
- **MONGO_URI** – MongoDB connection string. The only variable you must set for the app to work (e.g. Atlas URI). If unset, the app falls back to `mongodb://localhost:27017/github_webhook` for local MongoDB.

**Optional (defaults):**
- **SECRET_KEY** – Flask secret key. Default: `dev-secret-key-change-in-production`. Override with a strong value in production.
- **FLASK_DEBUG** – Enable Flask debug mode. Default: `False`. Set to `true` (lowercase) to enable.

## Troubleshooting

### MongoDB Connection Issues

Ensure MongoDB is running:

```bash
# Check MongoDB status
mongosh --eval "db.adminCommand('ping')"
```

### Webhook Not Receiving Events

1. Check webhook configuration in GitHub settings
2. Verify the endpoint URL is accessible
3. Check Flask application logs for errors
4. Ensure the `X-GitHub-Event` header is present

### Events Not Appearing in UI

1. Check browser console for JavaScript errors
2. Verify the polling API endpoint is working: `GET /webhook/events`
3. Check MongoDB to ensure events are being stored
4. Verify timestamps are in correct format (ISO 8601 UTC)

## License

This project is part of a GitHub webhook integration assessment.
