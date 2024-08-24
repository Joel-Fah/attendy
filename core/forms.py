from django import forms
from allauth.account.forms import LoginForm


# Create your forms here
class UserLoginForm(LoginForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # login field
        self.fields['login'].widget.attrs.update({
            'id': 'login',
            'name': 'login',
            'placeholder': 'attendy@ictuniversity.edu.cm',
            'class': 'rounded-2xl block w-full ps-10 p-2.5 bg-whiteColor border-darkColor placeholder-darkColor/50 focus:ring-primaryColor focus:border-primaryColor transition-all duration-300 ease-in-out',
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
            'class': 'rounded-2xl block w-full ps-10 p-2.5 bg-whiteColor border-darkColor placeholder-darkColor/50 focus:ring-primaryColor focus:border-primaryColor transition-all duration-300 ease-in-out',
        })
        self.fields['password'].label = 'Password'
        self.fields['password'].help_text = 'Enter your password.'
        self.fields['password'].error_messages = {
            'required': 'Please enter your password',
        }
        self.fields['password'].required = True
