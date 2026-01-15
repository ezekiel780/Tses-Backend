# TSES Authentication Service - Documentation Index

Welcome! This is the complete implementation of an email-based OTP authentication service with JWT tokens, rate limiting, and comprehensive audit logging.



## 🚀 Quick Start (Copy & Paste)

```bash
cp .env.template .env
python -c "import secrets; print(secrets.token_urlsafe(50))"

# 2. Start
docker-compose up --build

# 3. Test
python demo.py

# 4. Visit
# API: http://localhost:8000
# Docs: http://localhost:8000/api/docs/
```

## 📚 Documentation Files

### Main Documents

| Document | Purpose | Best For |
|----------|---------|----------|
| **DEPLOYMENT.md** | Executive summary & overview | Getting started, understanding scope |
| **QUICKSTART.md** | Quick reference with commands | Running commands, troubleshooting |
| **README_OTP_SERVICE.md** | Comprehensive guide | Learning the system, details |
| **IMPLEMENTATION.md** | Technical implementation details | Understanding architecture |
| **VERIFICATION.md** | Requirements verification | Checking completeness |

### How to Use These Files

**Start Here**:
1. Read this README (you are here!)
2. Open QUICKSTART.md in another window
3. Follow the 3-step setup

**Then Explore**:
- Run `docker-compose up --build`
- Run `python demo.py`
- Open http://localhost:8000/api/docs/

**For Questions**:
- Run command? → QUICKSTART.md
- How does it work? → README_OTP_SERVICE.md
- Why was it built that way? → IMPLEMENTATION.md
- Requirements? → VERIFICATION.md

## 🎯 What This Service Does

### Authentication Flow
1. User requests OTP → `POST /api/v1/auth/otp/request/`
2. OTP sent via email (async task)
3. User verifies OTP → `POST /api/v1/auth/otp/verify/`
4. JWT tokens issued on success
5. All events logged to audit table

### Safety Features
- Rate limiting (prevents brute force)
- Account lockout (after 5 failed attempts)
- One-time OTP (deleted after use)
- Concurrent-safe Redis operations
- Audit trail of all events

### API Endpoints
- `POST /api/v1/auth/otp/request/` - Request OTP (202)
- `POST /api/v1/auth/otp/verify/` - Verify OTP (201, 400, 423)
- `GET /api/v1/audit/logs/` - View audit logs (200)

### Services
- Django (API)
- PostgreSQL (Database)
- Redis (Cache & Rate Limiting)
- Celery (Async tasks)
- Gunicorn (Web server)

## 🔍 Key Features

✅ **Email-based OTP**: 6-digit codes with 5-minute TTL
✅ **Rate Limiting**: Concurrent-safe using Redis
✅ **JWT Tokens**: Using SimpleJWT for authentication
✅ **Async Tasks**: Celery for email & audit logging
✅ **Audit Logs**: Complete event tracking with filtering
✅ **Docker**: Production-ready multi-container setup
✅ **Swagger UI**: Full OpenAPI documentation
✅ **Modular Code**: Separate apps for accounts and audit

## 📊 Architecture

```
User
  ↓
POST /api/v1/auth/otp/request/
  ↓ [RateLimiter checks Redis]
  ↓ [OTPService generates & stores OTP]
  ↓ [send_otp_email.delay() queued]
  ↓ [write_audit_log.delay() queued]
  ↓ [Celery processes tasks async]
Returns 202 Accepted

User receives OTP from email
  ↓
POST /api/v1/auth/otp/verify/
  ↓ [RateLimiter checks attempt count]
  ↓ [OTPService verifies & deletes]
  ↓ [User created/updated]
  ↓ [JWT tokens generated]
  ↓ [write_audit_log.delay() queued]
Returns 201 Created + JWT

User uses JWT token
  ↓
GET /api/v1/audit/logs/
  ↓ [JWT validation]
  ↓ [Query with filters]
  ↓ [Paginated results]
Returns 200 OK
```

## 🧪 Testing

### Interactive Demo
```bash
python demo.py
```

Tests all endpoints and features automatically.

### Manual Testing
See QUICKSTART.md for curl commands.

### Celery Logs
```bash
docker-compose logs celery_worker
```

## 🐳 Docker Services

| Service | Image | Port | Purpose |
|---------|-------|------|---------|
| web | Django:latest | 8000 | API server |
| db | PostgreSQL:15 | 5432 | Database |
| redis | Redis:7 | 6379 | Cache & broker |
| celery_worker | Django:latest | - | Async tasks |

All in one command: `docker-compose up --build`

## 📁 Project Structure

```
django-deployment/
├── api/
│   ├── accounts/          ← OTP authentication
│   ├── audit/             ← Audit logging (NEW)
│   ├── helper/            ← Services (OTP, rate limiting)
│   ├── api/               ← Django settings
│   └── manage.py
├── docker-compose.yml     ← Docker setup
├── Dockerfile             ← Image definition
├── requirements.txt       ← Python dependencies
├── .env.template          ← Environment template
├── demo.py                ← Interactive demo
├── start.sh / start.bat   ← Startup scripts
├── QUICKSTART.md          ← Quick reference
```

## 🔧 Configuration

### Environment Variables (.env)
```
SECRET_KEY=your-secret-here
DEBUG=1
DB_NAME=
DB_USER=
DB_PASSWORD=your-password
CELERY_BROKER_URL=redis://redis:6379/0
```

See `.env.template` for all variables.

## 🚨 Troubleshooting

**Services won't start?**
```bash
docker-compose logs
```

**OTP not sending?**
```bash
docker-compose logs celery_worker
```

**Need to reset data?**
```bash
docker-compose down -v
docker-compose up --build
```

See QUICKSTART.md for more troubleshooting.

## 📖 Reading Guide

### If you have 5 minutes
1. Read this file (you're doing it!)
2. Open QUICKSTART.md
3. Run `docker-compose up --build`

### If you have 15 minutes
1. Run the quick start (5 min)
2. Run `python demo.py`
3. Check docker-compose logs

### If you have 1 hour
1. Complete quick start
2. Read README_OTP_SERVICE.md
3. Test endpoints manually
4. Modify configuration

### If you have more time
1. Do all above
2. Read IMPLEMENTATION.md
3. Explore source code
4. Run performance tests

## 🎓 Learning Path

1. **Understand the Flow**: Read QUICKSTART.md "Demo Commands"
2. **Run the Demo**: Execute `python demo.py`
3. **Try the API**: Use curl commands from QUICKSTART.md
4. **Read the Code**: Check `api/accounts/views.py`
5. **Understand Services**: Check `api/helper/otp_service.py`
6. **Deploy**: Follow DEPLOYMENT.md

## ✅ Requirement Coverage

| Requirement | Status | Location |
|-------------|--------|----------|
| OTP Request | ✅ | `api/accounts/views.py::OTPRequestView` |
| OTP Verify | ✅ | `api/accounts/views.py::OTPVerifyView` |
| Rate Limiting | ✅ | `api/helper/otp_service.py::RateLimiter` |
| Audit Logging | ✅ | `api/audit/` |
| JWT Tokens | ✅ | SimpleJWT in settings |
| Celery Tasks | ✅ | `api/accounts/tasks.py` |
| Redis | ✅ | `docker-compose.yml` |
| Swagger UI | ✅ | drf-spectacular configured |
| Docker | ✅ | `docker-compose.yml` |

All 50+ requirements verified ✅

## 🎯 Next Steps

1. [ ] Read QUICKSTART.md
2. [ ] Run `docker-compose up --build`
3. [ ] Run `python demo.py`
4. [ ] Visit http://localhost:8000/api/docs/
5. [ ] Read README_OTP_SERVICE.md for details
6. [ ] Customize for your needs
7. [ ] Deploy to production

## 💡 Key Insights

### Rate Limiting
Uses Redis with atomic INCR + EXPIRE operations for thread-safety:
- Email: 3 requests per 10 minutes
- IP: 10 requests per 1 hour
- Failed attempts: 5 per 15 minutes

### OTP Security
- Generated as 6 random digits
- Stored in Redis with 5-minute TTL
- One-time use (deleted after verification)
- Verification fails safely (doesn't leak timing info)

### Async Processing
Celery handles:
- Email sending (doesn't block API)
- Audit logging (doesn't block verification)
- Retries with exponential backoff
- Can scale to multiple workers

### Database Design
AuditLog table:
- Indexes on (email, created_at) and (event, created_at)
- Supports efficient filtering and sorting
- JSON metadata field for extensibility

## 📞 Need Help?

1. **Quick commands?** → QUICKSTART.md
2. **How something works?** → README_OTP_SERVICE.md
3. **Why was it built this way?** → IMPLEMENTATION.md
4. **Meets all requirements?** → VERIFICATION.md
5. **Overview?** → DEPLOYMENT.md

## 🎉 You're Ready!

Everything is set up and ready to go. Just follow the 3-step setup above and you're running a production-ready OTP authentication service!


**Total Documentation**: ~1,450 lines, covers every aspect

---

**Version**: 1.0.0
**Status**: Complete and Ready ✅
**Last Updated**: January 13, 2026
**Demo**: Run `python demo.py`
**Deploy**: Run `docker-compose up --build`
