# Generated by Django 3.2.9 on 2021-11-07 21:18

from django.db import migrations
import phone_field.models


class Migration(migrations.Migration):

    dependencies = [
        ('raceday', '0002_alter_racer_email_address'),
    ]

    operations = [
        migrations.AlterField(
            model_name='racer',
            name='phone_number',
            field=phone_field.models.PhoneField(blank=True, help_text='Contact Phone Number', max_length=31, null=True),
        ),
    ]