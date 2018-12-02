from django.db import models
from django.contrib.auth.models import User
import os
from datetime import datetime

from django.utils import timezone
# Create your models here.

def get_image_path(instance, filename):
	return os.path.join("photos", "item", filename)


class Category(models.Model):
	name = models.CharField(max_length=30)


class Item(models.Model):
	name = models.CharField(max_length=30)
	category = models.ForeignKey(Category, on_delete=models.CASCADE, null=True)
	image = models.ImageField(upload_to=get_image_path, blank=True, null=True)
	weight = models.DecimalField(max_digits=5, decimal_places=2)


class HospitalLocation(models.Model):
	name = models.CharField(max_length=200)
	latitute = models.DecimalField(max_digits=9, decimal_places=6)
	longitute = models.DecimalField(max_digits=9, decimal_places=6)
	altitude = models.DecimalField(max_digits=9, decimal_places=6)

class ClinicLocation(models.Model):
	name = models.CharField(max_length=200)
	latitute = models.DecimalField(max_digits=9, decimal_places=6)
	longitute = models.DecimalField(max_digits=9, decimal_places=6)
	altitude = models.DecimalField(max_digits=9, decimal_places=6)
	supplying_hospital = models.ForeignKey(HospitalLocation, on_delete=models.CASCADE, null=True)
	distance_from_supplying_hospital = models.DecimalField(max_digits=4, decimal_places=2)


class InterClinicDistance(models.Model):
	location_a = models.ForeignKey(ClinicLocation, on_delete=models.CASCADE, null=True, related_name='location_a')
	location_b = models.ForeignKey(ClinicLocation, on_delete=models.CASCADE, null=True, related_name='location_b')
	distance= models.DecimalField(max_digits=4, decimal_places=2)

	def get_distance(a,b):
		clinic_a = ClinicLocation.objects.get(id=a)
		clinic_b = ClinicLocation.objects.get(id=b)
		obj = None
		try:
			obj = InterClinicDistance.objects.get(location_a=clinic_a, location_b=clinic_b)
		except InterClinicDistance.DoesNotExist:
			obj = InterClinicDistance.objects.get(location_a=clinic_b, location_b=clinic_a)
		return obj.distance

class InitialTokenRegistration(models.Model):
	unique_token = models.CharField(max_length=64, unique=True)
	email = models.EmailField(max_length=254, unique=True)
	ROLE_CHOICES = (
		('CLINIC_MANAGER', 'Clinic Manager'),
		('WAREHOUSE_PERSONNEL', 'Warehouse Personnel'),
		('DISPATCHER', 'Dispatcher'),
	)
	role = models.CharField(max_length=200, choices=ROLE_CHOICES, default='CLINIC_MANAGER')

	def create(unique_token, email, role):
		initial_register = InitialTokenRegistration()
		initial_register.unique_token = unique_token
		initial_register.email = email
		# To map the role choices
		for select_role in InitialTokenRegistration.ROLE_CHOICES:
			if select_role[1] == role:
				initial_register.role = select_role[0]
		initial_register.save()

class Profile(models.Model):
	user = models.ForeignKey(User, on_delete=models.CASCADE)
	first_name = models.CharField(max_length=32)
	last_name = models.CharField(max_length=32, blank=True)
	ROLE_CHOICES = (
		('CLINIC_MANAGER', 'Clinic Manager'),
		('WAREHOUSE_PERSONNEL', 'Warehouse Personnel'),
		('DISPATCHER', 'Dispatcher'),
	)
	role = models.CharField(max_length=200,choices=ROLE_CHOICES,default='CLINIC_MANAGER')
	clinic_location = models.ForeignKey(ClinicLocation, on_delete=models.CASCADE, null=True)
	forgot_password_token = models.CharField(max_length=64, unique=True, null=True)

	def create_profile(firstName, lastName, email, role, clinicName,  username, password):
		user_details = Profile()
		user_details.first_name = firstName
		user_details.last_name = lastName
		user_details.role = role
		create_user = User.objects.create_user(username, email, password)
		create_user.save()
		user_details.user = create_user

		# To save the foreign key
		if clinicName != None:
			clinicLocation = ClinicLocation.objects.get(name=clinicName)
			clinicLocation.save()
		else:
			clinicLocation = clinicName

		user_details.clinic_location = clinicLocation
		user_details.save()

	def update_details(self, request):
		user = request.user
		user.email = request.POST['email']
		user.save()
		self.first_name = request.POST['firstName']
		self.last_name = request.POST['lastName']
		self.save()

	def update_password(self, user, password):
		user.set_password(password)
		user.save()
		self.save()

	def update_forgot_password_token(self, token):
		self.forgot_password_token = token
		self.save()

	def __str__(self):
		return self.first_name

class Shipment(models.Model):
	date_order_dispatched = models.DateTimeField(blank=True, null=True)
	date_order_delivered = models.DateTimeField(blank=True, null=True)
	csv_file_location = models.CharField(max_length=200, null=True)

	def create_shipment(self):
		shipment = Shipment()
		shipment.date_order_dispatched = timezone.now()
		shipment.save()
		return shipment

	def update_file_location(self, file_location):
		self.csv_file_location = file_location
		self.save()

class Order(models.Model):
	total_weight = models.DecimalField(max_digits=5, decimal_places=2)
	STATUS_CHOICES = (
		('QUEUED_FOR_PROCESSING', 'Queued for Processing'),
		('PROCESSING_BY_WAREHOUSE', 'Processing by Warehouse'),
		('QUEUED_FOR_DISPATCH', 'Queued for Dispatch'),
		('DISPATCHED', 'Dispatched'),
		('DELIVERED', 'Delivered')
	)
	HIGH_STATUS = '3'
	MEDIUM_STATUS = '2'
	LOW_STATUS = '1'
	PRIORITY_CHOICES = (
		(HIGH_STATUS , 'HIGH'),
		(MEDIUM_STATUS, 'MEDIUM'),
		(LOW_STATUS, 'LOW')
	)
	status = models.CharField(max_length=200,choices=STATUS_CHOICES,default='QUEUED_FOR_PROCESSING')
	ordering_clinic = models.ForeignKey(ClinicLocation, on_delete=models.CASCADE, null=True)
	supplying_hospital = models.ForeignKey(HospitalLocation, on_delete=models.CASCADE, null=True)
	priority = models.CharField(max_length=200, choices=PRIORITY_CHOICES,default=MEDIUM_STATUS)
	date_order_placed = models.DateTimeField(default=timezone.now, blank=True)
	date_order_dispatched = models.DateTimeField(blank=True, null=True)
	date_order_delivered = models.DateTimeField(blank=True, null=True)
	items = models.ManyToManyField(Item, through='OrderedItem')
	shipping_label_location = models.CharField(max_length=200, null=True)
	shipment = models.ForeignKey(Shipment, on_delete=models.CASCADE, null=True)

	def create_order(totalWeight, orderingClinic, supplyingHospital, priority):
		order = Order()
		order.total_weight = totalWeight
		order.ordering_clinic = orderingClinic
		order.supplying_hospital = supplyingHospital
		order.priority = priority
		order.save()
		return order

	def delete_order(id):
		order = Order.objects.get(id=id)
		order.delete()

	def ready_to_process(id):
		order = Order.objects.get(id=id)
		order.status = Order.STATUS_CHOICES[1][0]
		order.save()

	def complete_processing(id):
		order = Order.objects.get(id=id)
		order.status = Order.STATUS_CHOICES[2][0]
		order.save()

	def loaded_into_drone(id, shipment):
		order = Order.objects.get(id=id)
		order.status = Order.STATUS_CHOICES[3][0]
		order.date_order_dispatched = timezone.now()
		order.shipment = shipment
		order.save()

	def confirm_order_delivery(id):
		order = Order.objects.get(id=id)
		order.status = Order.STATUS_CHOICES[4][0]
		order.date_order_delivered = timezone.now()
		order.save()

	def update_shipping_label(id, location):
		order = Order.objects.get(id=id)
		order.shipping_label_location = location
		order.save()


class OrderedItem(models.Model):
	order = models.ForeignKey(Order, on_delete=models.CASCADE, null=True)
	item = models.ForeignKey(Item, on_delete=models.CASCADE, null=True)
	quantity = models.IntegerField(default=0)

	def create_orderedItem(orderId, itemId, quantity):
		orderedItem = OrderedItem()
		orderedItem.order = Order.objects.get(id=orderId)
		orderedItem.item = Item.objects.get(id=itemId)
		orderedItem.quantity = quantity
		orderedItem.save()
		return orderedItem
