import json
import uuid
from django.shortcuts import render, redirect
from django.http import HttpResponse
from django.contrib.auth import authenticate
from django.views.decorators.csrf import csrf_exempt

from .models import *


def index(request):
    if request.method == 'POST':
        username = request.POST['username']
        password = request.POST['password']
        user = authenticate(username=username, password=password)   
        if user is not None:
            # Authenticated
            return render(request, 'signin/index.html')
    else:
        return render(request, 'signin/index.html')

@csrf_exempt
def register_details(request):
    if request.method == 'POST':
        firstName = request.POST['firstName']
        lastName = request.POST['lastName']
        email = request.POST['email']
        role = request.POST['role']
        clinicName = request.POST['clinicName']
        username = request.POST['username']
        password = request.POST['password']
        register_user_instance = User.create_user(firstName, lastName, email, role, clinicName, username, password)
        return HttpResponse("Success")
    else:
        token_id = request.GET['token']
        initial_registration_data = InitialTokenRegistration.objects.get(unique_token=token_id)
        clinics = ClinicLocation.objects.all()
        context = {
            'initial_data': initial_registration_data,
            'clinics': clinics,
            'need_clinic_location': True,
        }
        return render(request, 'register_with_details/index.html', context)

@csrf_exempt
def register_send_token(request):
    if request.method == 'POST':
        email = request.POST['email']
        #role_choice = request.POST['role_choices']
        role = "CLINIC_MANAGER"
        # See how to generate email to log file
        unique_token = str(uuid.uuid3(uuid.NAMESPACE_DNS, email))
        print ("http://localhost:8000/app/registration?token=" + unique_token)
        register_token_instance = InitialTokenRegistration.create(unique_token, email, role)
        return render(request, 'register_send_token/index.html')
    else:
        return render(request, 'register_send_token/index.html')

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
