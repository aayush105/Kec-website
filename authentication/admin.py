from django.contrib import admin
from .models import FetchedData,ResultData,Subscriber

# Register your models here.
@admin.register(FetchedData)
class FetchedDataAdmin(admin.ModelAdmin):
    list_display = ('title','date','category','file_path','url')

@admin.register(ResultData)
class ResultDataAdmin(admin.ModelAdmin):
    list_display = ('faculty','year','part','symbol','bs')

@admin.register(Subscriber)
class SubscriberAdmin(admin.ModelAdmin):
    pass