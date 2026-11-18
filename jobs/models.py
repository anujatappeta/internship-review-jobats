from django.db import models

class Company(models.Model):
    name = models.CharField(max_length=100)
    website = models.URLField(blank=True)
    location = models.CharField(max_length=500)
    logo_url = models.URLField(blank=True, default="https://via.placeholder.com/100")

    def __str__(self):
        return self.name
        
    class Meta:
        verbose_name_plural = "Companies"

class JobPosting(models.Model):
    JOB_TYPES = [
        ('FULL', 'Full-Time'),
        ('PART', 'Part-Time'),
        ('REMOTE', 'Remote Work'),
        ('INTERN', 'Internship'),
    ]
    company = models.ForeignKey(Company, on_delete=models.CASCADE, related_name='jobs')
    title = models.CharField(max_length=150)
    job_type = models.CharField(max_length=10, choices=JOB_TYPES)
    required_skills = models.CharField(max_length=200, help_text="Comma separated e.g. Python, Django, SQL")
    salary_range = models.CharField(max_length=50, default="Competitive")
    description = models.TextField()
    external_url = models.URLField(blank=True, null=True, unique=True)
    is_active = models.BooleanField(default=True)
    posted_date = models.DateField(auto_now_add=True)

    def __str__(self):
        return f"{self.title} at {self.company.name}"

    @property
    def skills_list(self):
        if self.required_skills:
            return [s.strip() for s in self.required_skills.split(',') if s.strip()]
        return []


class Candidate(models.Model):
    full_name = models.CharField(max_length=100)
    email = models.EmailField(unique=True)
    phone = models.CharField(max_length=15)
    portfolio_url = models.URLField(blank=True)
    skills = models.CharField(max_length=200)

    def __str__(self):
        return f"{self.full_name} ({self.email})"

    @property
    def skills_list(self):
        if self.skills:
            return [s.strip() for s in self.skills.split(',') if s.strip()]
        return []


class JobApplication(models.Model):
    STATUS_STAGES = [
        ('APPLIED', 'Application Received'),
        ('REVIEW', 'Under HR Review'),
        ('SHORTLIST', 'Shortlisted for Interview'),
        ('REJECTED', 'Not Selected'),
    ]
    job = models.ForeignKey(JobPosting, on_delete=models.CASCADE, related_name='applications')
    candidate = models.ForeignKey(Candidate, on_delete=models.CASCADE, related_name='applications')
    cover_letter = models.TextField(blank=True)
    status = models.CharField(max_length=15, choices=STATUS_STAGES, default='APPLIED')
    applied_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ['job', 'candidate']

    def __str__(self):
        return f"{self.candidate.full_name} -> {self.job.title} ({self.get_status_display()})"
