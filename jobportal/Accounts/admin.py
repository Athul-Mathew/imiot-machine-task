from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import User,Company,JobApplication,JobListing

# Register your models here.
admin.site.register(User)
admin.site.register(Company)
admin.site.register(JobListing)
admin.site.register(JobApplication)




