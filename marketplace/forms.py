from django import forms
from .models import Listing, ListingImage, Message


class ListingForm(forms.ModelForm):
    class Meta:
        model = Listing
        fields = ['title', 'description', 'price', 'category', 'condition', 'acquisition_source', 'serial_number']
        widgets = {
            'title': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Item title'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 5, 'placeholder': 'Describe your item...'}),
            'price': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'Price in UGX'}),
            'category': forms.Select(attrs={'class': 'form-select'}),
            'condition': forms.Select(attrs={'class': 'form-select'}),
            'acquisition_source': forms.Select(attrs={'class': 'form-select'}),
            'serial_number': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Serial number (optional)'}),
        }

    def clean_price(self):
        price = self.cleaned_data.get('price')
        if price and price <= 0:
            raise forms.ValidationError("Price must be greater than 0.")
        return price


class ListingImageForm(forms.ModelForm):
    class Meta:
        model = ListingImage
        fields = ['image']
        widgets = {
            'image': forms.ClearableFileInput(attrs={'class': 'form-control'}),
        }


ListingImageFormSet = forms.modelformset_factory(
    ListingImage, form=ListingImageForm, extra=5, max_num=5, can_delete=True
)


class MessageForm(forms.ModelForm):
    class Meta:
        model = Message
        fields = ['content']
        widgets = {
            'content': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Type your message...'
            }),
        }
        labels = {'content': ''}


class ListingFilterForm(forms.Form):
    q = forms.CharField(required=False, widget=forms.TextInput(attrs={
        'class': 'form-control', 'placeholder': 'Search listings...'
    }))
    category = forms.CharField(required=False, widget=forms.HiddenInput())
    condition = forms.ChoiceField(
        required=False,
        choices=[('', 'Any Condition')] + Listing.CONDITION_CHOICES,
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    min_price = forms.IntegerField(required=False, widget=forms.NumberInput(attrs={
        'class': 'form-control', 'placeholder': 'Min price'
    }))
    max_price = forms.IntegerField(required=False, widget=forms.NumberInput(attrs={
        'class': 'form-control', 'placeholder': 'Max price'
    }))
    sort = forms.ChoiceField(
        required=False,
        choices=[
            ('-created_at', 'Newest'),
            ('price', 'Price: Low to High'),
            ('-price', 'Price: High to Low'),
            ('-views_count', 'Most Viewed'),
        ],
        widget=forms.Select(attrs={'class': 'form-select'})
    )
