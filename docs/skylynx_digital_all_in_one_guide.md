# Skylynx Digital All-in-One Cloud Guide (Copy/Paste Ready)

**Follow these steps in order. Every command is ready to paste. Replace only the placeholders wrapped in `<...>`. Wherever a command is listed, open the specified shell and paste it exactly. Expected results are listed so you know it succeeded.**

- Backend: FastAPI + SQLAlchemy + Alembic.
- Database: PostgreSQL on Google Cloud SQL (SQLite used locally for quick start).
- Hosting: Docker container on Google Cloud Run.
- Client: Existing PySide6 desktop app calling the API.

---
## 0. Prerequisites on your computer (Windows or macOS)
- Python **3.11** installed.
- Git installed.
- PyCharm Community (optional but recommended).
- Google Cloud account with billing enabled.

Open **PowerShell (Windows)** or **Terminal (macOS/Linux)** and run quick checks:
```bash
python --version
git --version
```
Expected: shows Python 3.11.x and git version (e.g., `git version 2.x.x`).
Example PowerShell output:
```
PS C:\Users\you> python --version
Python 3.11.9
PS C:\Users\you> git --version
git version 2.44.0.windows.1
```

---
## 1. Clone the repo and create a virtual environment
Open **PowerShell** (Windows) or **Terminal** (macOS/Linux), then paste:
```bash
cd ~
git clone https://github.com/<YOUR_ORG>/skylynx-digital.git
cd skylynx-digital
python -m venv .venv
# Activate venv: choose one based on your shell
source .venv/bin/activate          # macOS/Linux
.venv\\Scripts\\Activate.ps1          # Windows PowerShell
```
Expected: `skylynx-digital` directory exists, prompt shows `(.venv)` after activation.
Example PowerShell prompt after activation:
```
PS C:\Users\you\skylynx-digital> .venv\Scripts\Activate.ps1
(.venv) PS C:\Users\you\skylynx-digital>
```

Install all dependencies (backend + client):
```bash
pip install --upgrade pip
pip install -r requirements.txt
cd backend
pip install -e .
cd ..
```
Expected: installations finish without errors; `Successfully installed ...` appears.
Example ending lines:
```
Successfully installed fastapi-0.110.1 pydantic-1.10.14 uvicorn-0.29.0 ...
(.venv) PS C:\Users\you\skylynx-digital>
```

---
## 2. Prepare local environment files
Create the backend `.env` from the example (PowerShell/Terminal):
```bash
cp backend/.env.example backend/.env
```
Set local values inside `backend/.env` (SQLite for local runs). Use any editor, or run:
```
DATABASE_URL=sqlite+aiosqlite:///./skylynx_local.db
SECRET_KEY=dev-change-me
```
Expected: file `backend/.env` now contains those two lines.
Example file content (PowerShell `Get-Content backend/.env`):
```
DATABASE_URL=sqlite+aiosqlite:///./skylynx_local.db
SECRET_KEY=dev-change-me
```

---
## 3. Initialize and seed the local database (SQLite)
Run migrations (in the same shell with venv active):
```bash
cd backend
alembic upgrade head
```
Expected: output ends with `INFO  [alembic.runtime.migration] Running upgrade` and no errors.
Example tail of output:
```
INFO  [alembic.runtime.migration] Context impl AsyncPostgresqlImpl.
INFO  [alembic.runtime.migration] Running upgrade  -> <hash>, create core tables
```
Seed a starter company, modules, and admin user (copy/paste exactly; change the password if you like):
```bash
python - <<'PY'
from app.database import SessionLocal
from app import models
from app.auth import get_password_hash

db = SessionLocal()
# Ensure tables exist
models.Base.metadata.create_all(bind=db.get_bind())

company = models.Company(name="Demo Company", is_active=True)
modules = [
    models.Module(code="EMP", name="Employee Management"),
    models.Module(code="SAL", name="Salary"),
    models.Module(code="LEAVE", name="Leave"),
]
admin = models.User(email="admin@demo.test", company=company, role="admin", password_hash=get_password_hash("ChangeMe123!"))

# Attach modules to the company
company_modules = [models.CompanyModule(company=company, module=m, enabled=True) for m in modules]

db.add_all([company, admin, *modules, *company_modules])
db.commit()
db.close()
PY
cd ..
```
Expected: no traceback; if you re-run, duplicates may raise errors—run once.
Example successful end:
```
(.venv) PS C:\Users\you\skylynx-digital\backend> python - <<'PY'
... (no output) ...
(.venv) PS C:\Users\you\skylynx-digital\backend>
```

---
## 4. Run the backend locally
Open a **new PowerShell/Terminal window**, activate the venv, then start the API:
```bash
cd ~/skylynx-digital/backend
uvicorn app.main:app --reload --port 8000
```
Expected: server logs show `Uvicorn running on http://127.0.0.1:8000`. Leave this window open.
Example first lines:
```
INFO:     Uvicorn running on http://127.0.0.1:8000 (Press CTRL+C to quit)
INFO:     Started reloader process [12345] using StatReload
```
Open http://127.0.0.1:8000/docs in a browser and log in with:
- **email:** `admin@demo.test`
- **password:** `ChangeMe123!`

Leave this terminal running while testing.

---
## 5. Point the desktop client to the local API
Edit `skylynx_digital/config.json` to match:
```json
{
  "api_base_url": "http://127.0.0.1:8000",
  "api_access_token": "",        
  "api_account_id": ""
}
```
Run the desktop app locally (open another PowerShell/Terminal window, activate venv, then):
```bash
cd ~/skylynx-digital
python -m skylynx_digital
```
Expected: desktop UI opens; if run from console, it prints no errors.
After logging in via the API docs, paste the returned token into `api_access_token` and the company id into `api_account_id`, then rerun the app to see live data.

---
## 6. Prepare Google Cloud (one-time, copy/paste)
Open **PowerShell** (with `gcloud` installed) or **Google Cloud Shell** (browser): click the Cloud Shell icon in the top-right of the GCP console, then paste these variable definitions (replace placeholders once). **Use `asia-southeast1` for Singapore (Southeast Asia)**:
```bash
PROJECT_ID=<YOUR_GCP_PROJECT_ID>
REGION=asia-southeast1
SQL_INSTANCE=skylynx-pg
SQL_DB=skylynx_app
SQL_USER=skylynx_user
SQL_PASSWORD=<STRONG_PASSWORD>
REPO=skylynx-backend
IMAGE_TAG=api:0.1.0
SERVICE=skylynx-backend
SA=skylynx-backend
```
Expected: no output, just a new prompt.
Example Cloud Shell prompt afterward:
```
cloudshell:~ (your-project)$ PROJECT_ID=your-project-id
cloudshell:~ (your-project)$ REGION=asia-southeast1
cloudshell:~ (your-project)$
```

Login and set the project:
```bash
gcloud auth login
gcloud config set project $PROJECT_ID
```
Expected: browser opens for login (if local). After setting project, output `Updated property [core/project].`
Example Cloud Shell response:
```
Updated property [core/project].
```

Enable required services:
```bash
gcloud services enable compute.googleapis.com run.googleapis.com sqladmin.googleapis.com artifactregistry.googleapis.com secretmanager.googleapis.com cloudbuild.googleapis.com
```
Expected: finishes with `Operation "operations/..." finished successfully.`
Example ending:
```
Operation "operations/acf.p2-12345" finished successfully.
```

Create Artifact Registry (for Docker images):
```bash
gcloud artifacts repositories create $REPO --repository-format=docker --location=$REGION --description="Skylynx backend"
```
Expected: `Created repository [projects/.../repositories/skylynx-backend].`
Example:
```
Created repository [projects/your-project-id/locations/asia-southeast1/repositories/skylynx-backend].
```

Create Cloud SQL PostgreSQL and database:
```bash
gcloud sql instances create $SQL_INSTANCE --database-version=POSTGRES_15 --tier=db-f1-micro --region=$REGION
gcloud sql databases create $SQL_DB --instance=$SQL_INSTANCE
gcloud sql users create $SQL_USER --instance=$SQL_INSTANCE --password="$SQL_PASSWORD"
```
Expected: each command ends with `Created` and shows instance/database/user names.
Example instance creation tail:
```
Creating Cloud SQL instance...done.
Created [https://sqladmin.googleapis.com/sql/v1beta4/projects/your-project/instances/skylynx-pg].
```

Store the DB URL in Secret Manager:
```bash
DB_CONN=$(gcloud sql instances describe $SQL_INSTANCE --format='value(connectionName)')
SECRET_VALUE="postgresql+asyncpg://$SQL_USER:$SQL_PASSWORD@/$SQL_DB?host=/cloudsql/$DB_CONN"
gcloud secrets create SKYLYNX_DATABASE_URL --replication-policy=automatic || true
echo -n "$SECRET_VALUE" | gcloud secrets versions add SKYLYNX_DATABASE_URL --data-file=-
```
Expected: secret creation may say "already exists" (that is ok); version add prints `created version`.
Example version add:
```
Created version [1] of the secret [SKYLYNX_DATABASE_URL].
```

Create a service account and grant access:
```bash
gcloud iam service-accounts create $SA --display-name="Skylynx Backend"
gcloud projects add-iam-policy-binding $PROJECT_ID \
  --member="serviceAccount:$SA@$PROJECT_ID.iam.gserviceaccount.com" \
  --role="roles/cloudsql.client"
gcloud secrets add-iam-policy-binding SKYLYNX_DATABASE_URL \
  --member="serviceAccount:$SA@$PROJECT_ID.iam.gserviceaccount.com" \
  --role="roles/secretmanager.secretAccessor"
```
Expected: IAM bindings print `Updated IAM policy`; service account creation prints `created service account`.
Example snippet:
```
Created service account [skylynx-backend].
Updated IAM policy for project [your-project-id].
``` 

---
## 7. Build and push the backend image
From the repository root (PowerShell/Cloud Shell):
```bash
cd ~/skylynx-digital/backend
gcloud builds submit --tag $REGION-docker.pkg.dev/$PROJECT_ID/$REPO/$IMAGE_TAG .
cd ..
```
Expected: build log ends with `DONE` and image URL.
Example final lines:
```
DONE
Successfully tagged asia-southeast1-docker.pkg.dev/your-project-id/skylynx-backend/api:0.1.0
```

---
## 8. Deploy to Cloud Run and connect Cloud SQL
Deploy the service:
```bash
gcloud run deploy $SERVICE \
  --image $REGION-docker.pkg.dev/$PROJECT_ID/$REPO/$IMAGE_TAG \
  --region $REGION \
  --platform managed \
  --allow-unauthenticated \
  --service-account $SA@$PROJECT_ID.iam.gserviceaccount.com \
  --set-secrets DATABASE_URL=SKYLYNX_DATABASE_URL:latest \
  --add-cloudsql-instances $(gcloud sql instances describe $SQL_INSTANCE --format='value(connectionName)')
```
Expected: ends with `Service [skylynx-backend] revision [..] has been deployed` and shows a URL. Save that URL.
Example end:
```
Service [skylynx-backend] revision [skylynx-backend-00001] has been deployed and is serving 100 percent of traffic at https://skylynx-backend-<hash>-asia-southeast1.a.run.app
```

Run migrations in Cloud SQL using a Cloud Run job:
```bash
gcloud run jobs create skylynx-migrate \
  --image $REGION-docker.pkg.dev/$PROJECT_ID/$REPO/$IMAGE_TAG \
  --region $REGION \
  --set-secrets DATABASE_URL=SKYLYNX_DATABASE_URL:latest \
  --add-cloudsql-instances $(gcloud sql instances describe $SQL_INSTANCE --format='value(connectionName)') \
  --command "alembic" --args "upgrade,head" || true

gcloud run jobs execute skylynx-migrate --region $REGION
```
Expected: job creation prints `created` (or `already exists`), execution ends with `Execution finished with status: SUCCEEDED`.
Example execution tail:
```
Execution finished with status: SUCCEEDED
``` 

Verify the service:
```bash
gcloud run services list
```
Expected: status column shows `Ready`. Visit `https://<SERVICE_URL>/docs` in your browser; you should see the FastAPI Swagger UI.
Example table row:
```
SERVICE            REGION             URL                                                 LAST DEPLOYED BY
skylynx-backend    asia-southeast1    https://skylynx-backend-<hash>-asia-southeast1.a.run.app   you@example.com
```

---
## 9. Point the desktop client to Cloud Run
Edit `skylynx_digital/config.json`:
```json
{
  "api_base_url": "https://<YOUR_CLOUD_RUN_URL>",
  "api_access_token": "<TOKEN_FROM_LOGIN>",
  "api_account_id": "<COMPANY_ID_FROM_LOGIN>"
}
```
Run the client and confirm it loads data from Cloud Run:
```bash
cd ~/skylynx-digital
python -m skylynx_digital
```
Expected: app opens; data loads without errors when using the Cloud Run token and company ID.

---
## 10. Package the desktop app for Windows (.exe)
Create the PyInstaller spec file at project root (PowerShell/Terminal):
```bash
cat <<'PY' > nexacore.spec
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
PY
```

Build the executable (venv must be active):
```bash
pyinstaller nexacore.spec
```
Expected: build ends with `Building EXE from EXE-00.toc completed successfully`; the app appears at `dist/SkylynxDigitalERP/SkylynxDigitalERP.exe`.

---
## 11. Rolling out backend updates later
Rebuild, deploy, and migrate with new version numbers:
```bash
cd backend
gcloud builds submit --tag $REGION-docker.pkg.dev/$PROJECT_ID/$REPO/api:0.1.1 .
gcloud run deploy $SERVICE --image $REGION-docker.pkg.dev/$PROJECT_ID/$REPO/api:0.1.1 --region $REGION
cd ..
gcloud run jobs execute skylynx-migrate --region $REGION
```
Expected: same success messages as initial build/deploy/migrate steps.

---
## 12. Quick health checks
- Local: `http://127.0.0.1:8000/docs` loads and you can log in with the seeded admin.
- Cloud: `gcloud run services list` shows status `Ready`; `/docs` on the service URL loads.
- Desktop: Switching `api_base_url` between local and Cloud Run shows different data, confirming the client uses the config.

You now have one authoritative guide that merges the previous two documents with exact commands you can paste end-to-end.
