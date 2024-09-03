from collections import defaultdict
from datetime import timedelta

from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.urls import reverse_lazy
from django.utils.html import format_html
from django.views.generic import TemplateView, ListView, DetailView, CreateView, UpdateView

from .forms import CourseForm, LecturerForm, StudentForm, TeachingRecordForm
from .mixins import CommonContextMixin
from .models import Course, Student, Lecturer, TeachingRecord, StudentDelegate, Enrollment, CourseAttendance


# Create your views here.
class HomeView(CommonContextMixin, TemplateView):
    template_name = 'core/index.html'


# Dashboard views
class DashboardView(LoginRequiredMixin, CommonContextMixin, TemplateView):
    template_name = 'core/dashboard.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        grouped_attendances = group_items_by_week(CourseAttendance)
        for week, attendances in grouped_attendances.items():
            for attendance in attendances:
                attendance.course_title = attendance.course.title
                attendance.course_lecturer_name = attendance.course.lecturer.name
                attendance.course_delegate = StudentDelegate.objects.filter(course=attendance.course,
                                                                            role='delegate').first()
                attendance.course_assistant = StudentDelegate.objects.filter(course=attendance.course,
                                                                             role='assistant').first()
                attendance.enrollment_count = Enrollment.objects.filter(attendance=attendance).count()
        context['grouped_attendances'] = dict(grouped_attendances)
        return context


def group_items_by_week(model):
    items = model.objects.all().order_by('created_at')
    grouped_items = defaultdict(list)

    for item in items:
        # Calculate the start of the week (Monday) for each item
        week_start = item.created_at - timedelta(days=item.created_at.weekday())
        week_end = week_start + timedelta(days=6)

        # Format the week range as "Mon 19 Aug - Sun 25 Aug"
        week_range = f"{week_start.strftime('%a %d %b')} - {week_end.strftime('%a %d %b %Y')}"

        # Group items by this week range
        grouped_items[week_range].append(item)

    return grouped_items


class CourseView(LoginRequiredMixin, CommonContextMixin, ListView):
    model = Course
    template_name = 'core/courses/courses.html'
    paginate_by = 25
    context_object_name = 'courses'

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
        queryset = self.get_queryset()
        return queryset.get(id=self.kwargs['pk'], slug=self.kwargs['slug'])

    def get_queryset(self):
        return Course.objects.all()

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        course = self.get_object()
        context['delegates'] = StudentDelegate.objects.filter(course=course)
        return context


class CourseAddView(LoginRequiredMixin, CommonContextMixin, CreateView):
    model = Course
    template_name = 'core/courses/course_add.html'
    context_object_name = 'form'
    form_class = CourseForm
    success_url = reverse_lazy('core:courses')

    def form_valid(self, form):
        form.save()
        message = format_html(
            'Course added successfully.<br><a href="{}" class="font-bold underline">View</a>',
            reverse_lazy('core:course_detail', kwargs={'pk': form.instance.pk, 'slug': form.instance.slug})
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
    success_url = reverse_lazy('core:courses')

    def get_object(self, queryset=None):
        queryset = self.get_queryset()
        return queryset.get(id=self.kwargs['pk'], slug=self.kwargs['slug'])

    def get_queryset(self):
        return Course.objects.all()

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['course'] = self.get_object()
        return context

    def form_valid(self, form):
        form.save()
        message = format_html(
            'Course updated successfully.<br><a href="{}" class="font-bold underline">View</a>',
            reverse_lazy('core:course_detail', kwargs={'pk': form.instance.pk, 'slug': form.instance.slug})
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
        queryset = self.get_queryset()
        return queryset.get(id=self.kwargs['pk'], slug=self.kwargs['slug'])

    def get_queryset(self):
        return Student.objects.all()

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        return context


class StudentAddView(LoginRequiredMixin, CommonContextMixin, CreateView):
    model = Student
    template_name = 'core/students/student_add.html'
    context_object_name = 'form'
    form_class = StudentForm
    success_url = reverse_lazy('core:students')

    def form_valid(self, form):
        form.save()
        message = format_html(
            'Student added successfully.<br><a href="{}" class="font-bold underline">View</a>',
            reverse_lazy('core:student_detail', kwargs={'pk': form.instance.pk, 'slug': form.instance.slug})
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
    success_url = reverse_lazy('core:students')

    def get_object(self, queryset=None):
        queryset = self.get_queryset()
        return queryset.get(id=self.kwargs['pk'], slug=self.kwargs['slug'])

    def get_queryset(self):
        return Student.objects.all()

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['student'] = self.get_object()
        return context

    def form_valid(self, form):
        form.save()
        message = format_html(
            'Student updated successfully.<br><a href="{}" class="font-bold underline">View</a>',
            reverse_lazy('core:student_detail', kwargs={'pk': form.instance.pk, 'slug': form.instance.slug})
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
        queryset = self.get_queryset()
        return queryset.get(id=self.kwargs['pk'], slug=self.kwargs['slug'])

    def get_queryset(self):
        return Lecturer.objects.all()

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        return context


class LecturerAddView(LoginRequiredMixin, CommonContextMixin, CreateView):
    model = Lecturer
    template_name = 'core/lecturers/lecturer_add.html'
    context_object_name = 'form'
    form_class = LecturerForm
    success_url = reverse_lazy('core:lecturers')

    def form_valid(self, form):
        form.save()
        message = format_html(
            'Lecturer added successfully.<br><a href="{}" class="font-bold underline">View</a>',
            reverse_lazy('core:lecturer_detail', kwargs={'pk': form.instance.pk, 'slug': form.instance.slug})
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
    success_url = reverse_lazy('core:lecturers')

    def get_object(self, queryset=None):
        queryset = self.get_queryset()
        return queryset.get(id=self.kwargs['pk'], slug=self.kwargs['slug'])

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
            reverse_lazy('core:lecturer_detail', kwargs={'pk': form.instance.pk, 'slug': form.instance.slug})
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
        grouped_records = group_items_by_week(TeachingRecord)
        for week, records in grouped_records.items():
            for record in records:
                record.course_title = record.teaching_record_attendance.course.title
                record.course_lecturer_name = record.teaching_record_attendance.course.lecturer.name
                record.course_delegate = StudentDelegate.objects.filter(course=record.teaching_record_attendance.course,
                                                                        role='delegate').first()
                record.course_assistant = StudentDelegate.objects.filter(
                    course=record.teaching_record_attendance.course, role='assistant').first()
        context['grouped_records'] = dict(grouped_records)
        return context


class TeachingRecordDetailView(LoginRequiredMixin, CommonContextMixin, DetailView):
    model = TeachingRecord
    template_name = 'core/records/record_details.html'
    context_object_name = 'record'

    def get_object(self, queryset=None):
        queryset = self.get_queryset()
        return queryset.get(id=self.kwargs['pk'], teaching_record_attendance__course__slug=self.kwargs['slug'])

    def get_queryset(self):
        return TeachingRecord.objects.all()

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['course_delegates'] = StudentDelegate.objects.filter(
            course=self.object.teaching_record_attendance.course,
            student__is_delegate=True)
        context['enrollments'] = Enrollment.objects.filter(
            attendance__course=self.object.teaching_record_attendance.course).count()
        return context
    
class TeachingRecordUpdateView(LoginRequiredMixin, CommonContextMixin, UpdateView):
    model = TeachingRecord
    template_name = 'core/records/record_update.html'
    context_object_name = 'form'
    form_class = TeachingRecordForm

    def get_object(self, queryset=None):
        queryset = self.get_queryset()
        return queryset.get(id=self.kwargs['pk'], teaching_record_attendance__course__slug=self.kwargs['slug'])

    def get_queryset(self):
        return TeachingRecord.objects.all()

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['record'] = self.get_object()
        return context
    
    def get_success_url(self):
        return reverse_lazy('core:record_detail', kwargs={'pk': self.object.pk, 'slug': self.object.teaching_record_attendance.course.slug})

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