import csv
import io
from celery import shared_task
from .serializers import OrderSerializer
import time

@shared_task(bind=True)
def process_bulk_orders_csv(self, csv_data_string):
    csv_file = io.StringIO(csv_data_string)
    reader = list(csv.DictReader(csv_file))
    total_orders = len(reader)
    orders_created = 0
    errors = []

    for index, order_data in enumerate(reader):
        try:
            order_data['quantity'] = int(order_data['quantity'])
            order_data['customer'] = int(order_data['customer_id'])
        except (ValueError, KeyError) as e:
            errors.append({
                "row": index + 2,
                "error_details": f"Invalid or missing data for 'quantity' or 'customer_id': {str(e)}"
            })
            continue
        
        serializer = OrderSerializer(data=order_data)
        
        if serializer.is_valid():
            serializer.save()
            orders_created += 1
        else:
            errors.append({
                "row": index + 2,
                "error_details": serializer.errors
            })
      
        self.update_state(
            state='PROGRESS',
            meta={
                'current_progress': index + 1,
                'total_records': total_orders,
                'message': f'Processing record {index + 1} of {total_orders}'
            }
        )
        time.sleep(0.1)  

   
    return {
        'status': 'COMPLETED',
        'total_records': total_orders,
        'orders_successfully_created': orders_created,
        'records_with_errors': len(errors),
        'errors': errors  
    }

@shared_task(bind=True)
def process_bulk_orders_json(self, orders_data):
    total_orders = len(orders_data)
    orders_created = 0
    errors = []

    for index, order_data in enumerate(orders_data):
        serializer = OrderSerializer(data=order_data)
        
        if serializer.is_valid():
            serializer.save()
            orders_created += 1
        else:
            errors.append({
                "row": index + 1,
                "error_details": serializer.errors
            })
      
        self.update_state(
            state='PROGRESS',
            meta={'current_progress': index + 1, 'total_records': total_orders}
        )
        time.sleep(0.1)  
    return {
        'status': 'COMPLETED',
        'total_records': total_orders,
        'orders_successfully_created': orders_created,
        'records_with_errors': len(errors),
        'errors': errors  
    }
