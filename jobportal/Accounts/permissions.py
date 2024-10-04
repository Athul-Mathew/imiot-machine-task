from rest_framework import permissions

class IsAdmin(permissions.BasePermission):
    """
    Permission for Admin role - Full access.
    """
    def has_permission(self, request, view):
        return request.user.is_authenticated and request.user.role == 'admin'


class IsEmployer(permissions.BasePermission):
    """
    Permission for Employer role - Can manage job listings and view applications.
    """
    def has_permission(self, request, view):
        return request.user.is_authenticated and request.user.role == 'employer'


class IsCandidate(permissions.BasePermission):
    """
    Permission for Candidate role - Can apply for jobs and manage their own applications.
    """
    def has_permission(self, request, view):
        return request.user.is_authenticated and request.user.role == 'candidate'
