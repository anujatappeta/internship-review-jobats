from django.contrib import admin
from .models import Candidate, Company, JobApplication, JobPosting

admin.site.register((Candidate, Company, JobApplication, JobPosting))
