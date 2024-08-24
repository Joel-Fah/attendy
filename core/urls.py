from django.urls import path
from .views import HomeView

# Create your urls here
app_name = 'core'

urlpatterns = [
    path('', HomeView.as_view(), name='home'),
]