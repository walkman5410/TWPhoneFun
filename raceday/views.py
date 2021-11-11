from django.shortcuts import render
from django.http import JsonResponse

from rest_framework.decorators import api_view, permission_classes, authentication_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.authentication import TokenAuthentication

from raceday.models import Racer, Race, Result
from django.contrib.auth.models import User

@api_view(['POST', 'GET'])
def homepage(request):
    #check if user is logged in
    #not logged in -> go to login
    #is admin -> go to admin / provide token
    #is not admin -> go to racer / provide token
    #else fail
    pass

@api_view(['POST'])
def create_race(request):
    data = {}
    status=201
    #if not request.user.is_authenticated:
    #    status = 401
    #    data['message'] = 'Not authenticated'
    if request.method == 'POST':
        Race.objects.update_or_create(
            name = request.POST.get('race_name'),
            race_day_date = request.POST.get('race_date'),
            created_by = Racer.objects.get(racer_id=1),
            defaults={
                'start_lat': request.POST.get('start_lat'),
                'start_long': request.POST.get('start_long'),
                'end_lat': request.POST.get('end_lat'),
                'end_long': request.POST.get('end_long'),   
                'location_offset': 1/(111.111/(0.0003048 * request.POST.get('location_offset')))        
            }
        )
    else:
        status = 500
        data['message'] = 'There was an issue with your request.'

    return JsonResponse(data, status=status)

@api_view(['GET'])
def get_start_data(request):
    data = {}
    status = 201

    return JsonResponse