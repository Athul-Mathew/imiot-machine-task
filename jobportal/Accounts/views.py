from django.shortcuts import render
from .models import User
from .serializers import  UserRegisterSerializer
from rest_framework.decorators import api_view,permission_classes
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from rest_framework_simplejwt.views import TokenObtainPairView
from rest_framework.views import APIView
from rest_framework.response import Response
from django.template.loader import render_to_string
from django.contrib.sites.shortcuts import get_current_site
from django.utils.http import urlsafe_base64_decode,urlsafe_base64_encode
from django.contrib.auth.tokens import default_token_generator
from django.core.mail import EmailMessage
from django.utils.encoding import force_bytes
from rest_framework.permissions import AllowAny
from django.http import HttpResponse
from django.utils.encoding import force_str
from rest_framework import viewsets
from .models import Company, JobListing, JobApplication
from .serializers import CompanySerializer, JobListingSerializer, JobApplicationSerializer
from .permissions import *
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.filters import SearchFilter
from rest_framework.pagination import PageNumberPagination


class MyTokenObtainPairSerializer(TokenObtainPairSerializer):
    @classmethod
    def get_token(cls, user):
        token = super().get_token(user)
        token['email'] = user.email
        token['name'] = user.username
        token['is_admin'] = user.role == 'admin'
        token['is_employer'] = user.role == 'employer'
        token['is_candidate'] = user.role == 'candidate'
        

        return token
    
class MyTokenObtainPairView(TokenObtainPairView):
    serializer_class=MyTokenObtainPairSerializer 

@api_view(["GET"])
def getRoutes(request):
    routes = [
        "api/login",
    ]
    return Response(routes)

class UserRegistration(APIView):
    permission_classes = [AllowAny] 
    def post(self, request):
        email = request.data.get('email')
        password = request.data.get('password')
        role= request.data.get('role')
        
        serializer = UserRegisterSerializer(data=request.data)
        
        if serializer.is_valid(raise_exception=True):

            user = serializer.save()
            user.set_password(password)
            user.is_active = False
            if role :
                if role == "employer":
                    user.is_staff = True
                    user.role = role
                user.role = "candidate"        

            user.save()

            current_site = get_current_site(request)
            mail_subject = 'Please activate your account'
            message = f"Hi {user.username},\n\n" \
                      f"Please click on the link below to activate your account:\n" \
                      f"http://{current_site.domain}/activate/{urlsafe_base64_encode(force_bytes(user.pk))}/{default_token_generator.make_token(user)}\n\n" \
                      f"Thank you for registering."

            #send_email = EmailMessage(mail_subject, message, to=[email])
            #send_email.send()

            return Response({'status': 'success', 'msg': 'A verificaiton link sent to your registered email address', "data": serializer.data,'msgs':message})
        else:
            return Response({'status': 'error', 'msg': serializer.errors})

@api_view(['GET'])

@permission_classes([AllowAny])
def Activate(request, uidb64, token):
    try:
        uid = force_str(urlsafe_base64_decode(uidb64))
        user = User.objects.get(pk=uid)
    except (TypeError, ValueError, OverflowError, User.DoesNotExist):
        user = None

    if user is not None and default_token_generator.check_token(user, token):
        user.is_active = True  # Activate the user's account
        user.save()
        return HttpResponse('Thank you for confirming your email. Your account is now active.')
    else:
        return HttpResponse('Activation link is invalid!')        

#pagination


class JobListingPagination(PageNumberPagination):
    page_size = 10  # Number of items per page
    page_size_query_param = 'page_size'
    max_page_size = 100

#job applications



class JobListingViewSet(viewsets.ModelViewSet):
    queryset = JobListing.objects.all()
    serializer_class = JobListingSerializer
    filter_backends = [DjangoFilterBackend, SearchFilter]
    search_fields = ['title', 'company__name', 'location']
    filterset_fields = ['salary', 'location', 'is_active']
    pagination_class = JobListingPagination

    def get_permissions(self):
        if self.action in ['create', 'update', 'partial_update', 'destroy']:
            return [IsEmployerOrAdmin()]  # Employers and Admins can manage
        return [permissions.IsAuthenticated()]  # Candidates can view

    def get_queryset(self):
        user = self.request.user
        if user.role == 'employer':
            # Employers can manage their own company's job listings
            return JobListing.objects.filter(company=user.company)
        if user.role == 'admin':
            # Admins can access all job listings
            return JobListing.objects.all()
        # Candidates can only view active job listings
        return JobListing.objects.filter(is_active=True)

    def perform_create(self, serializer):
        # When an employer creates a job listing, it should be linked to their company
        serializer.save(company=self.request.user.company_set.first())

class CompanyViewSet(viewsets.ModelViewSet):
    queryset = Company.objects.all()
    serializer_class = CompanySerializer

class JobApplicationViewSet(viewsets.ModelViewSet):
    queryset = JobApplication.objects.all()
    serializer_class = JobApplicationSerializer
    pagination_class = JobListingPagination  # Apply pagination
    filter_backends = [DjangoFilterBackend, SearchFilter]
    search_fields = ['job__title', 'candidate__username']  # Search by job title or candidate's username
    filterset_fields = ['job__location', 'job__salary', 'status']

    def get_permissions(self):
        if self.request.method == 'POST':
            return [IsCandidate()]  # Only candidates can apply
        return [IsEmployerOrAdmin()]



