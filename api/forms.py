from django import forms
from .models import *


class UploadFileForm(forms.Form):
    file = forms.FileField(
        label="Select a file",
    )
