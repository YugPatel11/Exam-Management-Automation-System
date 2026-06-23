"""
Models for Student Management.
"""
from django.db import models
from apps.core.models import BaseModel
from apps.master_data.models import Program, Division


class Student(BaseModel):
    """
    Represents a student enrolled in a program.
    Data is primarily populated via CSV import from ERP.
    """
    class GenderChoices(models.TextChoices):
        MALE = 'M', 'Male'
        FEMALE = 'F', 'Female'
        OTHER = 'O', 'Other'

    roll_no = models.CharField(
        max_length=50, 
        unique=True,
        verbose_name="Roll Number"
    )
    enrollment_no = models.CharField(
        max_length=50, 
        unique=True,
        verbose_name="Enrollment Number"
    )
    name = models.CharField(max_length=255, verbose_name="Student Name")
    
    program = models.ForeignKey(
        Program, 
        on_delete=models.PROTECT,
        related_name='students'
    )
    semester = models.PositiveIntegerField()
    
    division = models.ForeignKey(
        Division, 
        on_delete=models.PROTECT,
        related_name='students',
        null=True,
        blank=True
    )
    
    lab_batch_no = models.CharField(max_length=50, blank=True, verbose_name="Lab Batch No")
    gender = models.CharField(max_length=1, choices=GenderChoices.choices)
    
    display_no = models.CharField(max_length=50, blank=True, verbose_name="Display No")
    admission_application_no = models.CharField(max_length=100, blank=True, verbose_name="Admission Application No")
    
    phone_1 = models.CharField(max_length=20, blank=True, verbose_name="Phone 1")
    phone_2 = models.CharField(max_length=20, blank=True, verbose_name="Phone 2")
    email = models.EmailField(blank=True)

    class Meta:
        ordering = ['program', 'semester', 'roll_no']
        verbose_name = "Student"
        verbose_name_plural = "Students"

    def __str__(self):
        return f"{self.roll_no} - {self.name}"
