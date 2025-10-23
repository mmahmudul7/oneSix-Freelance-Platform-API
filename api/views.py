from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from django.core.mail import send_mail
from django.conf import settings


class ContactView(APIView):
    def post(self, request):
        name = request.data.get("name")
        email = request.data.get("email")
        subject = request.data.get("subject", "No subject")
        message = request.data.get("message")

        if not all([name, email, message]):
            return Response(
                {"error": "Please provide all required fields."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        send_mail(
            subject=f"[Contact] {subject}",
            message=f"Name: {name}\nEmail: {email}\n\nMessage:\n{message}",
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=["admin@onesix.dev"],
        )

        return Response({"success": "Message sent successfully!"}, status=status.HTTP_200_OK)
