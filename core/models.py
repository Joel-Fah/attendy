from django.db import models
from datetime import datetime, timedelta
from django.utils import timezone

from slugify import slugify
from .utils import calculate_duration


# Create your models here.


def get_current_year():
    return datetime.now().year


class Student(models.Model):
    class Meta:
        verbose_name = "Student"
        verbose_name_plural = "Students"

    class DepartmentChoices(models.TextChoices):
        BMS = 'BMS', 'BMS'
        ICT = 'ICT', 'ICT'

    name = models.CharField(max_length=255, null=False,
                            blank=False, help_text="Name of the student")
    slug = models.SlugField(max_length=255, editable=False, null=False, blank=False, help_text="Slug of the student")
    matricule = models.CharField(max_length=255, null=False, blank=False,
                                 unique=True, default='ICTUXXXXxxxx', help_text="Student matricule")
    email = models.EmailField(
        null=False, blank=False,
        help_text="Student email address (preferably ICT University email: @ictuniversity.edu.cm)")
    department = models.CharField(
        max_length=255, choices=DepartmentChoices.choices, null=False, blank=False,
        help_text="Department of the student: BMS or ICT")
    phone = models.CharField(max_length=255, null=False,
                             blank=False, help_text="Student phone number")
    is_delegate = models.BooleanField(
        default=False, help_text="Is the student a course delegate?")

    created_at = models.DateTimeField(auto_now_add=True, help_text="Date and time this student was added")
    updated_at = models.DateTimeField(auto_now=True, help_text="Date and time this student was last updated")

    def save(self, *args, **kwargs):
        self.slug = slugify(self.name)
        super().save(*args, **kwargs)

    def __str__(self):
        return self.name


class StudentDelegate(models.Model):
    class Meta:
        verbose_name = "Student Delegate"
        verbose_name_plural = "Student Delegates"
        unique_together = ('student', 'course', 'role')

    class RoleChoices(models.TextChoices):
        DELEGATE = 'delegate', 'Delegate'
        ASSISTANT = 'assistant', 'Assistant'

    student = models.ForeignKey(
        Student, on_delete=models.CASCADE, related_name='delegates_student')
    course = models.ForeignKey(
        'Course', on_delete=models.CASCADE, related_name='delegates_course')
    role = models.CharField(
        max_length=100, choices=RoleChoices.choices, default=RoleChoices.DELEGATE)

    created_at = models.DateTimeField(auto_now_add=True, help_text="Date and time this student delegate was added")
    updated_at = models.DateTimeField(auto_now=True, help_text="Date and time this student delegate was last updated")

    def __str__(self):
        return f'{self.student.name} - {self.get_role_display()} for {self.course.title}'


class Lecturer(models.Model):
    class Meta:
        verbose_name = "Lecturer"
        verbose_name_plural = "Lecturers"

    class DepartmentChoices(models.TextChoices):
        BMS = 'BMS', 'BMS'
        ICT = 'ICT', 'ICT'

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

    course = models.OneToOneField(
        'Course', on_delete=models.CASCADE, related_name='teaching_record', null=False, blank=False,
        help_text="Course taught")
    description = models.TextField(
        null=False, blank=False, help_text="What was taught in the course")
    quality_assurance = models.CharField(
        max_length=255, choices=QualityChoices.choices, null=True, blank=True, default=QualityChoices.APPROVED,
        help_text="Quality assurance of the course")
    is_present = models.BooleanField(
        default=True, help_text="Was the lecturer present?")
    arrival = models.TimeField(
        null=True, blank=True, help_text="Time of arrival of the lecturer")
    departure = models.TimeField(
        null=True, blank=True, help_text="Time of departure of the lecturer")
    lecture_duration = models.DurationField(
        editable=False, null=True, blank=True,
        help_text="Actual duration of the course by the lecturer (Automatically calculated)")

    created_at = models.DateTimeField(auto_now_add=True, help_text="Date and time this teaching record was added")
    updated_at = models.DateTimeField(auto_now=True, help_text="Date and time this teaching record was last updated")

    def save(self, *args, **kwargs):
        if self.arrival and self.departure:
            self.lecture_duration = calculate_duration(self.arrival, self.departure)
        super().save(*args, **kwargs)

    def __str__(self):
        return f"Record for {self.course.title} by {self.course.lecturer.name}"


class Course(models.Model):
    class Meta:
        verbose_name = "Course"
        verbose_name_plural = "Courses"

    class SemesterChoices(models.TextChoices):
        FALL = 'FALL', 'FALL'
        SPRING = 'SPRING', 'SPRING'
        SUMMER = 'SUMMER', 'SUMMER'

    code = models.CharField(max_length=255, null=False,
                            blank=False, unique=True, help_text="Course code")
    title = models.CharField(max_length=255, null=False,
                             blank=False, help_text="Name of the course")
    lecturer = models.ForeignKey(
        'Lecturer', on_delete=models.CASCADE, related_name='teaching_records', null=False, blank=False,
        help_text="Lecturer teaching the course")
    slug = models.SlugField(max_length=255, editable=False, null=False, blank=False, help_text="Slug of the course")
    date = models.DateField(
        null=False, blank=False, default=timezone.now, help_text="Date the course is taught")
    start_time = models.TimeField(
        null=False, blank=False, help_text="Start time of the course")
    end_time = models.TimeField(
        null=False, blank=False, help_text="End time of the course")
    duration = models.DurationField(
        editable=False,
        help_text="Duration of the course (Automatically calculated)")
    is_catchup = models.BooleanField(
        default=False, help_text="Is this a catch-up class?")
    semester = models.CharField(
        max_length=255, choices=SemesterChoices.choices, null=False, blank=False, help_text="Semester of the course")
    year = models.IntegerField(
        default=get_current_year, null=False, blank=False, help_text="Semesters' year of the course")

    created_at = models.DateTimeField(auto_now_add=True, help_text="Date and time this course was added")
    updated_at = models.DateTimeField(auto_now=True, help_text="Date and time this course was last updated")

    def save(self, *args, **kwargs):
        if self.start_time and self.end_time:
            self.duration = calculate_duration(self.start_time, self.end_time)
        self.slug = slugify(self.title)
        super().save(*args, **kwargs)
        if not TeachingRecord.objects.filter(course=self).exists():
            TeachingRecord.objects.create(course=self,
                                          description=f'Teaching record for the course: {self.code} {self.title}')

    def has_teaching_record(self):
        return TeachingRecord.objects.filter(course=self).exists()

    def __str__(self):
        return f'{self.code} {self.title}'


class Enrollment(models.Model):
    class Meta:
        verbose_name = "Enrollment"
        verbose_name_plural = "Enrollments"
        unique_together = ('student', 'course')

    student = models.ForeignKey(Student, on_delete=models.CASCADE)
    course = models.ForeignKey(Course, on_delete=models.CASCADE)

    created_at = models.DateTimeField(auto_now_add=True, help_text="Date and time this enrollment was added")
    updated_at = models.DateTimeField(auto_now=True, help_text="Date and time this enrollment was last updated")

    def __str__(self):
        return f"{self.student.name} enrolled in {self.course.title}"
