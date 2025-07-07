from rest_framework import permissions
from django.contrib.auth.models import User

class IsAuthorOrReadOnly(permissions.BasePermission):
    """
    Custom permission to only allow authors of an article to edit it.
    """
    
    def has_object_permission(self, request, view, obj):
        # Read permissions for any request
        if request.method in permissions.SAFE_METHODS:
            return True
        
        # Write permissions only for the author or staff
        return obj.author == request.user or request.user.is_staff

class IsOwnerOrReadOnly(permissions.BasePermission):
    """
    Custom permission to only allow owners of an object to edit it.
    """
    
    def has_object_permission(self, request, view, obj):
        # Read permissions for any request
        if request.method in permissions.SAFE_METHODS:
            return True
        
        # Write permissions only for the owner or staff
        if hasattr(obj, 'user'):
            return obj.user == request.user or request.user.is_staff
        elif hasattr(obj, 'author'):
            return obj.author == request.user or request.user.is_staff
        return request.user.is_staff

class IsStaffOrReadOnly(permissions.BasePermission):
    """
    Custom permission to only allow staff users to edit.
    """
    
    def has_permission(self, request, view):
        if request.method in permissions.SAFE_METHODS:
            return True
        return request.user.is_authenticated and request.user.is_staff

class IsAuthorProfileOwner(permissions.BasePermission):
    """
    Custom permission for author profile management.
    """
    
    def has_object_permission(self, request, view, obj):
        if request.method in permissions.SAFE_METHODS:
            return True
        return obj.user == request.user or request.user.is_staff

class IsNewsletterOwner(permissions.BasePermission):
    """
    Custom permission for newsletter subscription management.
    """
    
    def has_object_permission(self, request, view, obj):
        # Anyone can read newsletter info (for admin purposes)
        if request.method in permissions.SAFE_METHODS:
            return request.user.is_staff
        
        # Only staff can modify newsletters
        return request.user.is_staff