from .models import TaskTracker
from .task import process_bulk_orders_csv, process_bulk_orders_json


# def start_task(request, orders_data):
           
#             task_result = process_bulk_orders.delay(orders_data)
            
            
#             TaskTracker.objects.create(
#                 user=request.user,
#                 task_id=task_result.id
#             )
#             return task_result.id


def start_task(request, data_to_process, task_function):
    task_result = task_function.delay(data_to_process)
    TaskTracker.objects.create(
        user=request.user,
        task_id=task_result.id
    )
    return task_result.id