from django.db import migrations
from django.contrib.auth.hashers import make_password

def crear_roles_y_admin(apps, schema_editor):
    Rol = apps.get_model('core', 'Rol')
    Usuario = apps.get_model('core', 'Usuario')
    Categoria = apps.get_model('core', 'Categoria')
    Formato = apps.get_model('core', 'Formato')
    Piso = apps.get_model('core', 'Piso')
    EstadoDepartamento = apps.get_model('core', 'EstadoDepartamento')

    # Crear roles
    admin_rol = Rol.objects.create(IdRol=1, Descripcion='Administrador')
    Rol.objects.create(IdRol=2, Descripcion='Supervisor')
    Rol.objects.create(IdRol=3, Descripcion='Usuario')

    # Crear usuario administrador
    Usuario.objects.create(
        email='admin@test.com',
        first_name='Admin',
        last_name='Test',
        Documento='V12345678',
        IdRol=admin_rol,
        is_staff=True,
        is_superuser=True,
        password=make_password('clave123')
    )

    # Insertar datos en Categoria
    Categoria.objects.bulk_create([
        Categoria(Descripcion='Medicamento'),
        Categoria(Descripcion='Insumo'),
    ])
    
     # Insertar datos en Formato
    Formato.objects.bulk_create([
        Formato(Descripcion='Tableta'),
        Formato(Descripcion='Cápsula'),
        Formato(Descripcion='Líquido'),
        Formato(Descripcion='Paquete'),
        Formato(Descripcion='Caja'),
    ])

    # Insertar datos en Piso
    Piso.objects.bulk_create([
        Piso(Descripcion='Planta'),
        Piso(Descripcion='Primero'),
        Piso(Descripcion='Segundo'),
        Piso(Descripcion='Tercero'),
        Piso(Descripcion='Cuarto'),
        Piso(Descripcion='Quinto'),
    ])
    
    # Insertar datos en Estado_Dpto
    EstadoDepartamento.objects.bulk_create([
        EstadoDepartamento(IdEstadoDpto=1, Descripcion='LIBRE'),
        EstadoDepartamento(IdEstadoDpto=2, Descripcion='SOLICITANDO'),
    ])

class Migration(migrations.Migration):
    dependencies = [
        ('core', '0001_initial'),  # Asegúrate de que sea tu última migración
    ]

    operations = [
        migrations.RunPython(crear_roles_y_admin),
    ]