# `core/management/commands/generate_qr_codes.py`
from django.core.management.base import BaseCommand
from core.models import Student
import os

class Command(BaseCommand):
    help = 'Generate QR codes for students if not already available'

    def handle(self, *args, **kwargs):
        students = Student.objects.all()
        for student in students:
            qr_code_path = f'media/qr_codes/{student.slug}_{student.student_number}.png'
            if not os.path.exists(qr_code_path):
                self.stdout.write(f'Generating QR code for {student.name}...')
                student.generate_qr_code_url()
                self.stdout.write(self.style.SUCCESS(f'Successfully generated QR code for {student.name}'))
            else:
                self.stdout.write(self.style.WARNING(f'QR code already exists for {student.name}'))