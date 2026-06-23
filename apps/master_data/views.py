"""
Views for Master Data management.
"""
from django.urls import reverse_lazy
from django.contrib import messages
from django.shortcuts import redirect
from django.db.models import Q
from django.views.generic import ListView, CreateView, UpdateView, DeleteView
from django.db.models.deletion import ProtectedError

from apps.core.mixins import ExamCoordinatorRequiredMixin
from apps.master_data.models import Program, Subject, Division, Classroom
from apps.master_data.forms import ProgramForm, SubjectForm, DivisionForm, ClassroomForm


# --- Program Views ---

class ProgramListView(ExamCoordinatorRequiredMixin, ListView):
    model = Program
    template_name = 'master_data/program_list.html'
    context_object_name = 'programs'
    paginate_by = 20

    def get_queryset(self):
        qs = super().get_queryset()
        query = self.request.GET.get('q')
        if query:
            qs = qs.filter(Q(name__icontains=query) | Q(code__icontains=query))
        
        status = self.request.GET.get('status')
        if status == 'active':
            qs = qs.filter(is_archived=False)
        elif status == 'archived':
            qs = qs.filter(is_archived=True)
            
        return qs


class ProgramCreateView(ExamCoordinatorRequiredMixin, CreateView):
    model = Program
    form_class = ProgramForm
    template_name = 'master_data/form.html'
    success_url = reverse_lazy('master_data:program_list')

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['title'] = 'Add New Program'
        ctx['cancel_url'] = self.success_url
        return ctx

    def form_valid(self, form):
        messages.success(self.request, "Program created successfully.")
        return super().form_valid(form)


class ProgramUpdateView(ExamCoordinatorRequiredMixin, UpdateView):
    model = Program
    form_class = ProgramForm
    template_name = 'master_data/form.html'
    success_url = reverse_lazy('master_data:program_list')

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['title'] = f'Edit Program: {self.object.code}'
        ctx['cancel_url'] = self.success_url
        return ctx

    def form_valid(self, form):
        messages.success(self.request, "Program updated successfully.")
        return super().form_valid(form)


class ProgramDeleteView(ExamCoordinatorRequiredMixin, DeleteView):
    model = Program
    template_name = 'master_data/confirm_delete.html'
    success_url = reverse_lazy('master_data:program_list')

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['title'] = 'Delete Program'
        ctx['cancel_url'] = self.success_url
        ctx['item_name'] = f"{self.object.code} - {self.object.name}"
        return ctx

    def form_valid(self, form):
        try:
            return super().form_valid(form)
        except ProtectedError:
            messages.error(self.request, "Cannot delete this Program because it is linked to existing Divisions. Archive it instead.")
            return redirect(self.success_url)
        except Exception as e:
            messages.error(self.request, f"An error occurred: {str(e)}")
            return redirect(self.success_url)


# --- Subject Views ---

class SubjectListView(ExamCoordinatorRequiredMixin, ListView):
    model = Subject
    template_name = 'master_data/subject_list.html'
    context_object_name = 'subjects'
    paginate_by = 20

    def get_queryset(self):
        qs = super().get_queryset()
        query = self.request.GET.get('q')
        if query:
            qs = qs.filter(Q(name__icontains=query) | Q(code__icontains=query))
            
        status = self.request.GET.get('status')
        if status == 'active':
            qs = qs.filter(is_archived=False)
        elif status == 'archived':
            qs = qs.filter(is_archived=True)
            
        return qs


class SubjectCreateView(ExamCoordinatorRequiredMixin, CreateView):
    model = Subject
    form_class = SubjectForm
    template_name = 'master_data/form.html'
    success_url = reverse_lazy('master_data:subject_list')

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['title'] = 'Add New Subject'
        ctx['cancel_url'] = self.success_url
        return ctx

    def form_valid(self, form):
        messages.success(self.request, "Subject created successfully.")
        return super().form_valid(form)


class SubjectUpdateView(ExamCoordinatorRequiredMixin, UpdateView):
    model = Subject
    form_class = SubjectForm
    template_name = 'master_data/form.html'
    success_url = reverse_lazy('master_data:subject_list')

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['title'] = f'Edit Subject: {self.object.code}'
        ctx['cancel_url'] = self.success_url
        return ctx

    def form_valid(self, form):
        messages.success(self.request, "Subject updated successfully.")
        return super().form_valid(form)


class SubjectDeleteView(ExamCoordinatorRequiredMixin, DeleteView):
    model = Subject
    template_name = 'master_data/confirm_delete.html'
    success_url = reverse_lazy('master_data:subject_list')

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['title'] = 'Delete Subject'
        ctx['cancel_url'] = self.success_url
        ctx['item_name'] = f"{self.object.code} - {self.object.name}"
        return ctx

    def form_valid(self, form):
        try:
            return super().form_valid(form)
        except ProtectedError:
            messages.error(self.request, "Cannot delete this Subject because it is used in existing assessment schemes. Archive it instead.")
            return redirect(self.success_url)
        except Exception as e:
            messages.error(self.request, f"An error occurred: {str(e)}")
            return redirect(self.success_url)


# --- Division Views ---

class DivisionListView(ExamCoordinatorRequiredMixin, ListView):
    model = Division
    template_name = 'master_data/division_list.html'
    context_object_name = 'divisions'
    paginate_by = 20

    def get_queryset(self):
        qs = super().get_queryset().select_related('program')
        query = self.request.GET.get('q')
        if query:
            qs = qs.filter(Q(name__icontains=query) | Q(program__code__icontains=query))
            
        program_id = self.request.GET.get('program')
        if program_id:
            qs = qs.filter(program_id=program_id)
            
        status = self.request.GET.get('status')
        if status == 'active':
            qs = qs.filter(is_archived=False)
        elif status == 'archived':
            qs = qs.filter(is_archived=True)
            
        return qs
        
    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['programs'] = Program.objects.filter(is_archived=False)
        return ctx


class DivisionCreateView(ExamCoordinatorRequiredMixin, CreateView):
    model = Division
    form_class = DivisionForm
    template_name = 'master_data/form.html'
    success_url = reverse_lazy('master_data:division_list')

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['title'] = 'Add New Division'
        ctx['cancel_url'] = self.success_url
        return ctx

    def form_valid(self, form):
        messages.success(self.request, "Division created successfully.")
        return super().form_valid(form)


class DivisionUpdateView(ExamCoordinatorRequiredMixin, UpdateView):
    model = Division
    form_class = DivisionForm
    template_name = 'master_data/form.html'
    success_url = reverse_lazy('master_data:division_list')

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['title'] = f'Edit Division: {self.object}'
        ctx['cancel_url'] = self.success_url
        return ctx

    def form_valid(self, form):
        messages.success(self.request, "Division updated successfully.")
        return super().form_valid(form)


class DivisionDeleteView(ExamCoordinatorRequiredMixin, DeleteView):
    model = Division
    template_name = 'master_data/confirm_delete.html'
    success_url = reverse_lazy('master_data:division_list')

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['title'] = 'Delete Division'
        ctx['cancel_url'] = self.success_url
        ctx['item_name'] = str(self.object)
        return ctx

    def form_valid(self, form):
        try:
            return super().form_valid(form)
        except ProtectedError:
            messages.error(self.request, "Cannot delete this Division because it is linked to students or schedules. Archive it instead.")
            return redirect(self.success_url)
        except Exception as e:
            messages.error(self.request, f"An error occurred: {str(e)}")
            return redirect(self.success_url)


# --- Classroom Views ---

class ClassroomListView(ExamCoordinatorRequiredMixin, ListView):
    model = Classroom
    template_name = 'master_data/classroom_list.html'
    context_object_name = 'classrooms'
    paginate_by = 20

    def get_queryset(self):
        qs = super().get_queryset()
        query = self.request.GET.get('q')
        if query:
            qs = qs.filter(room_number__icontains=query)
            
        status = self.request.GET.get('status')
        if status == 'active':
            qs = qs.filter(is_archived=False)
        elif status == 'archived':
            qs = qs.filter(is_archived=True)
            
        return qs


class ClassroomCreateView(ExamCoordinatorRequiredMixin, CreateView):
    model = Classroom
    form_class = ClassroomForm
    template_name = 'master_data/form.html'
    success_url = reverse_lazy('master_data:classroom_list')

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['title'] = 'Add New Classroom'
        ctx['cancel_url'] = self.success_url
        return ctx

    def form_valid(self, form):
        messages.success(self.request, "Classroom created successfully.")
        return super().form_valid(form)


class ClassroomUpdateView(ExamCoordinatorRequiredMixin, UpdateView):
    model = Classroom
    form_class = ClassroomForm
    template_name = 'master_data/form.html'
    success_url = reverse_lazy('master_data:classroom_list')

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['title'] = f'Edit Classroom: {self.object.room_number}'
        ctx['cancel_url'] = self.success_url
        return ctx

    def form_valid(self, form):
        messages.success(self.request, "Classroom updated successfully.")
        return super().form_valid(form)


class ClassroomDeleteView(ExamCoordinatorRequiredMixin, DeleteView):
    model = Classroom
    template_name = 'master_data/confirm_delete.html'
    success_url = reverse_lazy('master_data:classroom_list')

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['title'] = 'Delete Classroom'
        ctx['cancel_url'] = self.success_url
        ctx['item_name'] = f"Room {self.object.room_number}"
        return ctx

    def form_valid(self, form):
        try:
            return super().form_valid(form)
        except ProtectedError:
            messages.error(self.request, "Cannot delete this Classroom because it has been used in seating arrangements. Archive it instead.")
            return redirect(self.success_url)
        except Exception as e:
            messages.error(self.request, f"An error occurred: {str(e)}")
            return redirect(self.success_url)
