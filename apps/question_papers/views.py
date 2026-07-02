"""
Views for Question Paper Management.
"""
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.views.generic import ListView, CreateView, UpdateView, DetailView, View
from django.urls import reverse_lazy, reverse
from django.db import transaction

from apps.core.mixins import SubjectCoordinatorRequiredMixin, ExamCoordinatorRequiredMixin
from apps.question_papers.models import QuestionPaper, QuestionPaperTemplate
from apps.question_papers.forms import QuestionPaperForm, QuestionFormSet, QuestionPaperTemplateForm
from apps.question_papers.services import question_paper_service
from apps.core.models_audit import TextContent


class QuestionPaperTemplateUpdateView(ExamCoordinatorRequiredMixin, UpdateView):
    """
    Manage the global Question Paper Template.
    """
    model = QuestionPaperTemplate
    form_class = QuestionPaperTemplateForm
    template_name = 'question_papers/template_upload.html'
    success_url = reverse_lazy('dashboard:home')
    
    def get_object(self, queryset=None):
        template, created = QuestionPaperTemplate.objects.get_or_create(is_active=True, defaults={'name': 'Standard Template'})
        return template

    def form_valid(self, form):
        messages.success(self.request, "Question Paper Template updated successfully.")
        return super().form_valid(form)


class QuestionPaperListView(SubjectCoordinatorRequiredMixin, ListView):
    """
    List of Question Papers. Filtered by role in get_queryset.
    """
    model = QuestionPaper
    template_name = 'question_papers/list.html'
    context_object_name = 'papers'

    def get_queryset(self):
        qs = QuestionPaper.objects.all().select_related('exam', 'subject', 'program')
        
        # Subject Coordinator sees only papers for subjects they coordinate.
        if self.request.user.is_subject_coordinator:
            from apps.academic.models import FacultyTeachingAssignment
            coordinated_subjects = FacultyTeachingAssignment.objects.filter(
                faculty__user=self.request.user, is_coordinator=True
            ).values_list('semester_subject__subject_id', flat=True)
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
            from apps.core.services.text_content import text_content_service
            contents = text_content_service.get_by_module(
                'question_paper', 
                related_object_id=str(self.object.id)
            )
            context['generated_content'] = contents.first()
        except Exception:
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


class QuestionPaperPreviewView(SubjectCoordinatorRequiredMixin, DetailView):
    """
    Preview the generated question paper inside the template format.
    """
    model = QuestionPaper
    template_name = 'question_papers/preview.html'
    context_object_name = 'paper'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['questions'] = self.object.questions.all().order_by('order', 'created_at')
        template = QuestionPaperTemplate.objects.filter(is_active=True).first()
        if template and template.header_html:
            html = template.header_html
            html = html.replace('{{ subject_code }}', self.object.subject.code)
            html = html.replace('{{ subject_name }}', self.object.subject.name)
            html = html.replace('{{ date }}', str(self.object.date) if self.object.date else '___')
            html = html.replace('{{ marks }}', str(self.object.total_marks))
            context['rendered_header'] = html
        return context


class QuestionPaperLockView(ExamCoordinatorRequiredMixin, View):
    """
    Exam Coordinator locks the verified question paper.
    """
    def post(self, request, pk):
        paper = get_object_or_404(QuestionPaper, pk=pk)
        paper.status = 'approved'
        paper.save()
        messages.success(request, f"Question Paper for {paper.subject.code} has been locked.")
        return redirect('question_papers:list')


class QuestionPaperPrintView(ExamCoordinatorRequiredMixin, DetailView):
    """
    Print the locked question paper directly from the browser.
    """
    model = QuestionPaper
    template_name = 'question_papers/print.html'
    context_object_name = 'paper'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['questions'] = self.object.questions.all().order_by('order', 'created_at')
        template = QuestionPaperTemplate.objects.filter(is_active=True).first()
        if template and template.header_html:
            html = template.header_html
            html = html.replace('{{ subject_code }}', self.object.subject.code)
            html = html.replace('{{ subject_name }}', self.object.subject.name)
            html = html.replace('{{ date }}', str(self.object.date) if self.object.date else '___')
            html = html.replace('{{ marks }}', str(self.object.total_marks))
            context['rendered_header'] = html
        return context


class QuestionPaperPdfView(SubjectCoordinatorRequiredMixin, View):
    """
    Generate and download a Question Paper as a PDF using reportlab.
    """
    def get(self, request, pk):
        import io
        from reportlab.lib import colors
        from reportlab.lib.pagesizes import A4
        from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
        from reportlab.lib.units import inch
        from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, HRFlowable

        paper = get_object_or_404(QuestionPaper, pk=pk)
        questions = paper.questions.all().order_by('order', 'created_at')

        buf = io.BytesIO()
        doc = SimpleDocTemplate(buf, pagesize=A4, title=f'Question Paper - {paper.subject.code}')
        styles = getSampleStyleSheet()
        elements = []

        # Header
        header_style = ParagraphStyle('QPHeader', parent=styles['Title'], fontSize=14, alignment=1)
        sub_style = ParagraphStyle('QPSub', parent=styles['Normal'], fontSize=10, alignment=1, textColor=colors.grey)
        q_style = ParagraphStyle('QPQuestion', parent=styles['Normal'], fontSize=10, spaceAfter=4)

        elements.append(Paragraph(f'{paper.exam.name}', header_style))
        elements.append(Paragraph(f'{paper.subject.code} — {paper.subject.name}', sub_style))
        elements.append(Paragraph(f'Program: {paper.program.code} | Semester: {paper.semester} | Total Marks: {paper.total_marks}', sub_style))
        if paper.date:
            elements.append(Paragraph(f'Date: {paper.date} | Time: {paper.start_time} — {paper.end_time}', sub_style))
        elements.append(Spacer(1, 0.2 * inch))
        elements.append(HRFlowable(width='100%', thickness=1, color=colors.grey))
        elements.append(Spacer(1, 0.2 * inch))

        # Questions table
        table_data = [['Q.No', 'Question', 'Marks', 'CO', 'BTL']]
        for q in questions:
            table_data.append([q.question_number, q.text[:120], str(q.marks), q.co_mapping, q.btl_mapping])

        table = Table(table_data, colWidths=[0.6*inch, 3.5*inch, 0.6*inch, 0.6*inch, 0.6*inch], repeatRows=1)
        table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#0d9488')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 9),
            ('FONTSIZE', (0, 1), (-1, -1), 8),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('ALIGN', (1, 1), (1, -1), 'LEFT'),
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.whitesmoke, colors.white]),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
        ]))
        elements.append(table)
        doc.build(elements)
        buf.seek(0)

        from django.http import HttpResponse as HR
        response = HR(buf.read(), content_type='application/pdf')
        response['Content-Disposition'] = f'attachment; filename="QP_{paper.subject.code}_{paper.exam.name}.pdf"'
        return response


class COBTLReportView(SubjectCoordinatorRequiredMixin, View):
    """
    Shows CO & BTL coverage report for a question paper as a summary page with charts.
    """
    def get(self, request, pk):
        import json
        paper = get_object_or_404(QuestionPaper, pk=pk)
        coverage = question_paper_service.validate_co_btl_coverage(paper)

        co_labels = list(coverage['co_distribution'].keys())
        co_values = list(coverage['co_distribution'].values())
        btl_labels = list(coverage['btl_distribution'].keys())
        btl_values = list(coverage['btl_distribution'].values())

        context = {
            'paper': paper,
            'coverage': coverage,
            'co_labels': json.dumps(co_labels),
            'co_values': json.dumps(co_values),
            'btl_labels': json.dumps(btl_labels),
            'btl_values': json.dumps(btl_values),
        }
        return render(request, 'question_papers/co_btl_report.html', context)

