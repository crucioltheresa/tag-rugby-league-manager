from django.contrib import admin
from .models import InterestRegistration, EmailWhitelist

# Register your models here.
admin.site.register(InterestRegistration)
admin.site.register(EmailWhitelist)
