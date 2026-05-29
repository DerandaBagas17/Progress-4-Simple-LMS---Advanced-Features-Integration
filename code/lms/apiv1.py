from django.core.cache import cache
from ninja import NinjaAPI
from django.shortcuts import get_object_or_404
from courses.models import Course, Category, User
from courses.schemas import CourseSchema, CourseIn, Register, UserOut
from ninja.errors import HttpError
from ninja_simple_jwt.auth.views.api import mobile_auth_router
from ninja_simple_jwt.auth.ninja_auth import HttpJwtAuth
from django.conf import settings
from courses.tasks import export_course_report
from courses.tasks import send_enrollment_email
from courses.tasks import generate_certificate
apiv1 = NinjaAPI(
    title="Simple LMS API",
    version="1.0.0",
    description="API untuk Simple Learning Management System. "
                "Dokumentasi ini di-generate otomatis oleh Django Ninja.",
    docs_url="/docs/",          # Default: /docs
    openapi_url="/openapi.json" # Default: /openapi.json
)

@apiv1.post('register/', response=UserOut)
def register(request, data: Register):
    # Cek apakah username sudah digunakan
    if User.objects.filter(username=data.username).exists():
        raise HttpError(400, "Username sudah digunakan")
        
    # Cek apakah email sudah digunakan
    if User.objects.filter(email=data.email).exists():
        raise HttpError(400, "Email sudah digunakan")
        
    # Buat user baru 
    # create_user() otomatis melakukan hashing pada password
    newUser = User.objects.create_user(
        username=data.username,
        password=data.password,
        email=data.email,
        first_name=data.first_name,
        last_name=data.last_name
    )
    
    return newUser

apiv1.add_router("/auth/", mobile_auth_router)
apiAuth = HttpJwtAuth()

def rate_limit_check(request):
    ip = request.META.get('REMOTE_ADDR')
    cache_key = f"rate_limit_{ip}"
    requests_count = cache.get(cache_key, 0)
    
    if requests_count >= 60:
        raise HttpError(429, "Too Many Requests (Limit 60 per menit)")
        
    cache.set(cache_key, requests_count + 1, 60)

# --- ENDPOINT BARU ---
# --- 3. Update list_courses dan get_course ---
@apiv1.get('courses/', response=list[CourseSchema])
def list_courses(request):
    rate_limit_check(request) # Terapkan rate limiting
    
    # Cek apakah data ada di cache Redis
    courses = cache.get("course_list_cache")
    if not courses:
        # Jika belum ada di cache, ambil dari Database
        courses = list(Course.objects.for_listing())
        # Simpan ke Redis selama 15 menit (900 detik)
        cache.set("course_list_cache", courses, 900)
    return courses
@apiv1.get('courses/{course_id}', response=CourseSchema)
def get_course(request, course_id: int):
    rate_limit_check(request) # Terapkan rate limiting
    
    # Cek apakah detail course ada di cache Redis
    cache_key = f"course_detail_{course_id}"
    course = cache.get(cache_key)
    
    if not course:
        # Jika tidak ada, ambil dari Database
        course = get_object_or_404(Course, id=course_id)
        # Simpan ke Redis selama 15 menit (900 detik)
        cache.set(cache_key, course, 900)
    return course

# --- 2. MEMBUAT DATA BARU (POST) ---
@apiv1.post('courses/', response=CourseSchema, auth=apiAuth) # <--- Tambahkan auth=apiAuth di sini
def create_course(request, payload: CourseIn):
    # Pastikan Category dan Instructor yang diinputkan benar-benar ada di database
    category = get_object_or_404(Category, id=payload.category_id)
    instructor = get_object_or_404(User, id=payload.instructor_id, role='instructor')
    
    # Buat dan simpan data Course baru ke database
    course = Course.objects.create(
        title=payload.title,
        description=payload.description,
        category=category,
        instructor=instructor
    )
    
    # Mengembalikan data course yang baru dibuat sebagai response
    return course

# --- 3. MENGUBAH DATA (PUT) ---
@apiv1.put('courses/{course_id}', response=CourseSchema, auth=apiAuth) # <--- Tambahkan auth=apiAuth di sini
def update_course(request, course_id: int, payload: CourseIn):
    # 1. Cari data course yang mau diubah
    course = get_object_or_404(Course, id=course_id)
    
    # 2. Validasi input kategori dan instruktur yang baru
    category = get_object_or_404(Category, id=payload.category_id)
    instructor = get_object_or_404(User, id=payload.instructor_id, role='instructor')
    
    # 3. Timpa data lama dengan data baru
    course.title = payload.title
    course.description = payload.description
    course.category = category
    course.instructor = instructor
    
    # 4. Simpan ke database
    course.save()
    
    return course

# --- 4. MENGHAPUS DATA (DELETE) ---
@apiv1.delete('courses/{course_id}', auth=apiAuth) # <--- Tambahkan auth=apiAuth di sini
def delete_course(request, course_id: int):
    # Cari course-nya, lalu hapus
    course = get_object_or_404(Course, id=course_id)
    course.delete()
    
    # Kembalikan pesan sukses (tidak menggunakan CourseSchema karena datanya sudah hilang)
    return {"success": True, "message": f"Course '{course.title}' berhasil dihapus."}


@apiv1.get('analytics/report/')
def get_activity_report(request):
    # Menggunakan Aggregation Query MongoDB untuk menghitung total kunjungan per URL
    pipeline = [
        {"$group": {"_id": "$path", "total_visits": {"$sum": 1}}},
        {"$sort": {"total_visits": -1}}
    ]
    report = list(settings.MONGO_DB['activity_logs'].aggregate(pipeline))
    return {"report": report}

@apiv1.post('analytics/export/')
def trigger_export(request):
    # Panggil task secara asinkron dengan akhiran .delay()
    export_course_report.delay()
    return {"message": "Proses export CSV sedang berjalan di background. Tidak perlu menunggu!"}

@apiv1.post('courses/{course_id}/enroll')
def trigger_enrollment_email(request, course_id: int):
    # Simulasi pendaftaran kursus (Memanggil Celery Task: send_enrollment_email)
    course = get_object_or_404(Course, id=course_id)
    send_enrollment_email.delay("user@example.com", course.title)
    return {"message": f"Berhasil mendaftar! Email konfirmasi untuk '{course.title}' sedang dikirim di background."}

@apiv1.post('courses/{course_id}/certificate')
def trigger_certificate(request, course_id: int):
    # Simulasi kelulusan (Memanggil Celery Task: generate_certificate)
    course = get_object_or_404(Course, id=course_id)
    generate_certificate.delay(99, course_id)
    return {"message": f"Selamat! PDF Sertifikat untuk kursus '{course.title}' sedang digambar di background."}
