from datetime import datetime

from django.db import models
from slugify import slugify

from .utils import calculate_duration, is_valid_time


# Create your models here.


def get_current_year():
    return datetime.now().year


class DepartmentChoices(models.TextChoices):
    BMS = 'BMS', 'BMS'
    ICT = 'ICT', 'ICT'


class Student(models.Model):
    class Meta:
        verbose_name = "Student"
        verbose_name_plural = "Students"

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
        Student, on_delete=models.CASCADE, related_name='student_delegates')
    course = models.ForeignKey(
        'Course', on_delete=models.CASCADE, related_name='course_delegates')
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
        return (f"Record for {self.teaching_record_attendance.course.title} "
                f"by {self.teaching_record_attendance.course.lecturer.name}")


class Course(models.Model):
    class Meta:
        verbose_name = "Course"
        verbose_name_plural = "Courses"

    class SemesterChoices(models.TextChoices):
        FALL = 'FALL', 'FALL'
        SPRING = 'SPRING', 'SPRING'
        SUMMER = 'SUMMER', 'SUMMER'

    code = models.CharField(max_length=7, null=False,
                            blank=False, unique=True, help_text="Course code")
    title = models.CharField(max_length=255, null=False,
                             blank=False, help_text="Name of the course")
    lecturer = models.ForeignKey(
        'Lecturer', on_delete=models.CASCADE, related_name='course_lecturer', null=False, blank=False,
        help_text="Lecturer teaching the course")
    slug = models.SlugField(max_length=255, editable=False, null=False, blank=False, help_text="Slug of the course")
    semester = models.CharField(
        max_length=255, choices=SemesterChoices.choices, null=False, blank=False, help_text="Semester of the course")
    year = models.IntegerField(
        default=get_current_year, null=False, blank=False, help_text="Semesters' year of the course")

    created_at = models.DateTimeField(auto_now_add=True, help_text="Date and time this course was added")
    updated_at = models.DateTimeField(auto_now=True, help_text="Date and time this course was last updated")

    def save(self, *args, **kwargs):
        self.slug = slugify(self.title)
        super().save(*args, **kwargs)

    def __str__(self):
        return f'{self.code} {self.title}'


class Enrollment(models.Model):
    class Meta:
        verbose_name = "Enrollment"
        verbose_name_plural = "Enrollments"
        unique_together = ('student', 'attendance')

    student = models.ForeignKey(Student, on_delete=models.CASCADE, related_name='student_enrollments')
    attendance = models.ForeignKey('CourseAttendance', on_delete=models.CASCADE, related_name='course_attendance')

    created_at = models.DateTimeField(auto_now_add=True, help_text="Date and time this enrollment was added")
    updated_at = models.DateTimeField(auto_now=True, help_text="Date and time this enrollment was last updated")

    def __str__(self):
        return f"{self.student.name} enrolled in {self.attendance.course.title}"


class CourseAttendance(models.Model):
    class Meta:
        verbose_name = "Course Attendance"
        verbose_name_plural = "Course Attendances"

    course = models.OneToOneField(Course, on_delete=models.CASCADE, related_name='course_attendance')
    teaching_record = models.OneToOneField(TeachingRecord, on_delete=models.CASCADE, null=True, blank=True,
                                           related_name='teaching_record_attendance')
    course_date = models.DateField(null=False, blank=False, help_text="Date the course is taught")
    course_start_time = models.TimeField(null=False, blank=False, help_text="Time the course started")
    course_end_time = models.TimeField(null=False, blank=False, help_text="Time the course ended")
    course_duration = models.DurationField(editable=False, null=True, blank=True,
                                           help_text="Actual duration of the course (Automatically calculated)")
    is_catchup = models.BooleanField(default=False, help_text="Is the course a catch-up course?")

    created_at = models.DateTimeField(auto_now_add=True, help_text="Date and time this course attendance was added")
    updated_at = models.DateTimeField(auto_now=True, help_text="Date and time this course attendance was last updated")

    def has_teaching_record(self):
        return TeachingRecord.objects.filter(course=self).exists()

    def save(self, *args, **kwargs):
        # Automatically create a teaching record for the course
        if not self.teaching_record:
            self.teaching_record = TeachingRecord.objects.create(
                description=f"Teaching record for {self.course.title} by {self.course.lecturer.name}",
            )

        # Validate times
        if not is_valid_time(self.course_start_time, self.course_end_time):
            raise ValueError("Invalid time range")

        # Calculate course duration
        if self.course_start_time and self.course_end_time:
            self.course_duration = calculate_duration(self.course_start_time, self.course_end_time)
        super().save(*args, **kwargs)

    def __str__(self):
        return f"Attendance for {self.course.code} {self.course.title} on {self.course_date}"
