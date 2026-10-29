from django import forms
from .models import Comment, Review, Reply

class CommentForm(forms.ModelForm):
    class Meta:
        model = Comment
        fields = ['text']

class ReviewForm(CommentForm):
    class Meta(CommentForm.Meta):
        model = Review
        fields = ['text', 'rating']

class ReplyForm(forms.ModelForm):
    class Meta(CommentForm.Meta):
        model = Reply