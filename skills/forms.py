from django import forms
from .models import Skill, Booking, Review


class SkillForm(forms.ModelForm):
    class Meta:
        model = Skill
        fields = ['title', 'description', 'category', 'delivery_method', 'min_price', 'max_price',
                  'is_group_session', 'max_group_size', 'portfolio_link']
        widgets = {
            'title': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Skill title'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 5}),
            'category': forms.Select(attrs={'class': 'form-select'}),
            'delivery_method': forms.Select(attrs={'class': 'form-select'}),
            'min_price': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'Min price per session (UGX)'}),
            'max_price': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'Max price per session (UGX)'}),
            'is_group_session': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'max_group_size': forms.NumberInput(attrs={'class': 'form-control'}),
            'portfolio_link': forms.URLInput(attrs={'class': 'form-control', 'placeholder': 'https://...'}),
        }

    def clean(self):
        cleaned = super().clean()
        min_p = cleaned.get('min_price')
        max_p = cleaned.get('max_price')
        if min_p and max_p and min_p > max_p:
            raise forms.ValidationError("Minimum price cannot exceed maximum price.")
        return cleaned


class BookingForm(forms.ModelForm):
    session_date = forms.DateTimeField(
        widget=forms.DateTimeInput(attrs={'class': 'form-control', 'type': 'datetime-local'}),
        input_formats=['%Y-%m-%dT%H:%M']
    )

    class Meta:
        model = Booking
        fields = ['session_date', 'duration_hours', 'agreed_price', 'notes']
        widgets = {
            'duration_hours': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.5', 'min': '0.5'}),
            'agreed_price': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'Agreed price (UGX)'}),
            'notes': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'Any notes or special requirements...'}),
        }


class ReviewForm(forms.ModelForm):
    class Meta:
        model = Review
        fields = ['rating', 'comment']
        widgets = {
            'rating': forms.Select(
                choices=[(i, f"{i} Star{'s' if i > 1 else ''}") for i in range(1, 6)],
                attrs={'class': 'form-select'}
            ),
            'comment': forms.Textarea(attrs={'class': 'form-control', 'rows': 4, 'placeholder': 'Share your experience...'}),
        }


class SkillFilterForm(forms.Form):
    q = forms.CharField(required=False, widget=forms.TextInput(attrs={
        'class': 'form-control', 'placeholder': 'Search skills...'
    }))
    category = forms.CharField(required=False, widget=forms.HiddenInput())
    delivery_method = forms.ChoiceField(
        required=False,
        choices=[('', 'Any Method')] + Skill.DELIVERY_CHOICES,
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    min_price = forms.IntegerField(required=False, widget=forms.NumberInput(attrs={
        'class': 'form-control', 'placeholder': 'Min price'
    }))
    max_price = forms.IntegerField(required=False, widget=forms.NumberInput(attrs={
        'class': 'form-control', 'placeholder': 'Max price'
    }))
