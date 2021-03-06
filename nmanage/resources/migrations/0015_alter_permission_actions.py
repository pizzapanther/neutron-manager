# Generated by Django 4.0.3 on 2022-04-05 16:49

import django.contrib.postgres.fields
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('resources', '0014_powerschedule_last_executed'),
    ]

    operations = [
        migrations.AlterField(
            model_name='permission',
            name='actions',
            field=django.contrib.postgres.fields.ArrayField(base_field=models.CharField(choices=[('power', 'Power On/Off'), ('schedule', 'Edit Schedule')], max_length=10, verbose_name='Action Type'), size=None),
        ),
    ]
