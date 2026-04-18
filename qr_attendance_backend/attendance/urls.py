from django.urls import path
from .views import check_attendance, export_excel, signup
# from .views import export_csv
from .views import admin_login
from .views import home
from .views import get_attendance
from .views import CustomTokenObtainPairView
# from .views import register_student

urlpatterns = [
    path('', home),
    path('check-attendance/', check_attendance),
    path('get-attendance/', get_attendance),
    # path('export/', export_csv),
    # path('login/', admin_login),
    path('login/', CustomTokenObtainPairView.as_view(), name='login'),
    # path("register-student/", register_student),
    path('signup/', signup),
    path('export/', export_excel),
]