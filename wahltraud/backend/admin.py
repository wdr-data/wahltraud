from django.contrib import admin
from django import forms
from .models import Entry, FacebookUser


class EntryModelForm(forms.ModelForm):
    text = forms.CharField(
        required=True, label="Text", widget=forms.Textarea, max_length=640)

    class Meta:
        model = Entry
        fields = '__all__'


class EntryAdmin(admin.ModelAdmin):
    form = EntryModelForm
    date_hierarchy = 'pub_date'
    list_display = ('title', 'short_title', 'pub_date')


admin.site.register(Entry, EntryAdmin)
admin.site.register(FacebookUser)
