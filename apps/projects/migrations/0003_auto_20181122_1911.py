# Generated by Django 2.1.2 on 2018-11-22 19:11

from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('projects', '0002_auto_20181116_2021'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='project',
            name='creator',
        ),
        migrations.AddField(
            model_name='project',
            name='members',
            field=models.ManyToManyField(related_name='projects', to=settings.AUTH_USER_MODEL),
        ),
    ]