from django.shortcuts import render
from .models import User
from .serializers import  UserRegisterSerializer
from rest_framework.decorators import api_view,permission_classes
from rest_framework import status,viewsets
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
from .models import Company, JobListing, JobApplication
from .serializers import CompanySerializer, JobListingSerializer, JobApplicationSerializer
from .permissions import *
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.filters import SearchFilter
from rest_framework.pagination import PageNumberPagination
from rest_framework.permissions import IsAuthenticated

#REGISTRATION
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

            send_email = EmailMessage(mail_subject, message, to=[email])
            send_email.send()

            return Response({'status': 'success', 'msg': 'A verificaiton link sent to your registered email address', "data": serializer.data,},status=status.HTTP_201_CREATED)
        else:
            return Response({'status': 'error', 'msg': serializer.errors})

@api_view(['GET'])
#ACTIVATION OF THE ACCOUNT
@permission_classes([AllowAny])
def Activate(request, uidb64, token):
    try:
        uid = force_str(urlsafe_base64_decode(uidb64))
        user = User.objects.get(pk=uid)
    except (TypeError, ValueError, OverflowError, User.DoesNotExist):
        user = None

    if user is not None and default_token_generator.check_token(user, token):
        user.is_active = True 
        user.save()
        return HttpResponse('Thank you for confirming your email. Your account is now active.')
    else:
        return HttpResponse('Activation link is invalid!')        

#PAGINATION
class JobListingPagination(PageNumberPagination):
    page_size = 10 
    page_size_query_param = 'page_size'
    max_page_size = 100

#email notification
from django.core.mail import send_mail
from django.conf import settings

def send_email_notification(subject, message, recipient_list):
    send_mail(
        subject,
        message,
        settings.DEFAULT_FROM_EMAIL,
        recipient_list,
        fail_silently=False,
    )
#JOB APPLICATIONS
class JobListingViewSet(viewsets.ModelViewSet):
    queryset = JobListing.objects.all()
    serializer_class = JobListingSerializer
    filter_backends = [DjangoFilterBackend, SearchFilter]
    search_fields = ['title', 'company__name', 'location']
    filterset_fields = ['salary', 'location', 'is_active']
    pagination_class = JobListingPagination

    def get_permissions(self):
        if self.action in ['create', 'update', 'partial_update', 'destroy']:
            return [IsEmployerOrAdmin()] 
        return [permissions.IsAuthenticated()] 

    def get_queryset(self):
        user = self.request.user
        if user.role == 'employer':
            return JobListing.objects.filter(company__owner=user)
        if user.role == 'admin':
            return JobListing.objects.all()
        return JobListing.objects.filter(is_active=True)

    def perform_create(self, serializer):
        serializer.save(company=self.request.user.company_set.first())

class CompanyViewSet(viewsets.ModelViewSet):
    queryset = Company.objects.all()
    serializer_class = CompanySerializer
    permission_classes = [IsAuthenticated]  

    def perform_create(self, serializer):
        serializer.save(owner=self.request.user)

    def get_queryset(self):
        return Company.objects.filter(owner=self.request.user)

class JobApplicationViewSet(viewsets.ModelViewSet):
    queryset = JobApplication.objects.all()
    serializer_class = JobApplicationSerializer
    permission_classes = [IsAuthenticated]
    pagination_class = JobListingPagination 
    filter_backends = [DjangoFilterBackend, SearchFilter]
    search_fields = ['job__title', 'candidate__username']  
    filterset_fields = ['job__location', 'job__salary', 'status']

    def get_permissions(self):
        if self.request.method == 'POST':
            return [IsCandidate()] 
        return [IsEmployerOrAdmin()]
    
    
    def perform_create(self, serializer):
        candidate = self.request.user
        job_id = self.request.data.get('job') 
        job = JobListing.objects.get(id=job_id)  
        application = serializer.save(candidate=candidate, job=job)

# Prepare email notifications
        job_title = application.job.title
        candidate_email = candidate.email

# Send notification to the candidate
        subject = f'Application submitted for {job_title}'
        message = f'Thank you for applying to {job_title}. We will review your application soon.'
        send_email_notification(subject, message, [candidate_email])

# Send notification to the employer
        employer_email = application.job.company.contact_email
        subject = f'New application for {job_title}'
        message = f'{application.candidate.username} has applied for {job_title}.'
        send_email_notification(subject, message, [employer_email])



