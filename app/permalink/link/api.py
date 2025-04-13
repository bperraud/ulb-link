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


class LinkCreateSerializer(serializers.Serializer):
    email = serializers.EmailField()
    token = serializers.CharField(max_length=50)
    target_url = serializers.URLField()


class LinkCreateAPIView(APIView):
    def post(self, request):
        serializer = LinkCreateSerializer(data=request.data)
        if serializer.is_valid():
            email = serializer.validated_data.pop("email")
            user = get_object_or_404(User, email=email)
            # Create Link manually (or use ModelSerializer if you prefer)
            link = Link.objects.create(user=user, **serializer.validated_data)
            return Response(
                {"token": link.token, "target": link.target_url}, status=201
            )
        return Response(serializer.errors, status=400)
