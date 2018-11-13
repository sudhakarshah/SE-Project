import json
import io
from django.shortcuts import render, redirect
from django.http import HttpResponse
from reportlab.pdfgen import canvas
from .models import *


def index(request):
    if request.method == 'GET':        
        return render(request, 'signin/index.html')
    else:
        return render(request, 'signin/index.html')

def register(request):
    if request.method == 'POST':
        firstName = request.POST['firstName']
        lastName = request.POST['lastName']
        email = request.POST['email']
        password = request.POST['password']
        username = request.POST['username']
        role_choices = request.POST['role_choices']
        clinicLocation = request.POST['clinicLocation']
        register_instance = User.create_user(firstName=firstName, lastName=lastName, email=email,username=username,password=password,role_choices=role_choices, clinicLocation= clinicLocation);
        return render(request, 'register/index.html')
    else:    
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

def browse_to_be_processed(request):

	if request.method == 'POST':

		event = request.POST['event']
		orderId = request.POST['orderId']

		if event == 'READY_TO_PROCESS':
			Order.ready_to_process(orderId)
		elif event == 'COMPLETE_PROCESSING': 
			Order.complete_processing(orderId)
		elif event == 'DOWNLOAD_SHIPPING_LABEL':
			# Create the HttpResponse object with the appropriate PDF headers.
			response = HttpResponse(content_type='application/pdf')
			response['Content-Disposition'] = 'attachment; filename="somefilename.pdf"'

			# Create the PDF object, using the response object as its "file."
			p = canvas.Canvas(response)

			# Draw things on the PDF. Here's where the PDF generation happens.
			# See the ReportLab documentation for the full list of functionality.
			p.drawString(100, 100, "Hello world.")

			# Close the PDF object cleanly, and we're done.
			p.showPage()
			p.save()
			return response

		return HttpResponse('test')

	else:
		processOrders = Order.objects.filter(status=Order.STATUS_CHOICES[0][0])
		packOrders = Order.objects.filter(status=Order.STATUS_CHOICES[1][0])
		context = {
			'process_order_list': processOrders,
			'pack_order_list': packOrders,
		}
		return render(request, 'browse_orders_warehouse/index.html', context)
