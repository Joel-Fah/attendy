from django.contrib import messages
from django.shortcuts import get_object_or_404, redirect
from django.views.generic.base import ContextMixin

from .models import Course, Student, Lecturer, TeachingRecord, ClassLevel, ClassLevelUser, Attendance


class CommonContextMixin(ContextMixin):
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['level'] = get_object_or_404(ClassLevel, id=self.kwargs['level_pk'])
        context['course_attendance_count'] = Attendance.objects.filter(class_level=self.kwargs['level_pk']).count()
        context['courses'] = Course.objects.filter(class_level=self.kwargs['level_pk']).order_by('title')
        context['students'] = Student.objects.filter(class_level=self.kwargs['level_pk']).order_by('name')
        context['lecturers'] = Lecturer.objects.all().order_by('name')
        context['teaching_records'] = TeachingRecord.objects.filter(attendance__class_level=self.kwargs['level_pk'])
        return context


class ClassLevelAccessMixin:
    def dispatch(self, request, *args, **kwargs):
        # Get the ClassLevel instance using the primary key (pk) and slug from the URL
        class_level = get_object_or_404(ClassLevel, pk=self.kwargs.get('level_pk'), slug=self.kwargs.get('level_slug'))

        # Check if the user is authorized to access this class
        if request.user.is_superuser or ClassLevelUser.objects.filter(user=request.user,
                                                                      class_level=class_level).exists():
            return super().dispatch(request, *args, **kwargs)

        # Add an error message and redirect to the previous page
        messages.error(request, "Sorry dear but you don't have access to this class.")
        return redirect(request.META.get('HTTP_REFERER', 'core:home'))
