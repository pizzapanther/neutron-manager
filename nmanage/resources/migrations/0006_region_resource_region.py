# Generated by Django 4.0.3 on 2022-03-31 21:48

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('resources', '0005_remove_resource_account_remove_resource_endpoint_and_more'),
    ]

    operations = [
        migrations.CreateModel(
            name='Region',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=75)),
                ('region', models.CharField(blank=True, max_length=25, null=True)),
                ('endpoint', models.CharField(blank=True, max_length=128, null=True)),
                ('created', models.DateTimeField(auto_now_add=True, db_index=True)),
                ('modified', models.DateTimeField(auto_now=True, db_index=True)),
                ('account', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='resources.awsaccount')),
            ],
        ),
        migrations.AddField(
            model_name='resource',
            name='region',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to='resources.region'),
        ),
    ]
