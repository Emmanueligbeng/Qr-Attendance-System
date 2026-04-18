from django.http import HttpResponse
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from django.contrib.auth import authenticate
from django.contrib.auth.models import User
from rest_framework_simplejwt.views import TokenObtainPairView
from rest_framework_simplejwt.tokens import RefreshToken

from openpyxl import Workbook

from .models import Student, Course, Registration, Attendance
from .serializers import StudentSerializer, CustomTokenObtainPairSerializer


# ==========================
# AUTH
# ==========================

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

@api_view(['POST'])
def signup(request):
    username = request.data.get("username")
    password = request.data.get("password")

    if not username or not password:
        return Response({"error": "All fields required"}, status=400)

    if User.objects.filter(username=username).exists():
        return Response({"error": "Username already exists"}, status=400)

    user = User.objects.create_user(
        username=username,
        password=password
    )

    return Response({"message": "User created successfully"})

class CustomTokenObtainPairView(TokenObtainPairView):
    serializer_class = CustomTokenObtainPairSerializer


def home(request):
    return HttpResponse("QR Attendance Backend is Running ✅")


# ==========================
# ATTENDANCE CHECK
# ==========================

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def check_attendance(request):
    matric = request.data.get("matric_number")
    course_code = request.data.get("course_code")

    if not matric or not course_code:
        return Response({
            "status": "denied",
            "reason": "Missing required fields"
        }, status=400)

    # Check student
    student = Student.objects.filter(matric_number=matric).first()
    if not student:
        return Response({
            "status": "denied",
            "reason": "Student not found"
        }, status=404)

    # Check course
    course = Course.objects.filter(course_code=course_code).first()
    if not course:
        return Response({
            "status": "denied",
            "reason": "Invalid course"
        }, status=404)

    # Check registration
    is_registered = Registration.objects.filter(
        student=student,
        course=course
    ).exists()

    if not is_registered:
        return Response({
            "status": "denied",
            "reason": "Not registered for this course",
            "student": get_student_data(student)
        }, status=403)

    # Prevent duplicate (safe handling)
    attendance, created = Attendance.objects.get_or_create(
        student=student,
        course=course,
        defaults={"status": "granted"}
    )

    if not created:
        return Response({
            "status": "denied",
            "reason": "Already checked in",
            "student": get_student_data(student)
        }, status=409)

    return Response({
        "status": "granted",
        "reason": "Access granted",
        "student": get_student_data(student)
    })


# ==========================
# HELPER FUNCTION
# ==========================

def get_student_data(student):
    courses = student.registration_set.select_related('course').all()

    return {
        "name": student.name,
        "matric_number": student.matric_number,
        "department": student.department,
        "level": student.level,
        "image": student.image.url if student.image else None,
        "courses": [c.course.course_code for c in courses]
    }


# ==========================
# GET ATTENDANCE (OPTIMIZED)
# ==========================

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_attendance(request):
    students = Student.objects.prefetch_related(
        'registration_set__course',
        'attendance_set__course'
    )

    data = []

    for student in students:
        registrations = student.registration_set.all()
        attendance_records = {
            att.course_id: att for att in student.attendance_set.all()
        }

        for reg in registrations:
            record = attendance_records.get(reg.course.id)

            data.append({
                "name": student.name,
                "matric_number": student.matric_number,
                "department": student.department,
                "course": reg.course.course_code,
                "status": record.status if record else "absent",
                "time": record.timestamp.strftime("%Y-%m-%d %H:%M:%S") if record else None
            })

    return Response(data)


# ==========================
# EXPORT EXCEL
# ==========================

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def export_excel(request):
    wb = Workbook()
    ws = wb.active
    ws.title = "Attendance"

    headers = ['Name', 'Matric', 'Department', 'Course', 'Time', 'Status']
    ws.append(headers)

    records = Attendance.objects.select_related('student', 'course').all()

    for record in records:
        ws.append([
            record.student.name,
            record.student.matric_number,
            record.student.department,
            record.course.course_code,
            record.timestamp.strftime("%Y-%m-%d %H:%M:%S"),
            record.status
        ])

    response = HttpResponse(
        content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
    )
    response['Content-Disposition'] = 'attachment; filename=attendance.xlsx'

    wb.save(response)

    return response


# ==========================
# REGISTER STUDENT
# ==========================

@api_view(["POST"])
@permission_classes([IsAuthenticated])  # 🔒 Protect this
def register_student(request):
    serializer = StudentSerializer(data=request.data)

    if serializer.is_valid():
        student = serializer.save()
        return Response({
            "message": "Student registered",
            "data": StudentSerializer(student).data
        }, status=201)

    return Response(serializer.errors, status=400)