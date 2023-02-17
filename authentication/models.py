from django.db import models

# Create your models here.

class FetchedData(models.Model):
    title = models.CharField(max_length=255)
    date = models.DateField()
    category = models.CharField(max_length=10, choices=[('notice', 'Notice'), ('result', 'Result')])
    file_path = models.FileField(upload_to='fetched_data/%Y/%m/%d/')
    url = models.URLField(max_length=255)

    def __str__(self):
        return self.title
