# Vercel Deployment Guide: JSON to SQL Migration

## Overview
This guide walks you through deploying the SQL migration to Vercel (frontend only) with PostgreSQL backend on external server.

## Architecture Change
- **Previous:** Backend on Render.com, Frontend on Vercel
- **New:** Frontend on Vercel, Backend API calls to PostgreSQL (Neon.tech)

---

## ⚠️ Important: Vercel Limitations

Vercel is primarily for **static sites and serverless functions**. For a full FastAPI backend with PostgreSQL, you have 3 options:

### Option 1: Vercel Frontend + Keep Render Backend (RECOMMENDED)
- Frontend stays on Vercel ✅
- Backend stays on Render ✅
- Simplest migration
- **Only need to update main.py on Render**

### Option 2: Vercel Frontend + Vercel Serverless Backend
- Frontend on Vercel
- Backend as Vercel Functions
- Complex: requires restructuring code into `/api` folder
- Higher cost for serverless

### Option 3: Vercel Frontend + Railway/Fly.io Backend
- Frontend on Vercel
- Backend on Railway or Fly.io
- Similar complexity to Render

**I recommend Option 1** - minimal changes needed.

---

## Step 1: Current Setup (Render Backend)

Since you already deployed backend on Render.com, the best approach is:

1. **Keep backend on Render.com** (running main.py)
2. **Update Render with SQL migration** (as previously planned)
3. **Frontend stays on Vercel** (no changes needed!)

### Frontend to Backend Communication
The frontend already calls your backend API:
```javascript
// static/app.js
fetch('/api/kits/{kit_id}')  // Calls Render backend
```

When deployed:
- Vercel frontend: `https://first-aid-tracker.vercel.app`
- Render backend: `https://first-aid-tracker.onrender.com`

---

## Step 2: Deploy Backend to Render (SQL Migration)

### 2.1 Merge SQL Migration to Master
```bash
git checkout master
git merge sql-migration
git push origin master
```

### 2.2 Set Environment Variable on Render
Go to **Render Dashboard** → your service → **Settings** → **Environment**

Add:
```
DATABASE_URL = postgresql://neondb_owner:npg_p4lbiRzPfCL9@ep-proud-bird-aqn2uuie-pooler.c-8.us-east-1.aws.neon.tech/neondb?sslmode=require&channel_binding=require
```

### 2.3 Render Auto-Deploys
- Render detects push to master
- Installs `asyncpg` from requirements.txt
- Restarts with SQL support

### 2.4 Run Migration on Render
SSH into Render shell:
```bash
python migrate_to_sql.py
```

---

## Step 3: Update Vercel Frontend (CORS Configuration)

### 3.1 Add CORS Headers (if needed)
Update `main.py` on Render to allow Vercel frontend:

```python
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI()

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "https://first-aid-tracker.vercel.app",  # Vercel frontend
        "http://localhost:3000",                   # Local development
        "http://localhost:8001"                    # Local backend
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

### 3.2 Update Backend URL (if using custom domain)
If Vercel frontend needs to call backend:

**static/app.js** (no changes needed if using relative URLs)
```javascript
// Already configured to work with current deployment
fetch('/api/kits/{kit_id}')
```

### 3.3 Push Updated main.py to Render
```bash
git add main.py
git commit -m "Add CORS headers for Vercel frontend"
git push origin master
```

---

## Step 4: Vercel Deployment (Frontend Only)

### 4.1 Ensure Vercel is Connected
1. Go to https://vercel.com/dashboard
2. Select your project: `first-aid-tracker`
3. Verify it's connected to GitHub

### 4.2 Trigger Vercel Deployment
```bash
# Push any changes to master
git push origin master

# Or manually trigger in Vercel dashboard:
# - Go to Deployments
# - Click "Redeploy" on latest build
```

### 4.3 Vercel Auto-Deploys
- Detects push to GitHub master
- Builds static files (HTML/JS/CSS)
- Deploys to Vercel edge network

---

## Step 5: Verify Both Deployments

### 5.1 Test Frontend
Visit: https://first-aid-tracker.vercel.app
- ✅ Page loads
- ✅ Enter kit ID
- ✅ Items display (loading from Render backend)

### 5.2 Test Backend
Visit: https://first-aid-tracker.onrender.com
- ✅ API endpoint works
- ✅ Database connected
- ✅ Migration completed

### 5.3 Test Cross-Origin Requests
Open browser console (F12) on Vercel frontend:
```javascript
// Test API call from Vercel to Render
fetch('https://first-aid-tracker.onrender.com/api/firstaiditems')
  .then(r => r.json())
  .then(d => console.log(d))
```

Should return items without CORS errors.

---

## Option 2: Full Vercel Deployment (Advanced)

If you absolutely want everything on Vercel, you need to restructure:

### Folder Structure Needed
```
first-aid-tracker/
├── static/              # Frontend files
│   ├── index.html
│   ├── app.js
│   └── styles.css
├── api/                 # NEW: Vercel serverless functions
│   ├── kits.py
│   ├── items.py
│   └── [...routes].py
├── db.py                # Shared database module
├── requirements.txt
└── vercel.json          # Vercel config
```

### vercel.json Configuration
```json
{
  "buildCommand": "pip install -r requirements.txt",
  "functions": {
    "api/**/*.py": {
      "runtime": "python3.9"
    }
  },
  "rewrites": [
    {
      "source": "/api/(.*)",
      "destination": "/api/$1.py"
    },
    {
      "source": "/(.*)",
      "destination": "/static/$1"
    }
  ]
}
```

### Disadvantages
- ❌ More complex code restructuring
- ❌ Cold start delays on serverless
- ❌ Higher costs
- ❌ Not ideal for real-time apps

**Not recommended** - stick with Render backend.

---

## Recommended Deployment Architecture

```
┌─────────────────────────┐
│   Vercel (Frontend)     │
│ vercel.app/             │
│ - HTML/JS/CSS           │
│ - Client-side routing   │
└────────────┬────────────┘
             │ API calls
             ▼
┌─────────────────────────┐
│  Render (Backend)       │
│ onrender.com/api/       │
│ - FastAPI + Python      │
│ - Main.py               │
└────────────┬────────────┘
             │ Database
             ▼
┌─────────────────────────┐
│   Neon PostgreSQL       │
│   Database              │
│ - Kits table            │
│ - Kit items table       │
│ - First aid items table │
└─────────────────────────┘
```

---

## Deployment Checklist (Vercel + Render + PostgreSQL)

### Backend (Render) - SQL Migration
- [ ] Merge `sql-migration` to `master`
- [ ] Set `DATABASE_URL` in Render environment
- [ ] Verify Render deployment is "Live"
- [ ] SSH into Render and run `python migrate_to_sql.py`
- [ ] Verify migration success message
- [ ] Test backend API: https://first-aid-tracker.onrender.com/api/firstaiditems

### Backend (Render) - CORS Configuration
- [ ] Add CORS middleware to `main.py`
- [ ] Allow Vercel frontend origin
- [ ] Push changes to GitHub master
- [ ] Verify Render redeploys

### Frontend (Vercel)
- [ ] Vercel is connected to GitHub
- [ ] Verify latest deploy is "Live"
- [ ] Test frontend: https://first-aid-tracker.vercel.app
- [ ] Test API calls from frontend (F12 console)
- [ ] Verify no CORS errors

### Production Monitoring
- [ ] Monitor Render logs for errors
- [ ] Monitor Vercel build logs
- [ ] Test all features:
  - [ ] View kits
  - [ ] View items
  - [ ] Add item
  - [ ] Update quantity
  - [ ] Remove item
  - [ ] Edit first aid items

---

## Troubleshooting

### Issue: "CORS error" on Vercel frontend
**Solution:**
- Add Vercel domain to CORS allowed origins in `main.py`
- Redeploy Render backend

### Issue: "Connection refused" from Vercel
**Solution:**
- Check `DATABASE_URL` is set on Render
- Verify Neon database is active
- Check Render backend is running

### Issue: Vercel frontend shows old data
**Solution:**
- Hard refresh (Ctrl+Shift+R)
- Clear browser cache
- Check if Render backend is serving new data

### Issue: Render backend is slow
**Solution:**
- Connection pool initializing (first request slower)
- Check database performance on Neon dashboard
- Monitor Render logs for slow queries

---

## Performance Optimization

### Frontend (Vercel)
- Static files cached at edge
- No server computation needed
- Fast global CDN delivery

### Backend (Render)
- Async database queries
- Connection pooling (2-10 connections)
- Indexed database queries

### Database (Neon)
- PostgreSQL optimized for JSON
- Auto-scaling available

---

## Cost Breakdown

| Service | Tier | Monthly Cost |
|---------|------|--------------|
| Vercel | Pro/Free | $0-20 |
| Render | Standard | $7-15 |
| Neon | Pro | $5-20 |
| **Total** | | **$12-55** |

---

## Summary

### Recommended Path: Render Backend + Vercel Frontend
1. ✅ Keep backend on Render
2. ✅ Update Render with SQL migration
3. ✅ Add CORS headers to backend
4. ✅ Frontend stays on Vercel (no changes)
5. ✅ PostgreSQL on Neon (no changes)

**Time to deploy: ~20 minutes**

### Files to Update
- `main.py` - Add CORS middleware
- `requirements.txt` - Already has asyncpg
- `db.py` - No changes needed
- Frontend - No changes needed

---

## Next Steps

Would you like me to:
1. ✅ Create the updated `main.py` with CORS headers?
2. ✅ Create a `vercel.json` config (if you change your mind)?
3. ✅ Create monitoring/alerting setup?
4. ✅ Provide API documentation for frontend devs?

**Or proceed with deployment?**
