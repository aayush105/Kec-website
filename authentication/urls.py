from django.contrib import admin
from django.urls import path, include
from . import views

urlpatterns = [
    path('', views.home, name="home"),
    path('subscribe',views.subscribe, name="subscribe"),
    path('notices',views.notices,name="notices"),
    path('about',views.home,name="about"),
    path("contact",views.home,name="contact"),
    path('submit_form/',views.checkSymbol,name="checkSymbol"),
    path('activate/<uidb64>/<token>',views.activate,name="activate"),

]
