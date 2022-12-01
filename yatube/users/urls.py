from django.contrib.auth.views import LoginView, LogoutView
from django.urls import path
from django.contrib.auth import views as auth_views
from . import views

app_name = 'users'

urlpatterns = [
    path('signup/', views.SignUp.as_view(), name='signup'),
    path(
        'logout/',
        LogoutView.as_view(template_name='users/logged_out.html'),
        name='logout'
    ),
    path(
        'login/',
        LoginView.as_view(template_name='users/login.html'),
        name='login'
    ),
    path('password_change_form', auth_views.PasswordChangeView.as_view(),
         name='password_change'),
    path('password_change_done',
         auth_views.PasswordChangeDoneView.as_view(),
         name='password_change_done'),
    path('password_reset_form', auth_views.PasswordResetView.as_view(),
         name='password_reset'),
    path('password_reset',
         auth_views.PasswordResetDoneView.as_view(),
         name='password_reset_done'),
    path('password_reset_confirm',
         auth_views.PasswordResetConfirmView.as_view(),
         name='password_reset_confirm'),
    path('password_reset_complete',
         auth_views.PasswordResetCompleteView.as_view(),
         name='password_reset_complete'),
]
