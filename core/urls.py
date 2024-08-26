from django.urls import path
from .views import HomeView, DashboardView, CourseView, StudentView, LecturerView, TeachingRecordView, TeachingRecordDetailView

# Create your urls here
app_name = 'core'

urlpatterns = [
    path('', HomeView.as_view(), name='home'),
    path('app/', DashboardView.as_view(), name='dashboard'),
    path('app/courses/', CourseView.as_view(), name='courses'),
    path('app/students/', StudentView.as_view(), name='students'),
    path('app/lecturers/', LecturerView.as_view(), name='lecturers'),
    path('app/records/', TeachingRecordView.as_view(), name='records'),
    path('app/records/<int:pk>/<slug:slug>', TeachingRecordDetailView.as_view(),
         name='teaching_record_detail'),
]
