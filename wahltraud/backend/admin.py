from django.contrib import admin
from django import forms
from .models import Push, FacebookUser, Wiki


class PushModelForm(forms.ModelForm):
    intro_text = forms.CharField(
        required=True, label="Intro-Text", widget=forms.Textarea, max_length=200)
    first_text = forms.CharField(
        required=False, label="Erster Text", widget=forms.Textarea, max_length=600)
    second_text = forms.CharField(
        required=False, label="Zweiter Text", widget=forms.Textarea, max_length=600)
    third_text = forms.CharField(
        required=False, label="Dritter Text", widget=forms.Textarea, max_length=600)

    intro_attachment_id = forms.CharField(
        label='Facebook Attachment ID', help_text="Wird automatisch ausgefüllt", disabled=True,
        required=False)
    first_attachment_id = forms.CharField(
        label='Facebook Attachment ID', help_text="Wird automatisch ausgefüllt", disabled=True,
        required=False)
    second_attachment_id = forms.CharField(
        label='Facebook Attachment ID', help_text="Wird automatisch ausgefüllt", disabled=True,
        required=False)
    third_attachment_id = forms.CharField(
        label='Facebook Attachment ID', help_text="Wird automatisch ausgefüllt", disabled=True,
        required=False)

    delivered = forms.BooleanField(
        label='Versendet?',
        help_text="Wurde der Push bereits vom Bot versendet? Nur relevant für Breaking-News.",
        #disabled=True,
        required=False)

    class Meta:
        model = Push
        fields = '__all__'


class PushAdmin(admin.ModelAdmin):
    form = PushModelForm
    date_hierarchy = 'pub_date'
    list_filter = ['published', 'breaking']
    search_fields = ['headline']
    list_display = ('headline', 'pub_date', 'published', 'breaking')


# Register your models here.
admin.site.register(Push, PushAdmin)
admin.site.register(FacebookUser)
admin.site.register(Wiki)
