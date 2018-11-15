from django.db import models
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
	latitute =  models.DecimalField(max_digits=9, decimal_places=6)
	longitute = models.DecimalField(max_digits=9, decimal_places=6)
	altitude = models.DecimalField(max_digits=9, decimal_places=6)

class ClinicLocation(models.Model):
	name = models.CharField(max_length=200)
	latitute =  models.DecimalField(max_digits=9, decimal_places=6)
	longitute = models.DecimalField(max_digits=9, decimal_places=6)
	altitude = models.DecimalField(max_digits=9, decimal_places=6)
	supplying_hospital = models.ForeignKey(HospitalLocation, on_delete=models.CASCADE, null=True)
	distance_from_supplying_hospital = models.DecimalField(max_digits=4, decimal_places=2)

class InterClinicDistance(models.Model):
	location_a = models.ForeignKey(ClinicLocation, on_delete=models.CASCADE, null=True, related_name='location_a')
	location_b = models.ForeignKey(ClinicLocation, on_delete=models.CASCADE, null=True, related_name='location_b')
	distance= models.DecimalField(max_digits=4, decimal_places=2)

	def get_distance(a,b):
		return 0

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
		initial_register.role = role
		initial_register.save()

class User(models.Model):
	first_name = models.CharField(max_length=32)
	last_name = models.CharField(max_length=32, blank=True)
	email = models.EmailField(max_length=254, unique=True)
	username =  models.CharField(max_length=32, blank=True, unique=True)
	password = models.CharField(max_length=32)
	ROLE_CHOICES = (
		('CLINIC_MANAGER', 'Clinic Manager'),
		('WAREHOUSE_PERSONNEL', 'Warehouse Personnel'),
		('DISPATCHER', 'Dispatcher'),
	)
	role = models.CharField(max_length=200,choices=ROLE_CHOICES,default='CLINIC_MANAGER')
	clinic_location = models.ForeignKey(ClinicLocation, on_delete=models.CASCADE, null=True)

	def create_user(firstName, lastName, email, role, clinicName,  username, password):
		user = User()
		user.first_name = firstName
		user.last_name = lastName
		user.role = role
		user.email = email
		user.password = password
		user.username = username
		# To save the foreign key
		clinicLocation = ClinicLocation.objects.get(name=clinicName)
		clinicLocation.save()

		user.clinic_location = clinicLocation
		user.save()

	def __str__(self):
		return self.username


class Order(models.Model):
	total_weight = models.DecimalField(max_digits=5, decimal_places=2)
	STATUS_CHOICES = (
		('QUEUED_FOR_PROCESSING', 'Queued for Processing'),
		('PROCESSING_BY_WAREHOUSE', 'Processing by Warehouse'),
		('QUEUED_FOR_DISPATCH', 'Queued for Dispatch'),
		('DISPATCHED', 'Dispatched')
	)
	PRIORITY_CHOICES = (
		('HIGH', 'High'),
		('MEDIUM', 'Medium'),
		('LOW', 'Low')
	)
	status = models.CharField(max_length=200,choices=STATUS_CHOICES,default='QUEUED_FOR_PROCESSING')
	ordering_clinic = models.ForeignKey(ClinicLocation, on_delete=models.CASCADE, null=True)
	supplying_hospital = models.ForeignKey(HospitalLocation, on_delete=models.CASCADE, null=True)
	priority = models.CharField(max_length=200,choices=PRIORITY_CHOICES,default='MEDIUM')
	date_order_placed = models.DateTimeField(default=timezone.now, blank=True)
	date_order_dispatched = models.DateTimeField(blank=True, null=True)
	date_order_delivered = models.DateTimeField(blank=True, null=True)
	items = models.ManyToManyField(Item, through='OrderedItem')

	def create_order(totalWeight, orderingClinic, supplyingHospital, priority='MEDIUM'):
		order = Order()
		order.total_weight = totalWeight
		order.ordering_clinic = orderingClinic
		order.supplying_hospital = supplyingHospital
		order.priority = priority
		order.save()
		return order

	def loaded_into_drone(id):
		order = Order.objects.get(id=id)
		order.status = Order.STATUS_CHOICES[3][0]
		order.date_order_dispatched = timezone.now()
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
