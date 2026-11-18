from django.urls import path
from . import views

urlpatterns = [
    path('', views.JobListView.as_view(), name='job_list'),
    path('job/<int:pk>/', views.JobDetailView.as_view(), name='job_detail'),
    path('job/<int:job_id>/apply/', views.ApplicationCreateView.as_view(), name='job_apply'),
    path('dashboard/', views.RecruiterDashboardView.as_view(), name='recruiter_dashboard'),
    path('application/<int:application_id>/status/', views.UpdateApplicationStatusView.as_view(), name='update_application_status'),
    path('login/', views.RecruiterLoginView.as_view(), name='login'),
    path('logout/', views.RecruiterLogoutView.as_view(), name='logout'),
]
