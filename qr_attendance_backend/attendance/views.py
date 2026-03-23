from rest_framework.decorators import api_view
from django.http import HttpResponse
from rest_framework.response import Response

from rest_framework_simplejwt.views import TokenObtainPairView  # ✅ FIX ADDED
from .serializers import CustomTokenObtainPairSerializer
from attendance.serializers import CustomTokenObtainPairSerializer
from .models import Student, Course, Registration, Attendance
import csv
from django.contrib.auth import authenticate
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework.permissions import IsAuthenticated
from rest_framework.decorators import permission_classes


@api_view(['POST'])
def admin_login(request):
    username = request.data.get("username")
    password = request.data.get("password")

    user = authenticate(username=username, password=password)

    if user is None:
        return Response({"error": "Invalid credentials"}, status=401)

    if not user.is_staff:
        return Response({"error": "Not authorized"}, status=403)

    refresh = RefreshToken.for_user(user)

    return Response({
        "access": str(refresh.access_token),
        "refresh": str(refresh),
    })


class CustomTokenObtainPairView(TokenObtainPairView):
    serializer_class = CustomTokenObtainPairSerializer

def home(request):
    return HttpResponse("QR Attendance Backend is Running ✅")
@api_view(['POST'])
def check_attendance(request):
    try:
        matric = request.data.get("matric_number")
        course_code = request.data.get("course_code")

        # ✅ Validate input
        if not matric or not course_code:
            return Response({
                "status": "denied",
                "reason": "Missing required fields"
            })

        # 1. Check student
        try:
            student = Student.objects.get(matric_number=matric)
        except Student.DoesNotExist:
            return Response({
                "status": "denied",
                "reason": "Student not found"
            })

        # 2. Check course
        try:
            course = Course.objects.get(course_code=course_code)
        except Course.DoesNotExist:
            return Response({
                "status": "denied",
                "reason": "Invalid course"
            })

        # 3. Check registration
        is_registered = Registration.objects.filter(
            student=student,
            course=course
        ).exists()

        if not is_registered:
            return Response({
                "status": "denied",
                "reason": "Not registered for this course",
                "student": get_student_data(student)
            })

        # 4. Prevent duplicate (stronger check)
        if Attendance.objects.filter(student=student, course=course).exists():
            return Response({
                "status": "denied",
                "reason": "Already checked in",
                "student": get_student_data(student)
            })

        # 5. Save attendance
        Attendance.objects.create(
            student=student,
            course=course,
            status="granted"
        )

        return Response({
            "status": "granted",
            "reason": "Access granted",
            "student": get_student_data(student)
        })

    except Exception as e:
        return Response({
            "status": "error",
            "reason": "Server error",
            "debug": str(e)  # remove in production
        })
    

def get_student_data(student):
    courses = Registration.objects.filter(student=student).select_related('course')

    return {
        "name": student.name,
        "matric_number": student.matric_number,
        "department": student.department,
        "level": student.level,
        "image": student.image.url if student.image else None,
        "courses": [c.course.course_code for c in courses]
    }

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_attendance(request):
    records = Attendance.objects.select_related('student', 'course')\
        .all().order_by('-timestamp')[:100]  # limit for performance

    data = [
        {
            "name": r.student.name,
            "matric_number": r.student.matric_number,
            "department": r.student.department,
            "course": r.course.course_code,
            "time": r.timestamp.strftime("%Y-%m-%d %H:%M:%S"),
            "status": r.status
        }
        for r in records
    ]

    return Response(data)

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def export_csv(request):
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="attendance.csv"'

    writer = csv.writer(response)
    writer.writerow(['Name', 'Matric', 'Department', 'Course', 'Time', 'Status'])

    records = Attendance.objects.select_related('student', 'course').all()

    for record in records:
        writer.writerow([
            record.student.name,
            record.student.matric_number,
            record.student.department,
            record.course.course_code,
            record.timestamp.strftime("%Y-%m-%d %H:%M:%S"),
            record.status
        ])

    return response