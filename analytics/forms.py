from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
from .models import UserProfile

FC = {'class': 'form-control'}
FS = {'class': 'form-select'}

class SignupForm(UserCreationForm):
    email = forms.EmailField(required=True, widget=forms.EmailInput(attrs=FC))
    role  = forms.ChoiceField(choices=[('analyst', 'Analyst'), ('admin', 'Admin')], widget=forms.Select(attrs=FS))

    class Meta:
        model  = User
        fields = ['username', 'email', 'password1', 'password2', 'role']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for f in ['username', 'password1', 'password2']:
            self.fields[f].widget.attrs.update(FC)

    def save(self, commit=True):
        user = super().save(commit=False)
        user.email = self.cleaned_data['email']
        if commit:
            user.save()
            UserProfile.objects.create(user=user, role=self.cleaned_data['role'])
        return user

class LoginForm(forms.Form):
    username = forms.CharField(widget=forms.TextInput(attrs=FC))
    password = forms.CharField(widget=forms.PasswordInput(attrs=FC))

class CGWBUploadForm(forms.Form):
    MISSING_CHOICES = [
        ('mean',   'Fill Numeric with Mean'),
        ('median', 'Fill Numeric with Median'),
        ('mode',   'Fill Categorical with Mode'),
        ('drop',   'Drop Rows with Missing GW Level'),
    ]
    file             = forms.FileField(widget=forms.FileInput(attrs={'accept': '.csv,.xlsx,.xls', 'class': 'form-control'}))
    missing_strategy = forms.ChoiceField(choices=MISSING_CHOICES, initial='mean', widget=forms.Select(attrs=FS))
    replace_existing = forms.BooleanField(required=False, initial=True,
                                          widget=forms.CheckboxInput(attrs={'class': 'form-check-input'}),
                                          label='Replace existing dataset')
