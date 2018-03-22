from django.contrib import admin

# Register your models here.
from taskdo import models
admin.site.register(models.ConnectionInfo)
