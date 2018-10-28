from django.db import models
import os
from datetime import datetime

# Create your models here.

def get_image_path(instance, filename):
    return os.path.join('photos', str(instance.id), filename)


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

class User(models.Model):
    name = models.CharField(max_length=200)
    last_name = models.CharField(max_length=200, blank=True)
    email = models.EmailField(max_length=254, unique=True)
    password = models.CharField(max_length=200)
    ROLE_CHOICES = (
        ('CLINIC_MANAGER', 'Clinic Manager'),
        ('WAREHOUSE_PERSONNEL', 'Warehouse Personnel'),
        ('DISPATCHER', 'Dispatcher'),
    )
    role = models.CharField(max_length=200,choices=ROLE_CHOICES,default='CLINIC_MANAGER')
    clinic_location = models.ForeignKey(ClinicLocation, on_delete=models.CASCADE, null=True)


    def __str__(self):
        return self.name


class Order(models.Model):
    total_weight = models.DecimalField(max_digits=5, decimal_places=2)
    STATUS_CHOICES = (
        ('QUEUED_FOR_PROCESSING', 'Queued for Processing'),
        ('PROCESSING_BY_WAREHOUSE', 'Processing by Warehouse'),
        ('QUEUED_FOR_DISPATCH', 'Queued for Dispatch'),
        ('DISPATCHED', 'Dispatched')
    )
    status = models.CharField(max_length=200,choices=STATUS_CHOICES,default='QUEUED_FOR_PROCESSING')
    date = models.DateTimeField(default=datetime.now, blank=True)
    ordering_clinic = models.ForeignKey(ClinicLocation, on_delete=models.CASCADE, null=True)
    supplying_hospital = models.ForeignKey(HospitalLocation, on_delete=models.CASCADE, null=True)
    items = models.ManyToManyField(Item, through='OrderedItem')

class OrderedItem(models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE, null=True)
    item = models.ForeignKey(Item, on_delete=models.CASCADE, null=True)
    quantity = models.IntegerField(default=0)
