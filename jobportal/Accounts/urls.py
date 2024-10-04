from django.urls import path,include
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView
from rest_framework.routers import DefaultRouter
from .views import *
from .import views

router = DefaultRouter()
router.register(r'jobs', JobListingViewSet)
router.register(r'companies', CompanyViewSet)
router.register(r'applications', JobApplicationViewSet)



urlpatterns = [
    path('login/', views.MyTokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('signup/', views.UserRegistration.as_view()),
    path('activate/<uidb64>/<token>/', views.Activate, name='activate'),
    #job applications

    path('', include(router.urls)),

  
]
