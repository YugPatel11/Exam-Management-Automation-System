"""
Admin configuration for Academic Year Management.
"""
from django.contrib import admin
from apps.academic.models import (
    AcademicYear, Semester, SemesterSubject,
    MarksComponent, AcademicStructureImport,
    FacultyMaster, FacultyTeachingAssignment, FacultyImportLog,
)


class SemesterInline(admin.TabularInline):
    model = Semester
    extra = 0
    readonly_fields = ('created_at',)


@admin.register(AcademicYear)
class AcademicYearAdmin(admin.ModelAdmin):
    list_display = ('name', 'status', 'total_semesters', 'total_subjects', 'created_at')
    list_filter = ('status',)
    search_fields = ('name',)
    inlines = [SemesterInline]


class SemesterSubjectInline(admin.TabularInline):
    model = SemesterSubject
    extra = 0
    readonly_fields = ('subject_code', 'subject_name', 'created_at')


@admin.register(Semester)
class SemesterAdmin(admin.ModelAdmin):
    list_display = ('name', 'academic_year', 'number', 'total_subjects')
    list_filter = ('academic_year',)
    search_fields = ('name', 'number')
    inlines = [SemesterSubjectInline]


class MarksComponentInline(admin.TabularInline):
    model = MarksComponent
    extra = 0


@admin.register(SemesterSubject)
class SemesterSubjectAdmin(admin.ModelAdmin):
    list_display = ('subject_code', 'subject_name', 'semester', 'total_max_marks')
    list_filter = ('semester__academic_year', 'semester')
    search_fields = ('subject_code', 'subject_name')
    inlines = [MarksComponentInline]


@admin.register(MarksComponent)
class MarksComponentAdmin(admin.ModelAdmin):
    list_display = ('semester_subject', 'name', 'slug', 'max_marks', 'display_order')
    list_filter = ('semester_subject__semester__academic_year',)
    search_fields = ('name', 'semester_subject__subject_code')


@admin.register(AcademicStructureImport)
class AcademicStructureImportAdmin(admin.ModelAdmin):
    list_display = ('academic_year', 'original_filename', 'status', 'imported_by', 'created_at')
    list_filter = ('status', 'academic_year')
    readonly_fields = ('summary', 'error_log')


@admin.register(FacultyMaster)
class FacultyMasterAdmin(admin.ModelAdmin):
    list_display = ('faculty_name', 'short_form', 'email', 'department', 'is_active', 'academic_year')
    list_filter = ('is_active', 'academic_year', 'department')
    search_fields = ('faculty_name', 'short_form', 'email', 'employee_code')
    autocomplete_fields = ('user',)


@admin.register(FacultyTeachingAssignment)
class FacultyTeachingAssignmentAdmin(admin.ModelAdmin):
    list_display = ('academic_year', 'semester', 'class_name', 'semester_subject', 'teaching_type', 'faculty', 'is_coordinator')
    list_filter = ('academic_year', 'semester', 'teaching_type', 'is_coordinator')
    search_fields = ('class_name', 'semester_subject__subject_code', 'semester_subject__subject_name', 'faculty__faculty_name', 'faculty_alias_raw')
    autocomplete_fields = ('faculty', 'semester', 'semester_subject')


@admin.register(FacultyImportLog)
class FacultyImportLogAdmin(admin.ModelAdmin):
    list_display = ('academic_year', 'import_type', 'original_filename', 'status', 'imported_by', 'created_at')
    list_filter = ('import_type', 'status', 'academic_year')
    readonly_fields = ('summary', 'error_log')
