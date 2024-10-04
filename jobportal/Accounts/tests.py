from django.test import TestCase
from rest_framework.test import APIClient
from rest_framework_simplejwt.tokens import RefreshToken
from .models import User, Company, JobListing, JobApplication
from django.core.files.base import ContentFile
from rest_framework import status
from django.urls import reverse
from django.contrib.auth import get_user_model

class APITestCase(TestCase):
    def setUp(self):
        self.client = APIClient()
        
        # Create users
        self.admin_user = User.objects.create_user(username="admin", email="admin@example.com", password="adminpass", role="admin")
        self.employer_user = User.objects.create_user(username="employer", email="employer@example.com", password="employerpass", role="employer")
        self.candidate_user = User.objects.create_user(username="candidate", email="candidate@example.com", password="candidatepass", role="candidate")

        # Create company and job
        self.company = Company.objects.create(name="Test Company", location="Test Location", owner=self.employer_user)
        self.job = JobListing.objects.create(title="Test Job", company=self.company, location="Test Location", salary=50000)
       
    def authenticate(self, user):
        # Get the JWT token for the user
        refresh = RefreshToken.for_user(user)
        
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {refresh.access_token}')

    def test_job_listing(self):
        # Authenticate the candidate user
        self.authenticate(self.candidate_user)
        response = self.client.get('/api/jobs/')
        self.assertEqual(response.status_code, 200)

    def setUp(self):
        # Create a user with the Candidate role
        self.user = get_user_model().objects.create_user(
            username='test_candidate',
            password='password',
            email='candidate@example.com'  # Add email if required
        )
        self.user.role = 'Candidate'  # Assuming you have a field for roles
        self.user.save()

        # Create a Company instance
        self.company = Company.objects.create(
            name='Test Company',  # Name of the company
            # Add other required fields for Company if necessary...
        )

        # Create a JobListing instance with all required fields
        self.job_listing = JobListing.objects.create(
            title='Test Job Title',  # Title of the job
            description='This is a test job description.',  # Job description
            salary=50000,  # Salary for the job
            company=self.company,  # Assign the Company instance here
            location='Test Location',  # Job location
            employment_type='Full-time',  # Type of employment (e.g., Full-time, Part-time)
            required_experience='2 years',  # Required experience for the job
            qualifications='Bachelor\'s Degree',  # Required qualifications
            skills='Python, Django',  # Required skills
            responsibilities='Develop and maintain web applications.',  # Responsibilities of the job
            application_deadline='2024-12-31',  # Application deadline
            # Add any other required fields here...
        )

    def test_apply_to_job(self):
        data = {
            'candidate': self.user.id,  # Use the user ID here
            'job_listing': self.job_listing.id,
            'resume': 'path/to/resume.pdf',  # Example field for resume upload, adjust as needed
            # Add other fields if needed...
        }
        response = self.client.post(reverse('job_application_list'), data, format='multipart')  # Use 'multipart' for file uploads
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

   


    def test_job_creation_by_employer(self):
        self.authenticate(self.employer_user)
        data = {
            'title': 'New Job',
            'company': self.company.id,
            'location': 'New York',
            'salary': 60000,
            'description': 'Job Description',
            'requirements': 'Job Requirements',
        }
        response = self.client.post('/api/jobs/', data)
        self.assertEqual(response.status_code, 201)
