from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from django.core.cache import cache
from .models import Course

def clear_course_cache():
    cache.delete("course_list_cache")

@receiver(post_save, sender=Course)
def invalidate_course_cache_on_save(sender, instance, **kwargs):
    clear_course_cache()
    cache.delete(f"course_detail_{instance.id}")

@receiver(post_delete, sender=Course)
def invalidate_course_cache_on_delete(sender, instance, **kwargs):
    clear_course_cache()
    cache.delete(f"course_detail_{instance.id}")
