from django.db import models

import qrcode
from io import BytesIO
from django.core.files import File

class Student(models.Model):
    name = models.CharField(max_length=100)
    matric_number = models.CharField(max_length=50, unique=True)
    department = models.CharField(max_length=100)
    level = models.CharField(max_length=20, default="100L")  # ✅ ADD THIS

    image = models.ImageField(upload_to='students/', blank=True, null=True)  # ✅ ADD THIS
    qr_code = models.ImageField(upload_to='qr_codes/', blank=True)

    def save(self, *args, **kwargs):
        qr_data = self.matric_number
        qr = qrcode.make(qr_data)

        buffer = BytesIO()
        qr.save(buffer, format='PNG')

        self.qr_code.save(f"{self.matric_number}.png", File(buffer), save=False)

        super().save(*args, **kwargs)

class Course(models.Model):
    course_code = models.CharField(max_length=20)
    course_name = models.CharField(max_length=100)

    def __str__(self):
        return self.course_code


class Registration(models.Model):
    student = models.ForeignKey(Student, on_delete=models.CASCADE)
    course = models.ForeignKey(Course, on_delete=models.CASCADE)


    def __str__(self):
        return f"{self.student.name} → {self.course.course_code}"


class Attendance(models.Model):
    student = models.ForeignKey(Student, on_delete=models.CASCADE)
    course = models.ForeignKey(Course, on_delete=models.CASCADE)
    timestamp = models.DateTimeField(auto_now_add=True)
    status = models.CharField(max_length=10)

    class Meta:
        unique_together = ('student', 'course')