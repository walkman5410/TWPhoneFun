from django import forms

class TickerForm(forms.Form):
    ticker = forms.CharField(max_length=10)
    
class UploadForm(forms.Form):
    json_file = forms.FileField()
    