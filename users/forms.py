from django import forms

class BookingContactForm(forms.Form):
    name = forms.CharField(max_length=100, label="Full Name")
    email = forms.EmailField(label="Email Address")
    phone = forms.CharField(max_length=20, label="Phone Number")
    special_requests = forms.CharField(
        label="Special Requests (optional)",
        widget=forms.Textarea(attrs={
            'rows': 3,
            'placeholder': 'Let us know if you have any special rules, requests, or preferred timings...',
            'class': 'booking-input',  # or 'calendar-input' to match your style!
        }),
        required=False,
        max_length=1000,
    )



class ContactForm(forms.Form):
    name = forms.CharField(max_length=100, label='Your Name')
    email = forms.EmailField(label='Your Email')
    message = forms.CharField(widget=forms.Textarea, label='Message')