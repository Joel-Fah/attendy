import csv
import json
import os
import random
from collections import defaultdict
from datetime import timedelta, datetime

from django.conf import settings
from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.exceptions import ValidationError
from django.db.models import Q, Count
from django.http import JsonResponse, FileResponse, HttpResponseNotFound
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse_lazy
from django.utils.html import format_html
from django.views.decorators.csrf import csrf_exempt
from django.views.generic import TemplateView, ListView, DetailView, CreateView, UpdateView, View
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_LEFT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, Image

from .forms import CourseForm, LecturerForm, StudentForm, TeachingRecordForm, AttendanceForm, CourseAttendanceForm, \
    FeedbackForm
from .mixins import CommonContextMixin, ClassLevelAccessMixin
from .models import Course, Student, Lecturer, TeachingRecord, CourseDelegate, CourseAttendance, \
    ClassLevel, Attendance, ClassLevelUser, Feedback, CourseRegistration
from .utils import group_model_items_by_week, get_faqs, get_quotes, decode_data, date_formatter, time_formatter, \
    short_date_formatter, parse_html_to_flowables


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
        context['faqs'] = get_faqs
        context['current_year'] = datetime.now().year
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

    return dict(grouped_attendances)


# core/views.py
class DashboardView(LoginRequiredMixin, CommonContextMixin, ClassLevelAccessMixin, DetailView):
    model = ClassLevel
    template_name = 'core/dashboard/dashboard.html'
    context_object_name = 'level'

    def get_object(self, queryset=None):
        return get_object_or_404(self.model, id=self.kwargs['level_pk'], slug=self.kwargs['level_slug'])

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        grouped_attendances = group_items_by_week(
            Attendance.objects.filter(class_level=self.kwargs['level_pk'])
        )
        for week, attendances in grouped_attendances.items():
            for attendance in attendances:
                attendance.course_delegate = CourseDelegate.objects.filter(course=attendance.course,
                                                                           role='delegate').first()
                attendance.course_assistant = CourseDelegate.objects.filter(course=attendance.course,
                                                                            role='assistant').first()
                attendance.enrollment_count = CourseAttendance.objects.filter(attendance=attendance).count()
        context['grouped_attendances'] = dict(grouped_attendances)

        # Calculate number of attendances per course, including courses with zero attendance
        courses = Course.objects.filter(class_level=self.kwargs['level_pk'])
        course_attendance_counts = courses.annotate(count=Count('course_attendance')).values('title', 'count').order_by(
            'title')
        context['course_attendance_counts'] = json.dumps(list(course_attendance_counts))

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

    def post(self, request, *args, **kwargs):
        if 'delete_enrollment' in request.POST:
            enrollment_id = request.POST.get('enrollment_id')
            enrollment = CourseAttendance.objects.get(id=enrollment_id)
            enrollment.delete()
            message = format_html(
                '<strong>{}</strong> was removed successfully.',
                enrollment.student.name
            )
            messages.success(request, message)
        return self.get(request, *args, **kwargs)


class AttendancePDFView(LoginRequiredMixin, CommonContextMixin, DetailView):
    model = Attendance
    template_name = 'core/attendance/attendance_details.html'
    context_object_name = 'attendance'

    def get(self, request, *args, **kwargs):
        attendance = self.get_object()
        course_delegate = CourseDelegate.objects.filter(course=attendance.course, student__is_delegate=True,
                                                        role='delegate')
        enrollments = CourseAttendance.objects.filter(attendance=self.get_object(),
                                                      attendance__class_level=self.kwargs[
                                                          'level_pk']).order_by('created_at')

        # Generate PDF file path
        filename = f"{attendance.course.title}_attendance_sheet_{attendance.course_date}.pdf"
        pdf_folder_path = os.path.join(settings.MEDIA_ROOT, 'attendance_sheets')
        os.makedirs(pdf_folder_path, exist_ok=True)
        pdf_file_path = os.path.join(pdf_folder_path, filename)

        doc = SimpleDocTemplate(pdf_file_path, title=filename, pagesize=A4, rightMargin=24, leftMargin=24, topMargin=20,
                                bottomMargin=18)
        elements = []

        # Add the image at the top
        image_path = str(settings.BASE_DIR / 'static/core/images/ictu_logo.png')
        logo = Image(image_path)
        logo.drawHeight = 1.25 * inch
        logo.drawWidth = 1.25 * inch
        elements.append(logo)

        styles = getSampleStyleSheet()
        styles['Normal'].leading = 20
        title = Paragraph("Information and Communication Technology University<br/>Institute (ICT-U) Cameroon".upper(),
                          ParagraphStyle(
                              name='Heading3',
                              alignment=TA_CENTER,
                              fontSize=12,
                              spaceBefore=16,
                              spaceAfter=16,
                              textColor=colors.black,
                              fontName='Times-Roman',
                              leading=16
                          ))
        elements.append(title)
        sub_title = Paragraph(f"Course Attendance Sheet", ParagraphStyle(
            name='Heading2',
            alignment=TA_CENTER,
            fontSize=14,
            spaceBefore=16,
            spaceAfter=16,
            textColor=colors.black,
            fontName='Helvetica-Bold',
        ))
        elements.append(sub_title)

        course_details = f"""
        <strong>COURSE TITLE: </strong> {attendance.course.title} &nbsp;
        <strong>COURSE CODE: </strong> {attendance.course.code} &nbsp;
        <strong>LECTURER: </strong> {attendance.course.lecturer.name} &nbsp;
        <strong>DATE: </strong> {date_formatter(attendance.course_date)} &nbsp;
        <strong>START TIME: </strong> {time_formatter(attendance.course_start_time)} &nbsp;
        <strong>END TIME: </strong> {time_formatter(attendance.course_end_time)} &nbsp;
        <strong>DURATION: </strong> {attendance.course_duration} &nbsp;
        <strong>CLASS TYPE: </strong> {'Catchup Class' if attendance.is_catchup else 'Normal Class'} &nbsp;
        <strong>COURSE DELEGATE: </strong> {course_delegate.first().student.name if course_delegate.exists() else '_' * 10} &nbsp;
        """
        elements.append(Paragraph(course_details, styles['Normal']))
        elements.append(Spacer(width=20, height=10))

        data = [['No.', 'Names', 'Email', 'Dep\'t', 'Phone No.', 'Gender', 'Signature']]
        for i, enrollment in enumerate(enrollments, start=1):
            data.append(
                [i, enrollment.student.name, enrollment.student.email, enrollment.student.class_level.department,
                 enrollment.student.phone, enrollment.student.gender[0].upper(), ''])

        table = Table(data, colWidths=[None, None, None, None, None, None, None], hAlign='LEFT')
        table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.white),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.black),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 8),
            ('BACKGROUND', (0, 1), (-1, -1), colors.white),
            ('GRID', (0, 0), (-1, -1), 1, colors.black),
        ]))
        elements.append(table)

        # Add footer with placeholders for signatures
        elements.append(Spacer(width=20, height=50))
        footer = Table(
            [[f'{"_" * 30}\nLecturer'.upper(), '', '', '', '', '', '', f'{"_" * 30}\nAdmin Assistant'.upper()]],
            colWidths=[None, None, None, None, None, None, None, None],
            hAlign='LEFT'
        )
        footer.setStyle(TableStyle([
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, -1), 'Times-Roman'),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 12),
        ]))
        elements.append(footer)

        done_on = Paragraph(
            text=f"Generated on {date_formatter(datetime.now())} at {time_formatter(datetime.now())}",
            style=ParagraphStyle(
                name='Small',
                parent=styles['Normal'],
                fontSize=8,
                textColor=colors.grey,
                alignment=TA_LEFT,
            )
        )
        elements.append(Spacer(width=1, height=4))
        elements.append(done_on)

        doc.build(elements)

        # Serve the PDF file
        response = FileResponse(open(pdf_file_path, 'rb'), content_type='application/pdf')
        response['Content-Disposition'] = f'attachment; filename={filename}'

        # Redirect to attendance details page
        reverse_lazy('core:attendance_detail',
                     kwargs={'level_pk': self.kwargs['level_pk'],
                             'level_slug': self.kwargs['level_slug'],
                             'pk': attendance.pk})
        return response


class AttendanceAddView(LoginRequiredMixin, CommonContextMixin, CreateView):
    model = Attendance
    template_name = 'core/attendance/attendance_add.html'
    context_object_name = 'form'
    form_class = AttendanceForm

    def get_success_url(self):
        return reverse_lazy('core:dashboard',
                            kwargs={'level_pk': self.kwargs['level_pk'], 'level_slug': self.kwargs['level_slug']})

    def get_form(self, form_class=None):
        form = super().get_form(form_class)
        class_level_id = self.kwargs['level_pk']
        form.fields['class_level'].initial = ClassLevel.objects.get(pk=class_level_id)
        form.fields['course'].queryset = Course.objects.filter(class_level=class_level_id)
        return form

    def form_valid(self, form):
        form.save()
        message = format_html(
            'Attendance added successfully.<br><a href="{}" class="font-bold underline">View</a>',
            reverse_lazy('core:attendance_detail',
                         kwargs={'level_pk': self.kwargs['level_pk'], 'level_slug': self.kwargs['level_slug'],
                                 'pk': form.instance.pk})
        )
        messages.success(
            self.request,
            message
        )
        messages.info(
            self.request,
            "A teaching record has been created for this attendance. Remind to check and fill out accordingly."
        )
        return super().form_valid(form)

    def form_invalid(self, form):
        messages.error(
            self.request,
            format_html(
                'An error occurred while adding the attendance.<br>Please try again.'
            )
        )
        return super().form_invalid(form)


class AttendanceUpdateView(LoginRequiredMixin, CommonContextMixin, UpdateView):
    model = Attendance
    template_name = 'core/attendance/attendance_update.html'
    context_object_name = 'attendance'
    form_class = AttendanceForm

    def get_object(self, queryset=None):
        queryset = self.get_queryset()
        return queryset.get(id=self.kwargs['pk'], class_level=self.kwargs['level_pk'])

    def get_success_url(self):
        return reverse_lazy('core:attendance_detail',
                            kwargs={'level_pk': self.kwargs['level_pk'], 'level_slug': self.kwargs['level_slug'],
                                    'pk': self.kwargs['pk']})

    def get_form(self, form_class=None):
        form = super().get_form(form_class)
        form.fields['course'].queryset = Course.objects.filter(class_level=self.kwargs['level_pk'])
        return form

    def form_valid(self, form):
        form.save()
        messages.success(
            self.request,
            'Attendance updated successfully.'
        )
        return super().form_valid(form)

    def form_invalid(self, form):
        messages.error(
            self.request,
            format_html(
                'An error occurred while updating the attendance.<br>Please try again.'
            )
        )
        return super().form_invalid(form)


class CourseAttendanceAddView(LoginRequiredMixin, CommonContextMixin, CreateView):
    model = CourseAttendance
    template_name = 'core/enrollment/course_attendance_add.html'
    context_object_name = 'form'
    form_class = CourseAttendanceForm

    def get_success_url(self):
        return reverse_lazy('core:attendance_detail',
                            kwargs={'level_pk': self.kwargs['level_pk'], 'level_slug': self.kwargs['level_slug'],
                                    'pk': self.kwargs['pk']})

    def get_form(self, form_class=None):
        form = super().get_form(form_class)
        attendance = Attendance.objects.get(pk=self.kwargs['pk'])
        form.fields['student'].queryset = Student.objects.filter(
            Q(registration__course=attendance.course) | Q(class_level=attendance.class_level)).distinct()
        form.fields['attendance'].initial = attendance
        return form

    def form_valid(self, form):
        form.save()
        student_name = form.instance.student.name
        message = format_html(
            'Student <strong>{}</strong> admitted into attendance successfully.',
            student_name,
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
                'An error occurred while admitting the student into attendance.<br>Please try again.'
            )
        )
        return super().form_invalid(form)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['attendance'] = Attendance.objects.get(pk=self.kwargs['pk'])
        return context


@csrf_exempt
def decode_qr(request, *args, **kwargs):
    if request.method == 'POST':
        data = json.loads(request.body)
        encoded_qr_data = data.get('qr_data')

        try:
            # Decode the QR code data
            qr_data = decode_data(encoded_qr_data)
            student_id = qr_data.get('id')
            student_number = qr_data.get('student_number')
            class_level_id = qr_data.get('class_level_id')

            # Fetch the student and class level from the database
            student = Student.objects.get(id=student_id, student_number=student_number, class_level_id=class_level_id)

            # Check if student registered the course of the attendance
            attendance_course = Attendance.objects.get(pk=kwargs['pk']).course
            has_registered = CourseRegistration.objects.filter(student=student, course=attendance_course).exists() or \
                             student.class_level == attendance_course.class_level
            class_level = f'{attendance_course.class_level.get_level_display()} - Group {attendance_course.class_level.group} - {attendance_course.class_level.semester} {attendance_course.class_level.year} - {attendance_course.class_level.department}'

            if has_registered:
                return JsonResponse({
                    "success": True,
                    "student_name": student.name,
                    "class_level": class_level,
                    "has_registered": has_registered,
                })
            else:
                return JsonResponse({
                    "success": False,
                    "error": f'The student "{student.name}" is not registered for {attendance_course.title}'
                })
        except (Student.DoesNotExist, ClassLevel.DoesNotExist, ValueError, json.JSONDecodeError) as e:
            return JsonResponse({'success': False, 'error': str(e)})
    return JsonResponse({'success': False, 'error': 'Invalid request method'})


@csrf_exempt
def add_student_to_course_attendance(request, *args, **kwargs):
    if request.method == 'POST':
        data = json.loads(request.body)
        encoded_qr_data = data.get('qr_data')

        try:
            # Decode the QR code data
            qr_data = decode_data(encoded_qr_data)
            student_id = qr_data.get('id')
            student_number = qr_data.get('student_number')
            class_level_id = qr_data.get('class_level_id')

            # Fetch the student and class level from the database
            student = Student.objects.get(id=student_id, student_number=student_number, class_level_id=class_level_id)

            # Add the student to the CourseAttendance if they are registered for the course
            attendance = Attendance.objects.get(pk=kwargs['pk'])
            course = attendance.course
            has_registered = Course.objects.filter(
                Q(registration__student=student, id=attendance.course.id) | Q(class_level=student.class_level)).exists()

            # Check if student is already attending the course
            if CourseAttendance.objects.filter(student=student, attendance=attendance).exists():
                return JsonResponse({
                    'success': False,
                    'error': f'{student.name} is already admitted into attendance for {course.title}'
                })

            if has_registered:
                CourseAttendance.objects.create(student=student, attendance=attendance)

                message = format_html(
                    'Student <strong>{}</strong> was admitted into attendance successfully.',
                    student.name,
                )

                messages.success(request, message)

                return JsonResponse({
                    'success': True,
                    'student_name': student.name,
                    'course': f'{course.code} {course.title}',
                    'class_level': f'{attendance.class_level.get_level_display()} - Group {attendance.class_level.group} - {attendance.class_level.semester} {attendance.class_level.year} - {attendance.class_level.department}',
                })
            else:
                raise ValueError(f'{student.name} is not registered for {course.title}')

        except (Student.DoesNotExist, ClassLevel.DoesNotExist, ValueError, json.JSONDecodeError) as e:
            return JsonResponse({'success': False, 'error': str(e)})
    return JsonResponse({'success': False, 'error': 'Invalid request method'})


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
        registered_students = Student.objects.filter(
            Q(registration__course=course) | Q(class_level=course.class_level))

        context['delegates'] = CourseDelegate.objects.filter(course=course)
        context['registered_students'] = registered_students

        # Calculate male and female students
        male_students = registered_students.filter(gender='Male').count()
        female_students = registered_students.filter(gender='Female').count()
        context['gender_distribution'] = json.dumps({
            'male': male_students,
            'female': female_students
        })

        return context

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


class CoursePDFView(LoginRequiredMixin, CommonContextMixin, DetailView):
    model = Course
    template_name = 'core/courses/course_details.html'
    context_object_name = 'course'

    def get(self, request, *args, **kwargs):
        course = self.get_object()
        course_delegate = CourseDelegate.objects.filter(course=course, student__is_delegate=True, role='delegate')
        registered_students = Student.objects.filter(
            Q(registration__course=course) | Q(class_level=course.class_level)).distinct().order_by('name')

        # Generate PDF file path
        filename = f"{course.title}_class_list.pdf"
        pdf_folder_path = os.path.join(settings.MEDIA_ROOT, 'course_class_lists')
        os.makedirs(pdf_folder_path, exist_ok=True)
        pdf_file_path = os.path.join(pdf_folder_path, filename)

        doc = SimpleDocTemplate(pdf_file_path, title=filename, pagesize=A4, rightMargin=24, leftMargin=24, topMargin=20,
                                bottomMargin=18)
        elements = []

        # Add the image at the top
        image_path = str(settings.BASE_DIR / 'static/core/images/ictu_logo.png')
        logo = Image(image_path)
        logo.drawHeight = 1.25 * inch
        logo.drawWidth = 1.25 * inch
        elements.append(logo)

        styles = getSampleStyleSheet()
        styles['Normal'].leading = 20
        title = Paragraph("Information and Communication Technology University<br/>Institute (ICT-U) Cameroon".upper(),
                          ParagraphStyle(
                              name='Heading3',
                              alignment=TA_CENTER,
                              fontSize=12,
                              spaceBefore=16,
                              spaceAfter=16,
                              textColor=colors.black,
                              fontName='Times-Roman',
                              leading=16
                          ))
        elements.append(title)
        sub_title = Paragraph(f"Class List for {course.title}", ParagraphStyle(
            name='Heading2',
            alignment=TA_CENTER,
            fontSize=14,
            spaceBefore=16,
            spaceAfter=16,
            textColor=colors.black,
            fontName='Helvetica-Bold',
        ))
        elements.append(sub_title)

        course_details = f"""
        <strong>COURSE TITLE:</strong> {course.title} &nbsp;
        <strong>COURSE CODE:</strong> {course.code} &nbsp;
        <strong>LECTURER:</strong> {course.lecturer.name} &nbsp;
        <strong>COURSE DELEGATE:</strong> {course_delegate.first().student.name if course_delegate.exists() else '_' * 10} &nbsp;
        """
        elements.append(Paragraph(course_details, styles['Normal']))
        elements.append(Spacer(width=20, height=10))

        data = [['No.', 'Names', 'Email', 'Dep\'t', 'Phone No.', 'Gender']]
        for i, student in enumerate(registered_students, start=1):
            data.append([i, student.name, student.email, student.class_level.department, student.phone,
                         student.gender[0].upper()])

        table = Table(data, colWidths=[None, None, None, None, None, None], hAlign='LEFT')
        table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.white),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.black),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 8),
            ('BACKGROUND', (0, 1), (-1, -1), colors.white),
            ('GRID', (0, 0), (-1, -1), 1, colors.black),
        ]))
        elements.append(table)

        # Add footer with placeholders for signatures
        elements.append(Spacer(width=20, height=50))
        footer = Table(
            [[f'{"_" * 30}\nLecturer'.upper(), '', '', '', '', '', '', f'{"_" * 30}\nAdmin Assistant'.upper()]],
            colWidths=[None, None, None, None, None, None, None, None],
            hAlign='LEFT'
        )
        footer.setStyle(TableStyle([
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, -1), 'Times-Roman'),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 12),
        ]))
        elements.append(footer)

        done_on = Paragraph(
            text=f"Generated on {date_formatter(datetime.now())} at {time_formatter(datetime.now())}",
            style=ParagraphStyle(
                name='Small',
                parent=styles['Normal'],
                fontSize=8,
                textColor=colors.grey,
                alignment=TA_LEFT,
            )
        )
        elements.append(Spacer(width=1, height=4))
        elements.append(done_on)

        doc.build(elements)

        # Serve the PDF file
        response = FileResponse(open(pdf_file_path, 'rb'), content_type='application/pdf')
        response['Content-Disposition'] = f'attachment; filename={filename}'

        # Redirect to course details page
        reverse_lazy('core:course_detail',
                     kwargs={'level_pk': course.class_level.id, 'pk': course.id, 'slug': course.slug})
        return response


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
        return reverse_lazy('core:course_detail',
                            kwargs={'level_pk': self.kwargs['level_pk'], 'pk': self.kwargs['pk'],
                                    'slug': self.kwargs['slug']})

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['course'] = self.get_object()
        return context

    def form_valid(self, form):
        form.save()
        message = format_html(
            'Course updated successfully.'
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
        students = self.get_queryset()
        context['delegates'] = Student.objects.filter(is_delegate=True, class_level=self.kwargs['level_pk']).order_by(
            'name')

        # Calculate male and female students
        male_students = students.filter(gender='Male').count()
        female_students = students.filter(gender='Female').count()
        context['gender_distribution'] = json.dumps({
            'male': male_students,
            'female': female_students
        })

        # Prepare data for plotting attendance summary
        attendance_data = []
        courses = Course.objects.filter(class_level=self.kwargs['level_pk'])
        for student in students:
            student_attendance = {}
            for course in courses:
                attendance_count = CourseAttendance.objects.filter(student=student, attendance__course=course).count()
                student_attendance[course.title] = attendance_count
            attendance_data.append({
                'student': student.name,
                'attendance': student_attendance
            })

        # Pass the data to the context
        context['attendance_data'] = json.dumps(attendance_data)
        context['attendance_courses'] = json.dumps([course.title for course in courses])

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
        elif 'dropzone-file' in request.FILES:
            csv_file = request.FILES['dropzone-file']
            if not csv_file.name.endswith('.csv'):
                messages.error(request, 'This is not a CSV file.')
                return self.get(request, *args, **kwargs)

            try:
                class_level = ClassLevel.objects.get(pk=self.kwargs['level_pk'])
                decoded_file = csv_file.read().decode('utf-8').splitlines()
                reader = csv.DictReader(decoded_file)
                print(f"CSV reader >>> {reader}")
                students_added = 0
                for row in reader:
                    student_number = row['Student Number']
                    student_name = row['Student Name']
                    email = row['Email Address']
                    phone = row['Phone Number']
                    gender = row['Gender']
                    is_delegate = row['is_delegate'].lower() == 'true'

                    student, created = Student.objects.update_or_create(
                        student_number=student_number,
                        defaults={
                            'class_level': class_level,
                            'student_number': student_number,
                            'name': student_name,
                            'email': email,
                            'phone': phone,
                            'gender': gender,
                            'is_delegate': is_delegate,
                        }
                    )
                    if created:
                        students_added += 1

                messages.success(request, f'{students_added} students added to {class_level}.')
            except (csv.Error, ValidationError) as e:
                messages.error(request, f'Error processing CSV file: {e}')

            # redirect to same page
            reverse_lazy('core:students', kwargs={'level_pk': self.kwargs['level_pk']})

        return self.get(request, *args, **kwargs)


class StudentPDFView(LoginRequiredMixin, CommonContextMixin, ListView):
    model = Student
    template_name = 'core/students/students.html'
    paginate_by = 25
    context_object_name = 'students'

    def get_queryset(self):
        return self.model.objects.filter(class_level=self.kwargs['level_pk']).order_by('name')

    def get(self, request, *args, **kwargs):
        students = self.get_queryset()
        class_level = ClassLevel.objects.get(pk=self.kwargs['level_pk'])
        class_delegates = students.filter(is_delegate=True)

        # Generate PDF file path
        filename = f"{class_level}_overall_class_list.pdf"
        pdf_folder_path = os.path.join(settings.MEDIA_ROOT, 'overall_class_lists')
        os.makedirs(pdf_folder_path, exist_ok=True)
        pdf_file_path = os.path.join(pdf_folder_path, filename)

        doc = SimpleDocTemplate(pdf_file_path, title=filename, pagesize=A4, rightMargin=24, leftMargin=24, topMargin=20,
                                bottomMargin=18)
        elements = []

        # Add the image at the top
        image_path = str(settings.BASE_DIR / 'static/core/images/ictu_logo.png')
        logo = Image(image_path)
        logo.drawHeight = 1.25 * inch
        logo.drawWidth = 1.25 * inch
        elements.append(logo)

        styles = getSampleStyleSheet()
        styles['Normal'].leading = 20
        title = Paragraph("Information and Communication Technology University<br/>Institute (ICT-U) Cameroon".upper(),
                          ParagraphStyle(
                              name='Heading3',
                              alignment=TA_CENTER,
                              fontSize=12,
                              spaceBefore=16,
                              spaceAfter=16,
                              textColor=colors.black,
                              fontName='Times-Roman',
                              leading=16
                          ))
        elements.append(title)
        sub_title = Paragraph(f"Overall Class List for<br/>{class_level}", ParagraphStyle(
            name='Heading2',
            alignment=TA_CENTER,
            fontSize=14,
            spaceBefore=16,
            spaceAfter=16,
            textColor=colors.black,
            fontName='Helvetica-Bold',
            leading=16,
        ))
        elements.append(sub_title)

        class_details = f"""
                <strong>CLASS LEVEL:</strong> {class_level.get_level_display()} &nbsp;
                <strong>CLASS GROUP:</strong> Group {class_level.group} &nbsp;
                <strong>DEPARTMENT:</strong> {class_level.department} &nbsp;
                <strong>SEMESTER:</strong> {class_level.semester} {class_level.year} &nbsp;
                <strong>MAIN HALL:</strong> {class_level.main_hall} &nbsp;
                {f'<strong>ALT. HALL:</strong> {class_level.secondary_hall} &nbsp;' if class_level.secondary_hall else ''}
                <strong>CLASS SIZE:</strong> {students.count()} &nbsp;
                <strong>CLASS/COURSE DELEGATE(S):</strong> {', '.join([delegate.name for delegate in class_delegates]) if class_delegates else '_' * 30} &nbsp;
                """
        elements.append(Paragraph(class_details, styles['Normal']))
        elements.append(Spacer(width=20, height=10))

        data = [['No.', 'Names', 'Email', 'Phone No.', 'Gender', 'Obs.']]
        for i, student in enumerate(students, start=1):
            data.append([i, student.name, student.email, student.phone, student.gender[0].upper(),
                         f'Delegate' if student.is_delegate else ''])

        table = Table(data, colWidths=[None, None, None, None, None, None], hAlign='LEFT')
        table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.white),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.black),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 8),
            ('BACKGROUND', (0, 1), (-1, -1), colors.white),
            ('GRID', (0, 0), (-1, -1), 1, colors.black),
        ]))
        elements.append(table)

        # Add footer with placeholders for signatures
        elements.append(Spacer(width=20, height=50))
        footer = Table(
            [[f'{"_" * 30}\nAdministration'.upper(), '', '', '', '', '', '', f'{"_" * 30}\nAdmin Assistant'.upper()]],
            colWidths=[None, None, None, None, None, None, None, None],
            hAlign='LEFT'
        )
        footer.setStyle(TableStyle([
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, -1), 'Times-Roman'),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 12),
        ]))
        elements.append(footer)

        done_on = Paragraph(
            text=f"Generated on {date_formatter(datetime.now())} at {time_formatter(datetime.now())}",
            style=ParagraphStyle(
                name='Small',
                parent=styles['Normal'],
                fontSize=8,
                textColor=colors.grey,
                alignment=TA_LEFT,
            )
        )
        elements.append(Spacer(width=1, height=4))
        elements.append(done_on)

        doc.build(elements)

        # Serve the PDF file
        response = FileResponse(open(pdf_file_path, 'rb'), content_type='application/pdf')
        response['Content-Disposition'] = f'attachment; filename={filename}'

        # Redirect to students page
        reverse_lazy('core:students', kwargs={'level_pk': self.kwargs['level_pk']})
        return response


class StudentDetailView(LoginRequiredMixin, CommonContextMixin, DetailView):
    model = Student
    template_name = 'core/students/student_details.html'
    context_object_name = 'student'

    def get_object(self, queryset=None):
        return get_object_or_404(self.model, id=self.kwargs['pk'], slug=self.kwargs['slug'])

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        student = self.get_object()
        student_semester_courses = Course.objects.filter(
            Q(registration__student=student) | Q(class_level=student.class_level)).distinct()

        context['grouped_courses'] = student.get_courses_grouped_by_class_level()
        context['qr_code_url'] = self.object.generate_qr_code_url()
        context['courses_count'] = student_semester_courses.count()

        course_attended_count = {}
        total_attendance_count = {}
        for course in student_semester_courses.all():
            course_attended_count[course.id] = CourseAttendance.objects.filter(student=student,
                                                                               attendance__course=course).count()
            total_attendance_count[course.id] = Attendance.objects.filter(course=course).count()

        context['course_attended_count'] = course_attended_count
        context['total_attendance_count'] = total_attendance_count

        # Prepare data for the chart
        chart_data = []
        for course in student_semester_courses:
            chart_data.append({
                'course': course.title,
                'total_attendance': total_attendance_count[course.id],
                'student_attendance': course_attended_count[course.id]
            })
        context['chart_data'] = json.dumps(chart_data)

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
        return reverse_lazy('core:student_detail',
                            kwargs={'level_pk': self.kwargs['level_pk'], 'pk': self.kwargs['pk'],
                                    'slug': self.kwargs['slug']})

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['student'] = self.get_object()
        return context

    def form_valid(self, form):
        form.save()
        message = format_html(
            'Student updated successfully.'
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


class CourseRegistrationView(LoginRequiredMixin, CommonContextMixin, TemplateView):
    template_name = 'core/course_registration/course_registration.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        student = Student.objects.get(id=self.kwargs['pk'])
        context['student'] = student

        # Group courses by level
        all_courses = Course.objects.filter(
            # class_level__semester=student.class_level.semester,
            class_level__year=student.class_level.year)
        grouped_all_courses = defaultdict(list)
        for course in all_courses:
            class_level = course.class_level
            key = f"{class_level.get_level_display()} - Group {class_level.group}"
            grouped_all_courses[key].append(course)

        # Convert defaultdict to a regular dict
        grouped_all_courses = dict(grouped_all_courses)

        registered_courses = CourseRegistration.objects.filter(student=student).values_list('course_id', flat=True)
        for course in all_courses:
            course.is_registered = course.id in registered_courses
        context['courses'] = grouped_all_courses
        return context

    def post(self, request, *args, **kwargs):
        student = Student.objects.get(id=self.kwargs['pk'])
        course_ids = request.POST.getlist('courses')
        registered_courses = CourseRegistration.objects.filter(student=student).values_list('course_id', flat=True)

        newly_registered_count = 0
        unregistered_count = 0

        # Register new courses
        for course_id in course_ids:
            course = Course.objects.get(id=course_id)
            if course.id not in registered_courses:
                CourseRegistration.objects.create(student=student, course=course)
                newly_registered_count += 1

        # Unregister unchecked courses
        for course_id in registered_courses:
            if str(course_id) not in course_ids:
                CourseRegistration.objects.filter(student=student, course_id=course_id).delete()
                unregistered_count += 1

        if newly_registered_count == 0 and unregistered_count == 0:
            messages.info(
                request,
                'No changes were made to the course registration.'
            )
        else:
            message = format_html(
                '{} Courses registered successfully. {} Courses unregistered successfully.',
                newly_registered_count,
                unregistered_count
            )
            messages.success(request, message)
        return redirect('core:student_detail', level_pk=student.class_level.id, pk=student.id, slug=student.slug)


class LecturerView(LoginRequiredMixin, CommonContextMixin, ListView):
    model = Lecturer
    template_name = 'core/lecturers/lecturers.html'
    paginate_by = 25
    context_object_name = 'filteredLecturers'

    def get_queryset(self):
        return self.model.objects.filter(course_lecturer__class_level=self.kwargs['level_pk']).distinct().order_by('name')

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


class TeachingRecordPDFView(LoginRequiredMixin, CommonContextMixin, DetailView):
    model = TeachingRecord
    template_name = 'core/records/record_details.html'
    context_object_name = 'record'

    def get(self, request, *args, **kwargs):
        record = self.get_object()
        course_delegate = CourseDelegate.objects.filter(course=record.attendance.course, student__is_delegate=True,
                                                        role='delegate')
        enrollments = CourseAttendance.objects.filter(attendance=record.attendance,
                                                      attendance__class_level=self.kwargs[
                                                          'level_pk']).order_by('created_at')

        # Generate PDF file path
        filename = f"{record.attendance.course.title}_teaching_record.pdf"
        pdf_folder_path = os.path.join(settings.MEDIA_ROOT, 'teaching_records')
        os.makedirs(pdf_folder_path, exist_ok=True)
        pdf_file_path = os.path.join(pdf_folder_path, filename)

        doc = SimpleDocTemplate(pdf_file_path, title=filename, pagesize=A4, rightMargin=24, leftMargin=24, topMargin=20,
                                bottomMargin=18)
        elements = []

        # Add the image at the top
        image_path = str(settings.BASE_DIR / 'static/core/images/ictu_long_logo.png')
        logo = Image(image_path, hAlign="LEFT")
        logo.drawHeight = 0.9 * inch
        logo.drawWidth = 1.75 * inch
        elements.append(logo)

        styles = getSampleStyleSheet()
        styles['Normal'].leading = 20
        title = Paragraph("Teaching Record and Syllabus Coverage Protocol",
                          ParagraphStyle(
                              name='Heading3',
                              alignment=TA_CENTER,
                              fontSize=12,
                              spaceBefore=16,
                              spaceAfter=16,
                              textColor=colors.black,
                              fontName='Times-Roman',
                              leading=16
                          ))
        elements.append(title)

        # Heading Table
        times_roman_style = ParagraphStyle(name='Normal', fontName='Times-Roman', fontSize=12)

        heading_table_data = [
            [Paragraph('Name of Lecturer', times_roman_style), record.attendance.course.lecturer],
            [Paragraph('Course Code/Title', times_roman_style), record.attendance.course],
            [Paragraph('Start Time - Finish Time', times_roman_style),
             f'{time_formatter(record.attendance.course_start_time)} - {time_formatter(record.attendance.course_end_time)}'],
            [Paragraph('Duration', times_roman_style), record.attendance.course_duration],
            [Paragraph('Number of students', times_roman_style), enrollments.count()],
            [Paragraph('Date', times_roman_style), date_formatter(record.attendance.course_date)],
        ]
        heading_table = Table(heading_table_data, colWidths=[2 * inch, None], hAlign='LEFT')
        heading_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.white),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.black),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 1), (-1, 1), 'Helvetica'),
            ('FONTSIZE', (0, 1), (-1, 1), 12),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 8),
            ('BACKGROUND', (0, 1), (-1, -1), colors.white),
            ('GRID', (0, 0), (-1, -1), 1, colors.black),
        ]))
        elements.append(heading_table)
        elements.append(Spacer(width=20, height=16))

        # Subtitle
        subtitle_data_row = Table(
            [[Paragraph('Lessons and Brief Contents / Assignments',
                        style=ParagraphStyle(name='Heading3', fontName='Times-Roman', fontSize=12, spaceBefore=2,
                                             spaceAfter=2, alignment=TA_CENTER))]],
            colWidths=[None],
            hAlign='CENTER',
            style=TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.lightgrey),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.black),
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ('FONTNAME', (0, 0), (-1, 0), 'Times-Roman'),
                ('BOTTOMPADDING', (0, 0), (-1, 0), 8),
                ('GRID', (0, 0), (-1, -1), 1, colors.black),
            ])
        )
        elements.append(subtitle_data_row)
        elements.append(Spacer(width=20, height=16))

        # Lessons content
        # Replace <p><br></p> with <div><br/></div> and add <br/> between </p><p>
        description = record.description.replace('<p><br></p>', '<div><br/><br/></div>').replace('</p><p>',
                                                                                                 '</p><br/><p>')

        # Handle summernote content
        styles['Normal'].fontSize = 12
        summernote_content = parse_html_to_flowables(description, styles)
        elements.extend(summernote_content)
        elements.append(Spacer(width=20, height=10))

        # Footer table data
        footer_table_data = [
            [Paragraph(title, style=times_roman_style) for title in ['Official', 'Names', 'Signatures', 'Date']],
            [Paragraph('Lecturer', style=times_roman_style), record.attendance.course.lecturer.name, '',
             short_date_formatter(record.attendance.course_date)],
            [Paragraph('Course Delegate', style=times_roman_style),
             course_delegate.first().student.name if course_delegate.exists() else '', '',
             short_date_formatter(record.attendance.course_date)],
            [Paragraph('Quality Assurance', style=times_roman_style), '', '',
             short_date_formatter(record.attendance.course_date)],
        ]
        footer_table = Table(footer_table_data, colWidths=[1.75 * inch, 2.75 * inch, None, None], hAlign='LEFT')
        footer_table.setStyle(TableStyle([
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
            ('GRID', (0, 0), (-1, -1), 1, colors.black),
        ]))
        elements.append(footer_table)

        done_on = Paragraph(
            text=f"Generated on {date_formatter(datetime.now())} at {time_formatter(datetime.now())}",
            style=ParagraphStyle(
                name='Small',
                parent=styles['Normal'],
                fontSize=8,
                textColor=colors.grey,
                alignment=TA_LEFT,
            )
        )
        elements.append(Spacer(width=1, height=4))
        elements.append(done_on)

        doc.build(elements)

        response = FileResponse(open(pdf_file_path, 'rb'), content_type='application/pdf')
        response['Content-Disposition'] = f'attachment; filename={filename}'

        # Redirect to teaching record details page
        reverse_lazy('core:record_detail',
                     kwargs={'level_pk': record.attendance.class_level.id, 'pk': record.pk,
                             'slug': record.attendance.course.slug})

        return response


class TeachingRecordUpdateView(LoginRequiredMixin, CommonContextMixin, UpdateView):
    model = TeachingRecord
    template_name = 'core/records/record_update.html'
    context_object_name = 'form'
    form_class = TeachingRecordForm

    def get_object(self, queryset=None):
        queryset = self.get_queryset()
        return queryset.get(id=self.kwargs['pk'], attendance__course__slug=self.kwargs['slug'])

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['record'] = self.get_object()
        return context

    def get_success_url(self):
        return reverse_lazy('core:record_detail',
                            kwargs={'level_pk': self.kwargs.get('level_pk'), 'pk': self.object.pk,
                                    'slug': self.object.attendance.course.slug})

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


class FeedbackView(LoginRequiredMixin, CreateView):
    model = Feedback
    template_name = 'core/feedback.html'
    context_object_name = 'form'
    form_class = FeedbackForm

    def get_success_url(self):
        return reverse_lazy('core:feedback')

    def get_form(self, form_class=None):
        form = super().get_form(form_class)
        form.fields['user'].initial = self.request.user
        return form

    def form_valid(self, form):
        form.save()
        messages.success(
            self.request,
            'Feedback submitted successfully.'
        )
        return super().form_valid(form)

    def form_invalid(self, form):
        messages.error(
            self.request,
            'An error occurred while submitting your feedback.<br>Please try again.'
        )
        return super().form_invalid(form)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # Get a random quote from get_quotes
        random_quote = random.choice(get_quotes())
        context['quote'] = random_quote
        return context


# Utils classes
class DownloadTemplateFileView(LoginRequiredMixin, View):
    def get(self, request, *args, **kwargs):
        model_name = self.kwargs['model_name']
        class_level_id = self.kwargs['level_pk']
        class_level = get_object_or_404(ClassLevel, pk=class_level_id)

        file_name = f'add_{model_name.lower()}s_to_class.csv'
        file_path = os.path.join(settings.STATIC_ROOT, 'core/files', file_name)

        if not os.path.exists(file_path):
            return HttpResponseNotFound('The requested file was not found on the server.')

        response = FileResponse(open(file_path, 'rb'), content_type='text/csv')
        response[
            'Content-Disposition'] = f'attachment; filename=Add {model_name.lower()}s to {class_level} template file.csv'
        return response


# Handlers
def handler404(request, exception):
    return render(request, 'core/errors/404.html', status=404)


def handler500(request):
    return render(request, 'core/errors/500.html', status=500)
