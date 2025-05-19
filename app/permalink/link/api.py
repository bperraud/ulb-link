from django.shortcuts import render

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status, serializers
from rest_framework.generics import get_object_or_404

from rest_framework.permissions import IsAuthenticated

from link.models import Link, Share

import string, random
from urllib.parse import unquote

from link.auth import CustomJWTAuthentication


def generate_unique_token(length=10):
    chars = string.ascii_letters + string.digits

    while True:
        token = "".join(random.choices(chars, k=length))
        if not Link.objects.filter(token=token).exists():
            return token


class ShareCreateSerializer(serializers.ModelSerializer):

    class Meta:
        model = Share
        fields = ["uid", "expiration", "target_url", "path"]

    # uid = serializers.IntegerField()
    # target_url = serializers.URLField()
    # expiration = serializers.DateField(required=False, allow_blank=True)
    # path = serializers.CharField(required=False)


class LinkSerializer(serializers.ModelSerializer):
    class Meta:
        model = Link
        fields = ["user", "token", "target_url"]


class LinkEditSerializer(serializers.Serializer):
    target_url = serializers.URLField()
    token = serializers.CharField()


class ExternalLinkAPIView(APIView):
    authentication_classes = [CustomJWTAuthentication]

    def put(self, request):
        serializer = LinkEditSerializer(data=request.data)
        if serializer.is_valid():
            link = get_object_or_404(
                Link, user=request.user, token=serializer.validated_data["token"]
            )
            link.sharelink.target_url = request.data["target_url"]
            link.save()
            return Response(
                {"permalink": link.get_permalink()},
                status=200,
            )
        return Response(serializer.errors, status=400)

    def post(self, request):
        serializer = ShareCreateSerializer(data=request.data)
        if serializer.is_valid():
            print(serializer.validated_data)
            share = Share.objects.create(**serializer.validated_data)
            link = Link.objects.create(user=request.user, share=share)
            token = generate_unique_token()
            link.token = token
            return Response(
                {"permalink": link.get_permalink()},
                status=201,
            )
        return Response(serializer.errors, status=400)

    def get(self, request):
        target_url = request.query_params.get("target_url")

        if not target_url:
            return Response(
                {"error": "Missing 'target_url' query parameter"},
                status=400,
            )
        try:
            permalink = Link.objects.get(
                user=request.user, sharelink__target_url=unquote(target_url)
            )
        except Link.DoesNotExist:
            return Response(
                {"error": "Permalink does not exist"},
                status=400,
            )
        return Response(
            {
                "permalink": permalink.get_permalink(),
                "token": permalink.token,
                "target_url": permalink.sharelink.target_url,
            },
            status=200,
        )

    def delete(self, request):
        target_url = request.query_params.get("target_url")

        if not target_url:
            return Response(
                {"error": "Missing 'target_url' query parameter"},
                status=400,
            )
        try:
            permalink = Link.objects.get(
                user=request.user, sharelink__target_url=unquote(target_url)
            )
        except Link.DoesNotExist:
            return Response(
                {"error": "Permalink does not exist"},
                status=400,
            )
        permalink.delete()
        return Response({"message": "Permalink deleted successfully"}, status=200)


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
