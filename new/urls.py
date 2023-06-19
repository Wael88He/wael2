from django.urls import path
from django.contrib import admin
from USGS.views import *
from Details.views import *
from rest_framework import routers
from rest_framework_simplejwt.views import (
    TokenObtainPairView,
    TokenRefreshView,
    TokenVerifyView,
)

forget_password_viewset = ForgetPasswordViewset.as_view({'post': 'create'})
password_reset_viewset = PasswordResetViewset.as_view({'post': 'create'})
PasswordResetConfirmation = PasswordResetConfirmationViewset.as_view({'post': 'create'})
urlpatterns = [
    path('admin/',admin.site.urls),
    path('earthquakes/', EarthquakeView.as_view(),name='earthquake_view'),
    path('affected-users/', AffectedUsers.as_view(), name='affected-users'),
    path('register/', UserRegistrationView.as_view(), name='register'),
    path('users/profile/', ProfileView.as_view(), name='profile'),
    path('login/', login_view, name='login'),
    path('logout/', logout_view, name='logout'),
    path('password_reset/', password_reset_viewset, name='password_reset'),
    path('forget_pass/', forget_password_viewset, name = 'forget_pass'),
    path('confirm_pass/',PasswordResetConfirmation, name='confirm_pass'),
     path('delete-account/', DeleteAccountView.as_view(), name='delete-account'),
    
    #path('Get_user/', UserDetailView.as_view()),
    

]



