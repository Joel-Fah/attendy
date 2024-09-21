import os
from collections import defaultdict
from datetime import datetime

import qrcode
from PIL import Image, ImageDraw
from django.conf import settings
from django.contrib.auth.models import User, Group
from django.core.exceptions import ValidationError
from django.db import models
from django.db.models import Q
from qrcode.image.styledpil import StyledPilImage
from qrcode.image.styles.colormasks import SolidFillColorMask
from qrcode.image.styles.moduledrawers.pil import RoundedModuleDrawer, HorizontalBarsDrawer
from slugify import slugify

from .utils import calculate_duration, is_valid_time, encode_data


# Create your models here.


def get_current_year():
    return datetime.now().year


class DepartmentChoices(models.TextChoices):
    BMS = 'BMS', 'BMS'
    ICT = 'ICT', 'ICT'


class SemesterChoices(models.TextChoices):
    FALL = 'FALL', 'FALL'
    SPRING = 'SPRING', 'SPRING'
    SUMMER = 'SUMMER', 'SUMMER'


class Student(models.Model):
    class Meta:
        verbose_name = "Student"
        verbose_name_plural = "Students"
        unique_together = ('class_level', 'student_number')

    class GenderChoices(models.TextChoices):
        MALE = 'Male', 'Male'
        FEMALE = 'Female', 'Female'

    class_level = models.ForeignKey('ClassLevel', on_delete=models.CASCADE, related_name='class_level_students')
    name = models.CharField(max_length=255, null=False,
                            blank=False, help_text="Name of the student")
    slug = models.SlugField(max_length=255, editable=False, null=False, blank=False, help_text="Slug of the student")
    student_number = models.CharField(max_length=255, null=False, blank=False,
                                      default='ICTUXXXXxxxx', help_text="Student number")
    email = models.EmailField(
        null=False, blank=False,
        help_text="Student email address (preferably ICT University email: @ictuniversity.edu.cm)")
    phone = models.CharField(max_length=255, null=False,
                             blank=False, help_text="Student phone number")
    gender = models.CharField(
        max_length=255, choices=GenderChoices.choices, null=False, blank=False,
        help_text="Gender of the student: Male or Female")
    is_delegate = models.BooleanField(
        default=False, help_text="Is the student a course delegate?")
    encoded_data = models.TextField(unique=True, editable=False, null=True, blank=True,
                                    help_text="Encoded data for the QR code")

    created_at = models.DateTimeField(auto_now_add=True, help_text="Date and time this student was added")
    updated_at = models.DateTimeField(auto_now=True, help_text="Date and time this student was last updated")

    def save(self, *args, **kwargs):
        self.slug = slugify(self.name)
        super().save(*args, **kwargs)

    def get_courses_grouped_by_semester_year_and_class_level(self):
        grouped_courses = defaultdict(lambda: defaultdict(list))
        courses = Course.objects.filter(
            Q(registration__student=self) | Q(class_level=self.class_level))  # Get courses for the student

        for course in courses:
            semester_year = f'{course.class_level.semester} {course.class_level.year}'
            class_level = course.class_level
            course.is_registered = self.is_course_registered(course)
            grouped_courses[semester_year][class_level].append(course)

        return {semester_year: dict(class_levels) for semester_year, class_levels in grouped_courses.items()}

    def is_course_registered(self, course):
        return CourseRegistration.objects.filter(student=self, course=course).exists()

    def generate_qr_code_url(self):
        if not self.encoded_data:
            data = {
                'id': self.id,
                'student_number': self.student_number,
                'class_level_id': self.class_level.id
            }
            self.encoded_data = encode_data(data)
            self.save()

        qr = qrcode.QRCode(
            version=1,
            error_correction=qrcode.constants.ERROR_CORRECT_H,  # Use high error correction to accommodate the logo
            box_size=10,
            border=2,
        )
        qr.add_data(self.encoded_data)
        qr.make(fit=True)

        # Generate QR code with colored eyes
        qr_eyes_img = qr.make_image(
            image_factory=StyledPilImage,
            eye_drawer=RoundedModuleDrawer(radius_ratio=1),
            color_mask=SolidFillColorMask(back_color=(255, 255, 255), front_color=(241, 60, 3))
        )

        # Generate QR code with colored dots
        qr_dots_img = qr.make_image(
            image_factory=StyledPilImage,
            module_drawer=HorizontalBarsDrawer(),
            color_mask=SolidFillColorMask(back_color=(255, 255, 255), front_color=(5, 0, 65)),
        )

        # Create a mask for the eyes
        mask = Image.new('L', qr_eyes_img.size, 0)
        draw = ImageDraw.Draw(mask)
        eye_size = 70  # default
        quiet_zone = 20  # default
        img_size = qr_eyes_img.size[0]
        draw.rectangle((quiet_zone, quiet_zone, quiet_zone + eye_size, quiet_zone + eye_size), fill=255)
        draw.rectangle((img_size - quiet_zone - eye_size, quiet_zone, img_size - quiet_zone, quiet_zone + eye_size),
                       fill=255)
        draw.rectangle((quiet_zone, img_size - quiet_zone - eye_size, quiet_zone + eye_size, img_size - quiet_zone),
                       fill=255)

        # Combine the two images using the mask
        final_img = Image.composite(qr_eyes_img, qr_dots_img, mask)

        # Load the logo image
        logo_path = 'static/core/images/qr_image.png'
        logo = Image.open(logo_path)

        # Calculate the position to paste the logo
        logo_width, logo_height = logo.size
        qr_width, qr_height = final_img.size
        logo_size = (qr_width // 3, int((qr_width // 3) * (logo_height / logo_width)))  # Maintain aspect ratio
        logo = logo.resize(logo_size, Image.LANCZOS)
        logo_position = ((qr_width - logo_size[0]) // 2, (qr_height - logo_size[1]) // 2)

        # Paste the logo onto the QR code
        final_img.paste(logo, logo_position, logo)

        qr_code_path = f'media/qr_codes/{self.slug}_{self.student_number}.png'
        os.makedirs(os.path.dirname(qr_code_path), exist_ok=True)
        final_img.save(qr_code_path)
        return settings.SITE_URL + qr_code_path

    def __str__(self):
        return f'{self.name}'


class Course(models.Model):
    class Meta:
        verbose_name = "Course"
        verbose_name_plural = "Courses"

    class_level = models.ForeignKey('ClassLevel', on_delete=models.CASCADE, related_name='class_level_course')
    code = models.CharField(max_length=7, null=False,
                            blank=False, unique=True, help_text="Course code")
    title = models.CharField(max_length=255, null=False,
                             blank=False, help_text="Name of the course")
    lecturer = models.ForeignKey(
        'Lecturer', on_delete=models.SET_NULL, related_name='course_lecturer', null=True, blank=True,
        help_text="Lecturer teaching the course")
    slug = models.SlugField(max_length=255, editable=False, null=False, blank=False, help_text="Slug of the course")

    created_at = models.DateTimeField(auto_now_add=True, help_text="Date and time this course was added")
    updated_at = models.DateTimeField(auto_now=True, help_text="Date and time this course was last updated")

    def save(self, *args, **kwargs):
        self.slug = slugify(self.title)
        super().save(*args, **kwargs)

    def __str__(self):
        return f'{self.code} {self.title}'


class CourseDelegate(models.Model):
    class Meta:
        verbose_name = "Course Delegate"
        verbose_name_plural = "Course Delegates"

    class RoleChoices(models.TextChoices):
        DELEGATE = 'delegate', 'Delegate'
        ASSISTANT = 'assistant', 'Assistant'

    student = models.ForeignKey(
        Student, on_delete=models.CASCADE, related_name='student_delegates')
    course = models.ForeignKey(
        'Course', on_delete=models.CASCADE, related_name='course_delegates')
    role = models.CharField(
        max_length=100, choices=RoleChoices.choices, default=RoleChoices.DELEGATE)

    created_at = models.DateTimeField(auto_now_add=True, help_text="Date and time this student delegate was added")
    updated_at = models.DateTimeField(auto_now=True, help_text="Date and time this student delegate was last updated")

    def save(self, *args, **kwargs):
        if self.student.class_level != self.course.class_level:
            raise ValueError("The class level of the student does not match the class level of the course.")
        super().save(*args, **kwargs)

    def __str__(self):
        return f'{self.student.name} - {self.get_role_display()} for {self.course.title}'


class CourseRegistration(models.Model):
    class Meta:
        verbose_name = "Course Registration"
        verbose_name_plural = "Course Registrations"

    student = models.ForeignKey(
        Student, on_delete=models.CASCADE, related_name='registration')
    course = models.ForeignKey(
        'Course', on_delete=models.CASCADE, related_name='registration')

    created_at = models.DateTimeField(auto_now_add=True, help_text="Date and time this course registration was added")
    updated_at = models.DateTimeField(auto_now=True,
                                      help_text="Date and time this course registration was last updated")

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)

    def __str__(self):
        return f'{self.student.name} registered for {self.course.title}'


class Lecturer(models.Model):
    class Meta:
        verbose_name = "Lecturer"
        verbose_name_plural = "Lecturers"

    name = models.CharField(max_length=255, null=False,
                            blank=False, help_text="Name of the lecturer")
    slug = models.SlugField(max_length=255, editable=False, null=False, blank=False, help_text="Slug of the lecturer")
    department = models.CharField(max_length=255, choices=DepartmentChoices.choices, null=False, blank=False,
                                  help_text="Department of the lecturer: BMS or ICT", default=DepartmentChoices.ICT)
    phone = models.CharField(max_length=255, null=True, blank=True, help_text="Lecturer's phone number: 6xx xx xx xx")

    created_at = models.DateTimeField(auto_now_add=True, help_text="Date and time this lecturer was added")
    updated_at = models.DateTimeField(auto_now=True, help_text="Date and time this lecturer was last updated")

    def save(self, *args, **kwargs):
        self.slug = slugify(self.name)
        super().save()

    def __str__(self):
        return self.name


class TeachingRecord(models.Model):
    class Meta:
        verbose_name = "Teaching Record"
        verbose_name_plural = "Teaching Records"

    class QualityChoices(models.TextChoices):
        APPROVED = 'Approved', 'Approved'
        REJECTED = 'Rejected', 'Rejected'

    attendance = models.OneToOneField('Attendance', on_delete=models.CASCADE, related_name='teaching_record')
    description = models.TextField(
        null=False, blank=False, help_text="What was taught in the course")
    quality_assurance = models.CharField(
        max_length=255, choices=QualityChoices.choices, null=True, blank=True, default=QualityChoices.APPROVED,
        help_text="Quality assurance of the course")
    lecturer_arrival_time = models.TimeField(
        null=True, blank=True, help_text="Time of arrival of the lecturer")
    lecturer_departure_time = models.TimeField(
        null=True, blank=True, help_text="Time of departure of the lecturer")
    lecturer_duration = models.DurationField(
        editable=False, null=True, blank=True,
        help_text="Actual duration of the course by the lecturer (Automatically calculated)")

    created_at = models.DateTimeField(auto_now_add=True, help_text="Date and time this teaching record was added")
    updated_at = models.DateTimeField(auto_now=True, help_text="Date and time this teaching record was last updated")

    def save(self, *args, **kwargs):
        if self.lecturer_arrival_time and self.lecturer_departure_time:
            if is_valid_time(self.lecturer_arrival_time, self.lecturer_departure_time):
                self.lecturer_duration = calculate_duration(self.lecturer_arrival_time, self.lecturer_departure_time)
            else:
                raise ValueError("Invalid time range")
        super().save(*args, **kwargs)

    def __str__(self):
        return f"Teaching Record for {self.attendance.course}"


class CourseAttendance(models.Model):
    class Meta:
        verbose_name = "Course Attendance"
        verbose_name_plural = "Course Attendances"
        unique_together = ('student', 'attendance')

    student = models.ForeignKey(Student, on_delete=models.CASCADE, related_name='student_enrollments')
    attendance = models.ForeignKey('Attendance', on_delete=models.CASCADE, related_name='course_attendance')

    created_at = models.DateTimeField(auto_now_add=True, help_text="Date and time this enrollment was added")
    updated_at = models.DateTimeField(auto_now=True, help_text="Date and time this enrollment was last updated")

    def __str__(self):
        return f"{self.student.name} enrolled in {self.attendance.course.title}"


class ClassLevel(models.Model):
    class Meta:
        verbose_name = 'Class Level'
        verbose_name_plural = 'Class Levels'
        unique_together = ('level', 'group', 'semester', 'year')

    class LevelChoices(models.IntegerChoices):
        LEVEL_1 = 1, 'Level 1'
        LEVEL_2 = 2, 'Level 2'
        LEVEL_3 = 3, 'Level 3'
        LEVEL_4 = 4, 'Level 4'

    level = models.PositiveSmallIntegerField(choices=LevelChoices.choices, null=False, blank=False,
                                             help_text='Level of the class')
    group = models.PositiveSmallIntegerField(default=1, null=False, blank=False, help_text='Group of the class')
    department = models.CharField(
        max_length=255, choices=DepartmentChoices.choices, null=False, blank=False,
        help_text="Department of the class: BMS or ICT")
    slug = models.SlugField(max_length=255, editable=False, null=False, blank=False, help_text="Slug of the class")
    about = models.TextField(max_length=255, null=True, blank=True)
    main_hall = models.CharField(max_length=255, null=False, blank=False,
                                 help_text="Main hall of the class. Enter <strong>Online</strong> for not onsite "
                                           "levels.")
    secondary_hall = models.CharField(max_length=255, null=True, blank=True, help_text="Secondary hall of the class")
    semester = models.CharField(
        max_length=255, choices=SemesterChoices.choices, null=False, blank=False,
        help_text="Semester of the class level")
    year = models.IntegerField(
        default=get_current_year, null=False, blank=False, help_text="Semester's year of the class level")

    is_visible = models.BooleanField(default=True, help_text="Whether the class should be displayed or not")
    created_at = models.DateTimeField(auto_now_add=True, help_text="Date and time this class level was added")
    updated_at = models.DateTimeField(auto_now=True, help_text="Date and time this class level was last updated")

    def save(self, *args, **kwargs):
        if self.group < 1:
            raise ValueError("The value of group cannot be less than 1.")

        self.slug = slugify(
            f'{self.get_level_display()} - Group {self.group} - {self.semester} - {self.year} - {self.department}')
        super().save(*args, **kwargs)

    def __str__(self):
        return f'{self.get_level_display()} - Group {self.group} - {self.semester} {self.year} - {self.department}'


class ClassLevelUser(models.Model):
    class Meta:
        verbose_name = 'Class Level User'
        verbose_name_plural = 'Class Level Users'

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='class_level_users')
    class_level = models.ForeignKey('ClassLevel', on_delete=models.CASCADE, related_name='class_level_users')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f'{self.user.username} - {self.class_level}'


class Attendance(models.Model):
    class Meta:
        verbose_name = "Attendance"
        verbose_name_plural = "Attendances"

    class_level = models.ForeignKey(ClassLevel, on_delete=models.CASCADE, related_name='class_level_attendance')
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name='course_attendance')
    course_date = models.DateField(null=False, blank=False, help_text="Date the course is taught")
    course_start_time = models.TimeField(null=False, blank=False, help_text="Time the course started")
    course_end_time = models.TimeField(null=False, blank=False, help_text="Time the course ended")
    course_duration = models.DurationField(editable=False, null=True, blank=True,
                                           help_text="Actual duration of the course (Automatically calculated)")
    is_catchup = models.BooleanField(default=False, help_text="Is the course a catch-up course?")

    created_at = models.DateTimeField(auto_now_add=True, help_text="Date and time this course attendance was added")
    updated_at = models.DateTimeField(auto_now=True, help_text="Date and time this course attendance was last updated")

    def has_teaching_record(self):
        return TeachingRecord.objects.filter(attendance=self).exists()

    @staticmethod
    def count_attendance(self):
        return Attendance.objects.filter(course=self).count()

    def clean(self):
        # Ensure there's no conflict with other attendance on the same course
        overlapping_attendance = Attendance.objects.filter(
            course=self.course,
            course_date=self.course_date,
            course_start_time=self.course_start_time
        ).exclude(pk=self.pk)  # Exclude current record when editing

        if overlapping_attendance.exists():
            raise ValidationError("Attendance for this course at the same time already exists.")

    def save(self, *args, **kwargs):
        # Validate times
        if not is_valid_time(self.course_start_time, self.course_end_time):
            raise ValueError("Invalid time range")

        # Calculate course duration
        if self.course_start_time and self.course_end_time:
            self.course_duration = calculate_duration(self.course_start_time, self.course_end_time)
        self.full_clean()
        super().save(*args, **kwargs)

        # Automatically add CourseDelegate to CourseAttendance
        course_delegates = CourseDelegate.objects.filter(course=self.course)
        for delegate in course_delegates:
            CourseAttendance.objects.get_or_create(student=delegate.student, attendance=self)

    def __str__(self):
        return (f"Attendance for {self.course.code} {self.course.title} "
                f"on {self.course_date} at {self.course_start_time}")


class Profile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    phone_number = models.CharField(max_length=15, blank=True, null=True)

    created_at = models.DateTimeField(auto_now_add=True, help_text="Date and time this profile was added")
    updated_at = models.DateTimeField(auto_now=True, help_text="Date and time this profile was last updated")

    def __str__(self):
        return f'{self.user.username} profile'


class Feedback(models.Model):
    class Meta:
        verbose_name = "Feedback"
        verbose_name_plural = "Feedbacks"

    class FeedbackTypeChoices(models.TextChoices):
        COMPLAINT = 'Complaint', 'Complaint'
        SUGGESTION = 'Suggestion', 'Suggestion'
        COMPLIMENT = 'Compliment', 'Compliment'

    class FeedbackStatusChoices(models.TextChoices):
        PENDING = 'Pending', 'Pending'
        RESOLVED = 'Resolved', 'Resolved'

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='user_feedbacks')
    feedback_type = models.CharField(
        max_length=255, choices=FeedbackTypeChoices.choices, null=False, blank=False,
        help_text="Type of feedback: Complaint, Suggestion, Compliment")
    feedback = models.TextField(null=False, blank=False, help_text="Feedback message")
    status = models.CharField(
        max_length=255, choices=FeedbackStatusChoices.choices, null=False, blank=False,
        default=FeedbackStatusChoices.PENDING,
        help_text="Status of the feedback: Pending, Resolved")

    created_at = models.DateTimeField(auto_now_add=True, help_text="Date and time this feedback was added")
    updated_at = models.DateTimeField(auto_now=True, help_text="Date and time this feedback was last updated")

    def __str__(self):
        return f"{self.get_feedback_type_display()} by {self.user.username}"
