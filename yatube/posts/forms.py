from django import forms
from posts.models import Post, Comment


class PostForm(forms.ModelForm):
    class Meta:
        model = Post
        fields = ('text', 'group', 'image',)
        labels = {'text': 'Введите здесь текст своего поста',
                  'group': 'Выберите группу'}
        help_texts = {'text': 'Пишем самое умное здесь',
                      'group': 'Здесь выбираем подходящую группу'}


class CommentForm(forms.ModelForm):
    class Meta:
        model = Comment
        fields = ('text',)

    def clean_text(self):
        data = self.cleaned_data['text']
        if len(data) < 10:
            raise forms.ValidationError(
                'Должно быть напечатано не '
                'менее 10 символов!')
        return data
