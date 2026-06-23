"""
Services for Question Papers.
"""
from django.template.loader import render_to_string
from apps.core.services.text_content import text_content_service

class QuestionPaperService:
    """
    Handles question paper generation and validation.
    """

    @staticmethod
    def generate_question_paper_content(question_paper):
        """
        Generates the text/HTML representation of the question paper and saves it to TextContent.
        """
        context = {
            'paper': question_paper,
            'questions': question_paper.questions.all().order_by('order', 'created_at')
        }
        
        # Render a simple text/html version of the question paper
        html_content = render_to_string('question_papers/pdf_template.html', context)
        
        title = f"Question Paper: {question_paper.exam.name} - {question_paper.subject.code}"
        
        # Save to TextContent
        return text_content_service.save_content(
            title=title,
            content=html_content,
            module='question_paper',
            content_type='html',
            related_object_id=question_paper.id,
            related_model='QuestionPaper',
            user=question_paper.created_by
        )
        
    @staticmethod
    def validate_co_btl_coverage(question_paper):
        """
        Validates CO and BTL coverage for a question paper.
        Returns a dict with coverage statistics.
        """
        questions = question_paper.questions.all()
        
        co_marks = {}
        btl_marks = {}
        total = 0
        
        for q in questions:
            total += q.marks
            
            co = q.co_mapping.strip().upper()
            if co:
                co_marks[co] = co_marks.get(co, 0) + q.marks
                
            btl = q.btl_mapping.strip().upper()
            if btl:
                btl_marks[btl] = btl_marks.get(btl, 0) + q.marks
                
        return {
            'total_marks': total,
            'co_distribution': co_marks,
            'btl_distribution': btl_marks,
            'is_valid': total == question_paper.total_marks
        }

question_paper_service = QuestionPaperService()
