from django.db import models
from django.contrib.auth.models import User

# Create your models here.

class FetchedData(models.Model):
    title = models.CharField(max_length=255)
    date = models.DateField()
    category = models.CharField(max_length=10, choices=[('notice', 'Notice'), ('result', 'Result')])
    file_path = models.FileField(upload_to='fetched_data/%Y/%m/%d/')
    url = models.URLField(max_length=255, unique=True)
    is_downloaded = models.BooleanField(default=False)
    is_ocr_read = models.BooleanField(default=False)
        

    def __str__(self):
        return self.title


class ResultData(models.Model):
    faculty = models.CharField(max_length=5, choices=[('BCT','BCT'),('BEX','BEX'),('BCE','BCE')])
    bs = models.IntegerField()
    year = models.CharField(max_length=5, choices=[('I','I'),('II','II'),('III','III'),('IV','IV')])
    part = models.CharField(max_length=5, choices=[('I','I'),('II','II')])
    symbol = models.CharField(max_length=20)

    class Meta:
        unique_together = [('faculty', 'bs', 'year', 'part','symbol')]

    def __str__(self):
        return self.symbol

class Subscriber(models.Model):
    fullname = models.CharField(max_length=50)
    email = models.EmailField(unique=True)
    bs_year = models.IntegerField()
    faculty = models.CharField(max_length=5,choices=[('BCT','BCT'),('BEX','BEX'),('BCE','BCE')])
    year = models.CharField(max_length=5,choices=[('I','I'),('II','II'),('III','III'),('IV','IV')])
    part = models.CharField(max_length=5,choices=[('I','I'),('II','II')])
    symbol = models.CharField(max_length=20)
    is_active = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.email