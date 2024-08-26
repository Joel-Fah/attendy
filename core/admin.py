from django.contrib import admin
from django_summernote.admin import SummernoteModelAdmin
from django import forms
from .models import Student, StudentDelegate, Lecturer, TeachingRecord, Course, Enrollment


# Register your models here.


class StudentAdmin(admin.ModelAdmin):
    model = Student
    list_display = ['name', 'matricule', 'phone', 'is_present']
    list_filter = ['department', 'is_present', 'is_delegate']
    search_fields = ['name', 'matricule', 'email', 'department', 'phone']
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

    def student_name(self, obj):
        return obj.student.name

    def course_title(self, obj):
        return obj.course.title

    def save_model(self, request, obj, form, change):
        super().save_model(request, obj, form, change)
        obj.save()


class LecturerAdmin(admin.ModelAdmin):
    model = Lecturer
    list_display = ['name', 'is_present', 'arrival', 'departure']
    list_filter = ['is_present']
    search_fields = ['name', 'arrival', 'departure']
    list_per_page = 25

    readonly_fields = ['updated_at', 'created_at']


class TeachingRecordAdmin(SummernoteModelAdmin):
    model = TeachingRecord
    list_display = ['course_title', 'lecturer_name', 'quality_assurance']
    list_filter = ['quality_assurance']
    search_fields = ['course__title', 'lecturer__name']

    summernote_fields = ['description']

    readonly_fields = ['updated_at', 'created_at']

    # get course title
    def course_title(self, obj):
        return obj.course.title

    # get lecturer name
    def lecturer_name(self, obj):
        return obj.lecturer.name


class CourseAdmin(admin.ModelAdmin):
    model = Course
    list_display = ['title', 'code', 'semester_year']
    list_filter = ['semester']
    search_fields = ['title', 'code']
    list_per_page = 25

    readonly_fields = ['slug', 'duration', 'updated_at', 'created_at']

    def semester_year(self, obj):
        return f'{obj.semester} {obj.year}'


class EnrollmentAdmin(admin.ModelAdmin):
    model = Enrollment
    list_display = ['student_name', 'course_title']
    list_filter = ['course']
    search_fields = ['student_name', 'course_title']
    list_per_page = 25

    def student_name(self, obj):
        return obj.student.name

    def course_title(self, obj):
        return obj.course.title


# Register on dashboard admin
admin.site.register(Student, StudentAdmin)
admin.site.register(StudentDelegate, StudentDelegateAdmin)
admin.site.register(Lecturer, LecturerAdmin)
admin.site.register(TeachingRecord, TeachingRecordAdmin)
admin.site.register(Course, CourseAdmin)
admin.site.register(Enrollment, EnrollmentAdmin)
