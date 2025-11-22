# Skylynx ERP Cloud Rebuild Plan (Beginner Friendly)

This guide restarts everything from a clean slate and explains how to put the Skylynx desktop ERP online as a multi-tenant system. Every step is explicit so you can follow it even if you are new to Python, Google Cloud, or deployment.

---
## 1) Architecture snapshot (what we are building)

* **Backend**: FastAPI app (`backend/app`) packaged in a Docker image and deployed to **Google Cloud Run**. It exposes REST endpoints plus a `/ws` WebSocket for real-time events.
* **Database**: PostgreSQL on **Cloud SQL**. Tables share a simple multi-tenant key: every row includes `account_id` (see `backend/app/models/base.py`).
* **Tenants and modules**:
  * Desktop keeps track of the active tenant via `skylynx_digital/core/tenant.py` (`account_id`).
  * Module discovery is dynamic (`skylynx_digital/core/plugins.py`); enable/disable flags live in the `module_state` table (`skylynx_digital/core/models.py`).
* **Real-time updates**: Backend broadcasts to connected sockets per tenant (`backend/app/websocket_manager.py`); the desktop listens with `EmployeeRealtimeClient` (`skylynx_digital/core/realtime.py`).
* **Desktop client**: PySide6 UI that now calls the backend through `skylynx_digital/services/api_client.py` and respects module flags and tenant selection.
* **Packaging**: Build a Windows installer with PyInstaller so you can install on any PC.

---
## 2) High-level path (10 steps)

1. Prepare your workstation and clone the repo.
2. Create a new Google Cloud project and enable required APIs.
3. Set up a Cloud SQL (PostgreSQL) instance for multi-tenant data.
4. Create a service account for deployments and store its key safely.
5. Configure backend environment values (`DATABASE_URL`, `SECRET_KEY`).
6. Build and publish the backend container image to Artifact Registry.
7. Deploy the backend to Cloud Run and connect it to Cloud SQL.
8. Point the desktop app at the new API and test login + employees.
9. Wire up real-time updates in the desktop (WebSocket) and verify.
10. Package the desktop client with PyInstaller for distribution.

---
## 3) Step-by-step instructions

### Step 1 — Prepare your workstation (once per machine)
1. Open **PyCharm**.
2. Click **File → Open** and choose the `skylynx-digital` folder.
3. Create a virtual environment for backend work:
   1. Open **View → Tool Windows → Terminal**.
   2. Run:
      ```bash
      cd backend
      python -m venv .venv
      # Windows PowerShell
      .\.venv\Scripts\Activate
      # macOS/Linux
      source .venv/bin/activate
      ```
   3. Install dependencies:
      ```bash
      pip install -r ../requirements.txt
      pip install -e .
      ```

### Step 2 — Start fresh with Google Cloud
1. Sign in at https://console.cloud.google.com/.
2. Click the project dropdown (top bar) → **New Project** → name it `skylynx-online` → **Create**.
3. Open a terminal on your PC and run:
   ```bash
   gcloud init
   gcloud config set project <YOUR_PROJECT_ID>
   ```
4. Enable the needed APIs (Console: **APIs & Services → Library**):
   * Cloud Run API
   * Cloud SQL Admin API
   * Artifact Registry API
   * IAM Service Account Credentials API

### Step 3 — Create Cloud SQL (PostgreSQL)
1. Console: **Navigation menu (☰) → SQL**.
2. Click **Create Instance** → **Choose PostgreSQL**.
3. Pick a region close to you, set **Instance ID** (e.g., `skylynx-sql`), set a strong **postgres** password, then **Create**.
4. After it is ready, create a database:
   * In the instance page, go to **Databases → Create database** → name it `skylynx` → **Create**.
5. Add a user for the app:
   * **Users → Add user account** → username `skylynx_app` → strong password → **Create**.
6. Copy the **Public IP** of the instance (for the connection string). Add your current IP to **Connections → Authorization → Add network** so your Cloud Run service can talk to it later.

### Step 4 — Create a deployment service account
1. Console: **IAM & Admin → Service Accounts → Create Service Account**.
2. Name: `skylynx-deployer`. Grant roles:
   * Cloud Run Admin
   * Cloud SQL Client
   * Artifact Registry Writer
3. After creation, click the account → **Keys → Add Key → Create new key → JSON**. Download and save it in Bitwarden.

### Step 5 — Configure backend environment
1. In PyCharm, open `backend/.env.example` (create it if missing) and fill values, then save it as `backend/.env`:
   ```env
   DATABASE_URL=postgresql+asyncpg://skylynx_app:<DB_PASSWORD>@<DB_PUBLIC_IP>:5432/skylynx
   SECRET_KEY=<generate_a_new_random_string>
   ACCESS_TOKEN_EXPIRES_MINUTES=1440
   ```
   *Replace `<DB_PASSWORD>` and `<DB_PUBLIC_IP>` with your real values.*
2. The backend uses the `account_id` column on every table to keep tenant data separated (`backend/app/models/base.py`). Keep `account_id` values consistent between client logins and database rows.

### Step 6 — Build and push the container image
1. Still in the `backend` folder with the venv active, build the Docker image locally to be sure it works:
   ```bash
   docker build -t skylynx-backend:local .
   ```
2. Push through Google Cloud Build so Artifact Registry stores it:
   ```bash
   gcloud builds submit --tag "<REGION>-docker.pkg.dev/<PROJECT_ID>/skylynx/skylynx-backend:latest"
   ```
   *Replace `<REGION>` (e.g., `us-central1`) and `<PROJECT_ID>` with your project values. The first push will create the `skylynx` repository automatically.*

### Step 7 — Deploy to Cloud Run
1. Deploy with Cloud SQL access:
   ```bash
   gcloud run deploy skylynx-backend \
     --image "<REGION>-docker.pkg.dev/<PROJECT_ID>/skylynx/skylynx-backend:latest" \
     --region <REGION> \
     --platform managed \
     --allow-unauthenticated \
     --set-env-vars "DATABASE_URL=postgresql+asyncpg://skylynx_app:<DB_PASSWORD>@<DB_PUBLIC_IP>:5432/skylynx" \
     --set-env-vars "SECRET_KEY=<RANDOM_SECRET>" \
     --set-env-vars "ACCESS_TOKEN_EXPIRES_MINUTES=1440"
   ```
2. Wait for the URL output (e.g., `https://skylynx-backend-xxxxx.a.run.app`). Keep it for the desktop client.
3. Test the health endpoint from your terminal:
   ```bash
   curl https://skylynx-backend-xxxxx.a.run.app/health
   ```
   You should see `{"status":"ok"}`.

### Step 8 — Point the desktop client to the new backend
1. Open `skylynx_digital/config.json` and set:
   ```json
   {
     "api_base_url": "https://skylynx-backend-xxxxx.a.run.app",
     "api_username": "<your_first_admin_user>",
     "api_password": "<that_password>",
     "api_account_id": "<tenant_key>"
   }
   ```
2. In PyCharm, run the desktop app from the project root:
   ```bash
   python -m skylynx_digital
   ```
3. Log in with the user you created via the backend (use the `/auth/register` endpoint or seed a user directly in the database). After login, open **Employee Management** and confirm you can list/add employees.

### Step 9 — Verify real-time updates
1. On one PC, open the desktop app and log in as Company A.
2. On another PC, log in as the same company.
3. Add an employee on PC #1. The other window should refresh automatically because the backend broadcasts via `/ws` and the client listens (`skylynx_digital/core/realtime.py`). If it doesn’t, confirm ports are open and the `SKYLYNX_API_TOKEN` or login token is valid.

### Step 10 — Package the desktop client for Windows
1. From the project root (not inside `backend`), create a clean venv for packaging:
   ```bash
   python -m venv .venv
   .\.venv\Scripts\Activate
   pip install -r requirements.txt
   pip install pyinstaller
   ```
2. Build the installer:
   ```bash
   pyinstaller --name SkylynxERP --onefile skylynx_digital/__main__.py
   ```
3. The `.exe` will be in `dist/SkylynxERP.exe`. Share it with users. When they install, have them edit `config.json` (same folder as the executable) to point at your Cloud Run URL and enter their tenant `account_id`.

---
## 4) How updates roll out to all tenants
* Backend code lives in one place; deploying a new container to Cloud Run updates everyone instantly.
* Modules stay discoverable via `skylynx_digital/core/plugins.py`. Use the `module_state` table to toggle modules per company; clients read those flags to show/hide UI.
* Real-time notifications are tenant-scoped: `broadcast_event` in `backend/app/websocket_manager.py` only sends to sockets authenticated for that `account_id`.

Follow these steps in order and you will have a clean, multi-tenant Skylynx ERP running online with simple deployment and update workflows.
