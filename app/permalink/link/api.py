from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.http import HttpResponseBadRequest, JsonResponse
from django.shortcuts import redirect, render
from django.urls import reverse
from django.utils.html import escape
from django.views.decorators.http import require_GET, require_POST


# views.py
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status, serializers
from rest_framework.generics import get_object_or_404

from link.models import Link, User

import string
import random


def generate_unique_token(length=10):
    chars = string.ascii_letters + string.digits

    while True:
        token = "".join(random.choices(chars, k=length))
        if not Link.objects.filter(token=token).exists():
            return token


class LinkCreateSerializer(serializers.Serializer):
    email = serializers.EmailField()
    target_url = serializers.URLField()


class LinkSerializer(serializers.ModelSerializer):
    class Meta:
        model = Link
        fields = ["user", "token", "target_url"]


class LinkAPIView(APIView):
    def post(self, request):
        serializer = LinkCreateSerializer(data=request.data)
        if serializer.is_valid():
            email = serializer.validated_data.pop("email")
            user = get_object_or_404(User, email=email)
            link = Link.objects.create(
                user=user, token=generate_unique_token(), **serializer.validated_data
            )
            return Response(
                {"token": link.token, "target": link.target_url}, status=201
            )
        return Response(serializer.errors, status=400)

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
