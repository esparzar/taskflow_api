# TaskFlow API ⚡

A production-ready **Task & Project Management REST API** built with Python/Flask, deployed on **AWS EC2** with **S3 file storage**, containerized with **Docker**, and automated via **GitHub Actions CI/CD**.

**Live Demo:** `https://your-domain.com/docs`

---

## Features

- **JWT Authentication** — Register, login, refresh tokens, profile management
- **Projects** — Create, manage teams, track status, member permissions
- **Tasks** — Full CRUD, priorities, deadlines, status workflow, comments, archiving
- **File Uploads** → **AWS S3** — Task attachments, profile avatars (boto3)
- **Swagger UI** — Interactive API docs at `/docs` (auto-generated)
- **Docker** — Containerized with docker-compose for dev/prod parity
- **GitHub Actions CI/CD** — Test → lint → build Docker image → push to Docker Hub → deploy to EC2
- **AWS EC2** — Ubuntu + Nginx reverse proxy + Gunicorn + Let's Encrypt SSL
- **AWS RDS** — Managed PostgreSQL in production
- **Pytest** — Full test suite with coverage reports

---

## Tech Stack

| Layer | Technology |
|---|---|
| Language | Python 3.11 |
| Framework | Flask 3.0 + Flask-RESTX |
| Database | PostgreSQL + SQLAlchemy + Flask-Migrate |
| Auth | JWT (Flask-JWT-Extended) |
| File Storage | AWS S3 (boto3) |
| Docs | Swagger / OpenAPI (auto-generated) |
| Container | Docker + docker-compose |
| CI/CD | GitHub Actions |
| Deploy | AWS EC2 (Ubuntu 22) + Nginx |
| DB (prod) | AWS RDS PostgreSQL |

---

## Quick Start (Docker)

```bash
git clone https://github.com/esparzar/taskflow_api.git
cd taskflow_api
cp .env.example .env        # Fill in your values
docker-compose up --build   # Starts Flask + PostgreSQL
docker exec -it <container> flask db upgrade
docker exec -it <container> flask seed
```

API: `http://localhost:5000` | Docs: `http://localhost:5000/docs`

## Quick Start (Local)

```bash
python -m venv venv && source venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
flask db init && flask db migrate -m "init" && flask db upgrade
flask seed
python run.py
```

---

## API Endpoints

### Auth `/api/auth`
| Method | Endpoint | Auth |
|---|---|---|
| POST | `/register` | ❌ |
| POST | `/login` | ❌ |
| POST | `/refresh` | 🔄 Refresh |
| GET/PUT | `/me` | ✅ |

### Projects `/api/projects`
| Method | Endpoint | Description |
|---|---|---|
| GET | `/` | List my projects |
| POST | `/` | Create project |
| GET/PUT/DELETE | `/<id>` | Project detail |
| POST/DELETE | `/<id>/members` | Manage team |
| GET | `/<id>/stats` | Project analytics |

### Tasks `/api/tasks`
| Method | Endpoint | Description |
|---|---|---|
| GET | `/project/<id>` | List tasks (filtered) |
| POST | `/project/<id>` | Create task |
| GET/PUT/DELETE | `/<id>` | Task detail |
| POST | `/<id>/archive` | Archive task |
| GET/POST | `/<id>/comments` | Task comments |

### Uploads `/api/uploads`
| Method | Endpoint | Description |
|---|---|---|
| POST | `/task/<id>` | Upload file → S3 |
| GET | `/attachment/<id>` | Get presigned download URL |
| DELETE | `/attachment/<id>` | Delete from S3 |
| POST | `/avatar` | Upload profile photo → S3 |

---

## AWS Deployment

### 1. Set up S3 + IAM
```bash
chmod +x scripts/aws_s3_setup.sh
./scripts/aws_s3_setup.sh
```
Copy the keys it outputs into GitHub Secrets.

### 2. Launch EC2 instance
- Ubuntu 22.04 LTS, t2.micro (free tier)
- Open ports: 22 (SSH), 80 (HTTP), 443 (HTTPS)
- Create and download a `.pem` key pair

### 3. Set up EC2 server
```bash
ssh -i your-key.pem ubuntu@your-ec2-ip
git clone https://github.com/esparzar/taskflow_api.git
chmod +x taskflow_api/scripts/ec2_setup.sh
sudo ./taskflow_api/scripts/ec2_setup.sh
```

### 4. Configure GitHub Secrets
Go to repo → Settings → Secrets and add:

| Secret | Value |
|---|---|
| `DOCKERHUB_USERNAME` | Your Docker Hub username |
| `DOCKERHUB_TOKEN` | Docker Hub access token |
| `EC2_HOST` | Your EC2 public IP |
| `EC2_SSH_KEY` | Contents of your `.pem` file |
| `DATABASE_URL` | Your RDS PostgreSQL URL |
| `SECRET_KEY` | A random 32+ char string |
| `JWT_SECRET_KEY` | A random 32+ char string |
| `AWS_ACCESS_KEY_ID` | From aws_s3_setup.sh output |
| `AWS_SECRET_ACCESS_KEY` | From aws_s3_setup.sh output |
| `AWS_S3_BUCKET` | `taskflow-api-files` |
| `AWS_S3_REGION` | `us-east-1` |

### 5. Deploy
```bash
git push origin main
```
GitHub Actions runs automatically: test → lint → build Docker image → push to Docker Hub → SSH into EC2 and deploy.

---

## Running Tests

```bash
pytest tests/ -v --cov=app --cov-report=term-missing
```

---

## Project Structure

```
taskflow_api/
├── app/
│   ├── models/          # SQLAlchemy models
│   │   ├── user.py      # User, project_members
│   │   ├── project.py   # Project
│   │   └── task.py      # Task, Attachment, Comment
│   ├── routes/          # Flask-RESTX namespaces
│   │   ├── auth.py
│   │   ├── projects.py
│   │   ├── tasks.py
│   │   ├── uploads.py   # S3 file upload routes
│   │   └── users.py
│   ├── services/
│   │   └── s3_service.py  # AWS S3 boto3 wrapper
│   └── utils/
│       └── helpers.py
├── tests/
│   ├── conftest.py
│   ├── test_auth.py
│   ├── test_projects.py
│   └── test_tasks.py
├── .github/workflows/
│   └── ci.yml           # Full CI/CD pipeline
├── nginx/
│   └── taskflow.conf    # Nginx reverse proxy config
├── scripts/
│   ├── ec2_setup.sh     # One-command EC2 server setup
│   └── aws_s3_setup.sh  # S3 bucket + IAM setup
├── config.py
├── run.py
├── Dockerfile
├── docker-compose.yml
├── requirements.txt
└── README.md
```

---

## Author

**Emmanuel Amponsah** — Python/Flask Developer  
GitHub: [@esparzar](https://github.com/esparzar)

---

## License

MIT License
