from django import forms
from .models import Client, Order, Payment, ServiceType, NotificationSettings, ClinicSettings


class ClientForm(forms.ModelForm):
    class Meta:
        model = Client
        fields = ['full_name', 'phone', 'notes']
        widgets = {
            'full_name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'To\'liq ism'}),
            'phone': forms.TextInput(attrs={'class': 'form-control', 'placeholder': '+998 90 123 45 67'}),
            'notes': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'Eslatmalar'}),
        }


class OrderForm(forms.ModelForm):
    def clean_total_price(self):
        price = self.cleaned_data.get('total_price')
        if price is not None and price < 0:
            raise forms.ValidationError('Narx manfiy bo\'lmasligi kerak')
        return price

    class Meta:
        model = Order
        fields = ['client', 'description', 'service_type', 'total_price', 'deadline', 'debt_payment_deadline']
        widgets = {
            'client': forms.Select(attrs={'class': 'form-select'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'service_type': forms.Select(attrs={'class': 'form-select'}),
            'total_price': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'deadline': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'debt_payment_deadline': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
        }


class PaymentForm(forms.ModelForm):
    def clean_amount(self):
        amount = self.cleaned_data.get('amount')
        if amount is not None and amount <= 0:
            raise forms.ValidationError('Summa 0 dan katta bo\'lishi kerak')
        return amount

    class Meta:
        model = Payment
        fields = ['amount', 'payment_date', 'payment_type', 'notes']
        widgets = {
            'amount': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'payment_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'payment_type': forms.Select(attrs={'class': 'form-select'}),
            'notes': forms.Textarea(attrs={'class': 'form-control', 'rows': 2}),
        }


class ServiceTypeForm(forms.ModelForm):
    class Meta:
        model = ServiceType
        fields = ['name', 'default_price']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'default_price': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
        }


class NotificationSettingsForm(forms.ModelForm):
    class Meta:
        model = NotificationSettings
        fields = ['order_deadline_days', 'debt_reminder_days', 'notify_via_telegram', 'notify_in_system']
        widgets = {
            'order_deadline_days': forms.NumberInput(attrs={'class': 'form-control'}),
            'debt_reminder_days': forms.NumberInput(attrs={'class': 'form-control'}),
            'notify_via_telegram': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'notify_in_system': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }


class ClinicSettingsForm(forms.ModelForm):
    currency = forms.ChoiceField(
        choices=[('UZS', 'UZS'), ('USD', 'USD')],
        widget=forms.Select(attrs={'class': 'form-select'})
    )

    class Meta:
        model = ClinicSettings
        fields = ['clinic_name', 'address', 'phone', 'currency']
        widgets = {
            'clinic_name': forms.TextInput(attrs={'class': 'form-control'}),
            'address': forms.Textarea(attrs={'class': 'form-control', 'rows': 2}),
            'phone': forms.TextInput(attrs={'class': 'form-control'}),
        }
