from datetime import datetime

from django.db import models
from django.db.models import UniqueConstraint
from django.contrib.auth.models import User, Group
from slugify import slugify

from .utils import calculate_duration, is_valid_time


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

    class GenderChoices(models.TextChoices):
        MALE = 'Male', 'Male'
        FEMALE = 'Female', 'Female'

    class_level = models.ForeignKey('ClassLevel', on_delete=models.CASCADE, related_name='class_level_students')
    name = models.CharField(max_length=255, null=False,
                            blank=False, help_text="Name of the student")
    slug = models.SlugField(max_length=255, editable=False, null=False, blank=False, help_text="Slug of the student")
    student_number = models.CharField(max_length=255, null=False, blank=False,
                                      unique=True, default='ICTUXXXXxxxx', help_text="Student number")
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

    created_at = models.DateTimeField(auto_now_add=True, help_text="Date and time this student was added")
    updated_at = models.DateTimeField(auto_now=True, help_text="Date and time this student was last updated")

    def save(self, *args, **kwargs):
        self.slug = slugify(self.name)
        super().save(*args, **kwargs)

    def __str__(self):
        return self.name


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
    semester = models.CharField(
        max_length=255, choices=SemesterChoices.choices, null=False, blank=False, help_text="Semester of the course")
    year = models.IntegerField(
        default=get_current_year, null=False, blank=False, help_text="Semesters' year of the course")
    department = models.CharField(
        max_length=255, choices=DepartmentChoices.choices, null=False, blank=False,
        help_text="Department of the class: BMS or ICT")
    slug = models.SlugField(max_length=255, editable=False, null=False, blank=False, help_text="Slug of the class")
    about = models.TextField(max_length=255, null=True, blank=True)
    main_hall = models.CharField(max_length=255, null=False, blank=False,
                                 help_text="Main hall of the class. Enter <strong>Online</strong> for not onsite "
                                           "levels.")
    secondary_hall = models.CharField(max_length=255, null=True, blank=True, help_text="Secondary hall of the class")

    is_visible = models.BooleanField(default=True, help_text="Whether the class should be displayed or not")
    created_at = models.DateTimeField(auto_now_add=True, help_text="Date and time this class level was added")
    updated_at = models.DateTimeField(auto_now=True, help_text="Date and time this class level was last updated")

    def save(self, *args, **kwargs):
        self.slug = slugify(
            f'{self.get_level_display()} - Group {self.group} - {self.semester} {self.year} - {self.department}')
        super().save(*args, **kwargs)

    def __str__(self):
        return f'{self.get_level_display()} - Group {self.group}: {self.semester} {self.year} - {self.department}'


class ClassLevelUser(models.Model):
    class Meta:
        verbose_name = 'Class Level User'
        verbose_name_plural = 'Class Level Users'
        unique_together = ('user', 'class_level')

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
        constraints = [
            UniqueConstraint(fields=['course', 'teaching_record'], name='unique_course_record')
        ]

    class_level = models.ForeignKey(ClassLevel, on_delete=models.CASCADE, related_name='class_level_attendance')
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


class Profile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    phone_number = models.CharField(max_length=15, blank=True, null=True)

    created_at = models.DateTimeField(auto_now_add=True, help_text="Date and time this profile was added")
    updated_at = models.DateTimeField(auto_now=True, help_text="Date and time this profile was last updated")

    def __str__(self):
        return f'{self.user.username} profile'
