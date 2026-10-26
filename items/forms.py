from django import forms
from .models import Item

class ItemForm(forms.ModelForm):
    class Meta:
        model = Item
        fields = ['name', 'price', 'description', 'category', 'image']
        widgets = {
            'name': forms.TextInput(
                attrs={
                    'class': 'form-group', 
                    'placeholder': 'Item Name'
                }
            ),
            'price': forms.NumberInput(
                attrs={
                    'class': 'form-group',
                    'placeholder': 'Price ($)'
                }
            ),
            'description': forms.Textarea(
                attrs={
                    'class': 'form-group', 
                    'rows': 4, 
                    'placeholder': 'Describe your item...'
                }
            ),
            'category': forms.Select(
                attrs={
                    'class': 'form-group'
                }
            ),
            'image': forms.FileInput(
                attrs={
                    'id': 'image-input',
                    'class': 'form-group',
                }
            ),
        }