from django import forms
from .models import Order

class OrderForm(forms.ModelForm):
    class Meta:
        model = Order
        fields = ['shipping_address', 'note']
        widgets = {
            'shipping_address': forms.Textarea(attrs={'rows': 3, 'placeholder': 'Full shipping address', 'required': True}),
            'note': forms.TextInput(attrs={'placeholder': 'Note for the seller (optional)'}),
        }