from django.shortcuts import render

def home(request):
    u"""Oscar home page"""
    return render(request, 'home.html', locals())
