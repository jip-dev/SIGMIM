from django import forms
from django.contrib.auth.forms import AuthenticationForm
from core.models import Usuario,Mim,Proveedor,Departamento,Categoria,Formato,Piso

class CustomAuthenticationForm(AuthenticationForm):
    def confirm_login_allowed(self, user):
        if not user.is_active:
            raise forms.ValidationError(
                "Este usuario está inactivo. Contacta con el administrador.",
                code='inactive',
            )

    error_messages = {
        'invalid_login': (
            "Correo o contraseña incorrectos."
        ),
        'inactive': (
            "Esta cuenta está inactiva."
        ),
    }

class UsuarioForm(forms.ModelForm):
    class Meta:
        model = Usuario
        fields = ['Documento','first_name', 'last_name','email', 'IdRol']
        labels = {
            'first_name': 'Nombres',
            'last_name': 'Apellidos',
        }
        widgets = {
            'first_name': forms.TextInput(attrs={'class': 'form-control', 'autocomplete': 'off'}),
            'last_name': forms.TextInput(attrs={'class': 'form-control', 'autocomplete': 'off'}),
            'email': forms.EmailInput(attrs={'class': 'form-control', 'autocomplete': 'off'}),
            'IdRol': forms.Select(attrs={'class': 'form-control'}),
        }   

class MIMForm(forms.ModelForm):
    class Meta:
        model = Mim
        fields = ['Cod', 'Nombre', 'IdCategoria', 'IdFormato', 'Stock']
        widgets = {
            'Cod': forms.TextInput(attrs={'class': 'form-control'}),
            'Nombre': forms.TextInput(attrs={'class': 'form-control'}),
            'IdCategoria': forms.Select(attrs={'class': 'form-control'}),
            'IdFormato': forms.Select(attrs={'class': 'form-control'}),
            'Stock': forms.NumberInput(attrs={'class': 'form-control'}),
        }

class ProveedorForm(forms.ModelForm):
    class Meta:
        model = Proveedor
        fields = '__all__' 
        widgets = {
            'Documento':forms.TextInput(attrs={'class': 'form-control'}),
            'RazonSocial': forms.TextInput(attrs={'class': 'form-control'}),
            'Correo': forms.EmailInput(attrs={'class': 'form-control'}),
        }

class DepartamentoForm(forms.ModelForm):
    JefeDpto = forms.ModelChoiceField(
        queryset=Usuario.objects.filter(IdRol=3),
        label='Jefe de Departamento',
        widget=forms.Select(attrs={'class': 'form-control'})
    )

    class Meta:
        model = Departamento
        fields = ['JefeDpto','Departamento', 'IdPiso']
        widgets = {
            'Departamento': forms.TextInput(attrs={'class': 'form-control'}),
            'IdPiso': forms.Select(attrs={'class': 'form-control'}),
        }

        
class CatergoriaForm(forms.ModelForm):
    class Meta:
        model = Categoria
        fields = '__all__'
        widgets = {
            'Descripcion': forms.TextInput(attrs={'class': 'form-control'}),
        }
        
class FormatoForm(forms.ModelForm):
    class Meta:
        model = Formato
        fields = '__all__'
        widgets = {
            'Descripcion': forms.TextInput(attrs={'class': 'form-control'}),
        }

class PisoForm(forms.ModelForm):
    class Meta:
        model = Piso
        fields = '__all__'
        widgets = {
            'Descripcion': forms.TextInput(attrs={'class': 'form-control'}),
        }