from django.conf import settings
from datetime import datetime

class ActivityLogMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # Biarkan aplikasi memproses request terlebih dahulu
        response = self.get_response(request)
        
        # Siapkan data log aktivitas yang akan disimpan
        log_data = {
            "path": request.path,           # Rute yang diakses (misal: /api/courses/)
            "method": request.method,       # GET, POST, dll
            "ip_address": request.META.get("REMOTE_ADDR"),
            "status_code": response.status_code,
            "timestamp": datetime.utcnow()  # Waktu akses
        }
        
        # Simpan ke MongoDB secara langsung!
        settings.MONGO_DB['activity_logs'].insert_one(log_data)
        
        return response
