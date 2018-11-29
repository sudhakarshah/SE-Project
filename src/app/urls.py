from django.urls import path
from . import views
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('items/', views.browse_items),
    path('OrdersToBeLoaded/', views.browse_to_be_loaded),
    path('registration/', views.register_details),
    path('OrdersToBeProcessed/', views.browse_to_be_processed),
	path('ConfirmOrderDelivery/', views.browse_orders),
	path('BrowseUndeliveredOrders/', views.browse_undelivered_orders),
	path('home/', views.home),
    path('RegisterSendToken/', views.register_send_token),
	path('logout/', views.signout),
	path('', views.signin),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT+'/photos')
