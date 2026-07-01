# First-Aid Kit Tracker

A web application for tracking first-aid kit contents, quantities, and expiry dates. Built with FastAPI, Neon PostgreSQL, and deployed on Vercel.

**Live site:** [https://first-aid-tracker.vercel.app](https://first-aid-tracker.vercel.app)

## Features

- **Kit Management** — Enter a kit code to view and manage items
- **Item Tracking** — Track quantity, expiry dates, and item status (OK / Expires Soon / Expired / Empty)
- **Add / Edit / Delete** — Full CRUD operations via modal dialogs with confirmation
- **3-Dot Action Menu** — Each item has a ⋮ menu with Edit and Delete options to prevent accidental removal
- **Recent Changes History** — Draggable modal popup showing what changed, when, and by whom
  - ✏️ Edited — shows old → new values (e.g., Qty: 1 → 3)
  - ➕ Added — shows item details on creation
  - 🗑 Deleted — shows which item was removed
  - Changes persist across page refreshes via localStorage
- **First-Aid Items Editor** — Maintain a master list of first-aid items with categories
- **All Items View** — See all items across all kits in one place
- **Cloud Database** — Data persisted in Neon PostgreSQL (no data loss on server restarts)

## Architecture

```
┌─────────────────────────────────────┐
│           Vercel (Deploy)           │
│                                     │
│  ┌───────────┐   ┌───────────────┐  │
│  │  static/  │   │  api/main.py  │  │
│  │  HTML     │──▶│  FastAPI       │  │
│  │  CSS      │   │  Serverless   │  │
│  │  JS       │   │  Function     │  │
│  └───────────┘   └──────┬────────┘  │
│                         │           │
└─────────────────────────┼───────────┘
                          │ asyncpg
                          ▼
              ┌───────────────────┐
              │  Neon PostgreSQL  │
              │  (Cloud SQL)      │
              └───────────────────┘
```

| Layer | Technology | Description |
|-------|-----------|-------------|
| Frontend | HTML / CSS / Vanilla JS | Single-page app with kit selection, item management, and editing views |
| Backend | FastAPI (Python) | RESTful API serverless function on Vercel |
| Database | Neon PostgreSQL | Managed PostgreSQL with async connection pooling (asyncpg) |
| Hosting | Vercel | Static assets + Python serverless functions |

## API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/health` | Health check |
| GET | `/api/kits/{kit_id}` | Get all items for a kit (includes `updated_at`) |
| POST | `/api/kits/{kit_id}` | Add an item to a kit |
| PUT | `/api/kits/{kit_id}/{item_id}` | Update item quantity and/or expiry date |
| DELETE | `/api/kits/{kit_id}/{item_id}` | Remove an item from a kit |
| GET | `/api/all_items` | Get all items across all kits |
| GET | `/api/firstaiditems` | Get master first-aid items list |
| POST | `/api/firstaiditems` | Add a new first-aid item |
| PUT | `/api/firstaiditems/{item_name}` | Update a first-aid item |
| DELETE | `/api/firstaiditems/{item_name}` | Delete a first-aid item |

## Database Schema

Three tables in Neon PostgreSQL:

- **`kits`** — Kit box metadata (kit_id, last_edited timestamp)
- **`kit_items`** — Individual items within each kit (name, quantity, expiry_date, created_at, updated_at, linked to kit_id)
- **`first_aid_items`** — Master list of all available first-aid items with categories and expiring flag

See `schema.sql` for full DDL with indexes and comments.

## Local Development

### Prerequisites

- Python 3.10+
- Neon PostgreSQL connection string

### Setup

```powershell
# Clone the repository
git clone https://github.com/psphang/first_aid_tracker.git
cd first_aid_tracker

# Create virtual environment
python -m venv venv
.\venv\Scripts\Activate.ps1

# Install dependencies
pip install -r requirements.txt

# Set environment variable (or create .env file)
$env:DATABASE_URL = "postgresql://<user>:<password>@<host>/<db>?sslmode=require"

# Run the server
python api/main.py
```

Or use uvicorn directly:

```powershell
uvicorn api.main:app --reload --host 127.0.0.1 --port 8000
```

Open [http://localhost:8000](http://localhost:8000) in your browser.

### Database Migration (JSON to SQL)

If migrating from the old JSON-based version:

```powershell
python migrate_to_sql.py
```

This backs up the JSON files and inserts all data into the Neon PostgreSQL database.

## Deployment

The project is configured for Vercel auto-deployment from the `master` branch.

### Vercel Configuration

`vercel.json` routes all traffic through `api/main.py` (FastAPI), which serves both the API endpoints and the static frontend files from the `static/` directory.

### Environment Variables

Set in Vercel Dashboard → Settings → Environment Variables:

| Variable | Description |
|----------|-------------|
| `DATABASE_URL` | Neon PostgreSQL connection string (e.g., `postgresql://user:pass@host/db?sslmode=require`) |

### Deploy

```powershell
git add .
git commit -m "your changes"
git push origin master
```

Vercel automatically builds and deploys on push.

## Project Structure

```
first_aid_tracker/
├── api/
│   ├── main.py          # FastAPI application (API routes + static file serving)
│   └── db.py            # Database connection pool and query functions
├── static/
│   ├── index.html       # Main SPA page (with modals for edit/delete/recent)
│   ├── edit_items.html  # First-aid items editor page
│   ├── styles.css       # Global styles (modals, menus, status indicators)
│   ├── app.js           # Main application JavaScript (drag, changeLog, localStorage)
│   └── edit_items.js    # Items editor JavaScript
├── public/              # Mirror of static/ (fallback for Vercel builds)
├── schema.sql           # PostgreSQL database schema
├── migrate_to_sql.py    # JSON → SQL migration script
├── requirements.txt     # Python dependencies
├── vercel.json          # Vercel deployment configuration
└── README.md
```

## Key Dependencies

| Package | Version | Purpose |
|---------|---------|---------|
| fastapi | 0.104.1 | Web framework |
| uvicorn | 0.24.0 | ASGI server |
| asyncpg | 0.29.0 | Async PostgreSQL driver |
| pydantic | 2.5.0 | Data validation |
| python-dotenv | 1.0.0 | Environment variable management |

## Free Tier Limits

### Neon PostgreSQL (Free)
- 100 compute hours/month
- 0.5 GB storage
- 5 GB egress
- Scales to zero after 5 min inactivity

### Vercel Hobby (Free)
- 4 hours active CPU/month
- 1M function invocations/month
- 100 GB data transfer/month
- Unlimited deployments

Your project usage is well within both free tiers.

## License

MIT
