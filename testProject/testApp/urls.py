from django.urls import path
from . import views

urlpatterns = [
    path('', views.loadMainPage, name="main_page"),
    path('submit-vocab/', views.submit_vocab, name='submit_vocab'),  # handles AJAX POST
    path('success/', views.success_page, name='success_page'),
]