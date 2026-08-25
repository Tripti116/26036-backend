# SIH 26036 - Online Verification System for Weighing & Measuring Instruments

FastAPI backend for the Smart India Hackathon 2026 problem statement SIH26036.
Digitizes the verification process for weighing and measuring instruments with role-based access, certificate generation, QR-based public verification, and admin dashboard.

## Architecture

```
26036-backend/
├── main.py                  # FastAPI app, CORS, lifespan, health check
├── config.py                # Centralized environment configuration
├── database.py              # SQLAlchemy engine, session, Base
├── seed.py                  # Demo accounts and sample instrument seeding
├── models/
│   ├── user.py              # User model (ADMIN/INSPECTOR/OWNER)
│   ├── instrument.py        # Instrument model with status tracking
│   ├── verification.py      # Verification model (result, deviation)
│   └── certificate.py       # Certificate model with QR token
├── schemas/
│   ├── user.py              # Pydantic schemas for user endpoints
│   ├── instrument.py        # Pydantic schemas for instrument endpoints
│   ├── verification.py      # Pydantic schemas for verification endpoints
│   └── certificate.py       # Pydantic schemas for certificate endpoints
├── routes/
│   ├── auth.py              # Register, login, /me, role dependencies
│   ├── instruments.py       # CRUD for instruments with role-based access
│   ├── verification.py      # Verification workflow (request/assign/complete)
│   ├── certificates.py      # Certificate generation, listing, download
│   ├── dashboard.py         # Admin dashboard summary statistics
│   └── public.py            # Public certificate verification (no auth)
├── services/
│   ├── qr_service.py        # QR code generation for certificates
│   ├── certificate_service.py # PDF generation, certificate number logic
│   └── risk_service.py      # Modular prototype risk scoring
├── tests/
│   ├── conftest.py          # Test client, fixtures, test DB setup
│   ├── test_auth.py         # Auth tests (register, login, JWT, roles)
│   ├── test_instruments.py  # Instrument CRUD tests
│   ├── test_verification.py # Verification workflow tests
│   ├── test_certificates.py # Certificate generation, PDF, QR, public verify tests
│   ├── test_dashboard.py    # Dashboard authorization tests
│   └── test_risk.py         # Risk assessment tests
├── requirements.txt
├── pytest.ini
├── .env.example
└── .gitignore
```

## Tech Stack

- Python 3.11+
- FastAPI
- SQLAlchemy 2.0
- PostgreSQL (primary) / SQLite (local dev fallback)
- Pydantic v2
- JWT authentication (python-jose)
- Password hashing (passlib + bcrypt)
- QR code generation (qrcode + Pillow)
- PDF generation (ReportLab)
- pytest + httpx (testing)

## Setup

### 1. Clone and install

```bash
git clone https://github.com/Tripti116/26036-backend.git
cd 26036-backend
python -m venv venv
venv\Scripts\activate        # Windows
# source venv/bin/activate   # Linux/Mac
pip install -r requirements.txt
```

### 2. Environment variables

Copy `.env.example` to `.env` and configure:

```
DATABASE_URL=postgresql://user:password@localhost:5432/sih26036
SECRET_KEY=your-secret-key-change-in-production
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=60
CERTIFICATES_DIR=uploads/certificates
PUBLIC_BASE_URL=http://localhost:8000
CORS_ORIGINS=http://localhost:3000,http://localhost:5173
```

If `DATABASE_URL` is empty or not set, the app falls back to SQLite (`sih26036.db`).

### 3. Run the server

```bash
uvicorn main:app --reload
```

For deployment:
```bash
uvicorn main:app --host 0.0.0.0 --port $PORT
```

### 4. Access API docs

- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc
- Health check: http://localhost:8000/api/health

## Demo Accounts (Development Only)

| Role       | Email            | Password     |
|------------|------------------|--------------|
| ADMIN      | admin@sih.com    | admin123     |
| INSPECTOR  | inspector@sih.com| inspector123 |
| OWNER      | owner@sih.com    | owner123     |

These are fake development/demo accounts seeded automatically on startup. Do NOT use in production.

## API Endpoints

### Authentication
- `POST /api/auth/register` - Register new user
- `POST /api/auth/login` - Login (returns JWT)
- `GET /api/auth/me` - Get current user profile

### Instruments
- `POST /api/instruments/` - Register instrument (OWNER)
- `GET /api/instruments/` - List instruments (role-filtered)
- `GET /api/instruments/{id}` - Get instrument details
- `PUT /api/instruments/{id}` - Update instrument
- `DELETE /api/instruments/{id}` - Delete instrument (ADMIN/OWNER)
- `GET /api/instruments/{id}/risk` - Risk assessment for instrument (0-100, LOW/MEDIUM/HIGH)

### Verification
- `POST /api/verification/request` - Request verification (OWNER)
- `GET /api/verification/` - List verifications (role-filtered)
- `GET /api/verification/{id}` - Get verification details
- `PUT /api/verification/{id}/assign` - Assign inspector (ADMIN)
- `PUT /api/verification/{id}/complete` - Complete verification with measurements (INSPECTOR)
- `POST /api/verification/{id}/result` - Submit verification result (INSPECTOR, alias for complete)

### Certificates
- `POST /api/certificates/generate/{verification_id}` - Generate certificate (ADMIN/INSPECTOR)
- `GET /api/certificates/` - List certificates
- `GET /api/certificates/{id}` - Get certificate details
- `GET /api/certificates/{id}/download` - Download PDF

### Dashboard
- `GET /api/dashboard/summary` - Admin dashboard statistics

### Public
- `GET /api/public/verify/{certificate_number}` - Verify certificate (no auth required)

## Verification Workflow

```
OWNER registers instrument
  -> OWNER requests verification
    -> ADMIN assigns inspector
      -> INSPECTOR performs verification
        -> INSPECTOR submits expected/measured values
          -> Backend calculates deviation
          -> Backend compares with tolerance
          -> PASS or FAIL

IF PASS:
  -> Certificate generated (PDF + QR)
  -> Certificate publicly verifiable

IF FAIL:
  -> Instrument marked FAILED
  -> No certificate generated
```

## Deviation Calculation

```
deviation_percentage = abs(measured_value - expected_value) / abs(expected_value) * 100

IF deviation_percentage <= tolerance_limit: PASS
ELSE: FAIL

Expected value of 0 is rejected (division by zero).
```

Tolerance values are configurable per verification and are NOT official legal standards.

## Certificate Generation

- Unique certificate number format: `CERT-YYYY-NNNNNN`
- PDF generated via ReportLab with all verification details
- QR code links to public verification endpoint
- Validity: 1 year from issue date
- Stored in `uploads/certificates/`

## Risk Scoring (Prototype)

Endpoint: `GET /api/instruments/{id}/risk`

Modular prototype risk scoring based on:
- Previous verification failures
- Latest deviation percentage
- Instrument age
- Overdue verification status

Returns:
```json
{
  "instrument_id": "INS-001",
  "risk_score": 72,
  "risk_level": "HIGH",
  "risk_factors": ["Previous verification failure", "High measurement deviation", "Verification overdue"]
}
```

Risk levels: LOW (0-29), MEDIUM (30-59), HIGH (60-100). This is NOT an official government formula and can be replaced with an ML model later.

## Testing

```bash
python -m pytest tests/ -v
```

Test coverage includes:
- Registration, login, JWT authentication
- Role-based access control
- Instrument CRUD and duplicate prevention
- Cross-owner access prevention
- Verification request, assignment, completion
- Deviation calculation accuracy (PASS/FAIL)
- Certificate generation, duplicate prevention, PDF validation
- QR code file generation verification
- Public certificate verification
- Expired certificate detection
- Dashboard access control
- Expected value zero rejection
- Risk assessment scoring
- Unauthenticated and unauthorized access

## Running Tests

```bash
python -m pytest tests/ -v --tb=short
```

## Frontend Integration

- All endpoints return JSON
- JWT authentication via `Authorization: Bearer <token>` header
- Login returns `access_token` and `token_type`
- Consistent HTTP status codes (200, 400, 401, 403, 404, 409)
- CORS configurable via `CORS_ORIGINS` environment variable (defaults to `http://localhost:3000`)
- Swagger UI at `/docs` for API exploration

## Known Limitations

1. Demo accounts are development-only and use weak passwords
2. Certificate PDF storage is local filesystem (no cloud storage)
3. Risk scoring is a prototype, not an official government standard
4. Tolerance values are configurable, not legally certified
5. No email verification or password reset flow
6. No file upload for instrument images/documents
7. No complaint management system (mentioned in scope but deferred)
8. SQLite used in development (PostgreSQL recommended for production)
9. CORS configured via environment variable (default: localhost:3000)
10. No rate limiting on API endpoints
