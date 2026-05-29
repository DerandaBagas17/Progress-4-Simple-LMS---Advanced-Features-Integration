import os
import django

# Konfigurasi agar script ini bisa berjalan mandiri menggunakan environment Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'lms.settings')
django.setup()

from django.db import connection, reset_queries
from courses.models import Course, Category, User

def seed_data():
    """Fungsi ini akan membuat data awal (dummy) jika database masih kosong"""
    if Course.objects.exists():
        return # Jika sudah ada data course, lewati pembuatan data

    print("[*] Membuat data dummy untuk demonstrasi...")
    cat1 = Category.objects.create(name="Programming")
    cat2 = Category.objects.create(name="Design")
    
    inst1 = User.objects.create_user(username="inst_budi", password="123", role="instructor")
    inst2 = User.objects.create_user(username="inst_siti", password="123", role="instructor")
    
    # Membuat total 10 Course (5 untuk Budi, 5 untuk Siti)
    for i in range(5):
        Course.objects.create(title=f"Python Basic Part {i+1}", description="Belajar Python", category=cat1, instructor=inst1)
        Course.objects.create(title=f"UI/UX Design Part {i+1}", description="Belajar Figma", category=cat2, instructor=inst2)
    print("[*] Data dummy berhasil dibuat!\n")

def run_demo():
    # Pastikan ada data untuk dites
    seed_data()

    print("=== MENDEMONSTRASIKAN N+1 PROBLEM ===")
    reset_queries() # Bersihkan riwayat pencatatan query sebelumnya
    
    # 1. UNOPTIMIZED (Mengambil data biasa tanpa select_related)
    courses_unoptimized = Course.objects.all()
    for course in courses_unoptimized:
        # Mengakses relasi (category & instructor) di dalam loop
        # Ini akan memicu query baru ke database setiap kali dipanggil (Inilah N+1)
        text = f"{course.title} by {course.instructor.username} in {course.category.name}"
        
    unoptimized_count = len(connection.queries)
    print(f"Jumlah Query (Tanpa Optimasi) : {unoptimized_count} queries")
    
    
    print("\n=== MENDEMONSTRASIKAN OPTIMIZED QUERY ===")
    reset_queries()
    
    # 2. OPTIMIZED (Menggunakan custom manager for_listing() yang kita buat di models.py)
    courses_optimized = Course.objects.for_listing()
    for course in courses_optimized:
        # Mengakses relasi di sini TIDAK akan memicu query baru 
        # karena data sudah ditarik bersamaan di awal menggunakan select_related
        text = f"{course.title} by {course.instructor.username} in {course.category.name}"
        
    optimized_count = len(connection.queries)
    print(f"Jumlah Query (Dengan Optimasi): {optimized_count} queries")
    
    print("\n[KESIMPULAN] Custom Manager (select_related) berhasil memangkas query secara drastis!")

if __name__ == '__main__':
    from django.conf import settings
    # Pengecekan penting: Django hanya mencatat query history jika mode DEBUG = True
    if not settings.DEBUG:
        print("PENTING: Set DEBUG = True di settings.py agar Django menyimpan log query.")
    else:
        run_demo()