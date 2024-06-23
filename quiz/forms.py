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
