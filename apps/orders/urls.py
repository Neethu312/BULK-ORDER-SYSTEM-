from django.urls import path
from . import views


# app_name = 'orders'

urlpatterns = [
   
    path('users/', views.UserList.as_view(), name='user-list'),
    path('login/', views.LoginView.as_view()),

   
    path('customers/', views.CustomerList.as_view()),
    path('customers/<int:pk>/', views.CustomerDetail.as_view()),

    # Order Management
    path('orders/', views.OrderList.as_view()),
    path('orders/<int:pk>/', views.OrderDetail.as_view()),
    path('orders/bulk-upload/', views.OrderBulkUploadView.as_view(), name='bulk-upload'),
    
    path('tasks/', views.TaskListView.as_view()),
    path('tasks/<str:task_id>/', views.TaskStatusView.as_view(),name='task-status'),
]

