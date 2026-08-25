# Deployment Guide: JSON to SQL Migration

## Overview
This guide walks you through deploying the SQL migration to Render.com production.

## Prerequisites
- Access to Render.com dashboard
- GitHub account with access to repository
- Neon.tech PostgreSQL connection string (already provided)
- Local git setup

---

## Step 1: Local Testing (Recommended)

### 1.1 Setup Local Environment
```bash
# Clone the repository
git clone https://github.com/psphang/first_aid_tracker.git
cd first_aid_tracker

# Checkout the sql-migration branch
git checkout sql-migration

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

### 1.2 Test Migration Locally
```bash
# Run the migration script
python migrate_to_sql.py
```

Expected output:
```
============================================================
First Aid Tracker: JSON to SQL Migration
============================================================

[*] Creating backups...
[✓] Backed up first_aid_kit.json to backups/first_aid_kit.json.20260605_143000.backup
[✓] Backed up firstIAiditem.json to backups/firstIAiditem.json.20260605_143000.backup

[*] Creating database schema...
[✓] Schema created successfully

[*] Migrating first aid items...
[✓] Migrated 15 first aid items

[*] Migrating kits and items...
[✓] Migrated 2 kits and 45 items

[*] Verifying migration...
[✓] Database contains:
    - 2 kits
    - 45 kit items
    - 15 first aid items
[✓] Migration verified successfully!

============================================================
```

### 1.3 Test the Application
```bash
# Start the FastAPI server
python main.py

# Test in browser: http://localhost:8001
```

Verify:
- ✅ Home page loads
- ✅ Can enter kit ID
- ✅ Items display correctly
- ✅ Add/remove items work
- ✅ Edit items page works

---

## Step 2: Prepare for Production Deployment

### 2.1 Merge to Master Branch
```bash
# Switch to master
git checkout master

# Merge sql-migration branch
git merge sql-migration

# Push to GitHub
git push origin master
```

**Result:** Render.com will automatically detect the change and start deployment.

### 2.2 Set Environment Variables on Render.com

**Option A: Via Render Dashboard**

1. Go to https://dashboard.render.com
2. Select your service: `first-aid-tracker`
3. Click **Settings** → **Environment**
4. Add new environment variable:
   ```
   Key: DATABASE_URL
   Value: postgresql://neondb_owner:npg_p4lbiRzPfCL9@ep-proud-bird-aqn2uuie-pooler.c-8.us-east-1.aws.neon.tech/neondb?sslmode=require&channel_binding=require
   ```
5. Click **Save Changes**

**Option B: Via .env File (Local)**

Create `.env` file in project root:
```env
DATABASE_URL=postgresql://neondb_owner:npg_p4lbiRzPfCL9@ep-proud-bird-aqn2uuie-pooler.c-8.us-east-1.aws.neon.tech/neondb?sslmode=require&channel_binding=require
```

Then commit and push:
```bash
git add .env
git commit -m "Add database URL"
git push origin master
```

⚠️ **Note:** Be careful with .env files. Better to set via Render dashboard.

---

## Step 3: Monitor Deployment on Render.com

### 3.1 Check Deployment Status
1. Go to https://dashboard.render.com
2. Select `first-aid-tracker` service
3. Look for **"Deploys"** section

### 3.2 Watch Build Logs
Click on the latest deploy to see logs:

```
[1] Building...
[2] Installing dependencies: pip install -r requirements.txt
    - fastapi==0.104.1
    - uvicorn==0.24.0
    - asyncpg==0.29.0
    - ... (other packages)
[3] Starting service: uvicorn main:app --host 0.0.0.0 --port $PORT
[4] Live at: https://first-aid-tracker.onrender.com
```

### 3.3 Verify Deployment Success
- ✅ Status shows "Live" (green)
- ✅ No error messages in logs
- ✅ Can access https://first-aid-tracker.onrender.com

---

## Step 4: Run Migration on Production (IMPORTANT)

⚠️ **Only run migration ONCE on production!**

### Option A: SSH into Render Service (Recommended)
1. Go to Render dashboard
2. Select your service
3. Click **"Shell"** in top right
4. Run migration:
   ```bash
   python migrate_to_sql.py
   ```
5. Verify success - you should see:
   ```
   [✓] Migration verified successfully!
   [✓] Database contains:
       - X kits
       - X kit items
       - X first aid items
   ```

### Option B: Create Migration Endpoint (Advanced)
Add temporary endpoint to `main.py`:
```python
@app.post("/admin/migrate")
async def run_migration():
    """Temporary endpoint to run migration on production"""
    # Run migration code here
    return {"message": "Migration completed"}
```

Then call: `curl -X POST https://first-aid-tracker.onrender.com/admin/migrate`

---

## Step 5: Post-Deployment Verification

### 5.1 Check Database Connection
- Open production app: https://first-aid-tracker.onrender.com
- Enter a kit ID
- Verify items load from database (not JSON)

### 5.2 Test Core Features
- [ ] View kits
- [ ] View kit items
- [ ] Add new item
- [ ] Update item quantity
- [ ] Remove item
- [ ] View all items across kits
- [ ] Edit first aid items

### 5.3 Monitor Logs
Watch Render logs for errors:
```bash
# In Render dashboard, check "Logs" section
# Look for any connection errors or crashes
```

---

## Step 6: Rollback Plan (If Issues Occur)

### 6.1 Immediate Rollback
If something goes wrong:

1. **Stop the service:**
   - Go to Render dashboard
   - Click **"Suspend"** to stop the service

2. **Revert code:**
   ```bash
   git revert HEAD
   git push origin master
   ```
   Render will auto-redeploy with previous code

3. **Restore from backup:**
   - Keep JSON backups in `backups/` folder
   - Original JSON files still exist on server

### 6.2 Database Rollback
If database has issues:
1. Contact Neon.tech support
2. Request database snapshot restore
3. Update DATABASE_URL if needed

---

## Step 7: Cleanup (After Successful Deployment)

### 7.1 Remove Old JSON Files (Optional)
After confirming everything works for 1-2 weeks:

```bash
# Keep backups, but remove old JSON files
rm first_aid_kit.json
rm firstIAiditem.json
git add -A
git commit -m "Remove JSON files after SQL migration"
git push origin master
```

### 7.2 Archive Backups
Store backups securely:
```bash
# Zip backups folder
zip -r backups_$(date +%Y%m%d).zip backups/

# Upload to cloud storage (optional)
# Keep for 30-90 days as safety measure
```

---

## Troubleshooting

### Issue: "Connection refused" error
**Solution:**
- Verify DATABASE_URL is set correctly in Render environment
- Check Neon.tech dashboard for active database
- Ensure IP whitelist allows Render service

### Issue: "Relation does not exist" error
**Solution:**
- Migration script didn't run
- SSH into Render and run: `python migrate_to_sql.py`
- Check schema.sql was executed

### Issue: Data appears empty after deployment
**Solution:**
- Migration succeeded but data didn't transfer
- Check `migrate_to_sql.py` output for errors
- Verify original JSON files existed
- Manually check database: `SELECT COUNT(*) FROM kits;`

### Issue: Deployment fails during pip install
**Solution:**
- asyncpg requires build tools
- Render.com automatically handles this
- Check if Python version is 3.8+
- Try building locally first: `pip install -r requirements.txt`

---

## Performance Tips

### Database Optimization
- Connection pool is set to 2-10 connections
- Queries use indexes for fast lookups
- Consider query caching for first_aid_items (rarely changes)

### Monitoring
```python
# Add monitoring to db.py if needed
import time

async def query_with_timing(query_name, query_func):
    start = time.time()
    result = await query_func()
    elapsed = time.time() - start
    print(f"[{query_name}] {elapsed:.2f}s")
    return result
```

---

## Summary Checklist

- [ ] Merged `sql-migration` to `master`
- [ ] Set DATABASE_URL in Render environment
- [ ] Deployment shows "Live" status
- [ ] Migration ran successfully on production
- [ ] Tested all core features
- [ ] Logs show no errors
- [ ] Users can access the app
- [ ] Data loads from database correctly

---

## Support

**Issues during deployment?**
1. Check Render logs: https://dashboard.render.com
2. Check Neon.tech console: https://console.neon.tech
3. Review MIGRATION_GUIDE.md for details
4. Check GitHub issues in your repository

**After successful deployment:**
- Monitor for 24-48 hours
- Keep backups for 30 days
- Document any issues for future reference
