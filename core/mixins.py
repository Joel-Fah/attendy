from django.views.generic.base import ContextMixin
from .models import Course, Student, Lecturer, TeachingRecord, CourseAttendance


class CommonContextMixin(ContextMixin):
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['course_attendance_count'] = CourseAttendance.objects.count()
        context['courses'] = Course.objects.all().order_by('title')
        context['students'] = Student.objects.all().order_by('name')
        context['lecturers'] = Lecturer.objects.all().order_by('name')
        context['teaching_records'] = TeachingRecord.objects.all()
        return context
