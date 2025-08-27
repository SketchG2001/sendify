from django.contrib import admin
from .models import CustomUser,Configurations

admin.site.register(CustomUser)

@admin.register(Configurations)
class ConfigurationsAdmin(admin.ModelAdmin):
    list_display = ("user", "email", "is_active","_app_password")