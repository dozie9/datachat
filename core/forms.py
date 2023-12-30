from django import forms


class DataUploadForm(forms.Form):
    attachment = forms.FileField()  # Field for file upload


class QueryForm(forms.Form):
    query = forms.CharField(widget=forms.Textarea, label='Your Query')
