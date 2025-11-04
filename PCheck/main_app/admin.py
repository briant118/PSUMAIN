from django.contrib import admin
from . import models

# Register your models here.
admin.site.register(models.College)
admin.site.register(models.PC)
admin.site.register(models.Booking)
admin.site.register(models.Violation)
admin.site.register(models.Chat)