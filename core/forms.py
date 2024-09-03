import datetime

from django import forms
from allauth.account.forms import LoginForm
from .models import Course, Lecturer, Student, DepartmentChoices, TeachingRecord
from django_summernote.fields import SummernoteTextField
from django_summernote.widgets import SummernoteWidget, SummernoteInplaceWidget


# Create your forms here
class UserLoginForm(LoginForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # login field
        self.fields['login'].widget.attrs.update({
            'id': 'login',
            'name': 'login',
            'placeholder': 'attendy@ictuniversity.edu.cm',
            'class': 'rounded-2xl block w-full ps-10 p-2.5 bg-whiteColor border-darkColor placeholder-darkColor/50 '
                     'focus:ring-primaryColor focus:border-primaryColor transition-all duration-300 ease-in-out',
        })
        self.fields['login'].label = 'Student email address'
        self.fields['login'].help_text = 'Please enter your registered email address.'
        self.fields['login'].error_messages = {
            'required': 'Please enter your email address',
            'invalid_login': "Please enter a correct email and password."
        }
        self.fields['login'].required = True

        # password field
        self.fields['password'].widget.attrs.update({
            'id': 'password',
            'name': 'password',
            'placeholder': 'Password',
            'class': 'rounded-2xl block w-full ps-10 p-2.5 bg-whiteColor border-darkColor placeholder-darkColor/50 '
                     'focus:ring-primaryColor focus:border-primaryColor transition-all duration-300 ease-in-out',
        })
        self.fields['password'].label = 'Password'
        self.fields['password'].help_text = 'Enter your password.'
        self.fields['password'].error_messages = {
            'required': 'Please enter your password',
        }
        self.fields['password'].required = True


class CourseForm(forms.ModelForm):
    class Meta:
        model = Course
        fields = '__all__'

    code = forms.CharField(
        widget=forms.TextInput(
            attrs={
                'id': 'code',
                'name': 'code',
                'placeholder': 'Course code',
                'class': 'rounded-2xl block w-full ps-10 p-2.5 bg-whiteColor border-darkColor placeholder-darkColor/50 '
                         'focus:ring-primaryColor focus:border-primaryColor transition-all duration-300 ease-in-out',
            }
        ),
        label='Course code',
        help_text='Enter the code of the course.',
        error_messages={
            'required': 'Please enter the code of the course',
            'unique': 'A course with that code already exists.',
        },
        required=True,
        max_length=7,
    )

    title = forms.CharField(
        widget=forms.TextInput(
            attrs={
                'id': 'title',
                'name': 'title',
                'placeholder': 'Course title',
                'class': 'rounded-2xl block w-full ps-10 p-2.5 bg-whiteColor border-darkColor placeholder-darkColor/50 '
                         'focus:ring-primaryColor focus:border-primaryColor transition-all duration-300 ease-in-out',
            }
        ),
        label='Course title',
        help_text='Enter the title of the course.',
        error_messages={'required': 'Please enter the title of the course'},
        required=True,
    )

    lecturer = forms.ModelChoiceField(
        queryset=Lecturer.objects.all(),
        widget=forms.Select(
            attrs={
                'id': 'lecturer',
                'name': 'lecturer',
                'placeholder': 'Select lecturer',
                'class': 'rounded-2xl block w-full ps-10 p-2.5 bg-whiteColor border-darkColor placeholder-darkColor/50 '
                         'focus:ring-primaryColor focus:border-primaryColor transition-all duration-300 ease-in-out',
            }
        ),
        label='Lecturer',
        help_text='Select the lecturer teaching the course.',
        error_messages={'required': 'Please select the lecturer teaching the course'},
        required=True,
    )

    semester = forms.ChoiceField(
        widget=forms.Select(
            attrs={
                'id': 'semester',
                'name': 'semester',
                'placeholder': 'Select semester',
                'class': 'rounded-2xl block w-full ps-10 p-2.5 bg-whiteColor border-darkColor placeholder-darkColor/50 '
                         'focus:ring-primaryColor focus:border-primaryColor transition-all duration-300 ease-in-out',
            }
        ),
        label='Semester',
        help_text='Select the semester of the course.',
        choices=Course.SemesterChoices.choices,
        required=True,
    )

    year = forms.IntegerField(
        widget=forms.NumberInput(
            attrs={
                'id': 'year',
                'name': 'year',
                'placeholder': '2022',
                'class': 'rounded-2xl block w-full ps-10 p-2.5 bg-whiteColor border-darkColor placeholder-darkColor/50 '
                         'focus:ring-primaryColor focus:border-primaryColor transition-all duration-300 ease-in-out',
            }
        ),
        label='Year',
        help_text='Enter the year of the course.',
        error_messages={'required': 'Please enter the year of the course'},
        required=True,
        initial=datetime.date.today().year,
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['semester'].default = Course.SemesterChoices.FALL


class LecturerForm(forms.ModelForm):
    class Meta:
        model = Lecturer
        fields = '__all__'

    name = forms.CharField(
        widget=forms.TextInput(
            attrs={
                'id': 'name',
                'name': 'name',
                'placeholder': 'Lecturer\'s name',
                'class': 'rounded-2xl block w-full ps-10 p-2.5 bg-whiteColor border-darkColor placeholder-darkColor/50 '
                         'focus:ring-primaryColor focus:border-primaryColor transition-all duration-300 ease-in-out',
            }
        ),
        label='Lecturer\'s name',
        help_text='Enter the name of the lecturer.',
        error_messages={'required': 'Please enter the name of the lecturer'},
        required=True,
    )

    department = forms.ChoiceField(
        widget=forms.Select(
            attrs={
                'id': 'department',
                'name': 'department',
                'placeholder': 'Select department',
                'class': 'rounded-2xl block w-full ps-10 p-2.5 bg-whiteColor border-darkColor placeholder-darkColor/50 '
                         'focus:ring-primaryColor focus:border-primaryColor transition-all duration-300 ease-in-out',
            }
        ),
        label='Department',
        help_text='Select the department of the lecturer.',
        choices=DepartmentChoices.choices,
        required=True,
    )

    phone = forms.CharField(
        widget=forms.TextInput(
            attrs={
                'id': 'phone',
                'name': 'phone',
                'placeholder': 'Lecturer\'s phone number',
                'class': 'rounded-2xl block w-full ps-10 p-2.5 bg-whiteColor border-darkColor placeholder-darkColor/50 '
                         'focus:ring-primaryColor focus:border-primaryColor transition-all duration-300 ease-in-out',
            }
        ),
        label='Phone number',
        help_text='Enter the phone number of the lecturer.',
        error_messages={'required': 'Please enter the phone number of the lecturer'},
        required=False,
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['department'].default = DepartmentChoices.ICT


class StudentForm(forms.ModelForm):
    class Meta:
        model = Student
        fields = '__all__'

    name = forms.CharField(
        widget=forms.TextInput(
            attrs={
                'id': 'name',
                'name': 'name',
                'placeholder': 'Student\'s name',
                'class': 'rounded-2xl block w-full ps-10 p-2.5 bg-whiteColor border-darkColor placeholder-darkColor/50 '
                         'focus:ring-primaryColor focus:border-primaryColor transition-all duration-300 ease-in-out',
            }
        ),
        label='Student\'s name',
        help_text='Enter the name of the student.',
        error_messages={'required': 'Please enter the name of the student'},
        required=True,
    )

    matricule = forms.CharField(
        widget=forms.TextInput(
            attrs={
                'id': 'matricule',
                'name': 'matricule',
                'placeholder': 'ICTU20XXxxxx',
                'class': 'rounded-2xl block w-full ps-10 p-2.5 bg-whiteColor border-darkColor placeholder-darkColor/50 '
                         'focus:ring-primaryColor focus:border-primaryColor transition-all duration-300 ease-in-out',
            }
        ),
        label='Matricule',
        help_text='Enter the matricule of the student.',
        error_messages={
            'required': 'Please enter the matricule of the student',
            'unique': 'A student with that matricule already exists.',
        },
        required=True,
    )

    email = forms.EmailField(
        widget=forms.EmailInput(
            attrs={
                'id': 'email',
                'name': 'email',
                'placeholder': 'Student\'s email address',
                'class': 'rounded-2xl block w-full ps-10 p-2.5 bg-whiteColor border-darkColor placeholder-darkColor/50 '
                         'focus:ring-primaryColor focus:border-primaryColor transition-all duration-300 ease-in-out',
            }
        ),
        label='Email address',
        help_text='Enter the email address of the student.',
        error_messages={
            'required': 'Please enter the email address of the student',
            'invalid': 'Enter a valid email address.',
            'unique': 'A student with that email already exists.',
        },
        required=True,
    )

    department = forms.ChoiceField(
        widget=forms.Select(
            attrs={
                'id': 'department',
                'name': 'department',
                'placeholder': 'Select department',
                'class': 'rounded-2xl block w-full ps-10 p-2.5 bg-whiteColor border-darkColor placeholder-darkColor/50 '
                         'focus:ring-primaryColor focus:border-primaryColor transition-all duration-300 ease-in-out',
            }
        ),
        label='Department',
        help_text='Select the department of the student.',
        choices=DepartmentChoices.choices,
        required=True,
    )

    phone = forms.CharField(
        widget=forms.TextInput(
            attrs={
                'id': 'phone',
                'name': 'phone',
                'placeholder': 'Student\'s phone number',
                'class': 'rounded-2xl block w-full ps-10 p-2.5 bg-whiteColor border-darkColor placeholder-darkColor/50 '
                         'focus:ring-primaryColor focus:border-primaryColor transition-all duration-300 ease-in-out',
            }
        ),
        label='Phone number',
        help_text='Enter the phone number of the student.',
        error_messages={'required': 'Please enter the phone number of the student'},
        required=True,
    )

    gender = forms.ChoiceField(
        widget=forms.Select(
            attrs={
                'id': 'gender',
                'name': 'gender',
                'placeholder': 'Select gender',
                'class': 'rounded-2xl block w-full ps-10 p-2.5 bg-whiteColor border-darkColor placeholder-darkColor/50 '
                         'focus:ring-primaryColor focus:border-primaryColor transition-all duration-300 ease-in-out',
            }
        ),
        label='Gender',
        help_text='Select the gender of the student.',
        choices=Student.GenderChoices.choices,
        required=True,
    )

    is_delegate = forms.BooleanField(
        widget=forms.CheckboxInput(
            attrs={
                'id': 'is_delegate',
                'name': 'is_delegate',
                'class': 'w-4 h-4 border rounded-md focus:ring-3 bg-slate-700 border-slate-600 '
                         'focus:ring-primaryColor ring-offset-slate-800 focus:ring-offset-slate-800',
            }

        ),
        label='Course delegate',
        help_text='Is the student a course delegate?',
        required=False,
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['department'].default = DepartmentChoices.ICT
        self.fields['is_delegate'].default = False

class TeachingRecordForm(forms.ModelForm):
    class Meta:
        model = TeachingRecord
        fields = [
            'description',
            'lecturer_arrival_time',
            'lecturer_departure_time',   
            'quality_assurance',
        ]
        
    description = forms.CharField(
        widget=SummernoteWidget(),
        label='Description',
        help_text='Lessons and Brief Content/Assignments',
        error_messages={'required': 'Please enter a description of the teaching record'},
        required=True,
    )
    
    lecturer_arrival_time = forms.TimeField(
        widget=forms.TimeInput(
            attrs={
                'id': 'lecturer_arrival_time',
                'name': 'lecturer_arrival_time',
                'type': 'time',
                'placeholder': 'HH:MM:SS',
                'class': 'rounded-2xl block w-full ps-10 p-2.5 bg-whiteColor border-darkColor placeholder-darkColor/50 '
                         'focus:ring-primaryColor focus:border-primaryColor transition-all duration-300 ease-in-out',
            }
        ),
        label='Lecturer arrival time',
        help_text='Enter the time the lecturer arrived.',
        error_messages={'required': 'Please enter the time the lecturer arrived'},
        required=True,
    )
    
    lecturer_departure_time = forms.TimeField(
        widget=forms.TimeInput(
            attrs={
                'id': 'lecturer_departure_time',
                'name': 'lecturer_departure_time',
                'type': 'time',
                'placeholder': 'HH:MM:SS',
                'class': 'rounded-2xl block w-full ps-10 p-2.5 bg-whiteColor border-darkColor placeholder-darkColor/50 '
                         'focus:ring-primaryColor focus:border-primaryColor transition-all duration-300 ease-in-out',
            }
        ),
        label='Lecturer departure time',
        help_text='Enter the time the lecturer left.',
        error_messages={'required': 'Please enter the time the lecturer left'},
        required=True,
    )
    
    quality_assurance = forms.ChoiceField(
        widget=forms.Select(
            attrs={
                'id': 'quality_assurance',
                'name': 'quality_assurance',
                'placeholder': 'Select quality assurance',
                'class': 'rounded-2xl block w-full ps-10 p-2.5 bg-whiteColor border-darkColor placeholder-darkColor/50 '
                         'focus:ring-primaryColor focus:border-primaryColor transition-all duration-300 ease-in-out',
            }
        ),
        label='Quality assurance',
        help_text='Select the quality assurance of the teaching record.',
        choices=TeachingRecord.QualityChoices.choices,
        required=True,
    )
    
    def clean(self):
        cleaned_data = super().clean()
        arrival_time = cleaned_data.get('lecturer_arrival_time')
        departure_time = cleaned_data.get('lecturer_departure_time')

        if arrival_time and departure_time and departure_time <= arrival_time:
            raise forms.ValidationError("Lecturer departure time must come after arrival time.")

        return cleaned_data