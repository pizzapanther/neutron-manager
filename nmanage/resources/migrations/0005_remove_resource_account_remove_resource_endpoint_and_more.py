# Generated by Django 4.0.3 on 2022-03-31 21:44

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('resources', '0004_resource_endpoint_resource_region'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='resource',
            name='account',
        ),
        migrations.RemoveField(
            model_name='resource',
            name='endpoint',
        ),
        migrations.RemoveField(
            model_name='resource',
            name='region',
        ),
    ]