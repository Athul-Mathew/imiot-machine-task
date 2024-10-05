from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase
from .models import User, Company, JobListing, JobApplication
from rest_framework_simplejwt.tokens import AccessToken
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.utils.encoding import force_bytes, force_str
from django.contrib.auth.tokens import default_token_generator
from rest_framework.authtoken.models import Token
from django.core.files.base import ContentFile

class UserRegistrationTestCase(APITestCase):
    def test_user_registration(self):
        url = reverse('user-registration')
        data = {
            'username': 'testuser',
            'email': 'testuser@example.com',
            'password': 'testpassword',
            'role': 'candidate',
        }
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(User.objects.count(), 1)
        self.assertEqual(User.objects.get().email, 'testuser@example.com')


class ActivationTestCase(APITestCase):
    def setUp(self):
        Company.objects.all().delete()
        self.user = User.objects.create_user(
            username='testuser',
            email='testuser@example.com',
            password='testpassword',
            role='candidate'
        )
        self.user.is_active = False
        self.user.save()

    def test_activation(self):
        uidb64 = urlsafe_base64_encode(force_bytes(self.user.pk))
        token = default_token_generator.make_token(self.user)
        url = reverse('activate', kwargs={'uidb64': uidb64, 'token': token})
        response = self.client.get(url)
        self.user.refresh_from_db()
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(self.user.is_active)


class JobListingTestCase(APITestCase):
    def setUp(self):
        JobListing.objects.all().delete()
        User.objects.all().delete()  # Ensure user cleanup too
        Company.objects.all().delete()
        self.employer = User.objects.create_user(
            username='employer',
            email='employer@example.com',
            password='employerpassword',
            role='employer'
        )
        self.company = Company.objects.create(
            name='Test Company',
            location='Test Location',
            description='A test company.',
            owner=self.employer,
            contact_email='contact@testcompany.com'
        )
        self.job_listing = JobListing.objects.create(
            title='Test Job',
            company=self.company,
            description='A test job description.',
            requirements='Test requirements.',
            location='Test Location',
            salary=50000,
            is_active=True
        )
        self.access_token = AccessToken.for_user(self.employer)

    def test_create_job_listing(self):
        self.client.credentials(HTTP_AUTHORIZATION='Bearer ' + str(self.access_token))
        url = reverse('joblisting-list')
        data = {
            'title': 'New Job',
            'description': 'New job description.',
            'requirements': 'New job requirements.',
            'location': 'New Location',
            'salary': 60000,
            'is_active': True
        }
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(JobListing.objects.count(), 2)  # One existing + one created

    def test_list_job_listings(self):
        self.client.credentials(HTTP_AUTHORIZATION='Bearer ' + str(self.access_token))
        url = reverse('joblisting-list')
        response = self.client.get(url)
        
        # Print the response data for debugging
        print("Job Listings Returned:", response.data)  # This will show what listings are present
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 1)  # Only the existing job listing


class JobApplicationTestCase(APITestCase):
    def setUp(self):
        # Clean up the database
        Company.objects.all().delete()
        User.objects.all().delete()
        JobListing.objects.all().delete()

        # Create the candidate and employer users
        self.candidate = User.objects.create_user(
            username='candidate',
            email='candidate@example.com',
            password='candidatepassword',
            role='candidate'
        )
        

        self.employer = User.objects.create_user(
            username='employer',
            email='employer@example.com',
            password='employerpassword',
            role='employer'
        )
        
        self.company = Company.objects.create(
            name='Test Company',
            location='Test Location',
            description='A test company.',
            owner=self.employer,
            contact_email='contact@testcompany.com'
        )
        
        self.job_listing = JobListing.objects.create(
            title='Test Job',
            company=self.company,
            description='A test job description.',
            requirements='Test requirements.',
            location='Test Location',
            salary=50000,
            is_active=True
        )
        self.access_token = AccessToken.for_user(self.candidate)

    def test_apply_for_job(self):
        self.client.credentials(HTTP_AUTHORIZATION='Bearer ' + str(self.access_token)) 
        url = reverse('jobapplication-list')

        # Create a temporary file for the resume
        resume_file = ContentFile(b'This is a test resume content.', name='resume.pdf')

        data = {
            'job': self.job_listing.id,
            'resume': resume_file,
            'cover_letter': 'This is my cover letter.'
        }

        response = self.client.post(url, data, format='multipart')  # Ensure it's 'multipart'
        
        # Print the response to debug further if needed
        # print(response.data)
        
        # Check if the request was successful
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(JobApplication.objects.count(), 1)

class CompanyTestCase(APITestCase):
    def setUp(self):
        Company.objects.all().delete()
         
        User.objects.all().delete()
        self.employer = User.objects.create_user(
            username='employer',
            email='employer@example.com',
            password='employerpassword',
            role='employer'
        )
        self.access_token = AccessToken.for_user(self.employer)

    def test_create_company(self):
        self.client.credentials(HTTP_AUTHORIZATION='Bearer ' + str(self.access_token))
        url = reverse('company-list')
        data = {
            'name': 'New Company',
            'location': 'New Location',
            'description': 'New company description.',
            'contact_email': 'newcompany@example.com'
        }
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Company.objects.count(), 1)

    def test_list_companies(self):
        self.client.credentials(HTTP_AUTHORIZATION='Bearer ' + str(self.access_token))
        url = reverse('company-list')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 4)  # No companies yet


# Add more tests for other functionalities as needed
