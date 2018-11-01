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

		order = Order()
		order.total_weight = totalWeight
		order.ordering_clinic = ClinicLocation.objects.get(id=1)
		order.supplying_hospital = HospitalLocation.objects.get(id=1)
		order.save()

		for item in orders:
			item = json.loads(item)
			orderedItem = OrderedItem()
			orderedItem.order = Order.objects.get(id=order.id)
			orderedItem.item = Item.objects.get(id=item['id'])
			orderedItem.quantity = item['quantity']
			orderedItem.save()

		return HttpResponse(orders)

	else:
		items= Item.objects.all()
		Categories = Category.objects.all()
		context = {
			'item_list': items,
			'category_list': Categories,
		}
		return render(request, 'browse_items/index.html', context)

def browse_to_be_loaded(request):
    return render(request, 'browse_to_be_loaded/index.html')
