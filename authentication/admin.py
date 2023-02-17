from django.contrib import admin
from .models import FetchedData

# Register your models here.
@admin.register(FetchedData)
class FetchedDataAdmin(admin.ModelAdmin):
    list_display = ('title','date','category','file_path','url')