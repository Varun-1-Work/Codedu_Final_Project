# TrainerApp/forms.py
from django import forms
from .models import TrainerLeave 
from StudentApp.models import    ExamResult, Student, Batch, Course,ConductedExam




class TrainerLeaveForm(forms.ModelForm):
    class Meta:
        model = TrainerLeave
        fields = ['start_date', 'end_date', 'reason']
        widgets = {
            'start_date': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'end_date': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'reason': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'Reason for leave...'}),
        }

#####################################################################################################

class ExamResultForm(forms.ModelForm):
    exam_name = forms.ModelChoiceField(
        queryset=ConductedExam.objects.none(),
        empty_label="— Select Exam —",
        widget=forms.Select(attrs={'class': 'form-control'})
    )

    class Meta:
        model = ExamResult
        fields = ['student', 'exam_name', 'marks_obtained', 'total_marks']
        widgets = {
            'student': forms.Select(attrs={'class': 'form-control'}),
            'marks_obtained': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': 0
            }),
            'total_marks': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': 0
            }),
        }

    def __init__(self, *args, trainer=None, **kwargs):
        super().__init__(*args, **kwargs)

        if trainer:
            self.fields['student'].queryset = Student.objects.filter(
                batch__trainer=trainer
            )
            self.fields['exam_name'].queryset = ConductedExam.objects.filter(
                created_by=trainer
            )

    def clean(self):
        cleaned_data = super().clean()
        marks = cleaned_data.get('marks_obtained')
        total = cleaned_data.get('total_marks')

        if marks is not None and total is not None and marks > total:
            raise forms.ValidationError("Marks obtained cannot exceed total marks")

        return cleaned_data
    

class ExamResultEditForm(forms.ModelForm):
    class Meta:
        model = ExamResult
        fields = ['marks_obtained', 'total_marks']
        widgets = {
            'marks_obtained': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': 0
            }),
            'total_marks': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': 0
            }),
        }

    def clean(self):
        cleaned_data = super().clean()
        marks = cleaned_data.get('marks_obtained')
        total = cleaned_data.get('total_marks')

        if marks is not None and total is not None and marks > total:
            raise forms.ValidationError("Marks obtained cannot exceed total marks")

        return cleaned_data

class ConductExamForm(forms.ModelForm):
    class Meta:
        model = ConductedExam
        fields = ['batch', 'course', 'exam_name', 'date_conducted', 'total_marks']
        widgets = {
            'batch': forms.Select(attrs={'class': 'form-control'}),
            'course': forms.Select(attrs={'class': 'form-control'}),
            'exam_name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Enter exam name'}),
            'date_conducted': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'total_marks': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'Enter total marks', 'min': '0'}),
        }

    def __init__(self, *args, trainer=None, **kwargs):
        super().__init__(*args, **kwargs)
        if trainer:
            self.fields['batch'].queryset = Batch.objects.filter(trainer=trainer)
            
        # Start with an empty course list until a batch is selected
        self.fields['course'].queryset = Course.objects.none()

        # Handle data if the form is re-bound (e.g., after a failed validation)
        if 'batch' in self.data:
            try:
                batch_id = int(self.data.get('batch'))
                self.fields['course'].queryset = Course.objects.filter(batches__id=batch_id).distinct()
            except (ValueError, TypeError):
                pass