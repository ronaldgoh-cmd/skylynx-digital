# Skylynx Digital Cloud Beginner Guide (FastAPI + Google Cloud)

This guide is written for absolute beginners. Every action is broken into tiny
steps you can follow in PyCharm and in Google Cloud. The goal is to move the
Skylynx Digital desktop ERP (PySide/Qt) to an online, multi-tenant setup with a
shared backend.

## What you will build
- A FastAPI backend running on **Google Cloud Run**.
- A managed **PostgreSQL** database on **Google Cloud SQL**.
- A simple multi-tenant data model: every record has a `company_id`, and a
  `company_modules` table turns modules on/off per company.
- Real-time-ish updates using WebSockets (with short-polling as a fallback).
- The PySide desktop client calls the API instead of talking directly to the
  database, and you will package it as a Windows `.exe` with PyInstaller.

## Architecture snapshot
- **Backend**: FastAPI + SQLAlchemy + Alembic migrations. Runs in a Docker
  container deployed to Cloud Run. Connects to Cloud SQL via the Cloud SQL
  Python connector.
- **Database**: PostgreSQL in Cloud SQL. Tables include `companies`, `modules`,
  `company_modules`, `users`, and feature tables (employees, salaries, leaves)
  that all include `company_id`.
- **Desktop client**: Existing PySide UI, but the data flows through HTTP API
  calls (and optional WebSocket updates) instead of local SQLite.
- **Realtime**: A `/ws` WebSocket endpoint broadcasts changes; if the socket is
  unavailable, the client can poll every 10–15 seconds.

## Prerequisites
1. A Google account.
2. PyCharm installed on your computer.
3. Python 3.11 or later installed (Windows: use the official installer and check
   “Add Python to PATH”).
4. Git installed.
5. (Optional) Google Chrome to access Google Cloud Console.

## Part 1 — Open the project in PyCharm and prepare Python
1. **Clone the code (if you have not yet):**
   ```bash
   git clone https://github.com/<your-org>/skylynx_digital.git
   cd skylynx_digital
   ```
2. **Open PyCharm** → **Open** → choose the `skylynx-digital` folder.
3. **Create a virtual environment** (inside PyCharm):
   - PyCharm menu **File → Settings → Project: skylynx-digital → Python
     Interpreter**.
   - Click the gear icon → **Add** → **Virtualenv Environment** → Location:
     `<project>/.venv` → Base interpreter: your Python 3.11 → **OK**.
4. **Activate the venv in the terminal** (inside PyCharm’s built-in terminal):
   ```bash
   source .venv/bin/activate   # Windows PowerShell: .venv\Scripts\Activate.ps1
   ```
5. **Install desktop requirements**:
   ```bash
   pip install -r requirements.txt
   ```
6. **Install backend requirements**:
   ```bash
   cd backend
   pip install -e .
   cd ..
   ```
   This installs FastAPI, SQLAlchemy, Alembic, and Cloud SQL connector support.
7. **Run the desktop app locally (offline mode for now)**:
   ```bash
   python -m skylynx_digital
   ```
   This confirms PySide launches correctly before you connect it to the backend.

## Part 2 — Design the multi-tenant data model
We will keep a single database and include a `company_id` on every business
record. This is easiest for beginners.

Core tables:
- `companies`: id, name, status.
- `modules`: id, code (e.g., `employee_management`), name.
- `company_modules`: company_id, module_id, enabled flag.
- `users`: id, company_id, email, hashed_password, role.
- Feature tables (employees, salaries, leaves): each includes `company_id` and
  foreign keys back to `companies`.

Rules:
- Every API request carries the user’s company context (from the auth token).
- Queries always filter by `company_id` so each tenant only sees its own data.
- To turn a module on/off, toggle the row in `company_modules`.

## Part 3 — Set up Google Cloud
Choose one path and stick to it: **Cloud Run + Cloud SQL** (simplest and fully
managed).

1. **Create a Google Cloud project**
   - Go to https://console.cloud.google.com/ → top bar **Select a project** →
     **New Project**.
   - Name: `skylynx-digital` (or anything you like) → **Create**.
2. **Install the Google Cloud CLI** on your computer (one-time):
   - Download from https://cloud.google.com/sdk/docs/install.
   - After install, run:
     ```bash
     gcloud init
     ```
   - Follow the prompts to log in and select your project.
3. **Enable required APIs** (one command):
   ```bash
   gcloud services enable compute.googleapis.com run.googleapis.com sqladmin.googleapis.com artifactregistry.googleapis.com secretmanager.googleapis.com
   ```
4. **Create an Artifact Registry for Docker images**:
   ```bash
   gcloud artifacts repositories create skylynx-backend --repository-format=docker --location=us-central1 --description="Skylynx Digital backend"
   ```
5. **Create a Cloud SQL PostgreSQL instance**:
   ```bash
   gcloud sql instances create skylynx-pg --database-version=POSTGRES_15 --tier=db-f1-micro --region=us-central1
   gcloud sql databases create skylynx_app --instance=skylynx-pg
   gcloud sql users create skylynx_user --instance=skylynx-pg --password="CHOOSE_A_STRONG_PASSWORD"
   ```
6. **Create a Secret Manager entry for the DB URL**:
   ```bash
   gcloud secrets create SKYLYNX_DATABASE_URL --replication-policy=automatic
   echo -n "postgresql+asyncpg://skylynx_user:CHOOSE_A_STRONG_PASSWORD@/skylynx_app?host=/cloudsql/$(gcloud sql instances describe skylynx-pg --format='value(connectionName)')" | gcloud secrets versions add SKYLYNX_DATABASE_URL --data-file=-
   ```
7. **Create a service account for Cloud Run**:
   ```bash
   gcloud iam service-accounts create skylynx-backend --display-name="Skylynx Digital backend"
   gcloud projects add-iam-policy-binding $(gcloud config get-value project) \
     --member="serviceAccount:skylynx-backend@$(gcloud config get-value project).iam.gserviceaccount.com" \
     --role="roles/cloudsql.client"
   gcloud secrets add-iam-policy-binding SKYLYNX_DATABASE_URL \
     --member="serviceAccount:skylynx-backend@$(gcloud config get-value project).iam.gserviceaccount.com" \
     --role="roles/secretmanager.secretAccessor"
   ```

## Part 4 — Prepare the backend locally
1. **Copy the example environment file** (from project root):
   ```bash
   cp backend/.env.example backend/.env
   ```
   Then open `backend/.env` in PyCharm and set:
   ```env
   DATABASE_URL=sqlite+aiosqlite:///./skylynx_local.db
   SECRET_KEY=change-me
   ```
   The SQLite URL is only for local runs. Cloud Run will use the secret.
2. **Run database migrations locally**:
   ```bash
   cd backend
   alembic upgrade head
   cd ..
   ```
3. **Start the backend locally** (in a new terminal tab with the venv active):
   ```bash
   cd backend
   uvicorn app.main:app --reload --port 8000
   ```
   Open http://127.0.0.1:8000/docs to see the interactive API docs.
4. **Test the desktop client against the local API**:
   - Open `skylynx-digital/config.json`.
   - Set "api_base_url": "http://127.0.0.1:8000".
   - Run the client: `python -m skylynx-digital`.
   - Log in with a test user you create via the API (e.g., POST /auth/register
     if provided) or seed a test account directly in the database.

## Part 5 — Wire the desktop client to the backend
1. **Use the API client helper** already in `skylynx-digital/services/api_client.py`.
   Make sure `config.json` includes:
   ```json
   {
     "api_base_url": "https://<your-cloud-run-url>",
     "api_access_token": "<token returned by login>",
     "api_account_id": "<company id to scope requests>"
   }
   ```
2. **Company selection and permissions**:
   - When the user logs in, the backend returns their `company_id` and module
     permissions.
   - Save `company_id` in memory and include it in API calls (e.g., as a header
     `X-Company-ID` or inside the JWT claims). This keeps every request scoped to
     the tenant.
3. **Module toggles**:
   - Ask the backend for `/companies/{company_id}/modules`.
   - Enable or hide UI sections in PySide based on the returned module list.
4. **Realtime updates**:
   - Connect to `wss://<your-cloud-run-url>/ws?company_id=<id>&token=<jwt>`.
   - If the socket drops, fall back to polling key endpoints every 10–15 seconds
     (e.g., list employees) and refresh the UI.

## Part 6 — Build and push the backend container
1. **Create a Dockerfile** (already in `backend/Dockerfile`). Make sure it uses
   Uvicorn to run `app.main:app`.
2. **Build the image** from the project root:
   ```bash
   cd backend
   gcloud builds submit --tag us-central1-docker.pkg.dev/$(gcloud config get-value project)/skylynx-backend/api:0.1.0 .
   cd ..
   ```
3. **Deploy to Cloud Run**:
   ```bash
   gcloud run deploy skylynx-backend \
     --image us-central1-docker.pkg.dev/$(gcloud config get-value project)/skylynx-backend/api:0.1.0 \
     --region us-central1 \
     --platform managed \
     --allow-unauthenticated \
     --service-account skylynx-backend@$(gcloud config get-value project).iam.gserviceaccount.com \
     --set-secrets DATABASE_URL=SKYLYNX_DATABASE_URL:latest \
     --add-cloudsql-instances $(gcloud sql instances describe skylynx-pg --format='value(connectionName)')
   ```
   Note: keep `--allow-unauthenticated` only if you rely on your own auth inside
   the API. Otherwise, enable Cloud Run authentication and require an identity.
4. **Run migrations on Cloud SQL** (one-time after deploy):
   ```bash
   gcloud run jobs create skylynx-migrate \
     --image us-central1-docker.pkg.dev/$(gcloud config get-value project)/skylynx-backend/api:0.1.0 \
     --region us-central1 \
     --set-secrets DATABASE_URL=SKYLYNX_DATABASE_URL:latest \
     --add-cloudsql-instances $(gcloud sql instances describe skylynx-pg --format='value(connectionName)') \
     --command "alembic" --args "upgrade,head"
   gcloud run jobs execute skylynx-migrate --region us-central1
   ```

## Part 7 — Package the desktop client for Windows
1. **Create a PyInstaller spec file** `nexacore.spec` at project root:
   ```python
   # NEW FILE: nexacore.spec
   block_cipher = None

   a = Analysis([
       'skylynx_digital/__main__.py'
   ],
   pathex=['.'],
   binaries=[],
   datas=[('skylynx_digital/config.json', 'skylynx_digital')],
   hiddenimports=[],
   hookspath=[],
   hooksconfig={},
   runtime_hooks=[],
   excludes=[],
   noarchive=False)

   pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

   exe = EXE(
       pyz,
       a.scripts,
       [],
       exclude_binaries=True,
       name='SkylynxDigitalERP',
       debug=False,
       bootloader_ignore_signals=False,
       strip=False,
       upx=True,
       console=False)

   coll = COLLECT(
       exe,
       a.binaries,
       a.zipfiles,
       a.datas,
       strip=False,
       upx=True,
       name='SkylynxDigitalERP')
   ```
2. **Build the installer** (from the project root with venv active):
   ```bash
   pyinstaller nexacore.spec
   ```
   The Windows installer will appear under `dist/SkylynxDigitalERP/`. Zip that
   folder or wrap it with an installer creator of your choice if needed.
3. **Configure the client to point to Cloud Run**:
   - Edit `skylynx-digital/config.json` before packaging to include your Cloud Run
     URL and any default settings.

## Part 8 — Operating tips
- **Rotate secrets**: update the Secret Manager value and redeploy (Cloud Run
  automatically mounts the latest secret version on next revision).
- **Roll out backend updates**: rebuild the image with a new tag, deploy, and
  run migrations via the Cloud Run job.
- **Update modules for all companies**: change the shared module code once, then
  deploy. Every company that has the module enabled will see the update as soon
  as they restart the desktop app or when their WebSocket/poll refresh pulls new
  data.
- **Monitoring**: use Cloud Run logs (Cloud Logging) and Cloud SQL insights to
  check performance and errors.

## Part 9 — Quick troubleshooting
- **Cannot connect to database**: verify the service account has `cloudsql.client`
  and that `--add-cloudsql-instances` matches the instance connection name.
- **401/403 errors**: make sure the client sends the auth token and `company_id`
  header or includes the company in the JWT.
- **WebSocket fails on corporate networks**: fall back to short polling every
  10–15 seconds.
- **PyInstaller missing DLLs**: run `pip install pyinstaller==6.3.0` inside the
  venv and rebuild; ensure Visual C++ Redistributable is installed on Windows.

You now have a clean, beginner-friendly path to put Skylynx Digital online with
FastAPI, Cloud Run, and Cloud SQL while keeping multi-tenant control over
modules and real-time updates.
