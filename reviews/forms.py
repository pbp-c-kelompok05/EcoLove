from django import forms
from django.utils.html import conditional_escape
from .models import Comment, Review, Reply

class CommentForm(forms.ModelForm):
    class Meta:
        model = Comment
        fields = ['text']

    def clean_text(self):
        return conditional_escape(self.cleaned_data["text"])

class ReviewForm(CommentForm):
    class Meta(CommentForm.Meta):
        model = Review
        fields = ['text', 'rating']

class ReplyForm(forms.ModelForm):
    class Meta(CommentForm.Meta):
        model = Reply