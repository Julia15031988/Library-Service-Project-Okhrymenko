from rest_framework.permissions import SAFE_METHODS, BasePermission

class IsAdminOrReadOnly(BasePermission):
    def has_permission(self, request, view):
        # Дозволити усім (включно з анонімами) безпечні методи (GET, HEAD, OPTIONS)
        if request.method in SAFE_METHODS:
            return True

        # Для небезпечних методів — лише адміністратори
        return bool(request.user and request.user.is_staff)
