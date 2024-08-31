from django.urls import path
from .views import HomeView, DashboardView, CourseView, StudentView, LecturerView, TeachingRecordView, \
    TeachingRecordDetailView, CourseDetailView, StudentDetailView, LecturerDetailView, LecturerAddView, StudentAddView, \
    CourseAddView, CourseUpdateView, StudentUpdateView, LecturerUpdateView

# Create your urls here
app_name = 'core'

urlpatterns = [
    path('', HomeView.as_view(), name='home'),
    path('app/', DashboardView.as_view(), name='dashboard'),
    # Course URLs
    path('app/courses/', CourseView.as_view(), name='courses'),
    path('app/courses/<int:pk>/<slug:slug>', CourseDetailView.as_view(), name='course_detail'),
    path('app/courses/add/', CourseAddView.as_view(), name='course_add'),
    path('app/courses/<int:pk>/<slug:slug>/edit', CourseUpdateView.as_view(), name='course_update'),

    # Student URLs
    path('app/students/', StudentView.as_view(), name='students'),
    path('app/students/<int:pk>/<slug:slug>/', StudentDetailView.as_view(), name='student_detail'),
    path('app/students/add', StudentAddView.as_view(), name='student_add'),
    path('app/students/<int:pk>/<slug:slug>/edit/', StudentUpdateView.as_view(), name='student_update'),

    # Lecturer URLs
    path('app/lecturers/', LecturerView.as_view(), name='lecturers'),
    path('app/lecturers/<int:pk>/<slug:slug>/', LecturerDetailView.as_view(), name='lecturer_detail'),
    path('app/lecturers/add/', LecturerAddView.as_view(), name='lecturer_add'),
    path('app/lecturers/<int:pk>/<slug:slug>/edit', LecturerUpdateView.as_view(), name='lecturer_update'),

    # Teaching Record URLs
    path('app/records/', TeachingRecordView.as_view(), name='records'),
    path('app/records/<int:pk>/<slug:slug>/', TeachingRecordDetailView.as_view(),
         name='record_detail'),
]
