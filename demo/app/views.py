from django.shortcuts import render, redirect
from .models import *
# Create your views here.


def index(request):
    return render(request, 'signin.html')

def browse(request):
    return render(request, 'browse.html')
