import csv
import json
import io
from io import BytesIO
import uuid

from django.template import loader
from reportlab.pdfgen import canvas
from django.shortcuts import render, redirect
from django.http import HttpResponse
from django.contrib.auth import authenticate
from django.contrib.auth.models import User
from django.views.decorators.csrf import csrf_exempt

from .models import *


@csrf_exempt
def index(request):
    if request.method == 'POST':
        profile_data = {}
        username = request.POST['username']
        password = request.POST['password']
        user = authenticate(username=username, password=password)
        if user is not None:
            # Authenticated
            profile = Profile.objects.get(user=user)
            profile_data['role'] = profile.role
            profile_data['status'] = "Success"
            # Saving the appropriate session
            request.session['role'] = profile.role
            if (profile.role == "CLINIC_MANAGER"):
                request.session['clinicName'] = ClinicLocation.objects.get(id=profile.clinic_location.id).name
            return HttpResponse(json.dumps(profile_data), content_type="application/json")
        else:
            profile_data['status'] = "Fail"
            return HttpResponse(json.dumps(profile_data), content_type="application/json")
    else:
        return render(request, 'signin/index.html')


@csrf_exempt
def register_details(request):
    if request.method == 'POST':
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
        return HttpResponse("Success")
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
        email = request.POST['email']
        role = request.POST['role_choices']
        # See how to generate email to log file
        unique_token = str(uuid.uuid3(uuid.NAMESPACE_DNS, email))
        print("http://localhost:8000/app/registration?token=" + unique_token)
        register_token_instance = InitialTokenRegistration.create(unique_token, email, role)
        return render(request, 'register_send_token/index.html')
    else:
        return render(request, 'register_send_token/index.html')


def browse_items(request):
    # get all data of medicines
    if request.method == 'POST':
        orders = request.POST.getlist('order[]')
        totalWeight = request.POST['totalWeight']
        priority = request.POST['priority']
        # creating an order object
        order = Order.create_order(totalWeight, ClinicLocation.objects.get(name=request.session['clinicName']), HospitalLocation.objects.get(id=1),
                                   priority)

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

        #Creating CSV file and updating location
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
        return HttpResponse('test')
    else:
        # rendering all orders with status QUEUED_FOR_DISPATCH
        orders = Order.objects.filter(status=Order.STATUS_CHOICES[2][0]).order_by('-priority')
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
            p.drawString(100, height - 50, 'Order destination: ' + order.supplying_hospital.name)
            p.showPage()
            p.save()
            pdf = buffer.getvalue()
            buffer.close()
            response.write(pdf)
            return response
        return HttpResponse('test')

    else:
        processOrders = Order.objects.filter(status=Order.STATUS_CHOICES[0][0]).order_by('-priority')
        packOrders = Order.objects.filter(status=Order.STATUS_CHOICES[1][0]).order_by('-priority')
        context = {
            'process_order_list': processOrders,
            'pack_order_list': packOrders,
        }
        return render(request, 'browse_orders_warehouse/index.html', context)

@csrf_exempt
def browse_orders(request):
    if request.method == 'POST':
        orderId = request.POST['orderId']
        Order.confirm_order_delivery(orderId)
        return HttpResponse('test')
    else:
        orders = Order.objects.filter(status=Order.STATUS_CHOICES[3][0], ordering_clinic=ClinicLocation.objects.get(name = request.session['clinicName'])).order_by('-priority')
        template = loader.get_template('browse_orders/index.html')
        context = {
            'order_list': orders,
        }
        return HttpResponse(template.render(context, request))
