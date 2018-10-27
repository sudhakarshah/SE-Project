from django.db import models
import os
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
    role = models.CharField(max_length=2,choices=ROLE_CHOICES,default='CLINIC_MANAGER')

    def __str__(self):
        return self.name
