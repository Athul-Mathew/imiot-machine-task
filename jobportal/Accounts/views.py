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
