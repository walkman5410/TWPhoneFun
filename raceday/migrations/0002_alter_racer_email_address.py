# Generated by Django 3.2.9 on 2021-11-07 21:14

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('raceday', '0001_initial'),
    ]

    operations = [
        migrations.AlterField(
            model_name='racer',
            name='email_address',
            field=models.EmailField(blank=True, max_length=254, null=True),
        ),
    ]
