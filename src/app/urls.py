from django.urls import path
from . import views
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    # path('admin/', admin.site.urls),
    path('items', views.browse_items),
    path('OrdersToBeLoaded/', views.browse_to_be_loaded),
	path('OrdersToBeProcessed/', views.browse_to_be_processed),
    path('', views.index),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT+'/photos')
