from django import forms
from django.contrib.auth.models import User


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

    class Meta:
        model = User  # Specify the model class
        # Fields to include in the form
        fields = ['first_name', 'last_name', 'email']

    def __init__(self, *args, **kwargs):
        user = kwargs.pop('user')
        super(ProfileUpdateForm, self).__init__(*args, **kwargs)
        self.fields['first_name'].initial = user.first_name
        self.fields['last_name'].initial = user.last_name
        self.fields['email'].initial = user.email


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
    num_questions = forms.IntegerField(min_value=1, max_value=10000)

    def __init__(self, *args, **kwargs):
        topics_choices = kwargs.pop('topics_choices', [])
        super().__init__(*args, **kwargs)
        # Add 'Select All' option to the choices
        self.fields['topics'].choices = [
            (self.ALL_TOPICS_OPTION, 'Select All')] + topics_choices
        self.fields['num_questions'].widget.attrs.update(
            {'class': 'form-control'}
        )
        # self.fields['quiz_mode'].widget.attrs.update({'class': 'form-select'})
