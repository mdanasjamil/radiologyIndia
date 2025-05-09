from django.urls import path
from . import views

app_name = 'accounts'
urlpatterns = [
    path('',         views.home_view,   name='home'),   # landing page
    path('signup/',  views.signup_view, name='signup'),
    path('login/',   views.login_view,  name='login'),
    path('logout/',  views.logout_view, name='logout'),
]
