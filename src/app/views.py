import json
from django.shortcuts import render, redirect
from django.http import HttpResponse
from .models import *
# Create your views here.


def index(request):
    return render(request, 'signin/index.html')

def browse_items(request):
	# query from db
	# get all data of medicines
	# if request.POST

	if request.method == 'POST':
		orders = request.POST.getlist('order[]')
		totalWeight = request.POST['totalWeight']
		# creating an order object
		order = Order.create_order(totalWeight, ClinicLocation.objects.get(id=1), HospitalLocation.objects.get(id=1))

		for item in orders:
			item = json.loads(item)
			orderedItem = OrderedItem.create_orderedItem(order.id, item['id'], item['quantity'])

		return HttpResponse(orders)

	else:
		items = Item.objects.all()
		Categories = Category.objects.all()
		context = {
			'item_list': items,
			'category_list': Categories,
		}
		return render(request, 'browse_items/index.html', context)

def browse_to_be_loaded(request):
    return render(request, 'browse_to_be_loaded/index.html')
