from django import forms
from .models import Item
from django.core.exceptions import ValidationError
from django.utils.html import strip_tags

class ImageInput(forms.ClearableFileInput):
    template_name = 'widgets/image_input.html'

#karen
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
            'image': ImageInput(
                attrs={
                    'class': 'form-group',
                }
            ),
        }

    def clean_name(self):
        name  = strip_tags(self.cleaned_data["name"]).strip()
        if not name:
            raise ValidationError("Name of item should only be written in normal text")
        return name

    def clean_description(self):
        description = strip_tags(self.cleaned_data["description"]).strip()
        if not description:
            raise ValidationError("Description should only be written in normal text")
        return description