from django import forms
from django.core.exceptions import ValidationError
from django.contrib.auth.models import User
from .models import UserProfile




class ProfileUpdateForm(forms.ModelForm):
    first_name = forms.CharField(
        label='First Name',
        max_length=100,
        widget=forms.TextInput(
            attrs={'class': 'form-control', 'placeholder': 'Enter First Name'})
    )
    last_name = forms.CharField(
        label='Last Name',
        max_length=100,
        widget=forms.TextInput(
            attrs={'class': 'form-control', 'placeholder': 'Enter Last Name'})
    )
    email = forms.EmailField(
        label='Email Address',
        widget=forms.EmailInput(
            attrs={'class': 'form-control', 'placeholder': 'Enter Email Address'})
    )
    school_name = forms.CharField(
        label='School Name',
        max_length=255,
        required=False,
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Enter Your School Name'})
    )

    class Meta:
        model = UserProfile
        fields = ['school_name']

    def __init__(self, *args, **kwargs):
        user = kwargs.pop('user')
        super(ProfileUpdateForm, self).__init__(*args, **kwargs)
        self.fields['first_name'].initial = user.first_name
        self.fields['last_name'].initial = user.last_name
        self.fields['email'].initial = user.email
        if hasattr(user, 'profile'):
            self.fields['school_name'].initial = user.profile.school_name


 
class QuizForm(forms.Form):
    EXAM_MODE_CHOICES = [
        ("Study Mode", "Study Mode"),
        ("Exam Mode", "Exam Mode"),
    ]

    ALL_TOPICS_OPTION = 'ALL'

    topics = forms.MultipleChoiceField(
        widget=forms.CheckboxSelectMultiple,
        choices=[],  # This will be populated dynamically in the view
    )
    quiz_mode = forms.ChoiceField(
        choices=EXAM_MODE_CHOICES,
        initial="Study Mode",
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    num_questions = forms.IntegerField(min_value=1, max_value=250)

    def __init__(self, *args, **kwargs):
        topics_choices = kwargs.pop('topics_choices', [])
        super().__init__(*args, **kwargs)
        # Add 'Select All' option to the choices
        self.fields['topics'].choices = [
            (self.ALL_TOPICS_OPTION, 'Select All')] + topics_choices
        self.fields['num_questions'].widget.attrs.update(
            {'class': 'form-control'}
        )

    def clean_num_questions(self):
        """
        Custom validation for 'num_questions' field based on quiz_mode.
        """
        num_questions = self.cleaned_data.get('num_questions')
        quiz_mode = self.cleaned_data.get('quiz_mode')

        if quiz_mode == "Exam Mode" and num_questions > 250:
            raise ValidationError(
                f"In 'Exam Mode', the maximum number of questions is 250. You entered {num_questions}."
            )
        elif quiz_mode == "Study Mode" and num_questions > 100:
            raise ValidationError(
                f"In 'Study Mode', the maximum number of questions is 100. You entered {num_questions}."
            )

        return num_questions

