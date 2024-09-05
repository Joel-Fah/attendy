from django.contrib import admin
from django_summernote.admin import SummernoteModelAdmin
from django import forms
from .models import Student, StudentDelegate, Lecturer, TeachingRecord, Course, Enrollment, CourseAttendance, ClassLevel


# Register your models here.


class StudentAdmin(admin.ModelAdmin):
    model = Student
    list_display = ['name', 'matricule', 'phone', 'is_delegate', 'gender']
    list_filter = ['department', 'is_delegate', 'gender']
    search_fields = ['name', 'matricule', 'email', 'phone']
    list_per_page = 25

    readonly_fields = ['updated_at', 'created_at']


class StudentDelegateForm(forms.ModelForm):
    student = forms.ModelChoiceField(
        queryset=Student.objects.filter(is_delegate=True),
        required=True,
        label="Student Delegate"
    )

    class Meta:
        model = Course
        fields = '__all__'


class StudentDelegateAdmin(admin.ModelAdmin):
    model = StudentDelegate
    form = StudentDelegateForm
    list_display = ['student_name', 'course_title', 'role']
    list_filter = ['role']
    search_fields = ['student_name', 'course_title']
    list_per_page = 25

    @staticmethod
    def student_name(obj):
        return obj.student.name

    @staticmethod
    def course_title(obj):
        return obj.course.title

    def save_model(self, request, obj, form, change):
        super().save_model(request, obj, form, change)
        obj.save()


class LecturerAdmin(admin.ModelAdmin):
    model = Lecturer
    list_display = ['name', 'department', 'phone']
    list_filter = ['department']
    search_fields = ['name', 'phone']
    list_per_page = 25

    readonly_fields = ['updated_at', 'created_at']


class TeachingRecordAdmin(SummernoteModelAdmin):
    model = TeachingRecord
    list_display = ['course_title', 'lecturer_name', 'lecturer_duration']
    list_filter = ['quality_assurance']
    search_fields = ['course_title', 'lecturer_name']

    summernote_fields = ['description']

    readonly_fields = ['lecturer_duration', 'updated_at', 'created_at']

    # get course title
    @staticmethod
    def course_title(obj):
        return obj.teaching_record_attendance.course.title

    # get lecturer name
    @staticmethod
    def lecturer_name(obj):
        return obj.teaching_record_attendance.course.lecturer.name


class CourseAdmin(admin.ModelAdmin):
    model = Course
    list_display = ['title', 'code', 'semester_year']
    list_filter = ['semester']
    search_fields = ['title', 'code']
    list_per_page = 25

    readonly_fields = ['updated_at', 'created_at']

    @staticmethod
    def semester_year(obj):
        return f'{obj.semester} {obj.year}'


class EnrollmentAdmin(admin.ModelAdmin):
    model = Enrollment
    list_display = ['student_name', 'course_title']
    list_filter = ['attendance']
    search_fields = ['student_name', 'course_title']
    list_per_page = 25

    @staticmethod
    def student_name(obj):
        return obj.student.name

    @staticmethod
    def course_title(obj):
        return obj.attendance.course.title

class ClassLevelAdmin(admin.ModelAdmin):
    model = ClassLevel
    list_display = ['level', 'group_number', 'department', 'semester_year']
    list_filter = ['level', 'group', 'department']
    search_fields = ['level', 'group']
    list_per_page = 25

    readonly_fields = ['updated_at', 'created_at']
    
    @staticmethod
    def group_number(obj):
        if obj.group:
            return obj.group
        return 'Only one group for this level'
    
    @staticmethod
    def semester_year(obj):
        return f'{obj.semester} {obj.year}'
    
class CourseAttendanceAdmin(admin.ModelAdmin):
    model = CourseAttendance
    list_display = ['course_title', 'lecturer_name', 'class_level_name']
    list_filter = ['course_date', 'is_catchup', 'class_level']
    search_fields = ['course_title']
    list_per_page = 25

    @staticmethod
    def lecturer_name(obj):
        return obj.course.lecturer.name

    @staticmethod
    def course_title(obj):
        return obj.course.title
    
    @staticmethod
    def class_level_name(obj):
        if obj.class_level.group:
            return f'{obj.class_level.get_level_display()} - Group {obj.class_level.group}'
        return obj.class_level.get_level_display()


# Register on dashboard admin
admin.site.register(Student, StudentAdmin)
admin.site.register(StudentDelegate, StudentDelegateAdmin)
admin.site.register(Lecturer, LecturerAdmin)
admin.site.register(TeachingRecord, TeachingRecordAdmin)
admin.site.register(Course, CourseAdmin)
admin.site.register(Enrollment, EnrollmentAdmin)
admin.site.register(CourseAttendance, CourseAttendanceAdmin)
admin.site.register(ClassLevel, ClassLevelAdmin)
