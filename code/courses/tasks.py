import time
from celery import shared_task

@shared_task
def send_enrollment_email(user_email, course_title):
    # Simulasi proses kirim email (butuh waktu 3 detik)
    time.sleep(3)
    return f"Email sent successfully to {user_email} for course '{course_title}'"

@shared_task
def generate_certificate(user_id, course_id):
    # Simulasi proses membuat PDF sertifikat (butuh waktu 5 detik)
    time.sleep(5)
    return f"Certificate generated for user {user_id}, course {course_id}"

@shared_task
def update_course_statistics():
    # Simulasi perhitungan statistik (Task periodik)
    return "Course statistics updated successfully"

@shared_task
def export_course_report():
    # Simulasi proses export CSV yang berat (butuh waktu 10 detik)
    time.sleep(10)
    return "CSV report exported successfully"
