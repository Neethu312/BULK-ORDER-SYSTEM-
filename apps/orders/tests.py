from django.test import TestCase
from django.urls import reverse
from django.contrib.auth.models import User
from django.core.files.uploadedfile import SimpleUploadedFile
from rest_framework.test import APITestCase
from rest_framework import status
from unittest.mock import patch

from .models import TaskTracker

class SimpleBulkOrderTests(APITestCase):

    def setUp(self):
        
        self.user = User.objects.create_user(username='testuser', password='password123')
        self.client.force_authenticate(user=self.user)

    @patch("orders.views.start_task") 
    def test_csv_upload_is_accepted(self, mock_start_task):
       
        
        csv_content = b"product_name,quantity,customer_id\nTest Product,5,1"
        mock_file = SimpleUploadedFile("orders.csv", csv_content, content_type="text/csv")

       
        url = reverse("bulk-upload")
        response = self.client.post(url, {"file": mock_file}, format='multipart')

        
        self.assertEqual(response.status_code, status.HTTP_202_ACCEPTED)
     
        mock_start_task.assert_called_once()

    @patch("orders.views.start_task")  
    def test_json_upload_is_accepted(self, mock_start_task):
        
       
        json_payload = [{"product_name": "JSON Product", "quantity": 10, "customer": 1}]

       
        url = reverse("bulk-upload")
        response = self.client.post(url, json_payload, format='json')

      
        self.assertEqual(response.status_code, status.HTTP_202_ACCEPTED)
        
        mock_start_task.assert_called_once()

    @patch("orders.views.celery_app.AsyncResult")
    def test_task_status_can_be_retrieved(self, mock_async_result):
        
        task_id = "fake-task-id-123"
        TaskTracker.objects.create(user=self.user, task_id=task_id)

      
        mock_instance = mock_async_result.return_value
        mock_instance.status = "SUCCESS"
        mock_instance.result = "The task completed without errors."

        
        url = reverse("task-status", kwargs={"task_id": task_id})
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        self.assertEqual(response.data['data']['task_status'], "SUCCESS")
