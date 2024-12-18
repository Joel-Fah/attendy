from django.contrib import admin
from django.utils.safestring import mark_safe
from django_summernote.admin import SummernoteModelAdmin
from django import forms
from .models import Student, CourseDelegate, Lecturer, TeachingRecord, Course, CourseAttendance, \
    ClassLevel, ClassLevelUser, Attendance, Profile, Feedback, CourseRegistration


# Register your models here.


class StudentAdmin(admin.ModelAdmin):
    model = Student
    list_display = ['class_level', 'student_number', 'name', 'phone', 'gender', 'is_delegate']
    list_filter = ['class_level__department', 'gender', 'is_delegate']
    search_fields = ['name', 'student_number', 'email', 'phone']
    list_per_page = 25

    readonly_fields = ['encoded_data', 'updated_at', 'created_at']


class CourseAdmin(admin.ModelAdmin):
    model = Course
    list_display = ['code', 'title', 'level_group', 'semester_year']
    list_filter = ['class_level__semester', 'class_level__year']
    search_fields = ['title', 'code']
    list_per_page = 25

    readonly_fields = ['updated_at', 'created_at']

    @staticmethod
    def semester_year(obj):
        return f'{obj.class_level.semester} {obj.class_level.year}'

    @staticmethod
    def level_group(obj):
        return f'{obj.class_level.get_level_display()} - Group {obj.class_level.group}'


class CourseRegistrationAdmin(admin.ModelAdmin):
    model = CourseRegistration
    list_display = ['student__name', 'course__title', 'semester_year']
    list_filter = ['course__class_level__semester', 'course__class_level__year']
    search_fields = ['student__name', 'course__title']
    list_per_page = 25

    readonly_fields = ['updated_at', 'created_at']

    @staticmethod
    def semester_year(obj):
        return f'{obj.course.class_level.semester} {obj.course.class_level.year}'


class CourseDelegateForm(forms.ModelForm):
    student = forms.ModelChoiceField(
        queryset=Student.objects.filter(is_delegate=True),
        required=True,
        label="Course Delegate"
    )

    class Meta:
        model = CourseDelegate
        fields = '__all__'

    def clean(self):
        cleaned_data = super().clean()
        student = cleaned_data.get('student')
        course = cleaned_data.get('course')

        if student and course:
            if student.class_level != course.class_level:
                raise forms.ValidationError(
                    mark_safe(
                        f"<strong>{student.name}</strong> ({student.class_level}) cannot be a course delegate for a "
                        f"course in <strong>{course.class_level}</strong>.<br>"
                        "The class level of the student must match that of the course."
                    )
                )

        return cleaned_data

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['course'].label_from_instance = self.label_from_instance

    @staticmethod
    def label_from_instance(obj):
        return f"{obj.title} | {obj.class_level}"


class CourseDelegateAdmin(admin.ModelAdmin):
    model = CourseDelegate
    form = CourseDelegateForm
    list_display = ['student__name', 'course__title', 'role']
    list_filter = ['role']
    search_fields = ['student__name', 'course__title']
    list_per_page = 25

    def save_model(self, request, obj, form, change):
        super().save_model(request, obj, form, change)
        obj.save()


class LecturerAdmin(admin.ModelAdmin):
    model = Lecturer
    list_display = ['name', 'department', 'email', 'phone']
    list_filter = ['department']
    search_fields = ['name', 'phone']
    list_per_page = 25

    readonly_fields = ['updated_at', 'created_at']


class TeachingRecordAdmin(SummernoteModelAdmin):
    model = TeachingRecord
    list_display = ['attendance__id', 'course_title', 'lecturer_name', 'lecturer_duration', 'quality_assurance']
    list_filter = ['quality_assurance']
    search_fields = ['attendance__course__title', 'attendance__course__lecturer__name']

    summernote_fields = ['description']

    readonly_fields = ['lecturer_duration', 'updated_at', 'created_at']

    @staticmethod
    def course_title(obj):
        return obj.attendance.course

    @staticmethod
    def lecturer_name(obj):
        return obj.attendance.course.lecturer


class CourseAttendanceAdmin(admin.ModelAdmin):
    model = CourseAttendance
    list_display = ['student__name', 'course_title', 'class_level']
    search_fields = ['student__name', 'student__student_number', 'attendance']
    list_per_page = 25

    readonly_fields = ['updated_at', 'created_at']

    @staticmethod
    def course_title(obj):
        return obj.attendance.course.title

    @staticmethod
    def class_level(obj):
        return obj.attendance.class_level


class ClassLevelAdmin(admin.ModelAdmin):
    model = ClassLevel
    list_display = ['level', 'group', 'department', 'main_hall', 'semester_year']
    list_filter = ['level', 'group', 'department']
    search_fields = ['level', 'group']
    list_per_page = 25

    readonly_fields = ['updated_at', 'created_at']

    @staticmethod
    def semester_year(obj):
        return f'{obj.semester} {obj.year}'


class ClassLevelUserAdmin(admin.ModelAdmin):
    model = ClassLevelUser
    list_display = ['user', 'class_level']
    list_filter = ['class_level']
    search_fields = ['user', 'class_level']
    list_per_page = 25

    readonly_fields = ['updated_at', 'created_at']


class AttendanceAdmin(admin.ModelAdmin):
    model = Attendance
    list_display = ['id', 'course__title', 'course__lecturer__name', 'course_date', 'class_level_name', 'record_id']
    list_filter = ['course_date', 'is_catchup', 'class_level']
    search_fields = ['course__title']
    list_per_page = 25

    readonly_fields = ['course_duration', 'updated_at', 'created_at']

    @staticmethod
    def record_id(obj):
        return obj.teaching_record.id

    @staticmethod
    def class_level_name(obj):
        return f'{obj.class_level.get_level_display()} - Group {obj.class_level.group}'


class ProfileAdmin(admin.ModelAdmin):
    model = Profile
    list_display = ['user', 'phone_number', ]
    search_fields = ['user', 'phone_number']

    readonly_fields = ['updated_at', 'created_at']


class FeedbackAdmin(admin.ModelAdmin):
    model = Feedback
    list_display = ['user', 'feedback_type', 'status']
    list_filter = ['user', 'feedback_type', 'status']
    search_fields = ['feedback']

    readonly_fields = ['updated_at', 'created_at']


# Register on dashboard admin
admin.site.register(Student, StudentAdmin)
admin.site.register(CourseDelegate, CourseDelegateAdmin)
admin.site.register(Lecturer, LecturerAdmin)
admin.site.register(TeachingRecord, TeachingRecordAdmin)
admin.site.register(Course, CourseAdmin)
admin.site.register(CourseAttendance, CourseAttendanceAdmin)
admin.site.register(Attendance, AttendanceAdmin)
admin.site.register(ClassLevel, ClassLevelAdmin)
admin.site.register(ClassLevelUser, ClassLevelUserAdmin)
admin.site.register(Profile, ProfileAdmin)
admin.site.register(Feedback, FeedbackAdmin)
admin.site.register(CourseRegistration, CourseRegistrationAdmin)
