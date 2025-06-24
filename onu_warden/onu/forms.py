from django import forms

class IpForm(forms.Form):
    ip_address = forms.CharField(
        label='IP-адрес',
        max_length=15,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': '192.168.1.1'
        })

    )

    ports = forms.CharField(
        label='Кол-во портов на станции',
        max_length=15,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': '4'
        })
    )
    
    # Новое поле для числового фильтра
    rx_threshold = forms.IntegerField(
        label='Фильтр по Rx Power (dBm)',
        required=False,
        widget=forms.NumberInput(attrs={
            'class': 'form-control',
            'placeholder': 'Введите значение (например, -25)'
        }),
        help_text='Покажет ONT с Rx Power меньше этого значения'
    )


    def clean_ip_address(self):
        ip = self.cleaned_data['ip_address']
        # Простая валидация IP
        parts = ip.split('.')
        if len(parts) != 4 or not all(part.isdigit() for part in parts):
            raise forms.ValidationError("Введите корректный IPv4-адрес")
        return ip