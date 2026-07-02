# Blog API — Industry Grade FastAPI

## Tech Stack
- **FastAPI** — web framework
- **SQLAlchemy + PostgreSQL** — database
- **JWT** — Access + Refresh tokens
- **Google & GitHub OAuth2** — social login
- **Cloudinary** — image storage
- **Passlib (bcrypt)** — password hashing
- **Pydantic v2** — validation & settings

## Project Structure
```
blog-api/
├── app/
│   ├── core/
│   │   ├── config.py       # All settings from .env
│   │   ├── database.py     # SQLAlchemy engine + session
│   │   └── security.py     # JWT + password utils
│   ├── models/
│   │   ├── user.py         # User model (local + OAuth)
│   │   └── blog.py         # Blog model
│   ├── schemas/
│   │   ├── user.py         # Pydantic request/response schemas
│   │   └── blog.py
│   ├── routers/
│   │   ├── auth.py         # /auth/* endpoints
│   │   ├── blog.py         # /blogs/* endpoints
│   │   └── user.py         # /users/* endpoints
│   ├── services/
│   │   ├── cloudinary_service.py
│   │   └── oauth_service.py
│   └── main.py             # App entry point
├── .env.example
├── requirements.txt
└── README.md
```

## Setup

### 1. Install dependencies
```bash
pip install -r requirements.txt
```

### 2. Configure environment
```bash
cp .env.example .env
# Fill in all values in .env
```

### 3. Google OAuth Setup
1. Go to [Google Cloud Console](https://console.cloud.google.com)
2. Create a project → APIs & Services → Credentials
3. Create OAuth 2.0 Client ID (Web application)
4. Add `http://localhost:8000/auth/google/callback` to Authorized redirect URIs
5. Copy Client ID and Secret to `.env`

### 4. GitHub OAuth Setup
1. Go to GitHub → Settings → Developer settings → OAuth Apps
2. New OAuth App
3. Set Authorization callback URL to `http://localhost:8000/auth/github/callback`
4. Copy Client ID and Secret to `.env`

### 5. Cloudinary Setup
1. Sign up at [cloudinary.com](https://cloudinary.com)
2. Copy Cloud Name, API Key, API Secret from dashboard to `.env`

### 6. Run
```bash
uvicorn app.main:app --reload
```

Docs available at: `http://localhost:8000/docs`

## API Endpoints

### Auth
| Method | Endpoint | Auth | Description |
|--------|----------|------|-------------|
| POST | `/auth/register` | ❌ | Register with email/password |
| POST | `/auth/login` | ❌ | Login → get tokens |
| POST | `/auth/refresh` | ❌ | Get new access token |
| GET | `/auth/google` | ❌ | Start Google OAuth |
| GET | `/auth/google/callback` | ❌ | Google OAuth callback |
| GET | `/auth/github` | ❌ | Start GitHub OAuth |
| GET | `/auth/github/callback` | ❌ | GitHub OAuth callback |

### Blogs
| Method | Endpoint | Auth | Description |
|--------|----------|------|-------------|
| GET | `/blogs` | ❌ | List blogs (paginated, searchable) |
| GET | `/blogs/{id}` | ❌ | Get single blog |
| POST | `/blogs` | ✅ | Create blog (with optional image) |
| PUT | `/blogs/{id}` | ✅ | Update blog (owner only) |
| DELETE | `/blogs/{id}` | ✅ | Delete blog (owner only) |
| POST | `/blogs/upload-image` | ✅ | Upload image for rich editor |

### Users
| Method | Endpoint | Auth | Description |
|--------|----------|------|-------------|
| GET | `/users/me` | ✅ | Get own profile |
| PATCH | `/users/me/avatar` | ✅ | Update avatar |
| GET | `/users/{id}/blogs` | ❌ | Get a user's blogs |

## Production Notes
- Replace `Base.metadata.create_all` with **Alembic** migrations
- Store `SECRET_KEY` as a long random string (use `openssl rand -hex 32`)
- Use HTTPS in production — update all OAuth redirect URIs
- Add rate limiting with `slowapi`