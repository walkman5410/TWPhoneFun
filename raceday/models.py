from django.db import models

from phone_field import PhoneField

class Racer(models.Model):
    racer_id = models.AutoField(primary_key=True)
    first_name = models.CharField(max_length=50, null=False)
    last_name = models.CharField(max_length=50, null=False)
    bike_manufacturer = models.CharField(max_length=50, null=True)
    bike_model = models.CharField(max_length=50, null=True)
    email_address = models.EmailField(null=True, blank=True)
    phone_number = PhoneField(blank=True, null=True, help_text='Contact Phone Number')
    is_admin = models.BooleanField(null=True)

    def __str__(self):
        return self.first_name + ' ' + self.last_name

class Race(models.Model):
    race_id = models.AutoField(primary_key=True)
    name = models.CharField(max_length=50, null=False)
    start_lat = models.FloatField(null=True)
    start_long = models.FloatField(null=True)
    end_lat = models.FloatField(null=True)
    end_long = models.FloatField(null=True)
    location_offset = models.FloatField(null=True)
    race_day_date = models.DateField(auto_now=False, null=True, blank=True)
    start_time = models.DateTimeField(auto_now=False, null=True, blank=True)
    completed = models.BooleanField(default=False)
    completed_time = models.DateTimeField(auto_now=False, null=True, blank=True)
    created = models.DateTimeField(auto_now=True, null=False)
    created_by = models.ForeignKey(Racer, on_delete=models.CASCADE)
    
    def __str__(self):
        return self.name

class Result(models.Model):
    result_id = models.AutoField(primary_key=True)
    race_id = models.ForeignKey(Race, on_delete=models.CASCADE)
    racer_id = models.ForeignKey(Racer, on_delete=models.CASCADE)
    end_time = models.DateTimeField(auto_now=False, null=True, blank=True)
    is_checked_in = models.BooleanField(null=True)
    last_checked_in_time = models.DateTimeField(auto_now=False, null=True, blank=True)

    def __str__(self):
        return 'Race: %s Racer: %s %s' % (self.race_id.name, self.racer_id.first_name, self.racer_id.last_name)