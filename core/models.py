from django.db import models
from datetime import datetime, timedelta

from slugify import slugify


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
    is_present = models.BooleanField(
        default=True, help_text="Is the student present?")
    is_delegate = models.BooleanField(
        default=False, help_text="Is the student a course delegate?")

    created_at = models.DateTimeField(auto_now_add=True, help_text="Date and time this student was added")
    updated_at = models.DateTimeField(auto_now=True, help_text="Date and time this student was last updated")

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

    name = models.CharField(max_length=255, null=False,
                            blank=False, help_text="Name of the lecturer")
    is_present = models.BooleanField(
        default=True, help_text="Is the lecturer present?")
    arrival = models.TimeField(
        null=False, blank=False, help_text="Time of arrival of the lecturer")
    departure = models.TimeField(
        null=False, blank=False, help_text="Time of departure of the lecturer")

    created_at = models.DateTimeField(auto_now_add=True, help_text="Date and time this lecturer was added")
    updated_at = models.DateTimeField(auto_now=True, help_text="Date and time this lecturer was last updated")

    def __str__(self):
        return self.name


class TeachingRecord(models.Model):
    class Meta:
        verbose_name = "Teaching Record"
        verbose_name_plural = "Teaching Records"

    class QualityChoices(models.TextChoices):
        APPROVED = 'Approved', 'Approved'
        REJECTED = 'Rejected', 'Rejected'

    course = models.ForeignKey(
        'Course', on_delete=models.CASCADE, related_name='courses', null=False, blank=False, help_text="Course taught")
    lecturer = models.ForeignKey(
        'Lecturer', on_delete=models.CASCADE, related_name='teaching_records', null=False, blank=False,
        help_text="Lecturer teaching the course")
    description = models.TextField(
        null=False, blank=False, help_text="What was taught in the course")
    quality_assurance = models.CharField(
        max_length=255, choices=QualityChoices.choices, null=True, blank=True, default=QualityChoices.APPROVED,
        help_text="Quality assurance of the course")

    created_at = models.DateTimeField(auto_now_add=True, help_text="Date and time this teaching record was added")
    updated_at = models.DateTimeField(auto_now=True, help_text="Date and time this teaching record was last updated")

    def __str__(self):
        return f"{self.course.title} taught by {self.lecturer.name}"


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
    slug = models.SlugField(max_length=255, editable=False, null=False, blank=False, help_text="Slug of the course")
    start_time = models.TimeField(
        null=False, blank=False, help_text="Start time of the course")
    end_time = models.TimeField(
        null=False, blank=False, help_text="End time of the course")
    duration = models.DurationField(
        help_text="Duration of the course (Automatically calculated)")
    is_catchup = models.BooleanField(
        default=False, help_text="Is this a catch-up course?")
    semester = models.CharField(
        max_length=255, choices=SemesterChoices.choices, null=False, blank=False, help_text="Semester of the course")
    year = models.IntegerField(
        default=get_current_year, null=False, blank=False, help_text="Semesters' year of the course")

    created_at = models.DateTimeField(auto_now_add=True, help_text="Date and time this course was added")
    updated_at = models.DateTimeField(auto_now=True, help_text="Date and time this course was last updated")

    def save(self, *args, **kwargs):
        if self.start_time and self.end_time:
            # Assuming the date part is not important, use today's date for both times
            today = datetime.today().date()
            start_datetime = datetime.combine(today, self.start_time)
            end_datetime = datetime.combine(today, self.end_time)

            # Calculate the duration
            self.duration = end_datetime - start_datetime

            # If finish time is earlier than start time, assume it is on the next day
            if self.duration < timedelta(0):
                self.duration += timedelta(days=1)

        self.slug = slugify(self.title)
        super().save(*args, **kwargs)

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
