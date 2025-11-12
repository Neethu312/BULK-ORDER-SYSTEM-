from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.parsers import MultiPartParser, FormParser, JSONParser
from rest_framework.authtoken.models import Token

from django.http import Http404
from django.contrib.auth.models import User
from bulkorder.celery import app as celery_app
from django.db import transaction
from django.contrib.auth import authenticate
from rest_framework.permissions import IsAuthenticated

from .models import Customer, Order, TaskTracker
from .serializers import UserSerializer, CustomerSerializer, OrderSerializer,UserCreateSerializer,TaskTrackerSerializer

from .function import start_task
from rest_framework.parsers import MultiPartParser, FormParser, JSONParser
from .task import process_bulk_orders_csv, process_bulk_orders_json
import logging



class UserList(APIView):
  
    def get(self, request):
        users = User.objects.all()
        serializer = UserSerializer(users, many=True) 
        response = {
            "success": True,
            "status_code": status.HTTP_200_OK,
            "message": "Users retrieved successfully.",
            "data": serializer.data,
            "errors": None
        }
        return Response(response, status=status.HTTP_200_OK)

    def post(self, request, format=None):
       
        serializer = UserCreateSerializer(data=request.data)
        if serializer.is_valid():
            
            user = serializer.save()
            response_data = UserSerializer(user).data
            response = {
                "success": True,
                "status_code": status.HTTP_201_CREATED,
                "message": "User created successfully.",
                "data": response_data,
                "errors": None
            }
            return Response(response, status=status.HTTP_201_CREATED)
        
        
        error_response = {
            "success": False,
            "status_code": status.HTTP_400_BAD_REQUEST,
            "message": "Failed to create user due to validation errors.",
            "data": None,
            "errors": serializer.errors
        }
        return Response(error_response, status=status.HTTP_400_BAD_REQUEST)
    

class LoginView(APIView):
    
    def post(self, request, *args, **kwargs):
        username = request.data.get('username')
        password = request.data.get('password')

        user = authenticate(username=username, password=password)
        if user is not None:
            
            token, created = Token.objects.get_or_create(user=user)
            user_data = UserSerializer(user).data

            response = {
                "success": True,
                "status_code": status.HTTP_200_OK,
                "message": "Login successful.",
                "data": {
                    "token": token.key,
                    "user": user_data
                },
                "errors": None
            }
            return Response(response, status=status.HTTP_200_OK)
        else:
        
            error_response = {
                "success": False,
                "status_code": status.HTTP_401_UNAUTHORIZED,
                "message": "Invalid credentials provided.",
                "data": None,
                "errors": {"detail": "Unable to log in with provided credentials."}
            }
            return Response(error_response, status=status.HTTP_401_UNAUTHORIZED)


class CustomerList(APIView):
    def get(self, request, format=None):
        customers = Customer.objects.all()
        serializer = CustomerSerializer(customers, many=True)
        response = {
            "success": True,
            "status_code": status.HTTP_200_OK,
            "message": "Customers retrieved successfully.",
            "data": serializer.data,
            "errors": None
        }
        return Response(response, status=status.HTTP_200_OK)

    def post(self, request, format=None):
        serializer = CustomerSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            response = {
                "success": True,
                "status_code": status.HTTP_201_CREATED,
                "message": "Customer created successfully.",
                "data": serializer.data,
                "errors": None
            }
            return Response(response, status=status.HTTP_201_CREATED)
        
        response = {
            "success": False,
            "status_code": status.HTTP_400_BAD_REQUEST,
            "message": "Failed to create customer.",
            "data": None,
            "errors": serializer.errors
        }
        return Response(response, status=status.HTTP_400_BAD_REQUEST)


class CustomerDetail(APIView):
    
    def get_object(self, pk):
        try:
            return Customer.objects.get(pk=pk)
        except Customer.DoesNotExist:
            raise Http404

    def get(self, request, pk, format=None):
        try:
            customer = self.get_object(pk)
            serializer = CustomerSerializer(customer)
            response = {
                "success": True,
                "status_code": status.HTTP_200_OK,
                "message": "Customer retrieved successfully.",
                "data": serializer.data,
                "errors": None
            }
            return Response(response, status=status.HTTP_200_OK)
        except Http404:
            response = {
                "success": False,
                "status_code": status.HTTP_404_NOT_FOUND,
                "message": "Customer not found.",
                "data": None,
                "errors": {"detail": f"Customer with id '{pk}' does not exist."}
            }
            return Response(response, status=status.HTTP_404_NOT_FOUND)

    def put(self, request, pk, format=None):
        try:
            customer = self.get_object(pk)
            serializer = CustomerSerializer(customer, data=request.data)
            if serializer.is_valid():
                serializer.save()
                response = {
                    "success": True,
                    "status_code": status.HTTP_200_OK,
                    "message": "Customer updated successfully.",
                    "data": serializer.data,
                    "errors": None
                }
                return Response(response, status=status.HTTP_200_OK)
            
            error_response = {
                "success": False,
                "status_code": status.HTTP_400_BAD_REQUEST,
                "message": "Failed to update customer.",
                "data": None,
                "errors": serializer.errors
            }
            return Response(error_response, status=status.HTTP_400_BAD_REQUEST)
        except Http404:
            response = {
                "success": False,
                "status_code": status.HTTP_404_NOT_FOUND,
                "message": "Customer not found.",
                "data": None,
                "errors": {"detail": f"Customer with id '{pk}' does not exist."}
            }
            return Response(response, status=status.HTTP_404_NOT_FOUND)

    def delete(self, request, pk, format=None):
        try:
            customer = self.get_object(pk)
            customer.delete()
            response = {
                "success": True,
                "status_code": status.HTTP_200_OK, # Using 200 instead of 204 to allow a response body
                "message": "Customer deleted successfully.",
                "data": None,
                "errors": None
            }
            return Response(response, status=status.HTTP_200_OK)
        except Http404:
            response = {
                "success": False,
                "status_code": status.HTTP_404_NOT_FOUND,
                "message": "Customer not found.",
                "data": None,
                "errors": {"detail": f"Customer with id '{pk}' does not exist."}
            }
            return Response(response, status=status.HTTP_404_NOT_FOUND)


class OrderList(APIView):
  
    def get(self, request, format=None):
        orders = Order.objects.all()
        serializer = OrderSerializer(orders, many=True)
        return Response(serializer.data)

    def post(self, request, format=None):
        serializer = OrderSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class OrderDetail(APIView):
   
    def get_object(self, pk):
        try:
            return Order.objects.get(pk=pk)
        except Order.DoesNotExist:
            raise Http404

    def get(self, request, pk, format=None):
        order = self.get_object(pk)
        serializer = OrderSerializer(order)
        return Response(serializer.data)

    def put(self, request, pk, format=None):
        order = self.get_object(pk)
        serializer = OrderSerializer(order, data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, pk, format=None):
        order = self.get_object(pk)
        order.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)



logger = logging.getLogger(__name__)

# class OrderBulkUploadView(APIView):
#     parser_classes = (JSONParser, MultiPartParser, FormParser)
#     permission_classes = [IsAuthenticated]

#     def post(self, request, *args, **kwargs):
        
#         if 'file' in request.FILES:
#             csv_file = request.FILES['file']
            
#             try:
#                 csv_content_string = csv_file.read().decode('utf-8')
#             except UnicodeDecodeError:
#                 return Response({
#                     "success": False, 
#                     "status_code": status.HTTP_400_BAD_REQUEST,
#                     "message": "Invalid file encoding. Please use UTF-8.",
#                     "data": None, "errors": {"detail": "File encoding is not valid."}
#                 }, status=status.HTTP_400_BAD_REQUEST)

#             # transaction.on_commit(lambda: start_task(request, csv_content_string, process_bulk_orders_csv))
#             task_id = start_task(request, csv_content_string, process_bulk_orders_csv)

#         else:
#             orders_data = request.data
#             if not isinstance(orders_data, list):
#                 return Response({
#                     "success": False, 
#                     "status_code": status.HTTP_400_BAD_REQUEST,
#                     "message": "Invalid data format. A list of objects is expected.",
#                     "data": None, "errors": {"detail": "The provided JSON body is not a list."}
#                 }, status=status.HTTP_400_BAD_REQUEST)
            
#             # transaction.on_commit(lambda: start_task(request, orders_data, process_bulk_orders_json))
#             task_id = start_task(request, orders_data, process_bulk_orders_json)

#         return Response({
#             "success": True,
#             "status_code": status.HTTP_202_ACCEPTED,
#             "message": "Your bulk order request has been accepted and is being processed.",
#             "data": task_id,
#             "errors": None
#         }, status=status.HTTP_202_ACCEPTED)



class OrderBulkUploadView(APIView):
    
    parser_classes = (JSONParser, MultiPartParser, FormParser)
    permission_classes = [IsAuthenticated]

    def post(self, request, *args, **kwargs):
        try:
            
            if 'file' in request.FILES:
                csv_file = request.FILES['file']
                try:
                    csv_content_string = csv_file.read().decode('utf-8')
                except:
                    logger.warning(f"Invalid file encoding uploaded by {request.user}")
                    return Response({
                        "success": False,
                        "status_code": status.HTTP_400_BAD_REQUEST,
                        "message": "Invalid file encoding. Please use UTF-8.",
                        "data": None,
                        "errors": {"detail": "File encoding is not valid."}
                    }, status=status.HTTP_400_BAD_REQUEST)

                logger.info(f"User {request.user} uploaded CSV for bulk processing")
                task_id = start_task(request, csv_content_string, process_bulk_orders_csv)

            
            else:
                orders_data = request.data
                if not isinstance(orders_data, list):
                    logger.warning(f"Invalid JSON structure uploaded by {request.user}")
                    return Response({
                        "success": False,
                        "status_code": status.HTTP_400_BAD_REQUEST,
                        "message": "Invalid data format. A list of objects is expected.",
                        "data": None,
                        "errors": {"detail": "The provided JSON body is not a list."}
                    }, status=status.HTTP_400_BAD_REQUEST)

                logger.info(f"User {request.user} uploaded JSON for bulk processing")
                task_id = start_task(request, orders_data, process_bulk_orders_json)

            
            logger.info(f"Bulk task {task_id} created successfully by {request.user}")

            return Response({
                "success": True,
                "status_code": status.HTTP_202_ACCEPTED,
                "message": "Your bulk order request has been accepted and is being processed.",
                "data": {"task_id": task_id},
                "errors": None
            }, status=status.HTTP_202_ACCEPTED)

        except Exception as e:
            logger.exception(f"Bulk upload failed for user {request.user}: {e}")
            return Response({
                "success": False,
                "status_code": status.HTTP_500_INTERNAL_SERVER_ERROR,
                "message": "Error starting bulk upload.",
                "data": None,
                "errors": {"detail": str(e)}
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

class TaskListView(APIView):
    

    def get(self, request, *args, **kwargs):
        tasks = TaskTracker.objects.filter(user=request.user).order_by('-created_at')
        serializer = TaskTrackerSerializer(tasks, many=True)
        response = {
            "success": True, 
            "status_code": status.HTTP_200_OK,
            "message": "Tasks retrieved successfully.",
            "data": serializer.data,
            "errors": None
        }
        return Response(response)


# class TaskStatusView(APIView): 
    
#     def get(self, request, task_id, *args, **kwargs):
       
#         try:
#             TaskTracker.objects.get(user=request.user, task_id=task_id)
#         except TaskTracker.DoesNotExist:
           
#             response = {
#                 "success": False,
#                 "status_code": status.HTTP_404_NOT_FOUND,
#                 "message": "Task not found or permission denied.",
#                 "data": None,
#                 "errors": {"detail": "A task with this ID was not found for the current user."}
#             }
#             return Response(response, status=status.HTTP_404_NOT_FOUND)

        
#         task_result = celery_app.AsyncResult(task_id)
#         data = {
#             "task_id": task_id,
#             "task_status": task_result.status,
#             "task_result": task_result.result
#         }

#         response = {
#             "success": True,
#             "status_code": status.HTTP_200_OK,
#             "message": "Task status retrieved successfully.",
#             "data": data,
#             "errors": None
#         }
#         return Response(response, status=status.HTTP_200_OK)

class TaskStatusView(APIView):
    
    def get(self, request, task_id, *args, **kwargs):
        try:
            
            TaskTracker.objects.get(user=request.user, task_id=task_id)
        except TaskTracker.DoesNotExist:
            logger.warning(f"User {request.user} tried to access unauthorized or missing task {task_id}")
            response = {
                "success": False,
                "status_code": status.HTTP_404_NOT_FOUND,
                "message": "Task not found or permission denied.",
                "data": None,
                "errors": {"detail": "A task with this ID was not found for the current user."}
            }
            return Response(response, status=status.HTTP_404_NOT_FOUND)

        try:
          
            task_result = celery_app.AsyncResult(task_id)
            info = task_result.info or {}
            current = info.get("current_progress", 0)
            total = info.get("total_records", 0)
            percentage = round((current / total) * 100, 2) if total else 0

            data = {
                "task_id": task_id,
                "task_status": task_result.status,
                "current_progress": current,
                "total_records": total,
                "percentage_complete": percentage,
                "task_result": task_result.result if task_result.ready() else None
            }

            response = {
                "success": True,
                "status_code": status.HTTP_200_OK,
                "message": "Task status retrieved successfully.",
                "data": data,
                "errors": None
            }

            logger.info(f"User {request.user} checked status for task {task_id}: {task_result.status}")
            return Response(response, status=status.HTTP_200_OK)

        except Exception as e:
            logger.exception(f"Error fetching task status for user {request.user}, task {task_id}: {e}")
            return Response({
                "success": False,
                "status_code": status.HTTP_500_INTERNAL_SERVER_ERROR,
                "message": "Error retrieving task status.",
                "data": None,
                "errors": {"detail": str(e)}
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
 
