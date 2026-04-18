from django.db import models
import qrcode
from io import BytesIO
from django.core.files import File


class Student(models.Model):
    name = models.CharField(max_length=100)
    matric_number = models.CharField(max_length=50, unique=True)
    department = models.CharField(max_length=100)
    level = models.CharField(max_length=20, default="100L")

    image = models.ImageField(upload_to='students/', blank=True, null=True)
    qr_code = models.ImageField(upload_to='qr_codes/', blank=True, null=True)

    def save(self, *args, **kwargs):
        # ✅ Only generate QR if it doesn't already exist
        if not self.qr_code:
            qr_data = self.matric_number

            qr = qrcode.make(qr_data)

            buffer = BytesIO()
            qr.save(buffer, format='PNG')

            filename = f"{self.matric_number}.png"

            self.qr_code.save(filename, File(buffer), save=False)

        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.name} ({self.matric_number})"


class Course(models.Model):
    course_code = models.CharField(max_length=20, unique=True)  # ✅ make unique
    course_name = models.CharField(max_length=100)

    def __str__(self):
        return f"{self.course_code} - {self.course_name}"


class Registration(models.Model):
    student = models.ForeignKey(Student, on_delete=models.CASCADE)
    course = models.ForeignKey(Course, on_delete=models.CASCADE)

    class Meta:
        unique_together = ('student', 'course')  # ✅ prevent duplicate registration

    def __str__(self):
        return f"{self.student.name} → {self.course.course_code}"


class Attendance(models.Model):
    STATUS_CHOICES = [
        ('granted', 'Granted'),
        ('denied', 'Denied'),
        ('absent', 'Absent'),
    ]

    student = models.ForeignKey(Student, on_delete=models.CASCADE)
    course = models.ForeignKey(Course, on_delete=models.CASCADE)
    timestamp = models.DateTimeField(auto_now_add=True)
    status = models.CharField(max_length=10, choices=STATUS_CHOICES)

    class Meta:
        unique_together = ('student', 'course')  # ✅ one attendance per course

    def __str__(self):
        return f"{self.student.name} - {self.course.course_code} ({self.status})"