from django.urls import path, include
from . import views

urlpatterns = [
    path('', views.show_text_file, name='optical_info'),
    path('download/', views.download_file, name='download_file'),
]
