from django.contrib import admin
from django.utils.html import format_html
from .models import Student, Course, Registration, Attendance


class StudentAdmin(admin.ModelAdmin):
    list_display = ['name', 'matric_number', 'view_qr']

    def view_qr(self, obj):
        if obj.qr_code:
            return format_html(
                '<img src="{}" width="50" />',
                obj.qr_code.url
            )
        return "No QR"


admin.site.register(Student, StudentAdmin)
admin.site.register(Course)
admin.site.register(Registration)
admin.site.register(Attendance)