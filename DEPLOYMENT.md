# CompanyMind AI - Deployment Guide

## 🚀 Quick Start (Local Docker)

```bash
# Build image
docker-compose build

# Start services
docker-compose up
```

Services running:
- Email Dashboard: http://localhost:5000
- API Gateway: http://localhost:5001
- Admin Panel: http://localhost:5002

## ☁️ Deploy to Cloud

### Option 1: Render (Recommended)

1. Push to GitHub (already done ✅)
2. Go to https://render.com
3. Connect GitHub repo
4. Create new "Web Service"
5. Runtime: Docker
6. Deploy!

### Option 2: Railway

1. Go to https://railway.app
2. Create new project from GitHub
3. Select repository
4. Deploy!

### Option 3: Heroku

```bash
heroku login
heroku create your-app-name
git push heroku main
```

## 🔐 Environment Variables

## 🧪 Health Check

```bash
curl https://your-app.render.com/health
```

## 📈 Monitoring

Watch logs in Render/Railway dashboard

## 🆘 Troubleshooting

**Databases not found?**
```bash
docker exec container_name python -c "from src.platform_db import init_platform_db; init_platform_db()"
```

**Port conflicts?**
Update docker-compose.yml ports

**Out of memory?**
Reduce gunicorn workers: `-w 2`
