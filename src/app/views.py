import csv
import json
import io
from io import BytesIO
import uuid

import simplejson as simplejson
from django.template import loader
from reportlab.pdfgen import canvas
from django.shortcuts import render, redirect
from django.http import HttpResponse
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.models import User
from django.views.decorators.csrf import csrf_exempt
from django.db.models import Q

from .models import *


@csrf_exempt
def signin(request):
    if request.method == 'POST':
        result = {
            'success': False,
            'pageLink': "",
        }
        username = request.POST['username']
        password = request.POST['password']
        user = authenticate(username=username, password=password)
        if user is not None:
            print("user authenticated\n")
            result['success'] = True
            login(request, user)
            # Authenticated
            profile = Profile.objects.get(user=user)
            result['pageLink'] = '/app/home'
            # Saving the appropriate session
            request.session['role'] = profile.role
            if (profile.role == "CLINIC_MANAGER"):
                request.session['clinicName'] = ClinicLocation.objects.get(id=profile.clinic_location.id).name
            return HttpResponse(json.dumps(result), content_type="application/json")
        else:
            return HttpResponse(json.dumps(result), content_type="application/json")
    else:
        return render(request, 'signin/index.html')


@csrf_exempt
def signout(request):
    logout(request)
    return render(request, 'signin/index.html')


@csrf_exempt
def home(request):
    if not request.user.is_authenticated:
        return redirect('/app')

    if request.session['role'] == 'CLINIC_MANAGER':
        # browse_items(request)
        clinicName = request.session['clinicName']
        items = Item.objects.all()
        Categories = Category.objects.all()
        context = {
            'item_list': items,
            'category_list': Categories,
            'clinic_name': clinicName
        }
        return render(request, 'browse_items/index.html', context)
    elif request.session['role'] == 'WAREHOUSE_PERSONNEL':
        processOrders = Order.objects.filter(status=Order.STATUS_CHOICES[0][0]).order_by('-priority')
        packOrders = Order.objects.filter(status=Order.STATUS_CHOICES[1][0]).order_by('-priority')
        context = {
            'process_order_list': processOrders,
            'pack_order_list': packOrders,
        }
        return render(request, 'browse_orders_warehouse/index.html', context)
    # browse_to_be_loaded(request)

    elif request.session['role'] == 'DISPATCHER':
        # browse_to_be_processed(request)
        orders = Order.objects.filter(status=Order.STATUS_CHOICES[2][0]).order_by('-priority')
        context = {
            'order_list': orders,
        }
        return render(request, 'browse_to_be_loaded/index.html', context)


@csrf_exempt
def register_details(request):
    if request.method == 'POST':
        result = {
            'success': True,
            'reason': '',
        }
        firstName = request.POST['firstName']
        lastName = request.POST['lastName']
        email = request.POST['email']
        role = request.POST['role']
        clinicName = None
        if 'clinicName' in request.POST:
            clinicName = request.POST['clinicName']
        username = request.POST['username']
        password = request.POST['password']
        register_user_instance = Profile.create_profile(firstName, lastName, email, role, clinicName, username,
                                                        password)
        result['pageLink'] = '/app'
        return HttpResponse(json.dumps(result), content_type="application/json")
    else:
        token_id = request.GET['token']
        initial_registration_data = InitialTokenRegistration.objects.get(unique_token=token_id)
        clinics = ClinicLocation.objects.all()
        need_clinic_location = False
        # Will only need clinic location if they are a clinic manager
        if initial_registration_data.role == "CLINIC_MANAGER":
            need_clinic_location = True
        context = {
            'initial_data': initial_registration_data,
            'clinics': clinics,
            'need_clinic_location': need_clinic_location,
        }
        return render(request, 'register_with_details/index.html', context)


@csrf_exempt
def register_send_token(request):
    if request.method == 'POST':
        result = {
            'success': False,
            'reason': '',
        }
        email = request.POST['email']
        role = request.POST['role_choices']
        unique_token = str(uuid.uuid3(uuid.NAMESPACE_DNS, email))
        print("http://localhost:8000/app/registration?token=" + unique_token)
        register_token_instance = InitialTokenRegistration.create(unique_token, email, role)
        # send email and check if create in db is successful. If not then make result['success'] = false
        if True:
            result['success'] = True
        else:
            result['reason'] = 'reason'
        return HttpResponse(json.dumps(result), content_type="application/json")
    else:
        return render(request, 'register_send_token/index.html')


def browse_items(request):
    result = {
        'success': False,
        'reason': "",
    }
    if not request.user.is_authenticated:
        result['reason'] = "request not authenticated"
        return HttpResponse(json.dumps(result), content_type="application/json")

    if request.method != 'POST':
        result['reason'] = "Invalid request"
        return HttpResponse(json.dumps(result), content_type="application/json")

    # if post request
    orders = request.POST.getlist('order[]')
    totalWeight = request.POST['totalWeight']
    priority = request.POST['priority']
    # creating an order object
    order = Order.create_order(totalWeight, ClinicLocation.objects.get(name=request.session['clinicName']),
                               HospitalLocation.objects.get(id=1),
                               priority)
    for item in orders:
        item = json.loads(item)
        orderedItem = OrderedItem.create_orderedItem(order.id, item['id'], item['quantity'])
    result['success'] = True
    return HttpResponse(json.dumps(result), content_type="application/json")


def browse_to_be_loaded(request):
    result = {
        'success': False,
        'reason': "",
    }
    if not request.user.is_authenticated:
        result['reason'] = "request not authenticated"
        print("not authenticated")
        return HttpResponse(json.dumps(result), content_type="application/json")

    if request.method != 'POST':
        result['reason'] = "Invalid request"
        return HttpResponse(json.dumps(result), content_type="application/json")

    # updating order status to dispatched
    if request.POST['event'] == 'LOAD_INTO_DRONE':
        order_ids = request.POST.getlist('orderIds[]')
        shipment = Shipment.create_shipment(Shipment)
        lines_to_be_printed_in_csv = []
        clinics_to_be_added = []
        # Updating all the orders in the shipment
        for order_id in order_ids:
            current_order = Order.objects.get(id=order_id)
            if current_order.ordering_clinic.id not in clinics_to_be_added:
                clinics_to_be_added.append(current_order.ordering_clinic.id)
            Order.loaded_into_drone(order_id, shipment)

        # Checking the clinic where the shipment goes
        for clinic_id in clinics_to_be_added:
            ordering_clinic = ClinicLocation.objects.get(id=clinic_id)
            location_of_clinic = []
            location_of_clinic.append(ordering_clinic.latitute)
            location_of_clinic.append(ordering_clinic.longitute)
            location_of_clinic.append(ordering_clinic.altitude)
            lines_to_be_printed_in_csv.append(location_of_clinic)

        # Creating CSV file and updating location
        csv_file_name = 'shipment' + str(shipment.id) + '.csv'
        shipment.update_file_location(csv_file_name)
        # Adding the hospital as the last stop
        location_of_hospital = []
        location_of_hospital.append(HospitalLocation.objects.get(id=1).latitute)
        location_of_hospital.append(HospitalLocation.objects.get(id=1).longitute)
        location_of_hospital.append(HospitalLocation.objects.get(id=1).altitude)
        lines_to_be_printed_in_csv.append(location_of_hospital)
        # Writing to the CSV file
        with open(csv_file_name, 'w') as writeFile:
            writer = csv.writer(writeFile)
            writer.writerows(lines_to_be_printed_in_csv)
        writeFile.close()
        result['success'] = True
        result['shipmentId'] = shipment.id
        return HttpResponse(json.dumps(result), content_type="application/json")
    elif (request.POST['event'] == 'DOWNLOAD'):
        shipmentId = request.POST['shippmentId']
        csv_file_name = 'shipment' + str(shipmentId) + '.csv'
        with open(csv_file_name) as csvfile:
            reader = csv.reader(csvfile)
            data = [r for r in reader]
        total_data = []
        for row in data:
            total_data.append(row)
        result['success'] = True
        result['totalData'] = total_data
        return HttpResponse(json.dumps(result), content_type="application/json")


def browse_to_be_processed(request):
    result = {
        'success': False,
        'reason': "",
    }
    if not request.user.is_authenticated:
        result['reason'] = "request not authenticated"
        print("not authenticated")
        return HttpResponse(json.dumps(result), content_type="application/json")

    if request.method != 'POST':
        result['reason'] = "Invalid request"
        return HttpResponse(json.dumps(result), content_type="application/json")

    event = request.POST['event']
    orderId = request.POST['orderId']
    if event == 'READY_TO_PROCESS':
        Order.ready_to_process(orderId)
        result['success'] = True
    elif event == 'COMPLETE_PROCESSING':
        Order.complete_processing(orderId)
        result['success'] = True
    elif event == 'DOWNLOAD_SHIPPING_LABEL':
        order = Order.objects.get(pk=orderId)
        response = HttpResponse(content_type='application/pdf')
        response['Content-Disposition'] = 'inline; filename="mypdf.pdf"'
        buffer = BytesIO()
        p = canvas.Canvas(buffer)
        p.drawString(100, 700, 'Order Number: ' + orderId)
        p.drawString(100, 650, 'Order Content: ')
        height = 625
        for item in order.items.all():
            height = height - 25
            p.drawString(150, height, item.name)
        p.drawString(100, height - 50, 'Order destination: ' + order.ordering_clinic.name)
        p.showPage()
        p.save()
        pdf = buffer.getvalue()
        buffer.close()
        response.write(pdf)
        return response
    else:
        result['reason'] = 'Incorrect Event Name'

    return HttpResponse(json.dumps(result), content_type="application/json")


@csrf_exempt
def browse_orders(request):
    result = {
        'success': False,
        'reason': "",
    }
    if not request.user.is_authenticated:
        result['reason'] = "request not authenticated"
        print("not authenticated")
        return HttpResponse(json.dumps(result), content_type="application/json")

    if request.session['role'] != 'CLINIC_MANAGER':
        result['reason'] = "Only Clinic Manage can access"
        return HttpResponse(json.dumps(result), content_type="application/json")

    if request.method == 'POST':
        orderId = request.POST['orderId']
        Order.confirm_order_delivery(orderId)
        result['success'] = True
        return HttpResponse(json.dumps(result), content_type="application/json")
    else:
        orders = Order.objects.filter(status=Order.STATUS_CHOICES[3][0], ordering_clinic=ClinicLocation.objects.get(
            name=request.session['clinicName'])).order_by('-priority')
        template = loader.get_template('browse_orders/index.html')
        context = {
            'order_list': orders,
        }
        return HttpResponse(template.render(context, request))

@csrf_exempt
def edit_profile(request):
    result = {
        'success': False,
        'reason': "",
        'pageLink': "",
    }
    if not request.user.is_authenticated:
        result['reason'] = "request not authenticated"
        print("not authenticated")
        return HttpResponse(json.dumps(result), content_type="application/json")
      
    if request.method == 'POST':
        password = request.POST['password']
        profile = Profile.objects.get(user=request.user)
        profile.update_details(request)
        if request.POST['changePassword'] == "true":
            if not request.user.check_password(password):
                result['reason'] = "Old Password does not match"
                print("Password does not match")
                return HttpResponse(json.dumps(result), content_type="application/json")
            else:
                profile.update_password(request)
        result['success'] = True
        result['pageLink'] = '/app/home'
        return HttpResponse(json.dumps(result), content_type="application/json")
    else:
        profile = Profile.objects.get(user=request.user)
        template = loader.get_template('profile/index.html')
        context = {
            'user': request.user,
            'profile': profile
        }
        return HttpResponse(template.render(context, request))

@csrf_exempt
def forgot_password(request):
    if request.method == 'POST':
        result = {
            'success': False,
            'reason': "",
            'pageLink': "",
        }
        if not User.objects.filter(username=request.POST['username']).exists():
            result['reason'] = "Username does not exist"
        else:
            user = User.objects.get(username=request.POST['username'])
            if user.email != request.POST['email']:
                result['reason'] = "Incorrect matching email"
            else:
                profile = Profile.objects.get(user=user)
                unique_token = str(uuid.uuid3(uuid.NAMESPACE_DNS, user.email))
                profile.update_forgot_password_token(unique_token)
                result['success'] = True
                result['pageLink'] = '/app'
        return HttpResponse(json.dumps(result), content_type="application/json")
    else:
        return render(request, 'forgot_password/index.html')

      
def browse_undelivered_orders(request):
    result = {
        'success': False,
        'reason': "",
    }
    if not request.user.is_authenticated:
        result['reason'] = "request not authenticated"
        print("not authenticated")
        return HttpResponse(json.dumps(result), content_type="application/json")
      
    if request.session['role'] != 'CLINIC_MANAGER':
        result['reason'] = "Only Clinic Manage can access"
        return HttpResponse(json.dumps(result), content_type="application/json")

    if request.method == 'POST':
        orderId = request.POST['orderId']
        Order.delete_order(orderId)
        result['success'] = True
        return HttpResponse(json.dumps(result), content_type="application/json")
    else:
        orders = Order.objects.filter(~Q(status=Order.STATUS_CHOICES[4][0]), ordering_clinic=ClinicLocation.objects.get(
            name=request.session['clinicName'])).order_by('-priority')
        template = loader.get_template('browse_undelivered_orders/index.html')
        context = {
            'order_list': orders,
        }
        return HttpResponse(template.render(context, request))
