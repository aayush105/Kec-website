from django.contrib import admin
from django.urls import path, include
from . import views

urlpatterns = [
    path('', views.home, name="home"),
    path('signup',views.signup,name="signup"),
    path('signin',views.signin,name="signin"),
    path('signout',views.signout,name="signout"),
    path('result',views.result,name="result"),
    path('notices',views.notices,name="notices"),
    path('activate/<uidb64>/<token>',views.activate,name="activate"),

]
