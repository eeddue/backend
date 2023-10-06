from rest_framework import permissions


class IsPharmacist(permissions.BasePermission):
    message = "Only pharmacists are authorized"

    def has_permission(self, request, view):
        # Check if the user is logged in and has the role of "Pharmacist"
        return request.user.is_authenticated and request.user.is_pharmacist()


class IsCustomer(permissions.BasePermission):
    message = "Only customers are authorized."

    def has_permission(self, request, view):
        return request.user.is_authenticated and request.user.is_customer()


class IsProductOwner(permissions.BasePermission):
    """
    This IsProductOwner permission class checks if the user is authenticated,
    is a pharmacist (as determined by the is_pharmacist() method in the User model), 
    and if the user is the owner of the product.
    """

    def has_object_permission(self, request, view, obj):
        # Check if the user is a pharmacist and is the owner of the product
        return request.user.is_authenticated and request.user.is_pharmacist() and obj.created_by == request.user


class IsCustomerReviewOwner(permissions.BasePermission):
    """
    Only users who are Customers and who created the review
    can update or delete their own review (while Pharmacists 
    are not allowed to perform these actions).
    """

    def has_object_permission(self, request, view, obj):
        # Check if the user is authenticated and is a customer
        if request.user.is_authenticated and request.user.is_customer():
            # Check if the user is the owner of the review
            return obj.user == request.user
        return False
