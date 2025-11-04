from django.contrib import admin
from . import models


admin.site.register(models.PendingUser)
admin.site.register(models.Profile)
