# Generated by Django 4.1.7 on 2023-03-12 16:28

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('authentication', '0008_alter_subscriber_faculty'),
    ]

    operations = [
        migrations.AddField(
            model_name='fetcheddata',
            name='is_downloaded',
            field=models.BooleanField(default=False),
        ),
    ]
