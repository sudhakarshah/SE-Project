from django.urls import path

from . import views

urlpatterns = [
    # path('admin/', admin.site.urls),
    path('browse/items', views.browse_items),
    path('browse/OrdersToBeLoaded/', views.browse_to_be_loaded),
    path('', views.index),
]
