# Generated by Django 4.0.3 on 2022-04-01 21:18

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('resources', '0010_resource_zone_update'),
    ]

    operations = [
        migrations.AddField(
            model_name='resource',
            name='last_zone_ip',
            field=models.CharField(blank=True, max_length=75, null=True),
        ),
    ]
