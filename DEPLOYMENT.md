# Deployment Guide - SKU Database Tracker

This guide will help you deploy your SKU Database Tracker to the cloud with a public URL.

## ☁️ Option 1: Deploy to Railway (Recommended - Easiest)

Railway provides a free tier and automatic deployments from GitHub. You'll get a URL like `your-app.railway.app`.

### Prerequisites
- GitHub account
- Railway account (sign up at https://railway.app - free)

### Step-by-Step Deployment

#### 1. Push Your Code to GitHub

If you haven't already:

```bash
# Initialize git (if not already done)
git init

# Add all files
git add .

# Commit
git commit -m "Initial commit - SKU Database Tracker"

# Create a new repository on GitHub, then:
git remote add origin https://github.com/YOUR_USERNAME/SKU-Database-Tracker.git
git branch -M main
git push -u origin main
```

**Or if this is already a GitHub repo, just make sure it's pushed:**
```bash
git push origin main  # or your branch name
```

#### 2. Deploy to Railway

1. **Go to Railway**: https://railway.app

2. **Sign in** with your GitHub account

3. **Create New Project**:
   - Click "New Project"
   - Select "Deploy from GitHub repo"
   - Choose your `SKU-Database-Tracker` repository
   - Railway will auto-detect it's a Python/FastAPI app

4. **Deployment starts automatically!**
   - Railway reads `railway.json` and `requirements.txt`
   - Installs dependencies
   - Starts the app with uvicorn

5. **Get Your Public URL**:
   - Once deployed, click "Settings" tab
   - Click "Generate Domain"
   - You'll get a URL like: `https://sku-database-tracker-production.up.railway.app`

6. **Access Your App**:
   - Click the generated URL
   - You'll see your dashboard at the root URL!
   - API docs at: `https://your-url.railway.app/docs`

#### 3. Set Environment Variables (Important!)

In Railway dashboard:

1. Go to **Variables** tab
2. Add these variables:

```
SECRET_KEY=generate-a-random-32-character-string-here
DEBUG=False
APP_NAME=SKU Database Tracker
```

To generate a secure SECRET_KEY:
```bash
python -c "import secrets; print(secrets.token_urlsafe(32))"
```

#### 4. Monitor Your Deployment

- **Logs**: Check the "Deployments" tab for real-time logs
- **Metrics**: View CPU/Memory usage in dashboard
- **Redeploy**: Push to GitHub and Railway auto-redeploys

### Railway Free Tier Limits

- ✅ 500 hours/month execution time (always on)
- ✅ 512 MB RAM
- ✅ 1 GB Disk
- ✅ Custom domain support
- ✅ Automatic HTTPS

Perfect for testing and small production use!

---

## ☁️ Option 2: Deploy to Render

Render is another excellent option with a generous free tier.

### Step-by-Step

1. **Push code to GitHub** (same as above)

2. **Go to Render**: https://render.com

3. **Sign in** with GitHub

4. **Create New Web Service**:
   - Click "New +"
   - Select "Web Service"
   - Connect your GitHub repo
   - Configure:
     - **Name**: sku-database-tracker
     - **Environment**: Python 3
     - **Build Command**: `pip install -r requirements.txt`
     - **Start Command**: `uvicorn app.main:app --host 0.0.0.0 --port $PORT`

5. **Set Environment Variables**:
   ```
   SECRET_KEY=your-random-secret-key
   DEBUG=False
   ```

6. **Deploy**: Click "Create Web Service"

7. **Access**: You'll get a URL like `https://sku-database-tracker.onrender.com`

### Render Free Tier

- ✅ 750 hours/month
- ✅ Automatic HTTPS
- ✅ Auto-deploy from GitHub
- ⚠️ Spins down after 15 min inactivity (first request takes ~30s)

---

## ☁️ Option 3: Deploy to Fly.io

Fly.io is great for global edge deployment.

### Quick Setup

```bash
# Install flyctl
curl -L https://fly.io/install.sh | sh

# Login
fly auth login

# Launch app (from project directory)
fly launch

# Deploy
fly deploy

# Get URL
fly open
```

Configuration is auto-detected from your `Procfile`.

---

## 🌐 Custom Domain Setup

Once deployed, you can add your own domain:

### Railway Custom Domain

1. In Railway project, go to **Settings**
2. Click **Domains**
3. Click **Custom Domain**
4. Enter your domain: `skutracker.yourdomain.com`
5. Add the CNAME record to your DNS:
   ```
   CNAME skutracker -> your-app.up.railway.app
   ```
6. Wait for DNS propagation (~5-60 minutes)
7. Railway automatically provisions SSL certificate

### Render Custom Domain

1. In Render dashboard, go to your service
2. Click **Settings** → **Custom Domains**
3. Add your domain
4. Update DNS with provided CNAME record
5. SSL automatically provisioned

---

## 📊 Database Considerations

### Development (SQLite - Current Setup)
- ✅ Simple, no setup required
- ✅ Good for < 1000 products
- ⚠️ Single file, limited concurrency
- ⚠️ Lost on redeploy (unless using persistent volumes)

### Production Recommendations

For serious production use, consider PostgreSQL:

#### Railway PostgreSQL

1. In Railway project, click "New"
2. Select "Database" → "PostgreSQL"
3. Railway provisions database
4. Copy `DATABASE_URL` from Variables
5. Update your app's environment variables:
   ```
   DATABASE_URL=postgresql://user:pass@host/dbname
   ```
6. Update `app/database/connection.py` to use PostgreSQL

#### Add PostgreSQL Support

```bash
# Add to requirements.txt
asyncpg>=0.29.0
psycopg2-binary>=2.9.9
```

Update connection string in `.env`:
```
DATABASE_URL=postgresql+asyncpg://user:pass@host:port/dbname
```

---

## 🔒 Security Checklist

Before going to production:

- [ ] **Change SECRET_KEY** to a random string
- [ ] **Set DEBUG=False** in production
- [ ] **Use HTTPS** (automatic with Railway/Render)
- [ ] **Set up database backups**
- [ ] **Add rate limiting** (if expecting high traffic)
- [ ] **Configure CORS** if accessing from different domains
- [ ] **Review exposed endpoints** in API docs
- [ ] **Add authentication** for sensitive operations (optional)

---

## 🚀 Deployment Checklist

### Before First Deploy

- [x] Code pushed to GitHub
- [x] `requirements.txt` is up to date
- [x] Railway/deployment config files created
- [ ] Environment variables configured
- [ ] SECRET_KEY generated and set

### After Deploy

- [ ] Test the public URL
- [ ] Check `/health` endpoint
- [ ] Try creating a test SKU via `/docs`
- [ ] Test validation endpoints
- [ ] Test export functionality
- [ ] Verify NSF compliance checking works

### Post-Launch

- [ ] Set up monitoring/alerts
- [ ] Configure automatic backups
- [ ] Document your deployment URL
- [ ] Share with team/stakeholders
- [ ] Monitor logs for errors

---

## 🐛 Troubleshooting

### "Application Error" or 500 Error

**Check logs:**
- Railway: Deployments tab → View Logs
- Render: Logs tab
- Fly.io: `fly logs`

**Common issues:**
- Missing environment variables
- Database connection failed
- Port binding issues (use `$PORT` variable)

### "Module not found" Error

Make sure all dependencies are in `requirements.txt`:
```bash
pip freeze > requirements.txt
git add requirements.txt
git commit -m "Update requirements"
git push
```

### Database Resets on Deploy

**Problem**: SQLite file lost on redeploy

**Solutions:**
1. Use Railway Volumes (persistent storage)
2. Switch to PostgreSQL database
3. Set up automated backups

### Slow First Request (Render)

Render free tier spins down after inactivity.

**Solutions:**
1. Upgrade to paid tier ($7/month)
2. Use Railway (doesn't spin down)
3. Set up a ping service to keep it warm

---

## 📈 Scaling & Performance

### Current Setup (Good for)
- ✅ Up to 100 concurrent users
- ✅ 1,000-10,000 SKUs
- ✅ Development and testing
- ✅ Small team collaboration

### To Scale Further

1. **Upgrade Server Resources**
   - Railway: Upgrade plan for more RAM/CPU
   - Render: Move to paid tier

2. **Use PostgreSQL**
   - Better concurrency
   - More reliable
   - Built-in backups

3. **Add Caching**
   - Redis for frequently accessed data
   - CDN for static assets

4. **Load Balancing**
   - Deploy multiple instances
   - Use Railway's scaling features

---

## 💰 Cost Estimates

### Free Tier (Railway)
- **Cost**: $0/month
- **Good for**: Development, testing, small team
- **Limits**: 500 hours/month, 512MB RAM

### Starter Tier (Railway)
- **Cost**: $5/month
- **Includes**: More hours, better performance
- **Good for**: Small production, 10-50 users

### Production (Railway + PostgreSQL)
- **Cost**: ~$12-20/month
- **Includes**:
  - Web service: $5-10/month
  - PostgreSQL: $7/month
  - Better uptime and performance
- **Good for**: Full production, 100+ users

---

## 🎉 You're Ready to Deploy!

### Quick Start Command

```bash
# 1. Push to GitHub
git add .
git commit -m "Ready for deployment"
git push origin main

# 2. Go to Railway
open https://railway.app

# 3. Deploy from GitHub
# Follow the steps above

# 4. Access your app
# Use the URL Railway provides
```

### Your Public URLs Will Be:

- **Dashboard**: `https://your-app.railway.app`
- **API Docs**: `https://your-app.railway.app/docs`
- **NSF Validation**: `https://your-app.railway.app/validation`
- **Health Check**: `https://your-app.railway.app/health`

---

## 📞 Support

If you encounter issues:

1. **Check Railway logs** for error messages
2. **Review this guide** for common issues
3. **Check Railway docs**: https://docs.railway.app
4. **GitHub Issues**: Open an issue in your repo

---

## 🔄 Continuous Deployment

Once set up, every push to GitHub automatically deploys:

```bash
# Make changes
git add .
git commit -m "Add new feature"
git push

# Railway automatically:
# 1. Detects the push
# 2. Builds new version
# 3. Runs tests (if configured)
# 4. Deploys to production
# 5. Your app is updated!
```

---

**Ready to go live?** Follow the Railway steps above and you'll have your app accessible from anywhere in about 5 minutes! 🚀
