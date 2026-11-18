from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth.models import User
import json
import requests
from unittest.mock import patch

from .models import Company, JobPosting, Candidate, JobApplication

class JobBoardTests(TestCase):
    def setUp(self):
        # Create a test company
        self.company = Company.objects.create(
            name="Acme Corp",
            website="https://acme.org",
            location="Remote (Global)",
            logo_url="https://via.placeholder.com/100"
        )
        
        # Create a test job posting
        self.job = JobPosting.objects.create(
            company=self.company,
            title="Senior Django Developer",
            job_type="REMOTE",
            required_skills="Python, Django, SQL, PostgreSQL",
            salary_range="$130,000 - $160,000",
            description="Acme Corp is looking for a senior backend engineer to join our cloud platform team.",
            external_url="https://jobs.example.com/senior-django-developer",
            is_active=True
        )
        
        # Create a recruiter user
        self.recruiter = User.objects.create_superuser(
            username="admin", 
            email="admin@jobboard.com", 
            password="admin123"
        )
        
        self.client = Client()

    def test_model_string_representations(self):
        # Test Company
        self.assertEqual(str(self.company), "Acme Corp")
        
        # Test JobPosting
        self.assertEqual(str(self.job), "Senior Django Developer at Acme Corp")
        
        # Test Candidate
        candidate = Candidate.objects.create(
            full_name="Jane Doe",
            email="jane.doe@example.com",
            phone="1234567890",
            skills="React, Node"
        )
        self.assertEqual(str(candidate), "Jane Doe (jane.doe@example.com)")
        
        # Test JobApplication
        application = JobApplication.objects.create(
            job=self.job,
            candidate=candidate,
            cover_letter="Interested in the role.",
            status="APPLIED"
        )
        self.assertEqual(
            str(application), 
            "Jane Doe -> Senior Django Developer (Application Received)"
        )

    def test_model_skills_list_property(self):
        # Verify comma splitting behaves correctly
        self.assertEqual(self.job.skills_list, ["Python", "Django", "SQL", "PostgreSQL"])
        
        candidate = Candidate.objects.create(
            full_name="Jane Doe",
            email="jane.doe@example.com",
            phone="1234567890",
            skills="React, Node, TypeScript "
        )
        self.assertEqual(candidate.skills_list, ["React", "Node", "TypeScript"])

    def test_job_list_view(self):
        response = self.client.get(reverse('job_list'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Senior Django Developer")
        self.assertContains(response, "Acme Corp")

    def test_job_list_hides_jobs_without_an_api_source(self):
        JobPosting.objects.create(
            company=self.company,
            title="Unverified job",
            job_type="FULL",
            required_skills="Python",
            description="Not sourced from an API.",
        )

        response = self.client.get(reverse('job_list'))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Senior Django Developer")
        self.assertNotContains(response, "Unverified job")

    def test_job_detail_view(self):
        response = self.client.get(reverse('job_detail', args=[self.job.id]))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Senior Django Developer")
        self.assertContains(response, "Acme Corp is looking for a senior backend engineer")

    def test_job_application_submission_via_ajax(self):
        url = reverse('job_apply', args=[self.job.id])
        data = {
            'full_name': 'Alice Smith',
            'email': 'alice.smith@example.com',
            'phone': '1234567890',
            'portfolio_url': 'https://alicesmith.dev',
            'skills': 'Python, Django',
            'cover_letter': 'I love backend programming.',
            'ajax': 'true'
        }
        
        # Post via ajax
        response = self.client.post(
            url, 
            data, 
            HTTP_X_REQUESTED_WITH='XMLHttpRequest'
        )
        self.assertEqual(response.status_code, 200)
        
        # Check response JSON
        res_json = json.loads(response.content)
        self.assertTrue(res_json['success'])
        self.assertIn('submitted successfully', res_json['message'])
        
        # Verify records created in database
        candidate = Candidate.objects.get(email='alice.smith@example.com')
        self.assertEqual(candidate.full_name, 'Alice Smith')
        self.assertEqual(candidate.phone, '1234567890')
        
        application = JobApplication.objects.get(job=self.job, candidate=candidate)
        self.assertEqual(application.status, 'APPLIED')
        self.assertEqual(application.cover_letter, 'I love backend programming.')

    def test_duplicate_job_application_rejection(self):
        # Apply once
        candidate = Candidate.objects.create(
            full_name="Alice Smith",
            email="alice.smith@example.com",
            phone="1234567890",
            skills="Python, Django"
        )
        JobApplication.objects.create(
            job=self.job,
            candidate=candidate,
            cover_letter="First attempt"
        )
        
        # Apply again
        url = reverse('job_apply', args=[self.job.id])
        data = {
            'full_name': 'Alice Smith',
            'email': 'alice.smith@example.com',
            'phone': '1234567890',
            'portfolio_url': 'https://alicesmith.dev',
            'skills': 'Python, Django',
            'cover_letter': 'Second attempt',
            'ajax': 'true'
        }
        
        response = self.client.post(
            url, 
            data, 
            HTTP_X_REQUESTED_WITH='XMLHttpRequest'
        )
        self.assertEqual(response.status_code, 400)
        
        res_json = json.loads(response.content)
        self.assertFalse(res_json['success'])
        self.assertEqual(res_json['error'], 'You have already applied for this job posting.')

    def test_recruiter_dashboard_auth_enforced(self):
        # Anonymous user should be redirected to login page
        response = self.client.get(reverse('recruiter_dashboard'))
        self.assertEqual(response.status_code, 302)
        self.assertIn(reverse('login'), response.url)

    def test_recruiter_dashboard_access_for_logged_in_recruiter(self):
        self.client.login(username="admin", password="admin123")
        response = self.client.get(reverse('recruiter_dashboard'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "ATS Recruitment Pipeline")

    def test_update_application_status_via_ajax(self):
        candidate = Candidate.objects.create(
            full_name="Bob Miller",
            email="bob@example.com",
            phone="111222333",
            skills="Javascript"
        )
        application = JobApplication.objects.create(
            job=self.job,
            candidate=candidate,
            cover_letter="Cover letter here"
        )
        
        url = reverse('update_application_status', args=[application.id])
        
        # Try without login
        response = self.client.post(
            url, 
            json.dumps({'status': 'REVIEW'}), 
            content_type='application/json'
        )
        self.assertEqual(response.status_code, 302) # Redirects to login
        
        # Log in and update
        self.client.login(username="admin", password="admin123")
        response = self.client.post(
            url, 
            json.dumps({'status': 'REVIEW'}), 
            content_type='application/json',
            HTTP_X_REQUESTED_WITH='XMLHttpRequest'
        )
        self.assertEqual(response.status_code, 200)
        
        res_json = json.loads(response.content)
        self.assertTrue(res_json['success'])
        self.assertEqual(res_json['status'], 'REVIEW')
        
        # Check database
        application.refresh_from_db()
        self.assertEqual(application.status, 'REVIEW')


class JobApiImportTests(TestCase):
    @patch('seed_jobs.requests.get')
    def test_seed_imports_real_api_listings(self, mock_get):
        from seed_jobs import seed

        mock_get.return_value.json.return_value = {
            'data': [{
                'company_name': 'API Company',
                'title': 'Remote Python Developer',
                'description': '<p>Build reliable APIs.</p>',
                'url': 'https://jobs.example.com/python',
                'tags': ['Python', 'Django'],
                'job_types': ['Full-time'],
                'location': 'Worldwide',
                'remote': True,
            }]
        }

        seed()

        job = JobPosting.objects.get(external_url='https://jobs.example.com/python')
        self.assertEqual(job.company.name, 'API Company')
        self.assertEqual(job.job_type, 'REMOTE')
        self.assertEqual(job.description, 'Build reliable APIs.')
        self.assertEqual(JobPosting.objects.filter(is_active=True, external_url__isnull=False).count(), 1)

    def test_seed_fails_without_inserting_fabricated_jobs(self):
        from seed_jobs import seed

        with patch('seed_jobs.requests.get', side_effect=requests.ConnectionError('API unavailable')):
            with self.assertRaises(requests.ConnectionError):
                seed()

        self.assertEqual(JobPosting.objects.count(), 0)
