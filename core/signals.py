from django.db.models.signals import post_save
from django.dispatch import receiver
from django.contrib.auth.models import User
from .models import Profile, TeachingRecord, Attendance


@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
    if created:
        Profile.objects.create(user=instance)


@receiver(post_save, sender=User)
def save_user_profile(sender, instance, **kwargs):
    instance.profile.save()


@receiver(post_save, sender=Attendance)
def create_teaching_record(sender, instance, created, **kwargs):
    if created:
        # Automatically create a TeachingRecord when Attendance is created
        TeachingRecord.objects.create(
            attendance=instance,
            description=f'Teaching record for the course {instance.course} done on {instance.course_date} at {instance.course_start_time}',
            quality_assurance=TeachingRecord.QualityChoices.APPROVED,
        )
