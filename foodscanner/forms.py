from django import forms

class ScanForm(forms.Form):
    images = forms.FileField(required=True)