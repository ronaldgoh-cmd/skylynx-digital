# Skylynx Digital Cloud Beginner Guide (FastAPI + Google Cloud)

This guide is written for absolute beginners and favors simple, repeatable
steps. Follow it from top to bottom even if you have partial experience—the
order matters. The goal is to move the Skylynx Digital desktop ERP (PySide/Qt)
to an online, multi-tenant setup with a shared backend.

Tip: keep a terminal open while you work. After each section you will see a
"Checkpoint" list—run those quick commands to confirm you are on track.

## What you will build
- A FastAPI backend running on **Google Cloud Run**.
- A managed **PostgreSQL** database on **Google Cloud SQL**.
- A simple multi-tenant data model: every record has a `company_id`, and a
  `company_modules` table turns modules on/off per company.
- Real-time-ish updates using WebSockets (with short-polling as a fallback).
- The PySide desktop client calls the API instead of talking directly to the
  database, and you will package it as a Windows `.exe` with PyInstaller.

Estimated time: 2–3 hours for a first pass (includes waiting for Google Cloud
resources to finish creating).

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
1. A Google account with access to create a project and services.
2. PyCharm installed on your computer.
3. Python 3.11 or later installed (Windows: use the official installer and check
   “Add Python to PATH”).
4. Git installed.
5. (Optional) Google Chrome to access Google Cloud Console.

Checkpoint:
- In a terminal, confirm Python and Git are available:
  ```bash
  python --version
  git --version
  ```

## Part 1 — Open the project in PyCharm and prepare Python
1. **Clone the code (if you have not yet):**
   ```bash
   git clone https://github.com/<your-org>/skylynx_digital.git
   cd skylynx_digital
   ```
   If you already have the code, run `git pull` to make sure you are on the
   latest revision.
2. **Open PyCharm** → **Open** → choose the `skylynx-digital` folder.
3. **Create a virtual environment** (inside PyCharm):
   - PyCharm menu **File → Settings → Project: skylynx-digital → Python
     Interpreter**.
   - Click the gear icon → **Add** → **Virtualenv Environment** → Location:
     `<project>/.venv` → Base interpreter: your Python 3.11 → **OK**.
   - Wait for PyCharm to finish indexing; a status bar will disappear when done.
4. **Activate the venv in the terminal** (inside PyCharm’s built-in terminal):
   ```bash
   source .venv/bin/activate   # Windows PowerShell: .venv\Scripts\Activate.ps1
   ```
   You should see `(.venv)` at the start of your terminal prompt after running
   this command.
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

Checkpoint:
- `python -m skylynx_digital` opens a window without errors.
- `pip list | grep fastapi` shows FastAPI installed in your venv.

## Part 2 — Design the multi-tenant data model
We will keep a single database and include a `company_id` on every business
record. This is easiest for beginners and keeps the deployment steps short.

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

Checkpoint:
- Sketch the tables above on paper or in a note with arrows showing foreign
  keys. You will reference this when writing migrations and validating API
  responses.

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
   - Follow the prompts to log in and select your project. If you get an error
     about missing permissions, sign in with the Google account listed in the
     prerequisites.
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
   Replace `CHOOSE_A_STRONG_PASSWORD` with a long, unique password and save it
   in a password manager—this value is referenced again in the secret.
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

Checkpoint:
- `gcloud config list project` prints the project ID you just created.
- `gcloud sql instances list` shows `skylynx-pg` in the region you chose.
- `gcloud secrets describe SKYLYNX_DATABASE_URL` succeeds and lists one version.

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
   Avoid committing secrets; `.env` is already gitignored.
2. **Run database migrations locally**:
   ```bash
   cd backend
   alembic upgrade head
   cd ..
   ```
   If you see an error about the database file missing, double-check the
   `DATABASE_URL` value above.
3. **Start the backend locally** (in a new terminal tab with the venv active):
   ```bash
   cd backend
   uvicorn app.main:app --reload --port 8000
   ```
   Open http://127.0.0.1:8000/docs to see the interactive API docs.
   Leave this server running while you test the desktop client.
4. **Test the desktop client against the local API**:
   - Open `skylynx-digital/config.json`.
   - Set "api_base_url": "http://127.0.0.1:8000".
   - Run the client: `python -m skylynx-digital`.
   - Log in with a test user you create via the API (e.g., POST /auth/register
     if provided) or seed a test account directly in the database.

Checkpoint:
- `alembic current` (from the `backend` folder) shows `head`.
- http://127.0.0.1:8000/docs loads in a browser and lists your routes.
- Desktop client fetches data (or at least connects) when pointed at the local
  API.

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

Checkpoint:
- A login call returns a token that you paste into `config.json`.
- Changing `api_base_url` between local (http://127.0.0.1:8000) and Cloud Run
  shows different data, confirming the client is reading the config.

## Part 6 — Build and push the backend container
1. **Create a Dockerfile** (already in `backend/Dockerfile`). Make sure it uses
   Uvicorn to run `app.main:app`.
2. **Build the image** from the project root:
   ```bash
   cd backend
   gcloud builds submit --tag us-central1-docker.pkg.dev/$(gcloud config get-value project)/skylynx-backend/api:0.1.0 .
   cd ..
   ```
   If Cloud Build is disabled, rerun the command after enabling it in the Google
   Cloud Console.
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

Checkpoint:
- `gcloud run services list` shows `skylynx-backend` with status `Ready`.
- Visiting the Cloud Run URL `/docs` returns the FastAPI Swagger UI.
- `gcloud run jobs describe skylynx-migrate --region us-central1` shows the last
  execution succeeded.

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

Checkpoint:
- `dist/SkylynxDigitalERP/SkylynxDigitalERP.exe` exists after running
  PyInstaller.
- Launching the packaged app shows it using the Cloud Run URL you configured.

## Part 8 — Operating tips
- **Rotate secrets**: update the Secret Manager value and redeploy (Cloud Run
  automatically mounts the latest secret version on next revision).
- **Roll out backend updates**: rebuild the image with a new tag, deploy, and
  run migrations via the Cloud Run job. Example:
  ```bash
  cd backend
  gcloud builds submit --tag us-central1-docker.pkg.dev/$(gcloud config get-value project)/skylynx-backend/api:0.1.1 .
  gcloud run deploy skylynx-backend --image us-central1-docker.pkg.dev/$(gcloud config get-value project)/skylynx-backend/api:0.1.1 --region us-central1 --platform managed
  gcloud run jobs execute skylynx-migrate --region us-central1
  cd ..
  ```
- **Update modules for all companies**: change the shared module code once, then
  deploy. Every company that has the module enabled will see the update as soon
  as they restart the desktop app or when their WebSocket/poll refresh pulls new
  data.
- **Monitoring**: use Cloud Run logs (Cloud Logging) and Cloud SQL insights to
  check performance and errors.

Checkpoint:
- Cloud Run logs show requests from your desktop client after you deploy.
- Running the migrate job after a new deploy finishes without errors.

## Part 9 — Quick troubleshooting
- **Cannot connect to database**: verify the service account has `cloudsql.client`
  and that `--add-cloudsql-instances` matches the instance connection name.
  Running `gcloud sql instances describe skylynx-pg --format='value(connectionName)'`
  should print the same value you deploy with.
- **401/403 errors**: make sure the client sends the auth token and `company_id`
  header or includes the company in the JWT. Retest using the `/docs` UI to see
  required headers for each endpoint.
- **WebSocket fails on corporate networks**: fall back to short polling every
  10–15 seconds. Keep the polling code behind a single toggle so you can switch
  back to websockets when the network allows.
- **PyInstaller missing DLLs**: run `pip install pyinstaller==6.3.0` inside the
  venv and rebuild; ensure Visual C++ Redistributable is installed on Windows.
  If antivirus blocks the build, add the project folder to its allowlist during
  packaging.

You now have a clean, beginner-friendly path to put Skylynx Digital online with
FastAPI, Cloud Run, and Cloud SQL while keeping multi-tenant control over
modules and real-time updates.
