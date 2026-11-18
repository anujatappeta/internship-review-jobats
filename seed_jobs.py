import os

import django
import requests
from django.utils.html import strip_tags

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'myproject.settings')
django.setup()

from jobs.models import Company, JobPosting

API_URL = 'https://www.arbeitnow.com/api/job-board-api'


def map_job_type(job):
    title = (job.get('title') or '').lower()
    raw_job_types = job.get('job_types')
    job_types = ' '.join(
        job_type for job_type in raw_job_types
        if isinstance(job_type, str)
    ).lower() if isinstance(raw_job_types, list) else ''

    if job.get('remote'):
        return 'REMOTE'
    if 'intern' in title or 'intern' in job_types:
        return 'INTERN'
    if 'part-time' in title or 'part time' in title or 'part-time' in job_types:
        return 'PART'
    return 'FULL'


def normalize_job(job):
    if not isinstance(job, dict):
        return None

    company_value = job.get('company_name')
    title_value = job.get('title')
    url_value = job.get('url')
    company_name = company_value.strip() if isinstance(company_value, str) else ''
    title = title_value.strip() if isinstance(title_value, str) else ''
    external_url = url_value.strip() if isinstance(url_value, str) else ''
    if not company_name or not title or not external_url.startswith(('http://', 'https://')):
        return None

    tags = job.get('tags')
    if not isinstance(tags, list):
        tags = []
    raw_description = job.get('description')
    description = strip_tags(raw_description if isinstance(raw_description, str) else '').strip()
    location = job.get('location')
    salary = job.get('salary')

    return {
        'company': company_name[:100],
        'title': title[:150],
        'location': 'Remote' if job.get('remote') else (
            location.strip() if isinstance(location, str) and location.strip() else 'Not specified'
        ),
        'external_url': external_url,
        'description': description or 'No description provided.',
        'job_type': map_job_type(job),
        'skills': ', '.join(tag.strip() for tag in tags if isinstance(tag, str))[:200] or 'Not specified',
        'salary_range': (salary if isinstance(salary, str) and salary else 'Not specified')[:50],
    }


def fetch_jobs():
    response = requests.get(API_URL, params={'page': 1}, timeout=20)
    response.raise_for_status()
    payload = response.json()
    jobs = payload.get('data') if isinstance(payload, dict) else None
    if not isinstance(jobs, list):
        raise ValueError('The jobs API returned an unexpected response.')
    return jobs


def seed():
    api_jobs = fetch_jobs()
    normalized_jobs = [normalized for job in api_jobs if (normalized := normalize_job(job))]
    if not normalized_jobs:
        raise ValueError('The jobs API returned no usable listings.')

    JobPosting.objects.filter(external_url__isnull=False).update(is_active=False)
    created_count = 0
    updated_count = 0

    for job in normalized_jobs:
        company, _ = Company.objects.get_or_create(
            name=job['company'],
            defaults={
                'location': job['location'],
                'website': '',
                'logo_url': '',
            },
        )
        _, created = JobPosting.objects.update_or_create(
            external_url=job['external_url'],
            defaults={
                'company': company,
                'title': job['title'],
                'job_type': job['job_type'],
                'required_skills': job['skills'],
                'salary_range': job['salary_range'],
                'description': job['description'],
                'is_active': True,
            },
        )
        if created:
            created_count += 1
        else:
            updated_count += 1

    print(f'Imported {created_count} new jobs and refreshed {updated_count} existing jobs from Arbeitnow.')
    print(f'Active API listings: {JobPosting.objects.filter(is_active=True, external_url__isnull=False).count()}')


if __name__ == '__main__':
    seed()
