# Generated by Django 4.0.3 on 2022-04-04 21:31

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('resources', '0012_powerschedule'),
    ]

    operations = [
        migrations.AddField(
            model_name='resource',
            name='disable_power_schedule',
            field=models.BooleanField(default=False),
        ),
    ]
