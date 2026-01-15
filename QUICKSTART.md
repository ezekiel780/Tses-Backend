# OTP Authentication Service - Quick Reference

## 🚀 Get Started in 3 Steps

```bash
# 1. Copy environment template
cp .env.example .env

# 2. Generate SECRET_KEY
python -c "import secrets; print(secrets.token_urlsafe(50))"
# Paste into .env

# 3. Start all services
docker-compose up --build
```

## 📍 Service URLs

| Service | URL |
|---------|-----|
| API | http://localhost:8000 |
| Swagger UI | http://localhost:8000/api/docs/ |
| ReDoc | http://localhost:8000/api/redoc/ |
| Django Admin | http://localhost:8000/admin/ |
| PostgreSQL | localhost:5432 |
| Redis | localhost:6379 |

## 📡 API Endpoints

### POST /api/v1/auth/otp/request/
Request a new OTP

```bash
curl -X POST http://localhost:8000/api/v1/auth/otp/request/ \
  -H "Content-Type: application/json" \
  -d '{"email":"user@example.com"}'
```

**Response** (202 Accepted):
- OTP sent to email
- TTL: 300 seconds (5 minutes)
- Rate limits: 3/10min per email, 10/1hr per IP

### POST /api/v1/auth/otp/verify/
Verify OTP and get JWT tokens

```bash
curl -X POST http://localhost:8000/api/v1/auth/otp/verify/ \
  -H "Content-Type: application/json" \
  -d '{"email":"user@example.com","otp":"123456"}'
```

**Response** (201 Created):
- User created/updated
- JWT access token
- JWT refresh token
- Failed attempts: max 5/15min before lockout

### GET /api/v1/audit/logs/
Get audit logs (requires JWT)

```bash
curl -X GET "http://localhost:8000/api/v1/audit/logs/" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN"
```

**Query Parameters**:
- `email=user@example.com` - Filter by email
- `event=OTP_REQUESTED` - Filter by event
- `from=2025-01-13` - Date from
- `to=2025-01-14` - Date to
- `page=1` - Pagination

## 🧪 Demo Commands

### Test Happy Path
```bash
# 1. Request OTP
EMAIL="demo-$(date +%s)@example.com"
curl -X POST http://localhost:8000/api/v1/auth/otp/request/ \
  -H "Content-Type: application/json" \
  -d "{\"email\":\"$EMAIL\"}"

# 2. Get OTP from Redis
redis-cli get "otp:$EMAIL"

# 3. Verify OTP (replace 123456 with actual OTP)
curl -X POST http://localhost:8000/api/v1/auth/otp/verify/ \
  -H "Content-Type: application/json" \
  -d "{\"email\":\"$EMAIL\",\"otp\":\"123456\"}"

# 4. Copy access token from response
ACCESS_TOKEN="eyJhbGciOi..." # From response

# 5. View audit logs
curl -X GET "http://localhost:8000/api/v1/audit/logs/" \
  -H "Authorization: Bearer $ACCESS_TOKEN"
```

### Test Rate Limiting
```bash
# Make 4 rapid requests (3 succeed, 4th fails with 429)
EMAIL="rate-test@example.com"
for i in {1..4}; do
  echo "Request $i:"
  curl -X POST http://localhost:8000/api/v1/auth/otp/request/ \
    -H "Content-Type: application/json" \
    -d "{\"email\":\"$EMAIL\"}"
  sleep 1
done
```

### Test Lockout
```bash
# Make 6 failed attempts (5 tracked, 6th returns 423 Locked)
EMAIL="lockout-test@example.com"
for i in {1..6}; do
  echo "Attempt $i:"
  curl -X POST http://localhost:8000/api/v1/auth/otp/verify/ \
    -H "Content-Type: application/json" \
    -d "{\"email\":\"$EMAIL\",\"otp\":\"000000\"}"
  sleep 1
done
```

### Interactive Demo
```bash
python demo.py
```

## 📊 Status Codes

| Code | Meaning | When |
|------|---------|------|
| 200 | OK | Audit logs retrieved |
| 201 | Created | OTP verified, user created |
| 202 | Accepted | OTP request queued |
| 400 | Bad Request | Invalid input or wrong OTP |
| 401 | Unauthorized | Missing or invalid JWT |
| 403 | Forbidden | No permission |
| 429 | Too Many Requests | Rate limit exceeded |
| 423 | Locked | Account locked (5 failed attempts) |
| 500 | Server Error | Something went wrong |

## 🔐 Rate Limits

| Limit | Value | Window |
|-------|-------|--------|
| OTP requests per email | 3 | 10 minutes |
| OTP requests per IP | 10 | 1 hour |
| Failed verifications | 5 | 15 minutes |
| OTP expiry | 5 minutes | - |

## 🛠 Development Commands

### View Logs
```bash
# All services
docker-compose logs -f

# Specific service
docker-compose logs -f celery_worker

# Django web service
docker-compose logs -f web
```

### Database Operations
```bash
# Run migrations manually
docker-compose exec web python manage.py migrate

# Create superuser
docker-compose exec web python manage.py createsuperuser

# Django shell
docker-compose exec web python manage.py shell
```

### Redis Operations
```bash
# Connect to Redis
docker-compose exec redis redis-cli

# View all keys
KEYS *

# View OTP for email
GET "otp:user@example.com"

# View rate limit counter
GET "ratelimit:email:user@example.com"

# View failed attempts
GET "failed_otp:user@example.com"

# Clear all keys (warning: affects all apps)
FLUSHDB
```

### Database Access
```bash
# Connect to PostgreSQL
docker-compose exec db psql -U lipschitz_user -d lipschitz_db

# List tables
\dt

# View audit logs
SELECT * FROM audit_auditlog ORDER BY created_at DESC;

# Count logs by event
SELECT event, COUNT(*) FROM audit_auditlog GROUP BY event;
```

## 🔧 Configuration Files

### .env Variables
```
# Core
SECRET_KEY=xxx
DEBUG=1

# Database
DB_NAME=
DB_USER=
DB_PASSWORD=xxx
DB_HOST=db
DB_PORT=5432

# Redis & Celery
CELERY_BROKER_URL=redis://redis:6379/0
CELERY_RESULT_BACKEND=redis://redis:6379/0

# Security
CORS_ALLOWED_ORIGINS=http://localhost:3000

# Logging
LOG_LEVEL=INFO
```

## 📦 Docker Commands

```bash
# Build and start
docker-compose up --build

# Start in background
docker-compose up -d

# Stop services
docker-compose stop

# Stop and remove containers
docker-compose down

# Remove volumes too (WARNING: deletes data)
docker-compose down -v

# Rebuild specific service
docker-compose build web

# Execute command in container
docker-compose exec web python manage.py shell

# View resource usage
docker stats
```

## 🐛 Troubleshooting

### Services won't start
```bash
# Check logs
docker-compose logs

# Verify ports are free
lsof -i :8000  # API
lsof -i :5432  # PostgreSQL
lsof -i :6379  # Redis
```

### OTP not sending
```bash
# Check Celery worker is running
docker-compose logs celery_worker

# Verify Redis connection
docker-compose exec redis redis-cli ping

# Check EMAIL_BACKEND in settings.py
```

### Database issues
```bash
# Check connections
docker-compose exec db psql -U lipschitz_user -d lipschitz_db -c "SELECT 1"

# Clear migrations
docker-compose down -v
docker-compose up --build
```

### Rate limiting not working
```bash
# Check Redis
docker-compose exec redis redis-cli KEYS "ratelimit:*"

# Verify TTL
docker-compose exec redis redis-cli TTL "ratelimit:email:test@example.com"
```

## 📚 Documentation

- **Full Guide**: [README_OTP_SERVICE.md](README_OTP_SERVICE.md)
- **Implementation**: [IMPLEMENTATION.md](IMPLEMENTATION.md)
- **API Docs**: http://localhost:8000/api/docs/
- **Source Code**: See `api/` directory

## 🔗 Useful Links

- [Django REST Framework](https://www.django-rest-framework.org/)
- [drf-spectacular](https://drf-spectacular.readthedocs.io/)
- [Celery](https://docs.celeryproject.org/)
- [Redis](https://redis.io/docs/)
- [SimpleJWT](https://django-rest-framework-simplejwt.readthedocs.io/)
- [Docker Compose](https://docs.docker.com/compose/)

## 📞 Support

For issues:
1. Check logs: `docker-compose logs -f`
2. Read [README_OTP_SERVICE.md](README_OTP_SERVICE.md)
3. Check [IMPLEMENTATION.md](IMPLEMENTATION.md)
4. Review [Troubleshooting section](README_OTP_SERVICE.md#troubleshooting)

---

**Last Updated**: January 13, 2026
**Version**: 1.0.0
**Status**: Production Ready ✅
