from django.contrib.auth.models import AbstractUser
from django.db import models

class Rol(models.Model):
    IdRol = models.AutoField(primary_key=True)
    Descripcion = models.CharField(max_length=50)

    class Meta:
        db_table = 'Rol'

    def __str__(self):
        return self.Descripcion

class Usuario(AbstractUser):
    username = None  # Elimina el campo username
    Documento = models.CharField(max_length=30, unique=True, verbose_name='Documento')
    email = models.EmailField(unique=True, verbose_name='Correo Electrónico')  # Campo único
    IdRol = models.ForeignKey(Rol, on_delete=models.CASCADE, db_column='IdRol', verbose_name='Rol')
    cambiarClave = models.BooleanField(default=True)

    # Campos que heredamos de AbstractUser, como first_name y last_name
    USERNAME_FIELD = 'email'  # Ahora el correo será el campo principal para iniciar sesión
    REQUIRED_FIELDS = ['first_name', 'last_name', 'Documento', 'IdRol']

    class Meta:
        db_table = 'Usuario'

    def __str__(self):
        return f"{self.first_name} {self.last_name}"


class Categoria(models.Model):
    IdCategoria = models.AutoField(primary_key=True) 
    Descripcion = models.CharField(max_length=50)
    def __str__(self):
        return self.Descripcion

class Formato(models.Model):
    IdFormato = models.AutoField(primary_key=True) 
    Descripcion = models.CharField(max_length=50)
    def __str__(self):
        return self.Descripcion
    
class Mim(models.Model):
    IdMIM = models.AutoField(primary_key=True)  
    IdCategoria = models.ForeignKey(Categoria, on_delete=models.CASCADE, db_column='IdCategoria',verbose_name='Categoría')
    Cod = models.CharField(max_length=50,unique=True,verbose_name='Código')    
    Nombre = models.CharField(max_length=100)
    IdFormato = models.ForeignKey(Formato, on_delete=models.CASCADE, db_column='IdFormato', verbose_name='Formato')    
    Stock = models.IntegerField(default=0)
    Reservado = models.IntegerField(default=0)  # Nuevo campo para stock reservado
    
class Proveedor(models.Model):
    IdProveedor = models.AutoField(primary_key=True)  
    Documento = models.CharField(max_length=50, unique=True, verbose_name='Documento')
    RazonSocial = models.CharField(max_length=100)
    Correo = models.EmailField(max_length=100, unique=True , verbose_name='Correo Electrónico')
    FechaRegistro = models.DateField(auto_now_add=True)

class Suministro(models.Model):
    IdSuministro = models.AutoField(primary_key=True)
    Proveedor = models.ForeignKey(Proveedor, on_delete=models.CASCADE, db_column='IdProveedor')
    Usuario = models.ForeignKey(Usuario, on_delete=models.CASCADE, db_column='IdUsuario', verbose_name='Usuario Registrador')
    Lote = models.CharField(max_length=50)
    FechaRegistro = models.DateField(auto_now_add=True)


class DetalleSuministro(models.Model):
    IdSuministro = models.ForeignKey(Suministro, on_delete=models.CASCADE, db_column='IdSuministro')
    IdMIM = models.ForeignKey(Mim, on_delete=models.CASCADE, db_column='IdMIM')    
    FechaVencimiento = models.DateField(default='2199-12-31', verbose_name='Fecha de Vencimiento')
    Cantidad = models.IntegerField()


class Piso(models.Model):
    IdPiso = models.AutoField(primary_key=True)  
    Descripcion = models.CharField(max_length=50)
    def __str__(self):
        return self.Descripcion

class EstadoDepartamento(models.Model):
    IdEstadoDpto = models.AutoField(primary_key=True)  
    Descripcion = models.CharField(max_length=50)
    def __str__(self):
        return self.Descripcion

class Departamento(models.Model):
    IdDpto = models.AutoField(primary_key=True) 
    Departamento = models.CharField(max_length=100)
    JefeDpto = models.ForeignKey(Usuario, on_delete=models.CASCADE, db_column='IdJefeDpto', verbose_name='Jefe de Departamento')
    Correo = models.EmailField(max_length=100, unique=True , verbose_name='Correo Electrónico')
    IdPiso = models.ForeignKey(Piso, on_delete=models.CASCADE, db_column='IdPiso', verbose_name='Piso')
    IdEstadoDpto = models.ForeignKey(EstadoDepartamento, on_delete=models.CASCADE, db_column='IdEstadoDpto', default=1)
    FechaRegistro = models.DateField(auto_now_add=True)

    def save(self, *args, **kwargs):
        if self.JefeDpto:
            self.Correo = self.JefeDpto.email  # Asigna automáticamente el correo del jefe de departamento
        super().save(*args, **kwargs)


class Solicitud(models.Model):
    IdSolicitud = models.AutoField(primary_key=True)
    IdDpto = models.ForeignKey(Departamento, on_delete=models.CASCADE, db_column='IdDpto')
    Usuario = models.ForeignKey(Usuario, on_delete=models.CASCADE, db_column='IdUsuario', verbose_name='Usuario Registrador')
    FechaRegistro = models.DateField(auto_now_add=True)

class DetalleSolicitud(models.Model):
    IdSolicitud = models.ForeignKey(Solicitud, on_delete=models.CASCADE, db_column='IdSolicitud')
    IdMIM = models.ForeignKey(Mim, on_delete=models.CASCADE, db_column='IdMIM')
    CantidadSolicitada = models.IntegerField()

class Despacho(models.Model):
    IdDespacho = models.AutoField(primary_key=True)
    IdDpto = models.ForeignKey(Departamento, on_delete=models.CASCADE, db_column='IdDpto')
    Usuario = models.ForeignKey(Usuario, on_delete=models.CASCADE, db_column='IdUsuario', verbose_name='Usuario Registrador')
    FechaRegistro = models.DateField(auto_now_add=True)

class DetalleDespacho(models.Model):
    IdDespacho = models.ForeignKey(Despacho, on_delete=models.CASCADE, db_column='IdDespacho')
    IdMIM = models.ForeignKey(Mim, on_delete=models.CASCADE, db_column='IdMIM')
    CantidadEntregada = models.IntegerField()