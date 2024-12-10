from django.urls import path
from .views import HomeView, DashboardView, CourseView, StudentView, LecturerView, TeachingRecordView, \
    TeachingRecordDetailView, CourseDetailView, StudentDetailView, LecturerDetailView, LecturerAddView, \
    StudentAddView, CourseAddView, CourseUpdateView, StudentUpdateView, LecturerUpdateView, \
    TeachingRecordUpdateView, LevelView, DashboardDetailView, AttendanceDetailView, AttendanceAddView, \
    CourseAttendanceAddView, AttendanceUpdateView, decode_qr, add_student_to_course_attendance, FeedbackView, \
    CourseRegistrationView, CoursePDFView
from .views import handler404, handler500

# Create your urls here
app_name = 'core'

urlpatterns = [
    path('', HomeView.as_view(), name='home'),

    # Class levels URLs
    path('levels/', LevelView.as_view(), name='levels'),

    # Course URLs
    path('app/<int:level_pk>/courses/', CourseView.as_view(), name='courses'),
    path('app/<int:level_pk>/courses/<int:pk>/<slug:slug>', CourseDetailView.as_view(), name='course_detail'),
    path('app/<int:level_pk>/courses/<int:pk>/<slug:slug>/pdf/', CoursePDFView.as_view(), name='course_pdf'),
    path('app/<int:level_pk>/courses/add/', CourseAddView.as_view(), name='course_add'),
    path('app/<int:level_pk>/courses/<int:pk>/<slug:slug>/edit', CourseUpdateView.as_view(), name='course_update'),

    # Student URLs
    path('app/<int:level_pk>/students/', StudentView.as_view(), name='students'),
    path('app/<int:level_pk>/students/<int:pk>/<slug:slug>/', StudentDetailView.as_view(), name='student_detail'),
    path('app/<int:level_pk>/students/add', StudentAddView.as_view(), name='student_add'),
    path('app/<int:level_pk>/students/<int:pk>/<slug:slug>/edit/', StudentUpdateView.as_view(), name='student_update'),

    # Course Registration URLs
    path('app/<int:level_pk>/students/<int:pk>/<slug:slug>/register-courses/', CourseRegistrationView.as_view(),
         name='course_registration'),

    # Lecturer URLs
    path('app/<int:level_pk>/lecturers/', LecturerView.as_view(), name='lecturers'),
    path('app/<int:level_pk>    /lecturers/<int:pk>/<slug:slug>/', LecturerDetailView.as_view(),
         name='lecturer_detail'),
    path('app/<int:level_pk>/lecturers/add/', LecturerAddView.as_view(), name='lecturer_add'),
    path('app/<int:level_pk>/lecturers/<int:pk>/<slug:slug>/edit', LecturerUpdateView.as_view(),
         name='lecturer_update'),

    # Teaching Record URLs
    path('app/<int:level_pk>/records/', TeachingRecordView.as_view(), name='records'),
    path('app/<int:level_pk>/records/<int:pk>/<slug:slug>/', TeachingRecordDetailView.as_view(),
         name='record_detail'),
    path('app/<int:level_pk>/records/<int:pk>/<slug:slug>/edit', TeachingRecordUpdateView.as_view(),
         name='record_update'),

    # Dashboard URLs
    path('app/<int:level_pk>/<slug:level_slug>/', DashboardView.as_view(), name='dashboard'),
    path('app/<int:level_pk>/<slug:level_slug>/overview/', DashboardDetailView.as_view(), name='dashboard_detail'),

    # Attendance URLs
    path('app/<int:level_pk>/<slug:level_slug>/attendance/<int:pk>/', AttendanceDetailView.as_view(),
         name='attendance_detail'),
    path('app/<int:level_pk>/<slug:level_slug>/attendance/<int:pk>/edit/', AttendanceUpdateView.as_view(),
         name='attendance_update'),
    path('app/<int:level_pk>/<slug:level_slug>/attendance/add/', AttendanceAddView.as_view(), name='attendance_add'),

    # Enrollment URLs
    path('app/<int:level_pk>/<slug:level_slug>/attendance/<int:pk>/admit/', CourseAttendanceAddView.as_view(),
         name='enroll_add'),
    path('app/<int:level_pk>/<slug:level_slug>/attendance/<int:pk>/scan/', decode_qr, name='decode_qr'),
    path('app/<int:level_pk>/<slug:level_slug>/attendance/<int:pk>/scan/admit/', add_student_to_course_attendance,
         name='add_student_to_course_attendance'),

    # Feedback URLs
    path('app/feedback/', FeedbackView.as_view(), name='feedback'), 
]
