import json
from django.shortcuts import render, redirect
from django.http import HttpResponse
from .models import *


def index(request):
    return render(request, 'signin/index.html')

def register(request):
    return render(request, 'register/index.html')

def browse_items(request):
	# get all data of medicines
	if request.method == 'POST':
		print("post request")
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

	# updating order status to dispatched
	if request.method == 'POST':
		orderId = request.POST['orderId']
		Order.loaded_into_drone(orderId)
		return HttpResponse('test')

	else:
		# rendering all orders with status QUEUED_FOR_DISPATCH
		orders = Order.objects.filter(status=Order.STATUS_CHOICES[2][0])
		context = {
			'order_list': orders,
		}
		return render(request, 'browse_to_be_loaded/index.html', context)
