from django import forms
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from django.contrib.auth.models import User, Group
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
    FORMA_PAGO_OPCIONES = [
        ('efectivo', 'Efectivo'),
        ('transferencia', 'Transferencia'),
        ('gasto', 'Agregar a gastos'),
    ]

    forma_pago = forms.ChoiceField(
        choices=FORMA_PAGO_OPCIONES,
        widget=forms.Select(attrs={
            'class': 'form-select',
            'placeholder': 'Seleccione forma de pago'
        }),
        label="Forma de pago"
    )

    codigo_transferencia = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Código de transferencia (si aplica)',
        }),
        label="Código de transferencia"
    )

    # Campo motivo para gasto
    motivo_gasto = forms.CharField(
        required=False,
        widget=forms.Textarea(attrs={
            'class': 'form-control',
            'rows': 3,
            'placeholder': 'Especifique el motivo del gasto'
        }),
        label="Motivo del gasto"
    )

    class Meta:
        model = Venta
        fields = ['forma_pago', 'codigo_transferencia', 'motivo_gasto']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def clean(self):
        cleaned_data = super().clean()
        forma_pago = cleaned_data.get("forma_pago")
        codigo = cleaned_data.get("codigo_transferencia")
        motivo_gasto = cleaned_data.get("motivo_gasto")

        # Validaciones existentes
        if forma_pago == "transferencia" and not codigo:
            self.add_error("codigo_transferencia", "Debe ingresar el código de transferencia.")

        # Nueva validación: si se selecciona gasto, debe ingresar motivo
        if forma_pago == "gasto" and not motivo_gasto:
            self.add_error("motivo_gasto", "Debe especificar el motivo del gasto.")
            
            
            

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



# # Formulario para un nuevo gasto 
# class GastoForm(forms.ModelForm):
#     class Meta:
#         model = Gasto
#         fields = ['descripcion']
#         widgets = {
#             'descripcion': forms.Textarea(attrs={
#                 'class': 'form-control',
#                 'rows': 3,
#                 'placeholder': 'Ejemplo: Producto usado para limpieza de la tienda.'
#             })
#         }
#         labels = {
#             'descripcion': 'Motivo del gasto',
#         }