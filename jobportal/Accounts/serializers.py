from rest_framework import serializers
from .models import User
from .models import User, Company, JobListing, JobApplication

class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'role']

class UserRegisterSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = '__all__'

    def create(self, validated_data):
        password = validated_data.pop('password')
        user = super().create(validated_data)
        user.set_password(password)
        user.save()
        return user

#Job applications



class CompanySerializer(serializers.ModelSerializer):
    owner = UserSerializer(read_only=True)
    
    class Meta:
        model = Company
        fields = ['id', 'name', 'location', 'description', 'owner']

class JobListingSerializer(serializers.ModelSerializer):
    company = CompanySerializer(read_only=True)
    
    class Meta:
        model = JobListing
        fields = ['id', 'title', 'description', 'requirements', 'location', 'salary', 'created_at', 'is_active', 'company']

class JobApplicationSerializer(serializers.ModelSerializer):
    job = serializers.PrimaryKeyRelatedField(queryset=JobListing.objects.all())

    candidate = UserSerializer(read_only=True)

    class Meta:
        model = JobApplication
        fields = ['id', 'job', 'candidate', 'resume', 'cover_letter', 'applied_at', 'status']
