from django.urls import path
from .views import check_attendance
from .views import export_csv
from .views import get_attendance

urlpatterns = [
    # path('', home),
    path('check-attendance/', check_attendance),
    path('get-attendance/', get_attendance),
    path('export/', export_csv),
]