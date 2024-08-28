from django.urls import path
from .views import HomeView, DashboardView, CourseView, StudentView, LecturerView, TeachingRecordView, \
    TeachingRecordDetailView, CourseDetailView

# Create your urls here
app_name = 'core'

urlpatterns = [
    path('', HomeView.as_view(), name='home'),
    path('app/', DashboardView.as_view(), name='dashboard'),
    # Course URLs
    path('app/courses/', CourseView.as_view(), name='courses'),
    path('app/courses/<int:pk>/<slug:slug>', CourseDetailView.as_view(), name='course_detail'),
    # Student URLs
    path('app/students/', StudentView.as_view(), name='students'),
    # Lecturer URLs
    path('app/lecturers/', LecturerView.as_view(), name='lecturers'),
    # Teaching Record URLs
    path('app/records/', TeachingRecordView.as_view(), name='records'),
    path('app/records/<int:pk>/<slug:slug>', TeachingRecordDetailView.as_view(),
         name='record_detail'),
]
