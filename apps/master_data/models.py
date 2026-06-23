"""
Master Data Models for EMS.
"""
from django.db import models
from django.core.validators import MinValueValidator
from apps.core.models import BaseModel


class Program(BaseModel):
    """
    Represents an academic program (e.g., B.Tech Computer Engineering).
    """
    name = models.CharField(max_length=255, verbose_name="Program Name")
    code = models.CharField(max_length=50, unique=True, verbose_name="Program Code")
    
    class Meta:
        ordering = ['code']
        verbose_name = "Program"
        verbose_name_plural = "Programs"

    def __str__(self):
        return f"{self.code} - {self.name}"


class Subject(BaseModel):
    """
    Represents an academic subject/course.
    """
    name = models.CharField(max_length=255, verbose_name="Subject Name")
    code = models.CharField(max_length=50, unique=True, verbose_name="Subject Code")
    
    class Meta:
        ordering = ['code']
        verbose_name = "Subject"
        verbose_name_plural = "Subjects"

    def __str__(self):
        return f"{self.code} - {self.name}"


class Division(BaseModel):
    """
    Represents a division/section within a specific program and semester.
    """
    program = models.ForeignKey(Program, on_delete=models.PROTECT, related_name='divisions')
    semester = models.PositiveIntegerField(
        validators=[MinValueValidator(1)],
        help_text="Semester number (e.g., 1, 2, 3)"
    )
    name = models.CharField(max_length=50, verbose_name="Division Name", help_text="e.g., A, B, C")
    
    class Meta:
        ordering = ['program', 'semester', 'name']
        unique_together = ('program', 'semester', 'name')
        verbose_name = "Division"
        verbose_name_plural = "Divisions"

    def __str__(self):
        return f"{self.program.code} - Sem {self.semester} - Div {self.name}"


class Classroom(BaseModel):
    """
    Represents a physical classroom or lab used for seating.
    """
    room_number = models.CharField(max_length=50, unique=True, verbose_name="Room Number")
    capacity = models.PositiveIntegerField(
        validators=[MinValueValidator(1)],
        help_text="Maximum seating capacity"
    )
    
    class Meta:
        ordering = ['room_number']
        verbose_name = "Classroom"
        verbose_name_plural = "Classrooms"

    def __str__(self):
        return f"Room {self.room_number} (Capacity: {self.capacity})"
