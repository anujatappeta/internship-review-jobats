# JobSphere

JobSphere is a Django job board and recruiter ATS. Public job listings are imported from the live [Arbeitnow Job Board API](https://www.arbeitnow.com/api), and each listing links back to its original posting. The app does not create sample or fallback jobs when the API is unavailable.

## Local setup

Requires Python 3.11.

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
$env:DEBUG = "True"
python manage.py migrate
python seed_jobs.py
python manage.py runserver
```

Open `http://127.0.0.1:8000/`. Run `python seed_jobs.py` again to refresh the imported listings. If the external API is down, the command reports the error and does not add fabricated jobs.

Create a recruiter account locally with `python manage.py createsuperuser`.

## Deploy to Vercel

Vercel detects the Django `manage.py` and WSGI entry point. The `vercel.json` sets a function duration limit; Vercel handles static-file collection.

1. Push this project folder to a GitHub repository and import that repository into Vercel.
2. Connect a persistent PostgreSQL database and set these Vercel project environment variables:
   - `DATABASE_URL`: the database connection string.
   - `SECRET_KEY`: a long, unique Django secret.
   - `DEBUG`: `False`.
   - `ALLOWED_HOSTS`: `.vercel.app` and any custom domain.
   - `CSRF_TRUSTED_ORIGINS`: `https://*.vercel.app` and any custom-domain origin.
3. Before serving traffic, run `python manage.py migrate` and `python seed_jobs.py` in an environment configured with the same `DATABASE_URL`. Vercel's local environment can be obtained with `vercel env pull`; do not commit the downloaded environment file.
4. Deploy with the Vercel CLI (`vercel --prod`) or let Vercel deploy from GitHub.

SQLite is retained for local development only. Vercel's function filesystem is not a persistent database.

## Deploy to Render

The included `render.yaml` provisions PostgreSQL, runs migrations and imports API jobs during the build, and starts the Django app with Gunicorn. The generated `SECRET_KEY` and database URL are managed by Render. Create a recruiter account through Django's management command in an environment connected to the same database.
