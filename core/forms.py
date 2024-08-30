import datetime

from django import forms
from allauth.account.forms import LoginForm
from .models import Course, Lecturer, Student, DepartmentChoices


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


class CourseAddForm(forms.ModelForm):
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

    date = forms.DateField(
        widget=forms.DateInput(
            attrs={
                'id': 'date',
                'name': 'date',
                'type': 'date',
                'placeholder': 'Course date',
                'class': 'rounded-2xl block w-full ps-10 p-2.5 bg-whiteColor border-darkColor placeholder-darkColor/50 '
                         'focus:ring-primaryColor focus:border-primaryColor transition-all duration-300 ease-in-out',
            },
        ),
        initial=datetime.date.today,
        label='Course date',
        help_text='Enter the date the course is taught.',
        error_messages={'required': 'Please enter the date the course is taught'},
        required=True,
    )

    start_time = forms.TimeField(
        widget=forms.TimeInput(
            attrs={
                'id': 'start_time',
                'name': 'start_time',
                'type': 'time',
                'placeholder': 'Course start time',
                'class': 'rounded-2xl block w-full ps-10 p-2.5 bg-whiteColor border-darkColor placeholder-darkColor/50 '
                         'focus:ring-primaryColor focus:border-primaryColor transition-all duration-300 ease-in-out',
            }
        ),
        label='Course start time',
        help_text='Enter the start time of the course.',
        error_messages={'required': 'Please enter the start time of the course'},
        required=True,
        initial=datetime.datetime.now().time()
    )

    end_time = forms.TimeField(
        widget=forms.TimeInput(
            attrs={
                'id': 'end_time',
                'name': 'end_time',
                'type': 'time',
                'placeholder': 'Course end time',
                'class': 'rounded-2xl block w-full ps-10 p-2.5 bg-whiteColor border-darkColor placeholder-darkColor/50 '
                         'focus:ring-primaryColor focus:border-primaryColor transition-all duration-300 ease-in-out',
            }
        ),
        label='Course end time',
        help_text='Enter the end time of the course.',
        error_messages={'required': 'Please enter the end time of the course'},
        required=True,
        initial=datetime.datetime.now().time()
    )

    is_catchup = forms.BooleanField(
        widget=forms.CheckboxInput(
            attrs={
                'id': 'is_catchup',
                'name': 'is_catchup',
                'class': 'w-4 h-4 border rounded-md focus:ring-3 bg-slate-700 border-slate-600 '
                         'focus:ring-primaryColor ring-offset-slate-800 focus:ring-offset-slate-800',
            }
        ),
        label='Catch-up class',
        help_text='Is this a catch-up class?',
        required=False,
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
        self.fields['is_catchup'].default = False

    def clean_date(self):
        date = self.cleaned_data['date']
        if date > datetime.date.today():
            raise forms.ValidationError("The course date cannot be in the future.")
        return date


class LecturerAddForm(forms.ModelForm):
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


class StudentAddForm(forms.ModelForm):
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
