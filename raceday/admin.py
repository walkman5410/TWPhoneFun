from django.contrib import admin
from raceday.models import Racer, Race, Result

# Register your models here.
admin.site.register(Racer)
admin.site.register(Race)
admin.site.register(Result)