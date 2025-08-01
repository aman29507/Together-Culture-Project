"""
Forms for Together Culture CRM system.
"""

from django import forms
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from .models import Member, Interest


class MemberRegistrationForm(forms.Form):
    """
    Form for new member registration.
    """
    first_name = forms.CharField(
        max_length=30,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'First Name',
            'required': True
        })
    )
    
    last_name = forms.CharField(
        max_length=30,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Last Name',
            'required': True
        })
    )
    
    email = forms.EmailField(
        widget=forms.EmailInput(attrs={
            'class': 'form-control',
            'placeholder': 'Email Address',
            'required': True
        })
    )
    
    password = forms.CharField(
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': 'Password',
            'required': True
        })
    )
    
    password_confirm = forms.CharField(
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': 'Confirm Password',
            'required': True
        })
    )
    
    bio = forms.CharField(
        widget=forms.Textarea(attrs={
            'class': 'form-control',
            'placeholder': 'Tell us about yourself and your creative journey...',
            'rows': 4,
            'required': True
        }),
        help_text='Share your background, interests, and what brings you to our community.'
    )
    
    phone_number = forms.CharField(
        max_length=20,
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Phone Number (Optional)'
        })
    )
    
    interests = forms.ModelMultipleChoiceField(
        queryset=None,  # Will be set in __init__
        widget=forms.CheckboxSelectMultiple(attrs={
            'class': 'form-check-input'
        }),
        required=True,
        help_text='Select all that apply to your primary interests.'
    )
    
    profile_picture = forms.ImageField(
        required=False,
        widget=forms.FileInput(attrs={
            'class': 'form-control',
            'accept': 'image/*'
        }),
        help_text='Optional profile picture (JPG, PNG, GIF)'
    )
    
    terms_accepted = forms.BooleanField(
        required=True,
        widget=forms.CheckboxInput(attrs={
            'class': 'form-check-input'
        }),
        label='I agree to the Terms and Conditions and Privacy Policy'
    )
    
    def clean_email(self):
        """Validate email is unique."""
        email = self.cleaned_data['email']
        if User.objects.filter(email=email).exists():
            raise ValidationError('An account with this email already exists.')
        return email
    
    def clean_password(self):
        """Allow any password (no restrictions)."""
        password = self.cleaned_data['password']
        # No validation - allow any password
        return password
    
    def clean(self):
        """Validate password confirmation matches."""
        cleaned_data = super().clean()
        password = cleaned_data.get('password')
        password_confirm = cleaned_data.get('password_confirm')
        
        if password and password_confirm:
            if password != password_confirm:
                raise ValidationError('Passwords do not match.')
        
        # Validate at least one interest is selected
        interests = cleaned_data.get('interests')
        if not interests:
            raise ValidationError('Please select at least one interest.')
        
        return cleaned_data

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Set the queryset for interests field
        from .models import Interest
        self.fields['interests'].queryset = Interest.objects.all()


class MemberUpdateForm(forms.ModelForm):
    """
    Form for updating member profile information.
    """
    first_name = forms.CharField(
        max_length=30,
        widget=forms.TextInput(attrs={'class': 'form-control'})
    )
    
    last_name = forms.CharField(
        max_length=30,
        widget=forms.TextInput(attrs={'class': 'form-control'})
    )
    
    email = forms.EmailField(
        widget=forms.EmailInput(attrs={'class': 'form-control'})
    )
    
    class Meta:
        model = Member
        fields = ['bio', 'phone_number', 'profile_picture']
        widgets = {
            'bio': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 4
            }),
            'phone_number': forms.TextInput(attrs={
                'class': 'form-control'
            }),
            'profile_picture': forms.FileInput(attrs={
                'class': 'form-control',
                'accept': 'image/*'
            }),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.instance and self.instance.user:
            self.fields['first_name'].initial = self.instance.user.first_name
            self.fields['last_name'].initial = self.instance.user.last_name
            self.fields['email'].initial = self.instance.user.email
    
    def save(self, commit=True):
        """Save both User and Member data."""
        member = super().save(commit=False)
        
        if commit:
            # Update User fields
            user = member.user
            user.first_name = self.cleaned_data['first_name']
            user.last_name = self.cleaned_data['last_name']
            user.email = self.cleaned_data['email']
            user.save()
            
            # Save Member
            member.save()
        
        return member


class InterestUpdateForm(forms.ModelForm):
    """
    Form for updating member interests (admin only).
    """
    class Meta:
        model = Member
        fields = ['interests']
        widgets = {
            'interests': forms.CheckboxSelectMultiple(attrs={
                'class': 'form-check-input'
            })
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['interests'].help_text = 'Update member interests to track how they evolve in the community.'


class AdminMemberSearchForm(forms.Form):
    """
    Form for admin member search functionality.
    """
    search_query = forms.CharField(
        max_length=100,
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Search by name, email, or bio...',
            'id': 'searchInput'
        })
    )
    
    status_filter = forms.ChoiceField(
        choices=[('', 'All Statuses')],  # Will be set in __init__
        required=False,
        widget=forms.Select(attrs={
            'class': 'form-select'
        })
    )
    
    interest_filter = forms.ModelChoiceField(
        queryset=None,  # Will be set in __init__
        required=False,
        empty_label='All Interests',
        widget=forms.Select(attrs={
            'class': 'form-select'
        })
    )
    
    date_from = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={
            'class': 'form-control',
            'type': 'date'
        }),
        help_text='Filter by application date from'
    )
    
    date_to = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={
            'class': 'form-control',
            'type': 'date'
        }),
        help_text='Filter by application date to'
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Set the queryset for interest_filter field
        from .models import Interest, Member
        self.fields['interest_filter'].queryset = Interest.objects.all()
        # Set the choices for status_filter field
        self.fields['status_filter'].choices = [('', 'All Statuses')] + Member.STATUS_CHOICES


class LoginForm(forms.Form):
    """
    Custom login form.
    """
    email = forms.EmailField(
        widget=forms.EmailInput(attrs={
            'class': 'form-control',
            'placeholder': 'Email Address',
            'required': True,
            'autofocus': True
        })
    )
    
    password = forms.CharField(
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': 'Password',
            'required': True
        })
    )
    
    remember_me = forms.BooleanField(
        required=False,
        widget=forms.CheckboxInput(attrs={
            'class': 'form-check-input'
        }),
        label='Remember me'
    )


class ContactForm(forms.Form):
    """
    Contact form for general inquiries.
    """
    name = forms.CharField(
        max_length=100,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Your Name'
        })
    )
    
    email = forms.EmailField(
        widget=forms.EmailInput(attrs={
            'class': 'form-control',
            'placeholder': 'Your Email'
        })
    )
    
    subject = forms.CharField(
        max_length=200,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Subject'
        })
    )
    
    message = forms.CharField(
        widget=forms.Textarea(attrs={
            'class': 'form-control',
            'placeholder': 'Your Message',
            'rows': 5
        })
    )
    
    def send_email(self):
        """Send contact form email (placeholder for actual implementation)."""
        # Implementation would send email to admins
        pass