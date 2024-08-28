from datetime import timedelta
from django.shortcuts import render
from django.views.generic import TemplateView, ListView, DetailView, UpdateView, DeleteView
from django.contrib.auth.mixins import LoginRequiredMixin
from .models import Course, Student, Lecturer, TeachingRecord, StudentDelegate, Enrollment
from .mixins import CommonContextMixin
from collections import defaultdict
from slugify import slugify


# Create your views here.
class HomeView(TemplateView):
    template_name = 'core/index.html'


# Dashboard views
class DashboardView(LoginRequiredMixin, CommonContextMixin, TemplateView):
    template_name = 'core/dashboard.html'


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

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        grouped_courses = group_items_by_week(Course)
        # slugify the course title using slugify
        for week, courses in grouped_courses.items():
            for course in courses:
                course.slug = slugify(course.title)
        context['grouped_courses'] = dict(grouped_courses)

        return context


class CourseDetailView(LoginRequiredMixin, DetailView):
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
        context['enrolled_students'] = Enrollment.objects.filter(course=course).select_related('student')
        return context


class StudentView(LoginRequiredMixin, CommonContextMixin, ListView):
    model = Student
    template_name = 'core/students/students.html'
    paginate_by = 20
    context_object_name = 'students'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['delegates'] = Student.objects.filter(is_delegate=True).order_by('name')
        return context


class StudentDetailView(LoginRequiredMixin, DetailView):
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


class LecturerView(LoginRequiredMixin, CommonContextMixin, ListView):
    model = Lecturer
    template_name = 'core/lecturers/lecturers.html'
    paginate_by = 20
    context_object_name = 'lecturers'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        grouped_lecturers = group_items_by_week(Lecturer)
        context['grouped_lecturers'] = dict(grouped_lecturers)
        return context


class LecturerDetailView(LoginRequiredMixin, DetailView):
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


class TeachingRecordView(LoginRequiredMixin, CommonContextMixin, ListView):
    model = TeachingRecord
    template_name = 'core/records/records.html'
    paginate_by = 20
    context_object_name = 'records'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        grouped_records = group_items_by_week(TeachingRecord)
        for week, records in grouped_records.items():
            for record in records:
                record.course_title = record.course.title
                record.course_lecturer_name = record.course.lecturer.name
                record.course_delegate = StudentDelegate.objects.filter(course=record.course, role='delegate').first()
                record.course_assistant = StudentDelegate.objects.filter(course=record.course, role='assistant').first()
        context['grouped_records'] = dict(grouped_records)
        return context


class TeachingRecordDetailView(LoginRequiredMixin, DetailView):
    model = TeachingRecord
    template_name = 'core/records/record_details.html'
    context_object_name = 'record'

    def get_object(self, queryset=None):
        queryset = self.get_queryset()
        return queryset.get(id=self.kwargs['pk'], course__slug=self.kwargs['slug'])

    def get_queryset(self):
        return TeachingRecord.objects.all()

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['course_delegate'] = StudentDelegate.objects.filter(course=self.object.course, role='delegate').first()
        context['course_assistant'] = StudentDelegate.objects.filter(course=self.object.course,
                                                                     role='assistant').first()
        context['enrollments'] = Enrollment.objects.filter(course=self.object.course).count()
        return context
