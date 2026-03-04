from django import forms
from .models import Client, Expense, Order, OrderWorker, Payment, ServiceType, Worker, NotificationSettings, ClinicSettings


class ClientForm(forms.ModelForm):
    class Meta:
        model = Client
        fields = ['full_name', 'phone', 'notes']
        labels = {'full_name': 'To\'liq ism', 'phone': 'Telefon', 'notes': 'Eslatmalar'}
        widgets = {
            'full_name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'To\'liq ism'}),
            'phone': forms.TextInput(attrs={'class': 'form-control', 'placeholder': '+998 90 123 45 67'}),
            'notes': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'Eslatmalar'}),
        }


class WorkerForm(forms.ModelForm):
    class Meta:
        model = Worker
        fields = ['full_name', 'phone', 'is_active']
        labels = {'full_name': 'To\'liq ism', 'phone': 'Telefon', 'is_active': 'Faol'}
        widgets = {
            'full_name': forms.TextInput(attrs={'class': 'form-control'}),
            'phone': forms.TextInput(attrs={'class': 'form-control'}),
            'is_active': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }


class OrderWorkerForm(forms.ModelForm):
    class Meta:
        model = OrderWorker
        fields = ['worker', 'share_percent']
        labels = {'worker': 'Ishchi', 'share_percent': 'Ulush (%)'}
        widgets = {
            'worker': forms.Select(attrs={'class': 'form-select'}),
            'share_percent': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01', 'min': 0, 'max': 100}),
        }


OrderWorkerFormSet = forms.inlineformset_factory(
    Order,
    OrderWorker,
    form=OrderWorkerForm,
    extra=2,
    can_delete=True,
    max_num=10,
)


class OrderForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['client'].label = 'Mijoz'
        self.fields['description'].label = 'Tavsif'
        self.fields['service_type'].label = 'Xizmat turi'
        self.fields['quantity'].label = 'Miqdori (nechta)'
        self.fields['total_price'].label = 'Umumiy summa'
        self.fields['deadline'].label = 'Tayyor bo\'lish sanasi'
        self.fields['debt_payment_deadline'].label = 'Qarz to\'lov sanasi'

    def clean_total_price(self):
        price = self.cleaned_data.get('total_price')
        if price is not None and price < 0:
            raise forms.ValidationError('Narx manfiy bo\'lmasligi kerak')
        return price

    def clean(self):
        data = super().clean()
        service_type = data.get('service_type')
        quantity = data.get('quantity') or 1
        total = data.get('total_price')
        if service_type and quantity:
            auto_total = service_type.default_price * quantity
            if total is None or total == 0:
                data['total_price'] = auto_total
            else:
                data['total_price'] = total
        return data

    class Meta:
        model = Order
        fields = ['client', 'description', 'service_type', 'quantity', 'total_price', 'deadline', 'debt_payment_deadline']
        widgets = {
            'client': forms.Select(attrs={'class': 'form-select'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'service_type': forms.Select(attrs={'class': 'form-select', 'id': 'id_service_type'}),
            'quantity': forms.NumberInput(attrs={'class': 'form-control', 'min': 1, 'id': 'id_quantity'}),
            'total_price': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01', 'id': 'id_total_price'}),
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
        labels = {
            'amount': 'Summa',
            'payment_date': 'To\'lov sanasi',
            'payment_type': 'To\'lov turi',
            'notes': 'Eslatma',
        }
        widgets = {
            'amount': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'payment_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'payment_type': forms.Select(attrs={'class': 'form-select'}),
            'notes': forms.Textarea(attrs={'class': 'form-control', 'rows': 2}),
        }


class ExpenseForm(forms.ModelForm):
    def clean_amount(self):
        amount = self.cleaned_data.get('amount')
        if amount is not None and amount <= 0:
            raise forms.ValidationError('Summa 0 dan katta bo\'lishi kerak')
        return amount

    class Meta:
        model = Expense
        fields = ['expense_date', 'amount', 'category', 'description']
        labels = {
            'expense_date': 'Sana',
            'amount': 'Summa (so\'m)',
            'category': 'Turi',
            'description': 'Tavsif',
        }
        widgets = {
            'expense_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'amount': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'category': forms.Select(attrs={'class': 'form-select'}),
            'description': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Qisqacha tavsif (ixtiyoriy)'}),
        }


class ServiceTypeForm(forms.ModelForm):
    class Meta:
        model = ServiceType
        fields = ['name', 'default_price']
        labels = {'name': 'Nomi', 'default_price': 'Standart narx (so\'m)'}
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'default_price': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
        }


class NotificationSettingsForm(forms.ModelForm):
    class Meta:
        model = NotificationSettings
        fields = ['telegram_username', 'order_deadline_days', 'debt_reminder_days', 'notify_via_telegram', 'notify_in_system']
        labels = {
            'telegram_username': 'Telegram username',
            'order_deadline_days': 'Zakaz muddati (kun oldin)',
            'debt_reminder_days': 'Qarz eslatmasi (kun oldin)',
            'notify_via_telegram': 'Telegram orqali xabar yuborish',
            'notify_in_system': 'Tizimda ko\'rsatish',
        }
        widgets = {
            'telegram_username': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'username (@ siz)'}),
            'order_deadline_days': forms.NumberInput(attrs={'class': 'form-control'}),
            'debt_reminder_days': forms.NumberInput(attrs={'class': 'form-control'}),
            'notify_via_telegram': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'notify_in_system': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }

    def clean_telegram_username(self):
        value = (self.cleaned_data.get('telegram_username') or '').strip().lstrip('@').lower()
        return value


class ClinicSettingsForm(forms.ModelForm):
    currency = forms.ChoiceField(
        choices=[('UZS', 'UZS'), ('USD', 'USD')],
        widget=forms.Select(attrs={'class': 'form-select'}),
        label='Valyuta'
    )

    class Meta:
        model = ClinicSettings
        fields = ['clinic_name', 'address', 'phone', 'currency']
        labels = {
            'clinic_name': 'Klinika nomi',
            'address': 'Manzil',
            'phone': 'Telefon',
        }
        widgets = {
            'clinic_name': forms.TextInput(attrs={'class': 'form-control'}),
            'address': forms.Textarea(attrs={'class': 'form-control', 'rows': 2}),
            'phone': forms.TextInput(attrs={'class': 'form-control'}),
        }
