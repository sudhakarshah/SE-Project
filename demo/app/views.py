from django.shortcuts import render, redirect
from .models import *
# Create your views here.


def index(request):
    return render(request, 'signin.html')

def browse(request):
	# query from db
	# get all data of medicines
	# if request.POST
	items= Item.objects.all()
	Categories = Category.objects.all()
	context = {
        'item_list': items,
		'category_list': Categories,
    }
	return render(request, 'browse.html',context)
