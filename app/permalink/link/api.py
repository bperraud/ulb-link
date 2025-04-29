from django.contrib.auth.decorators import login_required
from django.http import HttpResponseBadRequest, JsonResponse
from django.shortcuts import redirect, render

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status, serializers
from rest_framework.generics import get_object_or_404
from django.utils.decorators import method_decorator
from django.contrib.auth.decorators import login_required

from django.conf import settings
from rest_framework.permissions import IsAuthenticated


from link.models import Link, User

import string
import random

from link.auth import CustomJWTAuthentication
from link.context_processors import get_host


def generate_unique_token(length=10):
    chars = string.ascii_letters + string.digits

    while True:
        token = "".join(random.choices(chars, k=length))
        if not Link.objects.filter(token=token).exists():
            return token


class LinkCreateSerializer(serializers.Serializer):
    target_url = serializers.URLField()


class LinkSerializer(serializers.ModelSerializer):
    class Meta:
        model = Link
        fields = ["user", "token", "target_url"]


class CreateLinkAPIView(APIView):
    authentication_classes = [CustomJWTAuthentication]

    def post(self, request):
        # token = request.headers.get("Authorization").split()[1]

        # try:
        #     payload = jwt.decode(
        #         token,
        #         settings.SECRET_KEY,
        #         algorithms=["HS256"],
        #     )
        #     user = get_object_or_404(User, email=payload.get("sub"))
        # except jwt.InvalidSignatureError:
        #     return Response({"Error": "Wrong JWT Secret"}, status=403)
        # except jwt.ExpiredSignatureError:
        #     return Response({"Error": "JWT Token expired"}, status=403)

        serializer = LinkCreateSerializer(data=request.data)
        if serializer.is_valid():
            link, created = Link.objects.get_or_create(
                user=request.user, **serializer.validated_data
            )
            if created:
                token = generate_unique_token()
                link.token = token
            link.save()
            return Response(
                {"permalink": f"{get_host()}/{link.token}", "target": link.target_url},
                status=201,
            )
        return Response(serializer.errors, status=400)

    def get(self, request):
        # Get 'url' from query parameters like ?url=https://example.com
        url = request.query_params.get("url")

        if not url:
            return Response(
                {"error": "Missing 'url' query parameter"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # You can now use the URL as needed
        return Response({"received_url": url}, status=status.HTTP_200_OK)


class LinkAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, pk):
        try:
            link = Link.objects.get(pk=pk)
            serializer = LinkSerializer(link)
            return Response(serializer.data)
        except Link.DoesNotExist:
            return Response({"detail": "Not found."}, status=status.HTTP_404_NOT_FOUND)

    def put(self, request, pk):
        try:
            link = Link.objects.get(pk=pk)
            serializer = LinkSerializer(link, data=request.data, partial=True)
            if serializer.is_valid():
                serializer.save()
                return render(request, "link_row.html", {"link": link})
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        except Link.DoesNotExist:
            return Response({"detail": "Not found."}, status=status.HTTP_404_NOT_FOUND)

    def delete(self, request, pk):
        try:
            link = Link.objects.get(pk=pk)
            link.delete()
            return Response(status=status.HTTP_204_NO_CONTENT)
        except Link.DoesNotExist:
            return Response({"detail": "Not found."}, status=status.HTTP_404_NOT_FOUND)
