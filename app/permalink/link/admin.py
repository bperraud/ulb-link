from django.contrib import admin

from link.models import *

admin.site.register(Link)
admin.site.register(Share)
admin.site.register(User)
admin.site.register(NextcloudShareBatchJob)
