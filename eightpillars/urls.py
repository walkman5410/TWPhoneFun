from django.urls import re_path

from django.contrib.auth import views as auth_views

from . import views

app_name = "eightpillars"

urlpatterns = [
    re_path(r'^$', views.HomePage.as_view(), name="homepage"),
    re_path(r'^view_all_eight_pillar_data$', views.view_all_eight_pillar_data, name="view_all_eight_pillar_data"),
    re_path(r'^view_all_eight_pillar_winner_data$', views.view_all_eight_pillar_winner_data, name="view_all_eight_pillar_winner_data"),

    re_path(r'^login/$', auth_views.LoginView.as_view(), name='login'),
    re_path(r'^logout/$', auth_views.LogoutView.as_view(), name='logout'),

    #Functions
    re_path(r'^get_the_pillars', views.get_the_pillars, name='get_the_pillars'),
    re_path(r'^get_the_pillar_table', views.get_the_pillar_table, name='get_the_pillar_table'),    
]