from collections import defaultdict
from datetime import timedelta

from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import get_object_or_404
from django.urls import reverse_lazy
from django.utils.html import format_html
from django.views.generic import TemplateView, ListView, DetailView, CreateView, UpdateView

from .forms import CourseForm, LecturerForm, StudentForm, TeachingRecordForm
from .mixins import CommonContextMixin, ClassLevelAccessMixin
from .models import Course, Student, Lecturer, TeachingRecord, CourseDelegate, CourseAttendance, \
    ClassLevel, Attendance, ClassLevelUser
from .utils import group_model_items_by_week


# Create your views here.
class HomeView(TemplateView):
    template_name = 'core/index.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['levels_count'] = ClassLevel.objects.all().count()
        context['course_attendance_count'] = Attendance.objects.all().count()
        context['courses_count'] = Course.objects.all().count()
        context['lecturers_count'] = Lecturer.objects.all().count()
        context['students_count'] = Student.objects.all().count()
        return context


class LevelView(LoginRequiredMixin, ListView):
    model = ClassLevel
    template_name = 'core/dashboard/levels.html'
    context_object_name = 'levels'
    paginate_by = 25

    def get_queryset(self):
        if self.request.user.is_superuser:
            return ClassLevel.objects.all()
        return ClassLevel.objects.filter(class_level_users__user=self.request.user)


# Dashboard views
def group_items_by_week(attendances):
    grouped_attendances = defaultdict(list)
    for attendance in attendances.order_by('created_at'):
        # Calculate the start of the week (Monday) for each item
        week_start = attendance.created_at - timedelta(days=attendance.created_at.weekday())
        week_end = week_start + timedelta(days=6)

        # Format the week range as "Mon 19 Aug - Sun 25 Aug"
        week_range = f"{week_start.strftime('%a %d %b')} - {week_end.strftime('%a %d %b %Y')}"

        # Group items by this week range
        grouped_attendances[week_range].append(attendance)
    return grouped_attendances


# core/views.py
class DashboardView(LoginRequiredMixin, CommonContextMixin, ClassLevelAccessMixin, DetailView):
    model = ClassLevel
    template_name = 'core/dashboard/dashboard.html'
    context_object_name = 'level'

    def get_object(self, queryset=None):
        return get_object_or_404(self.model, id=self.kwargs['level_pk'], slug=self.kwargs['level_slug'])

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        grouped_attendances = group_items_by_week(Attendance.objects.filter(class_level=self.kwargs['level_pk']))
        for week, attendances in grouped_attendances.items():
            for attendance in attendances:
                attendance.course_delegate = CourseDelegate.objects.filter(course=attendance.course,
                                                                           role='delegate').first()
                attendance.course_assistant = CourseDelegate.objects.filter(course=attendance.course,
                                                                            role='assistant').first()
                attendance.enrollment_count = CourseAttendance.objects.filter(attendance=attendance).count()
        context['grouped_attendances'] = dict(grouped_attendances)
        return context


class DashboardDetailView(LoginRequiredMixin, CommonContextMixin, DetailView):
    model = ClassLevel
    template_name = 'core/dashboard/dashboard_details.html'
    context_object_name = 'level'

    def get_object(self, queryset=None):
        return get_object_or_404(self.model, id=self.kwargs['level_pk'], slug=self.kwargs['level_slug'])

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['users'] = ClassLevelUser.objects.filter(class_level=self.kwargs['level_pk'])
        return context


class AttendanceDetailView(LoginRequiredMixin, CommonContextMixin, DetailView):
    model = Attendance
    template_name = 'core/attendance/attendance_details.html'
    context_object_name = 'attendance'

    def get_object(self, queryset=None):
        return get_object_or_404(
            self.model,
            class_level=self.kwargs['level_pk'],
            class_level__slug=self.kwargs['level_slug'],
            id=self.kwargs['pk']
        )

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['course_delegates'] = CourseDelegate.objects.filter(
            course=self.object.course,
            student__is_delegate=True
        )
        context['enrollments'] = CourseAttendance.objects.filter(attendance=self.object,
                                                                 attendance__class_level=self.kwargs[
                                                                     'level_pk']).order_by('created_at')
        return context


class CourseView(LoginRequiredMixin, CommonContextMixin, ListView):
    model = Course
    template_name = 'core/courses/courses.html'
    paginate_by = 25
    context_object_name = 'courses'

    def get_queryset(self):
        return Course.objects.filter(class_level=self.kwargs['level_pk']).order_by('title')

    def post(self, request, *args, **kwargs):
        if 'delete_course' in request.POST:
            course_id = request.POST.get('course_id')
            course = Course.objects.get(id=course_id)
            course.delete()
            message = format_html(
                '<strong>{} {}</strong> was deleted successfully.',
                course.code,
                course.title
            )
            messages.success(request, message)
        return self.get(request, *args, **kwargs)


class CourseDetailView(LoginRequiredMixin, CommonContextMixin, DetailView):
    model = Course
    template_name = 'core/courses/course_details.html'
    context_object_name = 'course'

    def get_object(self, queryset=None):
        return get_object_or_404(self.model, id=self.kwargs['pk'], slug=self.kwargs['slug'])

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        course = self.get_object()
        context['delegates'] = CourseDelegate.objects.filter(course=course)
        return context


class CourseAddView(LoginRequiredMixin, CommonContextMixin, CreateView):
    model = Course
    template_name = 'core/courses/course_add.html'
    context_object_name = 'form'
    form_class = CourseForm

    def get_success_url(self):
        return reverse_lazy('core:courses', kwargs={'level_pk': self.kwargs['level_pk']})

    def get_form(self, form_class=None):
        form = super().get_form(form_class)
        # Get the class level based on the URL parameter
        level_pk = self.kwargs.get('level_pk')
        class_level = ClassLevel.objects.get(pk=level_pk)

        # Set the class_level in the form
        form.fields['class_level'].initial = class_level
        return form

    def form_valid(self, form):
        # Get the class level from the URL
        level_pk = self.kwargs.get('level_pk')
        class_level = ClassLevel.objects.get(pk=level_pk)

        # Set the class_level for the student instance
        form.instance.class_level = class_level

        form.save()
        message = format_html(
            'Course added successfully.<br><a href="{}" class="font-bold underline">View</a>',
            reverse_lazy('core:course_detail', kwargs={'level_pk': self.kwargs.get('level_pk'), 'pk': form.instance.pk,
                                                       'slug': form.instance.slug})
        )
        messages.success(
            self.request,
            message
        )
        messages.info(
            self.request,
            'A teaching record has also been created for this course.'
        )
        return super().form_valid(form)

    def form_invalid(self, form):
        messages.error(
            self.request,
            format_html(
                'An error occurred while adding the course.<br>Please try again.'
            )
        )
        return super().form_invalid(form)


class CourseUpdateView(LoginRequiredMixin, CommonContextMixin, UpdateView):
    model = Course
    template_name = 'core/courses/course_update.html'
    context_object_name = 'form'
    form_class = CourseForm

    def get_object(self, queryset=None):
        queryset = self.get_queryset()
        return queryset.get(id=self.kwargs['pk'], slug=self.kwargs['slug'])

    def get_success_url(self):
        return reverse_lazy('core:courses', kwargs={'level_pk': self.kwargs['level_pk']})

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['course'] = self.get_object()
        return context

    def form_valid(self, form):
        form.save()
        message = format_html(
            'Course updated successfully.<br><a href="{}" class="font-bold underline">View</a>',
            reverse_lazy('core:course_detail', kwargs={'level_pk': self.kwargs.get('level_pk'), 'pk': form.instance.pk,
                                                       'slug': form.instance.slug})
        )
        messages.success(
            self.request,
            message
        )
        return super().form_valid(form)

    def form_invalid(self, form):
        messages.error(
            self.request,
            format_html(
                'An error occurred while updating the course.<br>Please try again.'
            )
        )
        return super().form_invalid(form)


class StudentView(LoginRequiredMixin, CommonContextMixin, ListView):
    model = Student
    template_name = 'core/students/students.html'
    paginate_by = 25
    context_object_name = 'students'

    def get_queryset(self):
        return self.model.objects.filter(class_level=self.kwargs['level_pk']).order_by('name')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['delegates'] = Student.objects.filter(is_delegate=True).order_by('name')
        return context

    def post(self, request, *args, **kwargs):
        if 'delete_student' in request.POST or 'delete_delegate' in request.POST:
            student_id = request.POST.get('student_id')
            student = Student.objects.get(id=student_id)
            student.delete()
            message = format_html(
                '<strong>{}</strong> was deleted successfully.',
                student.name
            )
            messages.success(request, message)
        return self.get(request, *args, **kwargs)


class StudentDetailView(LoginRequiredMixin, CommonContextMixin, DetailView):
    model = Student
    template_name = 'core/students/student_details.html'
    context_object_name = 'student'

    def get_object(self, queryset=None):
        return get_object_or_404(self.model, id=self.kwargs['pk'], slug=self.kwargs['slug'])


class StudentAddView(LoginRequiredMixin, CommonContextMixin, CreateView):
    model = Student
    template_name = 'core/students/student_add.html'
    context_object_name = 'form'
    form_class = StudentForm

    def get_success_url(self):
        return reverse_lazy('core:students', kwargs={'level_pk': self.kwargs['level_pk']})

    def get_form(self, form_class=None):
        form = super().get_form(form_class)
        # Get the class level based on the URL parameter
        level_pk = self.kwargs.get('level_pk')
        class_level = ClassLevel.objects.get(pk=level_pk)

        # Set the class_level in the form
        form.fields['class_level'].initial = class_level
        return form

    def form_valid(self, form):
        # Get the class level from the URL
        level_pk = self.kwargs.get('level_pk')
        class_level = ClassLevel.objects.get(pk=level_pk)

        # Set the class_level for the student instance
        form.instance.class_level = class_level

        form.save()
        message = format_html(
            'Student added successfully.<br><a href="{}" class="font-bold underline">View</a>',
            reverse_lazy('core:student_detail',
                         kwargs={'level_pk': level_pk, 'pk': form.instance.pk, 'slug': form.instance.slug})
        )
        messages.success(
            self.request,
            message
        )
        return super().form_valid(form)

    def form_invalid(self, form):
        messages.error(
            self.request,
            format_html(
                'An error occurred while adding the student.<br>Please try again.'
            )
        )
        return super().form_invalid(form)


class StudentUpdateView(LoginRequiredMixin, CommonContextMixin, UpdateView):
    model = Student
    template_name = 'core/students/student_update.html'
    context_object_name = 'form'
    form_class = StudentForm

    def get_object(self, queryset=None):
        queryset = self.get_queryset()
        return queryset.get(id=self.kwargs['pk'], slug=self.kwargs['slug'])

    def get_success_url(self):
        return reverse_lazy('core:students', kwargs={'level_pk': self.kwargs['level_pk']})

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['student'] = self.get_object()
        return context

    def form_valid(self, form):
        form.save()
        message = format_html(
            'Student updated successfully.<br><a href="{}" class="font-bold underline">View</a>',
            reverse_lazy('core:student_detail', kwargs={'level_pk': self.kwargs.get('level_pk'), 'pk': form.instance.pk,
                                                        'slug': form.instance.slug})
        )
        messages.success(
            self.request,
            message
        )
        return super().form_valid(form)

    def form_invalid(self, form):
        messages.error(
            self.request,
            format_html(
                'An error occurred while updating the student.<br>Please try again.'
            )
        )
        return super().form_invalid(form)


class LecturerView(LoginRequiredMixin, CommonContextMixin, ListView):
    model = Lecturer
    template_name = 'core/lecturers/lecturers.html'
    paginate_by = 25
    context_object_name = 'lecturers'

    def get_queryset(self):
        return self.model.objects.filter(course_lecturer__class_level=self.kwargs['level_pk']).order_by('name')

    def post(self, request, *args, **kwargs):
        if 'delete_lecturer' in request.POST:
            lecturer_id = request.POST.get('lecturer_id')
            lecturer = Lecturer.objects.get(id=lecturer_id)
            lecturer.delete()
            message = format_html(
                '<strong>{}</strong> was deleted successfully.',
                lecturer.name
            )
            messages.success(request, message)
        return self.get(request, *args, **kwargs)


class LecturerDetailView(LoginRequiredMixin, CommonContextMixin, DetailView):
    model = Lecturer
    template_name = 'core/lecturers/lecturer_details.html'
    context_object_name = 'lecturer'

    def get_object(self, queryset=None):
        return get_object_or_404(self.model, id=self.kwargs['pk'], slug=self.kwargs['slug'])


class LecturerAddView(LoginRequiredMixin, CommonContextMixin, CreateView):
    model = Lecturer
    template_name = 'core/lecturers/lecturer_add.html'
    context_object_name = 'form'
    form_class = LecturerForm

    def get_success_url(self):
        return reverse_lazy('core:lecturers', kwargs={'level_pk': self.kwargs['level_pk']})

    def form_valid(self, form):
        form.save()
        message = format_html(
            'Lecturer added successfully.<br><a href="{}" class="font-bold underline">View</a>',
            reverse_lazy('core:lecturer_detail',
                         kwargs={'level_pk': self.kwargs.get('level_pk'), 'pk': form.instance.pk,
                                 'slug': form.instance.slug})
        )
        messages.success(
            self.request,
            message
        )
        return super().form_valid(form)

    def form_invalid(self, form):
        messages.error(
            self.request,
            format_html(
                'An error occurred while adding the lecturer.<br>Please try again.'
            )
        )
        return super().form_invalid(form)


class LecturerUpdateView(LoginRequiredMixin, CommonContextMixin, UpdateView):
    model = Lecturer
    template_name = 'core/lecturers/lecturer_update.html'
    context_object_name = 'form'
    form_class = LecturerForm

    def get_object(self, queryset=None):
        queryset = self.get_queryset()
        return queryset.get(id=self.kwargs['pk'], slug=self.kwargs['slug'])

    def get_success_url(self):
        return reverse_lazy('core:lecturers', kwargs={'level_pk': self.kwargs['level_pk']})

    def get_queryset(self):
        return Lecturer.objects.all()

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['lecturer'] = self.get_object()
        return context

    def form_valid(self, form):
        form.save()
        message = format_html(
            'Lecturer updated successfully.<br><a href="{}" class="font-bold underline">View</a>',
            reverse_lazy('core:lecturer_detail',
                         kwargs={'level_pk': self.kwargs.get('level_pk'), 'pk': form.instance.pk,
                                 'slug': form.instance.slug})
        )
        messages.success(
            self.request,
            message
        )
        return super().form_valid(form)

    def form_invalid(self, form):
        messages.error(
            self.request,
            format_html(
                'An error occurred while updating the lecturer.<br>Please try again.'
            )
        )
        return super().form_invalid(form)


class TeachingRecordView(LoginRequiredMixin, CommonContextMixin, ListView):
    model = TeachingRecord
    template_name = 'core/records/records.html'
    paginate_by = 25
    context_object_name = 'records'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        records_queryset = TeachingRecord.objects.filter(
            attendance__class_level=self.kwargs['level_pk']
        )
        grouped_records = group_model_items_by_week(records_queryset)
        for week, records in grouped_records.items():
            for record in records:
                record.course_title = record.attendance.course.title
                record.course_lecturer_name = record.attendance.course.lecturer.name
                record.course_delegate = CourseDelegate.objects.filter(course=record.attendance.course,
                                                                       role='delegate').first()
                record.course_assistant = CourseDelegate.objects.filter(
                    course=record.attendance.course, role='assistant').first()
        context['grouped_records'] = dict(grouped_records)
        return context


class TeachingRecordDetailView(LoginRequiredMixin, CommonContextMixin, DetailView):
    model = TeachingRecord
    template_name = 'core/records/record_details.html'
    context_object_name = 'record'

    def get_object(self, queryset=None):
        return get_object_or_404(
            self.model,
            attendance__course__class_level_id=self.kwargs['level_pk'],
            id=self.kwargs['pk'],
            attendance__course__slug=self.kwargs['slug']
        )

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        class_level_id = self.kwargs['level_pk']
        context['course_delegates'] = CourseDelegate.objects.filter(
            course=self.object.attendance.course,
            student__is_delegate=True,
            course__class_level_id=class_level_id
        )
        context['enrollments'] = CourseAttendance.objects.filter(
            attendance__course=self.object.attendance.course,
            attendance__course__class_level_id=class_level_id
        ).count()
        return context


class TeachingRecordUpdateView(LoginRequiredMixin, CommonContextMixin, UpdateView):
    model = TeachingRecord
    template_name = 'core/records/record_update.html'
    context_object_name = 'form'
    form_class = TeachingRecordForm

    def get_object(self, queryset=None):
        queryset = self.get_queryset()
        return queryset.get(id=self.kwargs['pk'], teaching_record_attendance__course__slug=self.kwargs['slug'])

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['record'] = self.get_object()
        return context

    def get_success_url(self):
        return reverse_lazy('core:record_detail',
                            kwargs={'level_pk': self.kwargs.get('level_pk'), 'pk': self.object.pk,
                                    'slug': self.object.teaching_record_attendance.course.slug})

    def form_valid(self, form):
        form.save()
        message = format_html(
            'Teaching record updated successfully.',
        )
        messages.success(
            self.request,
            message
        )
        return super().form_valid(form)

    def form_invalid(self, form):
        messages.error(
            self.request,
            format_html(
                'An error occurred while updating the record.<br>Please try again.'
            )
        )
        return super().form_invalid(form)
