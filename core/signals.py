from django.db.models.signals import post_save
from django.dispatch import receiver
from django.contrib.auth.models import User
from .models import Profile, TeachingRecord, Attendance


@receiver(post_save, sender=User, weak=False)
def create_or_save_user_profile(sender, instance, created, **kwargs):
    # Create a new Profile only if one doesn't already exist
    if created:
        # Only create a new profile if one doesn't exist
        Profile.objects.get_or_create(user=instance)
    else:
        # Ensure the profile is saved when the User is updated
        Profile.objects.get_or_create(user=instance)
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