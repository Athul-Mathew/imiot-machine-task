# Job Listing and Application Management System

This project is a web-based system that allows employers to post job listings, candidates to apply for jobs, and administrators to manage users and listings. The system includes role-based access control, company profiles, and email notifications.

## Features

- User authentication and role-based permissions (Candidate, Employer, Admin)
- Job listing creation and management
- Job application process for candidates
- Search and filtering by salary, location, and job title
- Email notifications for job applications
- Pagination for job listings and applications

## Installation

1. Clone the repository:
  
    git clone 
    cd job-portal
    

2. Set up a virtual environment:
    
    python -m venv venv
    source venv/bin/activate  # For Linux/MacOS
    venv\Scripts\activate  # For Windows
  

3. Install dependencies:
   
    pip install -r requirements.txt
  

4. Create a `.env` file and configure environment variables (see `.env.example`).
    EMAIL_HOST_USER = 'youremail'
    EMAIL_HOST_PASSWORD ='password'
5. Apply migrations:
    
    python manage.py migrate
    

6. Run the development server:
   
    python manage.py runserver
  

## Running Tests

Run tests to ensure everything works:

python manage.py test
