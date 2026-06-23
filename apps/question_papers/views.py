"""
Views for Question Paper Management.
"""
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.views.generic import ListView, CreateView, UpdateView, DetailView, View
from django.urls import reverse_lazy, reverse
from django.db import transaction

from apps.core.mixins import SubjectCoordinatorRequiredMixin
from apps.question_papers.models import QuestionPaper
from apps.question_papers.forms import QuestionPaperForm, QuestionFormSet
from apps.question_papers.services import question_paper_service
from apps.core.models_audit import TextContent


class QuestionPaperListView(SubjectCoordinatorRequiredMixin, ListView):
    """
    List of Question Papers. Filtered by role in get_queryset.
    """
    model = QuestionPaper
    template_name = 'question_papers/list.html'
    context_object_name = 'papers'

    def get_queryset(self):
        qs = QuestionPaper.objects.all().select_related('exam', 'subject', 'program')
        
        # Admin and Exam Coordinator see all.
        # Subject Coordinator sees only papers for subjects they coordinate.
        if self.request.user.is_subject_coordinator:
            coordinated_subjects = self.request.user.coordinated_subjects.values_list('subject_id', flat=True)
            qs = qs.filter(subject_id__in=coordinated_subjects)
            
        return qs


class QuestionPaperCreateView(SubjectCoordinatorRequiredMixin, CreateView):
    """
    Create a Question Paper with inline Questions.
    """
    model = QuestionPaper
    form_class = QuestionPaperForm
    template_name = 'question_papers/form.html'
    success_url = reverse_lazy('question_papers:list')

    def get_context_data(self, **kwargs):
        data = super().get_context_data(**kwargs)
        if self.request.POST:
            data['questions'] = QuestionFormSet(self.request.POST)
        else:
            data['questions'] = QuestionFormSet()
        return data

    def form_valid(self, form):
        context = self.get_context_data()
        questions = context['questions']
        
        with transaction.atomic():
            form.instance.created_by = self.request.user
            self.object = form.save()
            
            if questions.is_valid():
                questions.instance = self.object
                questions.save()
            else:
                return self.form_invalid(form)
                
        messages.success(self.request, "Question Paper created successfully.")
        return super().form_valid(form)


class QuestionPaperUpdateView(SubjectCoordinatorRequiredMixin, UpdateView):
    """
    Update a Question Paper and its Questions.
    """
    model = QuestionPaper
    form_class = QuestionPaperForm
    template_name = 'question_papers/form.html'
    
    def get_success_url(self):
        return reverse('question_papers:detail', kwargs={'pk': self.object.pk})

    def get_context_data(self, **kwargs):
        data = super().get_context_data(**kwargs)
        if self.request.POST:
            data['questions'] = QuestionFormSet(self.request.POST, instance=self.object)
        else:
            data['questions'] = QuestionFormSet(instance=self.object)
        return data

    def form_valid(self, form):
        context = self.get_context_data()
        questions = context['questions']
        
        with transaction.atomic():
            self.object = form.save()
            if questions.is_valid():
                questions.instance = self.object
                questions.save()
            else:
                return self.form_invalid(form)
                
        messages.success(self.request, "Question Paper updated successfully.")
        return super().form_valid(form)


class QuestionPaperDetailView(SubjectCoordinatorRequiredMixin, DetailView):
    """
    View Question Paper details including CO/BTL coverage.
    """
    model = QuestionPaper
    template_name = 'question_papers/detail.html'
    context_object_name = 'paper'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['questions'] = self.object.questions.all().order_by('order', 'created_at')
        context['coverage'] = question_paper_service.validate_co_btl_coverage(self.object)
        
        # Try to find generated TextContent
        try:
            content = TextContent.objects.get(
                module='question_paper', 
                related_object_id=str(self.object.id)
            )
            context['generated_content'] = content
        except TextContent.DoesNotExist:
            context['generated_content'] = None
            
        return context


class QuestionPaperSubmitView(SubjectCoordinatorRequiredMixin, View):
    """
    Submit a Question Paper for approval and generate the text content.
    """
    def post(self, request, pk):
        paper = get_object_or_404(QuestionPaper, pk=pk)
        
        # Generate TextContent
        question_paper_service.generate_question_paper_content(paper)
        
        # Update status
        paper.status = 'submitted'
        paper.save()
        
        messages.success(request, f"Question Paper for {paper.subject.code} submitted successfully.")
        return redirect('question_papers:detail', pk=paper.pk)
