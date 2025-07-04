from django import forms
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _
from .models import Venta, VentaItem, Producto


# Formulario de Resgistro
class RegistroForm(UserCreationForm):
    first_name = forms.CharField(
        label="Nombre",
        max_length=30, required=True,
        widget=forms.TextInput(attrs={'class': 'form-control'}),
        error_messages={'required': 'El nombre es obligatorio.'}
    )
    last_name = forms.CharField(
        label="Apellidos",
        max_length=30, required=True,
        widget=forms.TextInput(attrs={'class': 'form-control'}),
        error_messages={'required': 'Los apellidos son obligatorios.'}
    )
    email = forms.EmailField(
        label="Correo electrónico",
        max_length=254, required=True,
        widget=forms.EmailInput(attrs={'class': 'form-control'}),
        error_messages={
            'required': 'El correo electrónico es obligatorio.',
            'invalid': 'Introduce un correo electrónico válido.'
        }
    )
    username = forms.CharField(
        label="Nombre de usuario",
        widget=forms.TextInput(attrs={'class': 'form-control'}),
        error_messages={
            'required': 'El nombre de usuario es obligatorio.',
            'unique': 'Este nombre de usuario ya está en uso.'
        }
    )
    password1 = forms.CharField(
        label="Contraseña",
        widget=forms.PasswordInput(attrs={'class': 'form-control'}),
        error_messages={'required': 'La contraseña es obligatoria.'}
    )
    password2 = forms.CharField(
        label="Confirmar contraseña",
        widget=forms.PasswordInput(attrs={'class': 'form-control'}),
        error_messages={'required': 'Debes confirmar la contraseña.'}
    )

    class Meta:
        model = User
        fields = ['first_name', 'last_name', 'username', 'email', 'password1', 'password2']

    def __init__(self, *args, **kwargs):
        super(RegistroForm, self).__init__(*args, **kwargs)
        self.fields['username'].error_messages['unique'] = 'Este nombre de usuario ya está en uso.'
        self.fields['email'].error_messages['invalid'] = 'Introduce un correo electrónico válido.'

    def clean_password2(self):
        password1 = self.cleaned_data.get("password1")
        password2 = self.cleaned_data.get("password2")
        if password1 and password2 and password1 != password2:
            raise ValidationError(_('Las contraseñas no coinciden.'))
        return password2

    def clean_password1(self):
        password1 = self.cleaned_data.get("password1")

        if len(password1) < 8:
            raise forms.ValidationError(_('La contraseña debe tener al menos 8 caracteres.'))

        if password1.lower() == password1:
            raise ValidationError(_('La contraseña es demasiado sencilla. Debe incluir al menos una letra mayúscula.'))

        return password1



# Formulario de inicio de sesión
class LoginForm(AuthenticationForm):
    username = forms.CharField(
        label="Usuario",
        widget=forms.TextInput(attrs={'class': 'form-control'}),
        error_messages={'required': 'El nombre de usuario es obligatorio.'}
    )
    password = forms.CharField(
        label="Contraseña",
        widget=forms.PasswordInput(attrs={'class': 'form-control'}),
        error_messages={'required': 'La contraseña es obligatoria.'}
    )

    error_messages = {
        'invalid_login': _(
            "Usuario o contraseña incorrectos. Por favor, inténtalo de nuevo."
        ),
        'inactive': _("Esta cuenta está inactiva."),
    }
    
    
    
# Formulario para los datos de la venta (forma de pago y código)
class VentaForm(forms.ModelForm):
    class Meta:
        model = Venta
        fields = ['forma_pago', 'codigo_transferencia']
        widgets = {
            'forma_pago': forms.Select(attrs={
                'class': 'form-select',
                'placeholder': 'Seleccione forma de pago'
            }),
            'codigo_transferencia': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Código de transferencia (si aplica)',
            }),
        }

    def __init__(self, *args, **kwargs):
        super(VentaForm, self).__init__(*args, **kwargs)
        self.fields['forma_pago'].label = "Forma de pago"
        self.fields['codigo_transferencia'].label = "Código de transferencia"




# Formulario individual para añadir productos a la venta
class VentaItemForm(forms.ModelForm):
    class Meta:
        model = VentaItem
        fields = ['producto', 'cantidad']
        widgets = {
            'producto': forms.Select(attrs={
                'class': 'form-select',
                'placeholder': 'Seleccione un producto'
            }),
            'cantidad': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': 1,
                'placeholder': 'Cantidad',
            }),
        }

    def __init__(self, *args, **kwargs):
        super(VentaItemForm, self).__init__(*args, **kwargs)
        self.fields['producto'].label = "Producto"
        self.fields['cantidad'].label = "Cantidad"

