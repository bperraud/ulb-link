from django.contrib.auth.decorators import login_required
from django.shortcuts import render

from link.models import Link

# Create your views here.


@login_required
def home(request):
    links = Link.objects.filter(user=request.user)
    return render(request, "home.html", locals())
