from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
# serializers.py
from rest_framework import serializers
from .models import Student


class CustomTokenObtainPairSerializer(TokenObtainPairSerializer):
    @classmethod
    def get_token(cls, user):
        token = super().get_token(user)

        # ✅ ADD CUSTOM DATA INTO TOKEN
        token["username"] = user.username
        token["email"] = user.email
        token["is_staff"] = user.is_staff

        return token
    
class StudentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Student
        fields = "__all__"