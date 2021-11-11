from django.urls import re_path, path, include
from django.contrib.auth import views as auth_views
from django.contrib.auth.models import User

from rest_framework import routers, serializers, viewsets

from raceday import views
from raceday.models import Racer, Race, Result

app_name = "raceday"


# Serializers define the API representation.
class RacerSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = Racer
        fields = ['first_name', 'last_name', 'email_address', 'is_admin']

class RacerViewSet(viewsets.ModelViewSet):
    queryset = Racer.objects.all()
    serializer_class = RacerSerializer

# Serializers define the API representation.
class RaceSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = Race
        fields = ['race_id', 'name', 'race_day_date', 'completed', 'start_lat', 'start_long', 'location_offset']

class RaceViewSet(viewsets.ModelViewSet):
    queryset = Race.objects.all()
    serializer_class = RaceSerializer

# Serializers define the API representation.
class UserSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = User
        fields = ['url', 'username', 'email', 'is_staff']

# ViewSets define the view behavior.
class UserViewSet(viewsets.ModelViewSet):
    queryset = User.objects.all()
    serializer_class = UserSerializer


# Routers provide an easy way of automatically determining the URL conf.
router = routers.DefaultRouter()
router.register(r'users', UserViewSet)
router.register(r'racers', RacerViewSet)
router.register(r'race_list', RaceViewSet)

urlpatterns = [
    re_path(r'^$', views.homepage, name="homepage"),
    path('', include(router.urls)),
    #Get info

    #functions
    re_path(r'^create_race$', views.create_race, name="create_race"),
    
]