# JobSphere — Job Board and Applicant Tracking System

**JobSphere** is a web application where job seekers can browse API-sourced job listings and submit applications, while recruiters can review and organize those applications in a hiring pipeline.

- **Live application:** https://jobsphere-8w9s.onrender.com
- **Source repository:** https://github.com/anujatappeta/internship-review-jobats
- **Current hosting:** Render

## Project summary

JobSphere combines two related tools:

1. A public job board with searchable listings, job details, and an application form.
2. A recruiter portal with a protected dashboard for reviewing applications and updating their statuses.

Listings are imported from the [Arbeitnow Job Board API](https://www.arbeitnow.com/api). They are stored in the application database and link back to the original posting. If the API is unavailable, the importer reports an error instead of creating made-up listings.

## Problem and solution

Job seekers need one place to discover opportunities and apply. Recruiters need a simple way to view incoming applications and track where candidates are in the hiring process.

JobSphere addresses this by connecting an API-fed job board to an internal application tracker. Candidates can search and apply; recruiters can organize applications through a small, clear status pipeline.

## Goals

- Display real job listings rather than hard-coded sample jobs.
- Help candidates find roles by keyword, location, and job type.
- Collect candidate details and application information.
- Prevent duplicate applications to the same job by the same candidate.
- Give authenticated recruiters an overview of applications and their statuses.
- Deploy the application with a persistent PostgreSQL database.

## Users and main features

### Job seekers

- Browse active API-sourced jobs.
- Search by title, company, description, or skills.
- Filter by location and job type.
- View job details, required skills, company details, and the original listing.
- Submit contact details, skills, portfolio URL, and an optional cover letter.

### Recruiters

- Sign in through the recruiter portal.
- View application totals and counts for each hiring stage.
- Filter the dashboard by job.
- Review candidates in a Kanban-style pipeline.
- Update an application's status to **Applied**, **Under Review**, **Shortlisted**, or **Not Selected**.

### Interface

- Responsive layout built with Bootstrap and custom CSS.
- Light/dark theme toggle; the selected theme is saved in browser local storage.
- JavaScript-powered search, application form validation, and AJAX interactions.

## Technology stack

| Area | Technologies | Use in this project |
|---|---|---|
| Backend | Python 3.11, Django 5.2 | Web framework, routing, authentication, forms, ORM, and server-rendered pages |
| Frontend | HTML, Django Templates, CSS, JavaScript | Job board, application form, recruiter dashboard, filtering, and interactive actions |
| UI libraries | Bootstrap 5.3, Font Awesome 6, Google Fonts (Inter) | Responsive components, icons, and typography |
| Database | SQLite locally; PostgreSQL in production | Stores companies, listings, candidates, and applications |
| Database driver | Psycopg 3 | Connects Django to PostgreSQL |
| Job data | Arbeitnow Job Board API | Provides external job listings |
| HTTP client | Python Requests | Fetches API data during import |
| Production server | Gunicorn | Serves the Django WSGI application |
| Static assets | WhiteNoise | Serves collected static files in production |
| Hosting | Render | Hosts the web service and PostgreSQL database |
| Source control | Git and GitHub | Stores and versions the project |

## Application architecture

1. A browser requests a page from the Django application.
2. Django URL routes select a view in `jobs/views.py`.
3. Views validate input and read or update records through the Django ORM.
4. Django renders templates from `templates/` and returns HTML.
5. Browser JavaScript handles interactive filtering, application submissions, and recruiter status updates.
6. PostgreSQL stores production data; local development uses SQLite.
7. The separate `seed_jobs.py` script fetches and synchronizes job listings from Arbeitnow.

## Data model

| Model | Purpose | Important relationships |
|---|---|---|
| `Company` | Stores a company name, location, website, and logo URL | One company can have many job postings |
| `JobPosting` | Stores a job's title, type, skills, salary, description, active state, and source URL | Belongs to a company; can have many applications |
| `Candidate` | Stores a candidate's name, unique email, phone, portfolio URL, and skills | Can submit applications to multiple jobs |
| `JobApplication` | Connects a candidate to a job; stores cover letter, status, and submission time | A candidate can apply only once to a given job |

Recruiter accounts use Django's built-in user and authentication system. The recruiter dashboard and application-status update view require an authenticated user.

## Job data import

`seed_jobs.py` performs the following steps:

1. Requests the first page of the Arbeitnow Job Board API with a timeout.
2. Checks the response and reads the job data.
3. Skips records missing a company, title, or valid HTTP(S) source URL.
4. Normalizes fields, removes HTML tags from descriptions, and derives a job type.
5. Finds or creates companies and upserts postings by their unique external URL.
6. Deactivates old API-sourced records before reactivating the current import.

The importer is run during the Render build and can also be run manually. It is not a continuous live API proxy; listings are stored in the database between imports.

## How the project was built

1. **Set up the Django project.** `myproject/` contains settings and WSGI/ASGI entry points; `jobs/` contains the job-board application.
2. **Designed the data layer.** Added company, job, candidate, and application models, then generated Django migrations.
3. **Connected a real listings source.** Implemented and tested the Arbeitnow importer, including validation, normalization, and duplicate-safe synchronization.
4. **Built the public job board.** Added list and detail pages with keyword search, filters, and original-posting links.
5. **Added candidate applications.** Created Django forms and an application view that saves candidate/application records and rejects repeat applications.
6. **Built the recruiter workflow.** Added authenticated login, a dashboard grouped by hiring status, per-job filtering, and status updates.
7. **Added browser interactions.** Used JavaScript for theme selection, client-side search, form feedback, and AJAX requests.
8. **Prepared production deployment.** Configured PostgreSQL, environment-based secrets, static-file handling, Gunicorn, and a Render Blueprint in `render.yaml`.
9. **Validated the behavior.** Django tests cover models, pages, applications, recruiter access, status updates, and API-import behavior.

## Run locally (Windows PowerShell)

Requires Python 3.11 and Git.

```powershell
git clone https://github.com/anujatappeta/internship-review-jobats.git
cd internship-review-jobats
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
$env:DEBUG = "True"
python manage.py migrate
python seed_jobs.py
python manage.py runserver
```

Open http://127.0.0.1:8000/. To create a local recruiter account, run:

```powershell
python manage.py createsuperuser
```

To refresh imported listings later, run `python seed_jobs.py` again. The command needs an internet connection to reach the external API.

## Deploy to Render

The included `render.yaml` describes a Render web service and PostgreSQL database.

1. Push the repository to GitHub and connect it to Render as a Blueprint.
2. Render provisions the web service and database, installs requirements, runs migrations, collects static files, and imports jobs.
3. In the Render service's Environment settings, set `ADMIN_PASSWORD` to a strong private value. Do not put credentials in GitHub or this README.
4. Save and deploy the environment change. At service startup, `create_superuser.py` creates the configured recruiter account if it does not already exist.
5. Visit the live site and sign in through the **Recruiter Portal**.

Render manages the production database URL and generated Django secret key. The current free Render database has a 30-day expiration policy, and a free web service may sleep when idle; review Render's current plan terms before relying on it for long-term data storage.

## Tests

Run the Django test suite with:

```powershell
python manage.py test
```

The tests cover job and candidate model behavior, API-only listing display, job detail, application submission and duplicate prevention, recruiter authentication, application-status updates, and API-import success/failure cases. API calls in importer tests are mocked.

## Current scope and limitations

- Job imports use the first API page and run when the import command is invoked; no scheduled refresh is configured.
- The application form saves applications in JobSphere. It does not submit them to the external job site's own application system.
- The project does not currently include resume-file uploads, email notifications, or candidate self-service accounts.
- Free hosting is suitable for a demonstration, but its sleep and database-expiration policies are not intended for durable production data.

## Suggested presentation outline

1. **Title:** JobSphere — Job Board and Applicant Tracking System
2. **Problem:** Job discovery and application tracking are split across separate workflows.
3. **Solution and objectives:** API-backed job search connected to a recruiter pipeline.
4. **Technology stack:** Django/Python, templates/JavaScript/Bootstrap, PostgreSQL, Arbeitnow API, Render.
5. **System architecture:** Browser → Django views/forms → ORM/database; importer → external API → database.
6. **Database design:** Company, JobPosting, Candidate, and JobApplication relationships.
7. **Candidate workflow:** Search/filter → view details → submit application.
8. **Recruiter workflow:** Sign in → filter applications → move candidates through hiring stages.
9. **Implementation and testing:** API normalization, duplicate prevention, authentication, and Django tests.
10. **Deployment and future work:** Render deployment, current limitations, and possible scheduled imports, email updates, and resume uploads.
