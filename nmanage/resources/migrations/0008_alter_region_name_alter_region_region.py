# Generated by Django 4.0.3 on 2022-04-01 20:42

import django.core.validators
from django.db import migrations, models
import re


class Migration(migrations.Migration):

    dependencies = [
        ('resources', '0007_alter_region_name_alter_resource_name'),
    ]

    operations = [
        migrations.AlterField(
            model_name='region',
            name='name',
            field=models.CharField(max_length=75),
        ),
        migrations.AlterField(
            model_name='region',
            name='region',
            field=models.CharField(blank=True, max_length=25, null=True, validators=[django.core.validators.RegexValidator(re.compile('^[-a-zA-Z0-9_]+\\Z'), 'Enter a valid “slug” consisting of letters, numbers, underscores or hyphens.', 'invalid')]),
        ),
    ]