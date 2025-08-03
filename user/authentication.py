from rest_framework_simplejwt.authentication import JWTAuthentication


class CustomJWTAuthentication(JWTAuthentication):
    def get_header(self, request):
        """
        Return the value of the 'Authorize' header instead of 'Authorization'.
        """
        header = request.META.get("HTTP_AUTHORIZE")
        if isinstance(header, str):
            return header.encode("utf-8")
        return header
