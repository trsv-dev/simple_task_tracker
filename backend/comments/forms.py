from django import forms

from comments.models import Comment, CommentImage


class CommentForm(forms.ModelForm):
    """Форма создания комментария."""

    class Meta:
        model = Comment
        fields = ('text',)

    labels = {
        'text': 'Текст'
    }


class CommentImageForm(forms.ModelForm):
    """Форма прикрепления изображения к комментарию."""

    class Meta:
        model = CommentImage
        fields = ('image',)

        labels = {
            'image': 'Изображение'
        }
