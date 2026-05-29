from ninja import ModelSchema, Schema
from .models import Course, Category
from typing import Optional
from datetime import datetime

class Register(Schema):
    username: str
    password: str
    email: str
    first_name: str
    last_name: str

class UserOut(Schema):
    id: int
    username: str
    first_name: str
    last_name: str
    email: str

# Schema untuk Category (agar bisa ditampilkan di dalam Course)
class CategorySchema(ModelSchema):
    class Meta:
        model = Category
        fields = ['id', 'name']

# Schema utama untuk Course
class CourseSchema(ModelSchema):
    category: CategorySchema | None = None # Menambahkan relasi kategori
    instructor_name: str # Kita akan ambil nama instruktur, bukan cuma ID-nya

    class Meta:
        model = Course
        fields = ['id', 'title', 'description', 'created_at']
        
    # Fungsi ini memberitahu Ninja cara mendapatkan 'instructor_name'
    @staticmethod
    def resolve_instructor_name(obj):
        return obj.instructor.username if obj.instructor else "No Instructor"
    
# Schema baru khusus untuk menerima input POST (Membuat Course Baru)
class CourseIn(Schema):
    title: str
    description: str
    category_id: int
    instructor_id: int