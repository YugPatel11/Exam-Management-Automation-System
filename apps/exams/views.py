"""
Views for Exam Management.
"""
from django.urls import reverse_lazy
from django.contrib import messages
from django.shortcuts import redirect
from django.db.models import Q
from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView
from django.db.models.deletion import ProtectedError

from apps.core.mixins import ExamCoordinatorRequiredMixin
from apps.exams.models import Exam
from apps.exams.forms import ExamForm


class ExamListView(ExamCoordinatorRequiredMixin, ListView):
    model = Exam
    template_name = 'exams/exam_list.html'
    context_object_name = 'exams'
    paginate_by = 20

    def get_queryset(self):
        qs = super().get_queryset().prefetch_related('programs')
        
        # Search by name or academic year
        query = self.request.GET.get('q')
        if query:
            qs = qs.filter(Q(name__icontains=query) | Q(academic_year__icontains=query))
        
        # Filter by Exam Type
        exam_type = self.request.GET.get('exam_type')
        if exam_type:
            qs = qs.filter(exam_type=exam_type)
            
        # Filter by Status
        status = self.request.GET.get('status')
        if status:
            qs = qs.filter(status=status)
            
        # Archived filter
        archive_status = self.request.GET.get('archive_status')
        if archive_status == 'active':
            qs = qs.filter(is_archived=False)
        elif archive_status == 'archived':
            qs = qs.filter(is_archived=True)
            
        return qs

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['exam_types'] = Exam.ExamType.choices
        ctx['exam_statuses'] = Exam.ExamStatus.choices
        return ctx


class ExamDetailView(ExamCoordinatorRequiredMixin, DetailView):
    model = Exam
    template_name = 'exams/exam_detail.html'
    context_object_name = 'exam'
    
    def get_queryset(self):
        return super().get_queryset().prefetch_related('programs')


class ExamCreateView(ExamCoordinatorRequiredMixin, CreateView):
    model = Exam
    form_class = ExamForm
    template_name = 'exams/exam_form.html'
    
    def get_success_url(self):
        return reverse_lazy('exams:exam_detail', kwargs={'pk': self.object.pk})

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['title'] = 'Create New Exam'
        ctx['cancel_url'] = reverse_lazy('exams:exam_list')
        return ctx

    def form_valid(self, form):
        messages.success(self.request, "Exam created successfully.")
        return super().form_valid(form)


class ExamUpdateView(ExamCoordinatorRequiredMixin, UpdateView):
    model = Exam
    form_class = ExamForm
    template_name = 'exams/exam_form.html'
    
    def get_success_url(self):
        return reverse_lazy('exams:exam_detail', kwargs={'pk': self.object.pk})

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['title'] = f'Edit Exam: {self.object.name}'
        ctx['cancel_url'] = reverse_lazy('exams:exam_detail', kwargs={'pk': self.object.pk})
        return ctx

    def form_valid(self, form):
        messages.success(self.request, "Exam updated successfully.")
        return super().form_valid(form)


class ExamDeleteView(ExamCoordinatorRequiredMixin, DeleteView):
    model = Exam
    template_name = 'master_data/confirm_delete.html'  # Reusing the beautiful delete template
    success_url = reverse_lazy('exams:exam_list')

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['title'] = 'Delete Exam'
        ctx['cancel_url'] = reverse_lazy('exams:exam_detail', kwargs={'pk': self.object.pk})
        ctx['item_name'] = f"{self.object.name} ({self.object.academic_year})"
        return ctx

    def form_valid(self, form):
        try:
            return super().form_valid(form)
        except ProtectedError:
            messages.error(
                self.request, 
                "Cannot delete this Exam because it is linked to schedules, seating, or marks. Archive it instead."
            )
            return redirect(self.success_url)
        except Exception as e:
            messages.error(self.request, f"An error occurred: {str(e)}")
            return redirect(self.success_url)
