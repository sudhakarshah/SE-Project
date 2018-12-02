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
from itertools import permutations
from django.db.models import Q

from .models import *


def isAuthenticated(request):
	return request.user.is_authenticated and 'role' in request.session

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
			login(request, user)
			# Authenticated
			profile = Profile.objects.get(user=user)
			result['pageLink'] = '/app/home'
			# Saving the appropriate session
			request.session['role'] = profile.role
			if (profile.role == "CLINIC_MANAGER"):
				request.session['clinicName'] = ClinicLocation.objects.get(id=profile.clinic_location.id).name
			result['success'] = True
			return HttpResponse(json.dumps(result), content_type="application/json")
		else:
			return HttpResponse(json.dumps(result), content_type="application/json")
	else:
		if isAuthenticated(request):
			return redirect('/app/home')
		return render(request, 'signin/index.html')


@csrf_exempt
def signout(request):
	logout(request)
	return redirect('/app')


@csrf_exempt
def home(request):
	if not isAuthenticated(request):
		return redirect('/app')

	if request.session['role'] == 'CLINIC_MANAGER':
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

	elif request.session['role'] == 'DISPATCHER':
		orders = Order.objects.filter(status=Order.STATUS_CHOICES[2][0]).order_by('-priority')
		context = {
			'order_list': orders,
		}
		return render(request, 'browse_to_be_loaded/index.html', context)


@csrf_exempt
def register_details(request):
	result = {
		'success': False,
		'reason': '',
	}
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
		result['pageLink'] = '/app'
		result['success'] = True
		return HttpResponse(json.dumps(result), content_type="application/json")
	else:
		token_id = request.GET['token']
		initial_registration_data = None
		try:
			initial_registration_data = InitialTokenRegistration.objects.get(unique_token=token_id)
		except InitialTokenRegistration.DoesNotExist:
			result['reason'] = 'incorrect token'
			return HttpResponse(json.dumps(result), content_type="application/json")

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
	if request.method != 'POST':
		return render(request, 'register_send_token/index.html')

	result = {
		'success': False,
		'reason': '',
	}
	email = request.POST['email']
	role = request.POST['role_choices']
	unique_token = str(uuid.uuid3(uuid.NAMESPACE_DNS, email))
	print("http://localhost:8000/app/registration?token=" + unique_token + " send to " + email)
	register_token_instance = InitialTokenRegistration.create(unique_token, email, role)
	# send email and check if create in db is successful. If not then make result['success'] = false
	if True:
		result['success'] = True
	else:
		result['reason'] = 'reason'
	return HttpResponse(json.dumps(result), content_type="application/json")



def browse_items(request):
	result = {
		'success': False,
		'reason': "",
	}
	if not isAuthenticated(request):
		return redirect('/app')

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


# Going through all permutations and finding the shortest one
def find_shortest_path(list_of_clinics):
	all_permutations = list(permutations(list_of_clinics))
	smallest_route = all_permutations[0]
	minimum = 10000000;
	for permutation in all_permutations:
		temp = ClinicLocation.objects.get(id=permutation[0]).distance_from_supplying_hospital
		for i in range(0, len(permutation) - 1):
			temp = temp + InterClinicDistance.get_distance(permutation[i], permutation[i + 1])
		temp = temp + ClinicLocation.objects.get(id=permutation[-1]).distance_from_supplying_hospital
		# THIS HAS TO BE IMPLEMENTED
		# To decide among itineraries of equal distance, AS-P should select the itinerary that delivers
		# the highest priority orders earliest in the route. If there are still equally suitable candidates,
		# then any one of them can be chosen.
		if (temp < minimum):
			minimum = temp
			smallest_route = permutation

	return smallest_route


def browse_to_be_loaded(request):
	result = {
		'success': False,
		'reason': "",
	}
	if not isAuthenticated(request):
		return redirect('/app')

	if request.method != 'POST':
		result['reason'] = "Invalid request"
		return HttpResponse(json.dumps(result), content_type="application/json")

	# updating order status to dispatched
	if request.POST['event'] == 'LOAD_INTO_DRONE':
		order_ids = request.POST.getlist('orderIds[]')
		shipment = Shipment.create_shipment(Shipment)
		lines_to_be_printed_in_csv = []
		clinics = []

		# Updating all the orders in the shipment
		for order_id in order_ids:
			current_order = Order.objects.get(id=order_id)
			if current_order.ordering_clinic.id not in clinics:
				clinics.append(current_order.ordering_clinic.id)
			Order.loaded_into_drone(order_id, shipment)
			print(Profile.objects.get(clinic_location=current_order.ordering_clinic).user.email, "order id ", order_id , " is dispatched")
			print(current_order.shipping_label_location, "is the shipping label pdf name")
		smallest_route = find_shortest_path(clinics)

		path = []
		path.append(['Location', 'Latitude', 'Longitude', 'Altitude'])
		for clinic_id in smallest_route:
			ordering_clinic = ClinicLocation.objects.get(id=clinic_id)
			node = [ordering_clinic.name, ordering_clinic.latitute, ordering_clinic.longitute, ordering_clinic.altitude]
			path.append(node)

		# Adding the hospital as the last stop
		supplying_hospital = ClinicLocation.objects.get(id=smallest_route[0]).supplying_hospital
		supply_node = [supplying_hospital.name, supplying_hospital.latitute, supplying_hospital.longitute,
					   supplying_hospital.altitude]
		path.append(supply_node)

		# Creating CSV file and updating location
		csv_file_name = 'shipment' + str(shipment.id) + '.csv'
		shipment.update_file_location(csv_file_name)

		# Writing to the CSV file
		with open(csv_file_name, 'w') as writeFile:
			writer = csv.writer(writeFile)
			writer.writerows(path)
		writeFile.close()

		with open(csv_file_name) as csvfile:
			reader = csv.reader(csvfile)
			data = [r for r in reader]
		total_data = []
		for row in data:
			total_data.append(row)
		result['totalData'] = total_data
		result['success'] = True
		return HttpResponse(json.dumps(result), content_type="application/json")


def browse_to_be_processed(request):
	result = {
		'success': False,
		'reason': "",
	}
	if not isAuthenticated(request):
		return redirect('/app')

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
        # saving pdf in db
		file_name = "label" + str(orderId) + ".pdf"
		Order.update_shipping_label(orderId, file_name)
		with open(file_name, 'wb') as writeFile:
			writeFile.write(pdf)
		writeFile.close()
		response.write(pdf)
		return response
	else:
		result['reason'] = 'Incorrect Event Name'

	return HttpResponse(json.dumps(result), content_type="application/json")


@csrf_exempt
def edit_profile(request):
	result = {
		'success': False,
		'reason': "",
		'pageLink': "",
	}
	if not isAuthenticated(request):
		return redirect('/app')

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
				profile.update_password(request.user, request.POST['newPassword'])
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
	if request.method != 'POST':
		return render(request, 'forgot_password/index.html')

	result = {
		'success': False,
		'reason': "",
		'pageLink': "",
	}
	if not User.objects.filter(username=request.POST['username']).exists():
		result['reason'] = "Username does not exist"
	else:
		user = User.objects.get(username=request.POST['username'])
		profile = Profile.objects.get(user=user)
		unique_token = str(uuid.uuid3(uuid.NAMESPACE_DNS, user.email))
		profile.update_forgot_password_token(unique_token)
		print("http://localhost:8000/app/enterNewPassword?token=" + unique_token + " send to " + profile.user.email)
		result['success'] = True
		result['pageLink'] = '/app'
	return HttpResponse(json.dumps(result), content_type="application/json")



@csrf_exempt
def enter_new_password(request):
	result = {
		'success': False,
		'reason': "",
		'pageLink': "/app",
	}
	if request.method != 'POST':
		return render(request, 'enter_new_password/index.html')

	token_id = request.POST['token']
	if not Profile.objects.filter(forgot_password_token=token_id).exists():
		result['reason'] = "Token Does not exist"
	else:
		profile = Profile.objects.get(forgot_password_token=token_id)
		profile.update_password(profile.user, request.POST['password'])
		profile.update_forgot_password_token(None)
		result['success'] = True
	return HttpResponse(json.dumps(result), content_type="application/json")


@csrf_exempt
def browse_undelivered_orders(request):
	result = {
		'success': False,
		'reason': "",
	}
	if not isAuthenticated(request):
		result['reason'] = "request not authenticated"
		print("not authenticated")
		return redirect('/app')

	if request.session['role'] != 'CLINIC_MANAGER':
		result['reason'] = "Only Clinic Manage can access"
		return HttpResponse(json.dumps(result), content_type="application/json")

	if request.method == 'POST':
		orderId = request.POST['orderId']
		if request.POST['task'] == "Cancel":
			Order.delete_order(orderId)
			result['success'] = True
		elif request.POST['task'] == "Confirm":
			Order.confirm_order_delivery(orderId)
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
