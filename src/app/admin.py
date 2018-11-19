from django.contrib import admin
from .models import *

# Register your models here.
# For adding dummy record
admin.site.register(Category)
admin.site.register(Item)
admin.site.register(Profile)
admin.site.register(HospitalLocation)
admin.site.register(ClinicLocation)
admin.site.register(InterClinicDistance)
admin.site.register(Order)
admin.site.register(OrderedItem)
admin.site.register(InitialTokenRegistration)
admin.site.register(Shipment)

