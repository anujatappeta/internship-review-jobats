import json
from django.shortcuts import render, get_object_or_404
from django.views.generic import ListView, DetailView, View
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.views import LoginView, LogoutView
from django.http import JsonResponse
from django.db import transaction
from django.urls import reverse_lazy
from django.db.models import Q

from .models import Company, JobPosting, Candidate, JobApplication
from .forms import CandidateForm, JobApplicationForm

class JobListView(ListView):
    model = JobPosting
    template_name = 'jobs/job_list.html'
    context_object_name = 'jobs'
    
    def get_queryset(self):
        queryset = JobPosting.objects.filter(
            is_active=True,
            external_url__isnull=False,
        ).select_related('company').order_by('-posted_date')
        
        # GET parameter filtering
        q = self.request.GET.get('q')
        location = self.request.GET.get('location')
        job_type = self.request.GET.get('job_type')
        skill = self.request.GET.get('skill')
        
        if q:
            queryset = queryset.filter(
                Q(title__icontains=q) | 
                Q(company__name__icontains=q) | 
                Q(description__icontains=q)
            )
        if location:
            queryset = queryset.filter(company__location__icontains=location)
        if job_type:
            queryset = queryset.filter(job_type=job_type)
        if skill:
            queryset = queryset.filter(required_skills__icontains=skill)
            
        return queryset
        
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # Unique list of locations for filters
        context['locations'] = Company.objects.filter(
            jobs__is_active=True,
            jobs__external_url__isnull=False,
        ).exclude(location="").values_list('location', flat=True).distinct().order_by('location')
        context['job_types'] = JobPosting.JOB_TYPES
        context['candidate_form'] = CandidateForm()
        context['application_form'] = JobApplicationForm()
        return context

class JobDetailView(DetailView):
    model = JobPosting
    template_name = 'jobs/job_detail.html'
    context_object_name = 'job'
    
    def get_queryset(self):
        return JobPosting.objects.filter(
            is_active=True,
            external_url__isnull=False,
        ).select_related('company')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['candidate_form'] = CandidateForm()
        context['application_form'] = JobApplicationForm()
        # Get up to 3 similar jobs from same company
        context['similar_jobs'] = JobPosting.objects.filter(
            company=self.object.company,
            is_active=True,
            external_url__isnull=False,
        ).exclude(id=self.object.id)[:3]
        return context

class ApplicationCreateView(View):
    def post(self, request, job_id):
        job = get_object_or_404(
            JobPosting,
            id=job_id,
            is_active=True,
            external_url__isnull=False,
        )
        
        candidate_form = CandidateForm(request.POST)
        application_form = JobApplicationForm(request.POST)
        
        is_ajax = request.headers.get('x-requested-with') == 'XMLHttpRequest' or request.POST.get('ajax') == 'true'
        
        if candidate_form.is_valid() and application_form.is_valid():
            email = candidate_form.cleaned_data['email']
            with transaction.atomic():
                candidate, created = Candidate.objects.get_or_create(
                    email=email,
                    defaults={
                        'full_name': candidate_form.cleaned_data['full_name'],
                        'phone': candidate_form.cleaned_data['phone'],
                        'portfolio_url': candidate_form.cleaned_data['portfolio_url'],
                        'skills': candidate_form.cleaned_data['skills'],
                    }
                )

                if not created:
                    candidate.full_name = candidate_form.cleaned_data['full_name']
                    candidate.phone = candidate_form.cleaned_data['phone']
                    candidate.portfolio_url = candidate_form.cleaned_data['portfolio_url']
                    candidate.skills = candidate_form.cleaned_data['skills']
                    candidate.save()

                _, app_created = JobApplication.objects.get_or_create(
                    job=job,
                    candidate=candidate,
                    defaults={
                        'cover_letter': application_form.cleaned_data['cover_letter'],
                        'status': 'APPLIED'
                    }
                )

                if not app_created:
                    error_msg = 'You have already applied for this job posting.'
                    if is_ajax:
                        return JsonResponse({'success': False, 'error': error_msg}, status=400)
                    return render(request, 'jobs/job_detail.html', {
                        'job': job,
                        'candidate_form': candidate_form,
                        'application_form': application_form,
                        'error': error_msg
                    })

                if is_ajax:
                    return JsonResponse({
                        'success': True,
                        'message': 'Your application has been submitted successfully!'
                    })
                return render(request, 'jobs/job_detail.html', {
                    'job': job,
                    'success_message': 'Your application has been submitted successfully!'
                })
        else:
            # Bundle errors
            errors = {}
            for field, err in candidate_form.errors.items():
                errors[field] = err[0]
            for field, err in application_form.errors.items():
                errors[field] = err[0]
                
            if is_ajax:
                return JsonResponse({'success': False, 'errors': errors}, status=400)
            return render(request, 'jobs/job_detail.html', {
                'job': job,
                'candidate_form': candidate_form,
                'application_form': application_form
            })

class RecruiterDashboardView(LoginRequiredMixin, ListView):
    model = JobApplication
    template_name = 'jobs/recruiter_dashboard.html'
    context_object_name = 'applications'
    login_url = reverse_lazy('login')
    
    def get_queryset(self):
        queryset = JobApplication.objects.select_related('job', 'candidate', 'job__company').order_by('-applied_at')
        job_id = self.request.GET.get('job_filter')
        if job_id:
            queryset = queryset.filter(job_id=job_id)
        return queryset
        
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        qs = self.get_queryset()
        
        # Categorize by pipeline status
        stages = {
            'APPLIED': [],
            'REVIEW': [],
            'SHORTLIST': [],
            'REJECTED': []
        }
        for app in qs:
            if app.status in stages:
                stages[app.status].append(app)
                
        context['stages'] = stages
        context['job_postings'] = JobPosting.objects.filter(
            is_active=True,
            external_url__isnull=False,
        ).order_by('title')
        context['selected_job_id'] = self.request.GET.get('job_filter', '')
        
        # Statistics
        context['total_apps'] = qs.count()
        context['applied_count'] = len(stages['APPLIED'])
        context['review_count'] = len(stages['REVIEW'])
        context['shortlist_count'] = len(stages['SHORTLIST'])
        context['rejected_count'] = len(stages['REJECTED'])
        
        return context

class UpdateApplicationStatusView(LoginRequiredMixin, View):
    login_url = reverse_lazy('login')
    
    def post(self, request, application_id):
        application = get_object_or_404(JobApplication, id=application_id)
        
        # Parse body for status
        try:
            data = json.loads(request.body)
            new_status = data.get('status')
        except json.JSONDecodeError:
            new_status = request.POST.get('status')
            
        valid_statuses = [stage[0] for stage in JobApplication.STATUS_STAGES]
        if new_status not in valid_statuses:
            return JsonResponse({'success': False, 'error': 'Invalid status.'}, status=400)
            
        application.status = new_status
        application.save()
        
        return JsonResponse({
            'success': True,
            'message': f'Status updated to {application.get_status_display()}',
            'status': application.status,
            'status_display': application.get_status_display()
        })

class RecruiterLoginView(LoginView):
    template_name = 'jobs/login.html'
    redirect_authenticated_user = True
    
    def get_success_url(self):
        return reverse_lazy('recruiter_dashboard')

class RecruiterLogoutView(LogoutView):
    next_page = reverse_lazy('job_list')
