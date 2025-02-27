from django.shortcuts import render, redirect, get_object_or_404
from django.http import HttpResponse
from .forms import UsuarioForm,MIMForm,ProveedorForm,DepartamentoForm,CatergoriaForm,FormatoForm,PisoForm
from django.contrib.auth.decorators import login_required
from django.contrib.auth.hashers import make_password
from django.contrib import messages
from django.contrib.auth import update_session_auth_hash
from core.decorators import role_required
from .models import Usuario,Mim,Proveedor,Departamento,EstadoDepartamento,Suministro,DetalleSuministro
from .models import Categoria,Formato,Piso,Solicitud,DetalleSolicitud,Despacho, DetalleDespacho
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Image, Paragraph, Spacer
from reportlab.lib.units import inch
from django.conf import settings

import io,os
from django.db import transaction
from django.utils.timezone import now, timedelta

@login_required
def inicio(request):
    user = request.user

    # Obtener estadísticas para el dashboard
    total_mim = Mim.objects.count()
    total_departamentos = Departamento.objects.count()
    dptos_con_solicitud = Departamento.objects.filter(IdEstadoDpto__IdEstadoDpto=2).count()

    context = {
        'user': user,
        'total_mim': total_mim,
        'total_departamentos': total_departamentos,
        'dptos_con_solicitud': dptos_con_solicitud
    }

    return render(request, 'inicio.html', context)


def restablecer_contrasena(request):
    if request.method == 'POST':
        correo = request.POST.get('correo')
        documento = request.POST.get('documento')

        try:
            usuario = Usuario.objects.get(email=correo, Documento=documento)
            usuario.password = make_password('12345678')  # Establecer la contraseña predefinida
            usuario.cambiarClave = True  # Forzar cambio de contraseña
            usuario.save()

            messages.success(request, "Se ha enviado una nueva contraseña. Por favor, cámbiala al iniciar sesión.")
            return redirect('login')
        except Usuario.DoesNotExist:
            messages.error(request, "No se encontró un usuario con ese correo y documento.")
            return redirect('restablecer')

    return render(request, 'registration/restablecer.html')

@login_required
def cambiar_clave(request):
    if request.method == 'POST':
        nueva_clave = request.POST.get('nuevaclave')
        confirmar_clave = request.POST.get('confirmarclave')

        if nueva_clave != confirmar_clave:
            messages.error(request, "Las contraseñas no coinciden.")
            return redirect('cambiar_clave')

        usuario = request.user
        usuario.set_password(nueva_clave)
        usuario.cambiarClave = False
        usuario.save()

        update_session_auth_hash(request, usuario)  # Mantener la sesión activa
        messages.success(request, "Contraseña cambiada exitosamente.")
        return redirect('inicio')

    return render(request, 'registration/cambiar_clave.html')


# Sección de GESTIONA--------------------------------------
@role_required(allowed_roles=['Administrador', 'Supervisor'])
def MIM_listar(request):
    MIM = Mim.objects.all()
    return render(request, 'gestiones/MIM/listar.html', {'MIM':MIM})
@role_required(allowed_roles=['Administrador', 'Supervisor'])
def MIM_crear(request):
    form = MIMForm(request.POST or None)
    if form.is_valid():
        form.save()
        return redirect('MIM_listar')
    return render(request, 'gestiones/MIM/crear.html', {'form':form})
@role_required(allowed_roles=['Administrador'])
def MIM_editar(request, id):
    MIM = Mim.objects.get(IdMIM=id)
    form = MIMForm(request.POST or None, instance=MIM)
    if form.is_valid() and request.POST:
        form.save()
        return redirect('MIM_listar')
    return render(request, 'gestiones/MIM/editar.html', {'form':form})
@role_required(allowed_roles=['Administrador'])
def MIM_eliminar(request, id):
    MIM = Mim.objects.get(IdMIM=id)
    MIM.delete()
    return redirect('MIM_listar')

def generar_MIM_all(request):
    mim_list = Mim.objects.all()

    # Crear un buffer para almacenar el PDF en memoria
    buffer = io.BytesIO()
    p = canvas.Canvas(buffer)

    # Título del reporte
    p.drawString(200, 800, "Reporte Completo de MIM")
    
    y = 760
    for m in mim_list:
        p.drawString(50, y, f"# {m.Cod} - MIM: {m.Nombre} - Categoría: {m.IdCategoria} - Formato: {m.IdFormato} - Stock: {m.Stock}")
        y -= 20
        if y < 50:  # Controlar el salto de página
            p.showPage()
            y = 800

    p.showPage()
    p.save()
    
    # Configurar la respuesta HTTP con el PDF generado
    buffer.seek(0)
    response = HttpResponse(buffer, content_type='application/pdf')
    response['Content-Disposition'] = 'inline; filename="reporte_MIM.pdf"'
    
    return response

@role_required(allowed_roles=['Administrador', 'Supervisor'])
def suministros(request):
    if request.method == 'POST':
        try:
            print(request.POST)  # Verificar los datos enviados
            
            # **1. Crear el Suministro Principal**
            proveedor_id = request.POST.get('proveedor')  # ID del proveedor
            lote = request.POST.get('lote')  # Lote general
            proveedor = Proveedor.objects.get(IdProveedor=proveedor_id)  # Obtener proveedor
            usuario = request.user  # Usuario autenticado (registrador)

            # Crear el registro del suministro principal
            suministro = Suministro.objects.create(
                Proveedor=proveedor,
                Usuario=usuario,
                Lote=lote,
            )

            # **2. Guardar Detalles del Suministro**
            detalle_mim_list = request.POST.getlist('detalle_mim[]')  # Lista de MIM enviados

            for mim_id in detalle_mim_list:
                mim = Mim.objects.get(IdMIM=mim_id)  # Obtener objeto Mim

                # Obtener los valores específicos con prefijos en los nombres
                cantidad = int(request.POST.get(f'cantidad_{mim_id}', 0))
                fecha_vencimiento = request.POST.get(f'fecha_vencimiento_{mim_id}')
                
                if cantidad > 0 and fecha_vencimiento:
                    # Verificar si ya existe el detalle
                    detalle_existente = DetalleSuministro.objects.filter(
                        IdSuministro=suministro,
                        IdMIM=mim,
                        FechaVencimiento=fecha_vencimiento
                    ).first()

                    if detalle_existente:
                        # Si existe, actualizar la cantidad
                        detalle_existente.Cantidad += cantidad
                        detalle_existente.save()
                    else:
                        # Crear nuevo detalle
                        DetalleSuministro.objects.create(
                            IdSuministro=suministro,
                            IdMIM=mim,
                            FechaVencimiento=fecha_vencimiento,
                            Cantidad=cantidad,
                        )

                    # Actualizar stock del MIM
                    mim.Stock += cantidad
                    mim.save()
            
            # Redirigir a la Página Reportes Suministros
            return redirect('r_suministros')

        except Exception as e:
            print(f"Error al procesar el suministro: {e}")  # Mostrar error en consola
            return render(request, 'gestiones/almacen/suministros.html', {
                'proveedores': Proveedor.objects.all(),
                'mim_list': Mim.objects.all(),
                'error': 'Ocurrió un error al guardar el suministro. Verifica los datos e inténtalo nuevamente.'
            })

    # **GET Request: Mostrar Formulario**
    proveedores = Proveedor.objects.all()
    mim_list = Mim.objects.all()

    return render(request, 'gestiones/almacen/suministros.html', {
        'proveedores': proveedores,
        'mim_list': mim_list,
    })

@role_required(allowed_roles=['Administrador', 'Supervisor'])
def generar_pdf(request, suministro_id):
    suministro = Suministro.objects.get(IdSuministro=suministro_id)
    detalles = DetalleSuministro.objects.filter(IdSuministro=suministro)

    # Crear buffer para el PDF
    buffer = io.BytesIO()
    
    # Reducir margen superior
    doc = SimpleDocTemplate(buffer, pagesize=letter, topMargin=0.5 * inch)

    # Estilos base
    styles = getSampleStyleSheet()
    title_style = ParagraphStyle(
        'Title',
        fontName='Helvetica-Bold',
        fontSize=16,
        alignment=1  # Centrado
    )
    normal_style = styles['Normal']

    # Contenido del PDF
    content = []

    # Cargar el logo
    logo_path = os.path.join(settings.BASE_DIR, 'core/static/img/hospital.webp')
    logo = Image(logo_path, 1*inch, 1*inch)  # Tamaño reducido

    # Tabla de ID Reporte (el valor queda debajo)
    reporte_data = [['Reporte NRO:'], [suministro_id]]  # Ahora el ID está en la segunda fila
    reporte_table = Table(reporte_data, colWidths=[1.5*inch])
    reporte_table.setStyle(TableStyle([
        ('GRID', (0, 0), (-1, -1), 1, colors.black),
        ('FONTNAME', (0, 0), (-1, -1), 'Helvetica-Bold'),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('BACKGROUND', (0, 0), (-1, 0), colors.lightgrey),
    ]))

    # Fila con logo a la izquierda, título centrado y tabla ID Reporte a la derecha
    header_table = Table([
        [logo, Paragraph("Reporte de Suministros", title_style), reporte_table]
    ], colWidths=[1.5*inch, 4*inch, 1.5*inch])
    
    header_table.setStyle(TableStyle([
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
    ]))

    content.append(header_table)
    content.append(Spacer(1, 0.1*inch))  # Espacio reducido

    # Información del proveedor, lote y usuario registrador
    content.append(Paragraph(f"<b>Proveedor:</b> {suministro.Proveedor.RazonSocial}", normal_style))
    content.append(Paragraph(f"<b>Lote:</b> {suministro.Lote}", normal_style))
    content.append(Paragraph(f"<b>Usuario Registrador:</b> {suministro.Usuario}", normal_style))
    content.append(Spacer(1, 0.2*inch))  # Espacio reducido

    # Crear tabla para los detalles
    data = [['Código', 'Nombre del Item', 'Cantidad', 'F. Vencimiento']]  # Encabezados

    for detalle in detalles:
        data.append([
            detalle.IdMIM.Cod, 
            detalle.IdMIM.Nombre, 
            str(detalle.Cantidad), 
            detalle.FechaVencimiento.strftime('%d-%m-%Y')
        ])

    table = Table(data, colWidths=[1.5*inch, 3*inch, 1*inch, 1.5*inch])
    table.setStyle(TableStyle([
        ('GRID', (0, 0), (-1, -1), 0.5, colors.black),  # Bordes de la tabla
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),  # Encabezado en negrita
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('BACKGROUND', (0, 0), (-1, 0), colors.lightgrey),
    ]))

    content.append(table)

    # Construir el PDF
    doc.build(content)

    # Enviar respuesta HTTP con el PDF generado
    buffer.seek(0)
    response = HttpResponse(buffer, content_type='application/pdf')
    response['Content-Disposition'] = f'inline; filename="suministro_{suministro_id}.pdf"'

    return response

@role_required(allowed_roles=['Administrador', 'Supervisor'])
def generar_pdf_all(request):
    detalles = DetalleSuministro.objects.all()

    # Crear un buffer para almacenar el PDF en memoria
    buffer = io.BytesIO()
    p = canvas.Canvas(buffer)

    # Título del reporte
    p.drawString(200, 800, "Reporte Completo de Suministros")
    
    y = 760
    for detalle in detalles:
        p.drawString(50, y, f"Lote: {detalle.IdSuministro.Lote} - # {detalle.IdMIM.Cod} - MIM: {detalle.IdMIM.Nombre} - Cant: {detalle.Cantidad} - Vence: {detalle.FechaVencimiento}")
        y -= 20
        if y < 50:  # Controlar el salto de página
            p.showPage()
            y = 800

    p.showPage()
    p.save()
    
    # Configurar la respuesta HTTP con el PDF generado
    buffer.seek(0)
    response = HttpResponse(buffer, content_type='application/pdf')
    response['Content-Disposition'] = 'inline; filename="reporte_suministros.pdf"'
    
    return response



def solicitud(request):
    if request.user.is_authenticated and request.user.IdRol_id == 3:
        return render(request, 'gestiones/solicitudes/u_solicitud.html')
    
    pisos = Piso.objects.all()
    piso_seleccionado = request.GET.get('piso', '0')

    departamentos = Departamento.objects.all()
    if piso_seleccionado != '0':
        departamentos = departamentos.filter(IdPiso=piso_seleccionado)

    return render(request, 'gestiones/solicitudes/solicitud.html', {
        'pisos': pisos,
        'departamentos': departamentos,
        'piso_seleccionado': piso_seleccionado
    })
@login_required
def detalle_solicitud(request, id):
    departamento = get_object_or_404(Departamento, IdDpto=id)
    mim_list = Mim.objects.filter(Stock__gt=0)

    if request.method == 'POST':
        mim_ids = request.POST.getlist('detalle_mim[]')
        cantidades = request.POST.getlist('cantidad[]')

        if not mim_ids or not cantidades:
            messages.error(request, "Debe agregar al menos un MIM para generar la solicitud.")
            return redirect('detalle_solicitud', id=id)

        with transaction.atomic():
            # Crear la solicitud principal
            solicitud = Solicitud.objects.create(
                IdDpto=departamento,
                Usuario=request.user
            )

            mims_reservados = []
            for mim_id, cantidad in zip(mim_ids, cantidades):
                mim = Mim.objects.select_for_update().get(IdMIM=mim_id)
                cantidad = int(cantidad)

                if cantidad > (mim.Stock - mim.Reservado):
                    messages.error(request, f"No hay suficiente stock disponible para {mim.Nombre}.")
                    return redirect('detalle_solicitud', id=id)

                # Guardar el detalle de la solicitud
                DetalleSolicitud.objects.create(
                    IdSolicitud=solicitud,
                    IdMIM=mim,
                    CantidadSolicitada=cantidad
                )

                # Reservar temporalmente el stock
                mim.Reservado += cantidad
                mim.save()

                mims_reservados.append((mim_id, cantidad))

            # Guardar reservas en la sesión
            request.session['mims_reservados'] = mims_reservados

        # Actualizar el estado del departamento a 'SOLICITANDO'
        departamento.IdEstadoDpto = EstadoDepartamento.objects.get(IdEstadoDpto=2)  # Estado SOLICITANDO
        departamento.save()

        messages.success(request, "Solicitud registrada con éxito.")
        return redirect('solicitud')

    return render(request, 'gestiones/solicitudes/detalle_solicitud.html', {
        'departamento': departamento,
        'mim_list': mim_list,
    })


def cancelar_solicitud(request):
    if 'mims_reservados' in request.session:
        for mim_id, cantidad in request.session['mims_reservados']:
            mim = Mim.objects.get(IdMIM=mim_id)
            mim.Reservado -= int(cantidad)  # Liberar stock reservado
            mim.save()

        del request.session['mims_reservados']  # Eliminar reservas de la sesión

    messages.info(request, "Solicitud cancelada y stock restaurado.")
    return redirect('solicitud')

def limpiar_reservas_pendientes():
    tiempo_limite = now() - timedelta(minutes=30)  # Reservas mayores a 30 minutos
    Mims = Mim.objects.filter(updated_at__lt=tiempo_limite, Reservado__gt=0)
    for mim in Mims:
        mim.Stock += mim.Reservado
        mim.Reservado = 0
        mim.save()

@login_required
def detalle_despacho(request, id_dpto):
    departamento = get_object_or_404(Departamento, pk=id_dpto)
    solicitud = Solicitud.objects.filter(IdDpto=departamento).first()
    detalles_solicitud = DetalleSolicitud.objects.filter(IdSolicitud=solicitud) if solicitud else None

    if request.method == "POST":
        with transaction.atomic():
            if 'finalizar' in request.POST:
                if detalles_solicitud and detalles_solicitud.exists():
                    # Crear un nuevo despacho
                    despacho = Despacho.objects.create(
                        IdDpto=departamento,
                        Usuario=request.user
                    )

                    # Actualizar stock y liberar reservados, registrar detalles de despacho
                    for detalle in detalles_solicitud:
                        mim = detalle.IdMIM
                        mim.Stock -= detalle.CantidadSolicitada  # Restar stock real
                        mim.Reservado -= detalle.CantidadSolicitada  # Liberar reservado
                        mim.save()

                        # Crear un nuevo registro en DetalleDespacho
                        DetalleDespacho.objects.create(
                            IdDespacho=despacho,
                            IdMIM=detalle.IdMIM,
                            CantidadEntregada=detalle.CantidadSolicitada
                        )

                    # Cambiar estado del departamento a 'LIBRE'
                    departamento.IdEstadoDpto_id = 1  # Estado 'LIBRE'
                    departamento.save()

                    # Eliminar la solicitud y sus detalles procesados
                    detalles_solicitud.delete()
                    solicitud.delete()

                    messages.success(request, "Despacho finalizado con éxito.")
                    return redirect('generate_despacho_pdf', despacho_id=despacho.IdDespacho)
                else:
                    messages.error(request, "No hay detalles de solicitud para procesar.")

            elif 'cancelar' in request.POST:
                if detalles_solicitud and detalles_solicitud.exists():
                    # Revertir la reserva de stock de cada MIM
                    for detalle in detalles_solicitud:
                        mim = detalle.IdMIM
                        mim.Reservado -= detalle.CantidadSolicitada  # Liberar stock reservado
                        mim.save()

                    # Cancelar la solicitud (eliminar registros de la base de datos)
                    detalles_solicitud.delete()
                    solicitud.delete()
                    departamento.IdEstadoDpto_id = 1  # Estado 'LIBRE'
                    departamento.save()

                    messages.info(request, "Solicitud cancelada y stock restaurado.")
                else:
                    messages.warning(request, "No hay solicitud para cancelar.")

                return redirect('solicitud')

    return render(request, 'gestiones/solicitudes/detalle_despacho.html', {
        'departamento': departamento,
        'solicitud': solicitud,
        'detalles_solicitud': detalles_solicitud
    })


@role_required(allowed_roles=['Administrador', 'Supervisor'])
def generate_despacho_pdf(request, despacho_id):
    despacho = Despacho.objects.get(IdDespacho=despacho_id)
    detalles = DetalleDespacho.objects.filter(IdDespacho=despacho)

    # Crear un buffer para almacenar el PDF en memoria
    buffer = io.BytesIO()
    p = canvas.Canvas(buffer)
    
    # Agregar contenido al PDF
    p.drawString(100, 800, f"Departamento: {despacho.IdDpto.Departamento} - Piso: {despacho.IdDpto.IdPiso}")
    p.drawString(100, 780, f"Usuario Registrador: {despacho.Usuario} - Fecha: {despacho.FechaRegistro}")

    y = 740
    for detalle in detalles:
        p.drawString(100, y, f"# {detalle.IdMIM.Cod} - MIM: {detalle.IdMIM.Nombre} - Cantidad: {detalle.CantidadEntregada}")
        y -= 20

    p.showPage()
    p.save()

    # Configurar la respuesta HTTP con el PDF generado
    buffer.seek(0)
    response = HttpResponse(buffer, content_type='application/pdf')
    response['Content-Disposition'] = f'inline; filename="despacho_{despacho_id}.pdf"'
    
    return response




#Sección de ADMINISTRA -----------------------
#Usuarios
@role_required(allowed_roles=['Administrador'])
def u_listar(request):
    usuarios = Usuario.objects.all()
    return render(request, 'administracion/usuarios/listar.html', {'usuarios': usuarios})
@role_required(allowed_roles=['Administrador'])
def u_crear(request):    
    form = UsuarioForm(request.POST or None)
    if form.is_valid():
        usuario = form.save(commit=False)  # Crear el objeto Usuario sin guardar aún
        usuario.set_password('12345678')  # Establecer la contraseña predefinida cifrada automáticamente
        usuario.save()  # Guardar el usuario en la base de datos
        return redirect('u_listar')  # Redirigir a la lista de usuarios
    return render(request, 'administracion/usuarios/crear.html', {'form': form})
@role_required(allowed_roles=['Administrador'])
def u_editar(request, id):
    usuarios = Usuario.objects.get(id=id)
    form = UsuarioForm(request.POST or None, instance=usuarios)
    if form.is_valid() and request.POST:
        form.save()
        return redirect('u_listar')
    return render(request, 'administracion/usuarios/editar.html', {'form': form})
@role_required(allowed_roles=['Administrador'])
def u_eliminar(request, id):
    usuarios = Usuario.objects.get(id=id)
    usuarios.delete()
    return redirect('u_listar')

#Proveedores
@role_required(allowed_roles=['Administrador'])
def pr_listar(request):
    proveedor = Proveedor.objects.all()
    return render(request, 'administracion/proveedores/listar.html', {'proveedor': proveedor})
@role_required(allowed_roles=['Administrador'])
def pr_crear(request):
    form = ProveedorForm(request.POST or None)
    if form.is_valid():
        form.save()
        return redirect('pr_listar')
    return render(request, 'administracion/proveedores/crear.html', {'form':form})
@role_required(allowed_roles=['Administrador'])
def pr_editar(request, id):
    proveedor = Proveedor.objects.get(IdProveedor=id)
    form = ProveedorForm(request.POST or None, instance=proveedor)
    if form.is_valid() and request.POST:
        form.save()
        return redirect('pr_listar')
    return render(request, 'administracion/proveedores/editar.html', {'form':form})
@role_required(allowed_roles=['Administrador'])
def pr_eliminar(request, id):
    proveedor = Proveedor.objects.get(IdProveedor=id)
    proveedor.delete()
    return redirect('pr_listar')

#Departamentos
@role_required(allowed_roles=['Administrador'])
def d_listar(request):
    departamento = Departamento.objects.all()
    return render(request, 'administracion/departamentos/listar.html', {'departamento': departamento})
@role_required(allowed_roles=['Administrador'])
def d_crear(request):
    if request.method == 'POST':
        form = DepartamentoForm(request.POST)
        if form.is_valid():
            departamento = form.save(commit=False)
            departamento.Correo = departamento.JefeDpto.email  # Asignar correo automáticamente
            departamento.save()
            messages.success(request, 'Departamento registrado con éxito.')
            return redirect('d_listar')
    else:
        form = DepartamentoForm()

    return render(request, 'administracion/departamentos/crear.html', {'form': form})
@role_required(allowed_roles=['Administrador'])
def d_editar(request, id):
    departamento = Departamento.objects.get(IdDpto=id)
    form = DepartamentoForm(request.POST or None, instance=departamento)
    if form.is_valid() and request.POST:
        form.save()
        return redirect('d_listar')
    return render(request, 'administracion/departamentos/editar.html', {'form':form})
@role_required(allowed_roles=['Administrador'])
def d_eliminar(request, id):
    departamento = Departamento.objects.get(IdDpto=id)
    departamento.delete()
    return redirect('d_listar')

#Sección de Reportes -----------------------
@role_required(allowed_roles=['Administrador', 'Supervisor'])
def r_suministros(request):
    suministros = Suministro.objects.all()
    return render(request, 'reportes/r_suministros.html', {'suministros': suministros})

@role_required(allowed_roles=['Administrador', 'Supervisor'])
def r_despachos(request):
    despachos = Despacho.objects.all()
    return render(request, 'reportes/r_despachos.html', {'despachos': despachos})

#Sección de Catálogo -----------------------
@role_required(allowed_roles=['Administrador', 'Supervisor'])
def c_listar(request):
    categoria = Categoria.objects.all()
    return render(request, 'catalogos/categoria/listar.html', {'categoria': categoria})
@role_required(allowed_roles=['Administrador', 'Supervisor'])
def c_crear(request):
    form = CatergoriaForm(request.POST or None)
    if form.is_valid():
        form.save()
        return redirect('c_listar')
    return render(request, 'catalogos/categoria/crear.html', {'form':form})
@role_required(allowed_roles=['Administrador', 'Supervisor'])
def c_editar(request, id):
    categoria = Categoria.objects.get(IdCategoria=id)
    form = CatergoriaForm(request.POST or None, instance=categoria)
    if form.is_valid() and request.POST:
        form.save()
        return redirect('c_listar')
    return render(request, 'catalogos/categoria/editar.html', {'form':form})
@role_required(allowed_roles=['Administrador', 'Supervisor'])
def c_eliminar(request, id):
    categoria = Categoria.objects.get(IdCategoria=id)
    categoria.delete()
    return redirect('c_listar')

@role_required(allowed_roles=['Administrador', 'Supervisor'])
def f_listar(request):
    formato = Formato.objects.all()
    return render(request, 'catalogos/formato/listar.html', {'formato': formato})
@role_required(allowed_roles=['Administrador', 'Supervisor'])
def f_crear(request):
    form = FormatoForm(request.POST or None)
    if form.is_valid():
        form.save()
        return redirect('f_listar')
    return render(request, 'catalogos/formato/crear.html', {'form':form})
@role_required(allowed_roles=['Administrador', 'Supervisor'])
def f_editar(request, id):
    formato = Formato.objects.get(IdFormato=id)
    form = FormatoForm(request.POST or None, instance=formato)
    if form.is_valid() and request.POST:
        form.save()
        return redirect('f_listar')
    return render(request, 'catalogos/formato/editar.html', {'form':form})
@role_required(allowed_roles=['Administrador', 'Supervisor'])
def f_eliminar(request, id):
    formato = Formato.objects.get(IdFormato=id)
    formato.delete()
    return redirect('f_listar')

@role_required(allowed_roles=['Administrador', 'Supervisor'])
def p_listar(request):
    piso = Piso.objects.all()
    return render(request, 'catalogos/piso/listar.html', {'piso': piso})
@role_required(allowed_roles=['Administrador', 'Supervisor'])
def p_crear(request):
    form = PisoForm(request.POST or None)
    if form.is_valid():
        form.save()
        return redirect('p_listar')
    return render(request, 'catalogos/piso/crear.html', {'form':form})
@role_required(allowed_roles=['Administrador', 'Supervisor'])
def p_editar(request, id):
    piso = Piso.objects.get(IdPiso=id)
    form = PisoForm(request.POST or None, instance=piso)
    if form.is_valid() and request.POST:
        form.save()
        return redirect('p_listar')
    return render(request, 'catalogos/piso/editar.html', {'form':form})
@role_required(allowed_roles=['Administrador', 'Supervisor'])
def p_eliminar(request, id):
    piso = Piso.objects.get(IdPiso=id)
    piso.delete()
    return redirect('p_listar')