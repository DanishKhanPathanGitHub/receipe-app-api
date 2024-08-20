from django.urls import path
from .views import (
    CreateUserView,
    ManageUserView,
    ForgotPasswordView,
    ResetPasswordView,
    ActivateUserView,
    AuthTokenView,
    #LoginView,
    #LogoutView,
)

app_name = 'user'

urlpatterns = [
    path('create/', CreateUserView.as_view(), name='create'),
    path('me/', ManageUserView.as_view(), name='me'),
    path('token/', AuthTokenView.as_view(), name='token'),
    path('forgot-password/', ForgotPasswordView.as_view(), name='forgot-password'),
    path('activate/', ActivateUserView.as_view(), name='activate'),
    path('reset-password/', ResetPasswordView.as_view(), name='reset-password'),
    #path('login/', LoginView.as_view(), name='login'),
    #path('logout/', LogoutView.as_view(), name='logout'),
]
