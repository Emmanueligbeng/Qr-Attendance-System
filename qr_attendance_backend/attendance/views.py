from rest_framework.decorators import api_view
from django.http import HttpResponse
from rest_framework.response import Response
from .models import Student, Course, Registration, Attendance
import csv

def home(request):
    return HttpResponse("QR Attendance Backend is Running ✅")

@api_view(['POST'])
def check_attendance(request):
    matric = request.data.get("matric_number")
    course_code = request.data.get("course_code")

    # 1. Check student
    try:
        student = Student.objects.get(matric_number=matric)
    except Student.DoesNotExist:
        return Response({
            "status": "denied",
            "message": "Student not found"
        })

    # 2. Check course
    try:
        course = Course.objects.get(course_code=course_code)
    except Course.DoesNotExist:
        return Response({
            "status": "denied",
            "message": "Invalid course"
        })

    # 3. Check registration
    is_registered = Registration.objects.filter(
        student=student,
        course=course
    ).exists()

    if not is_registered:
        return Response({
            "status": "denied",
            "message": "Not registered for this course"
        })

    # 4. Check duplicate
    already_checked = Attendance.objects.filter(
        student=student,
        course=course
    ).exists()

    if already_checked:
        return Response({
            "status": "denied",
            "message": "Already checked in"
        })

    # 5. Save attendance
    Attendance.objects.create(
        student=student,
        course=course,
        status="granted"
    )

    return Response({
        "status": "granted",
        "message": "Access granted",
        "student": {
            "name": student.name,
            "matric_number": student.matric_number,
            "department": student.department
        }
    })

@api_view(['GET'])
def get_attendance(request):
    records = Attendance.objects.select_related('student', 'course').all().order_by('-timestamp')

    data = []
    for record in records:
        data.append({
            "name": record.student.name,
            "matric_number": record.student.matric_number,
            "department": record.student.department,
            "course": record.course.course_code,
            "time": record.timestamp.strftime("%Y-%m-%d %H:%M:%S"),
            "status": record.status
        })

    return Response(data)

def export_csv(request):
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="attendance.csv"'

    writer = csv.writer(response)
    writer.writerow(['Name', 'Matric', 'Course', 'Time', 'Status'])

    records = Attendance.objects.all()

    for record in records:
        writer.writerow([
            record.student.name,
            record.student.matric_number,
            record.course.course_code,
            record.timestamp,
            record.status
        ])

    return response