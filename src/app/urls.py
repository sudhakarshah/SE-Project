from django.urls import path
from . import views
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('items/', views.browse_items),
    path('OrdersToBeLoaded/', views.browse_to_be_loaded),
    path('registration/', views.register_details),
    path('OrdersToBeProcessed/', views.browse_to_be_processed),
	path('BrowseUndeliveredOrders/', views.browse_undelivered_orders),
	path('home/', views.home),
    path('forgotPassword/', views.forgot_password),
    path('enterNewPassword/', views.enter_new_password),
    path('Profile/', views.edit_profile),
    path('RegisterSendToken/', views.register_send_token),
	path('logout/', views.signout),
	path('', views.signin),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT+'/photos')
