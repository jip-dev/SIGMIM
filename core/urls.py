from django.urls import path
from django.contrib.auth import views as auth_views
from core.forms import CustomAuthenticationForm
from core import views


urlpatterns = [
    # Rutas de autenticación
    path('login/', auth_views.LoginView.as_view(
        template_name='registration/login.html',
        authentication_form=CustomAuthenticationForm
    ), name='login'),
    path('logout/', auth_views.LogoutView.as_view(), name='logout'),
    path('restablecer/', views.restablecer_contrasena, name='restablecer'),
    path('cambiar_clave/', views.cambiar_clave, name='cambiar_clave'),
    
    # Rutas para GESTIONA ----------------------------------------------------
    path('MIM/listar', views.MIM_listar, name='MIM_listar'),
    path('MIM/crear', views.MIM_crear, name='MIM_crear'),
    path('MIM/editar/<int:id>/', views.MIM_editar, name='MIM_editar'),
    path('MIM/eliminar/<int:id>/', views.MIM_eliminar, name='MIM_eliminar'),
    path('MIM/pdf/', views.generar_MIM_all, name='generar_MIM_all'),
    
    path('suministros', views.suministros, name='suministros'),
    path('suministro/pdf/<int:suministro_id>/', views.generar_pdf, name='generar_pdf'),
    path('suministro/pdf/', views.generar_pdf_all, name='generar_pdf_all'),
    
    path('solicitudes/solicitud', views.solicitud, name='solicitud'),
    path('solicitudes/d_solicitud/<int:id>/', views.detalle_solicitud, name='detalle_solicitud'),
    path('detalle_despacho/<int:id_dpto>/', views.detalle_despacho, name='detalle_despacho'),    
    path('despacho/pdf/<int:despacho_id>/', views.generate_despacho_pdf, name='generate_despacho_pdf'),
    path('cancelar_solicitud/', views.cancelar_solicitud, name='cancelar_solicitud'),

    # Rutas para ADMINISTRA ---------------------------------------------------
    path('', views.inicio, name='inicio'),
    path('usuarios/listar', views.u_listar, name='u_listar'),
    path('usuarios/crear', views.u_crear, name='u_crear'),
    path('usuarios/editar/<int:id>/', views.u_editar, name='u_editar'),
    path('usuarios/eliminar/<int:id>/', views.u_eliminar, name='u_eliminar'),
    
    path('proveedores/listar', views.pr_listar, name='pr_listar'),
    path('proveedores/crear', views.pr_crear, name='pr_crear'),
    path('proveedores/editar/<int:id>', views.pr_editar, name='pr_editar'),
    path('proveedores/eliminar/<int:id>', views.pr_eliminar, name='pr_eliminar'),
    
    path('departamentos/listar', views.d_listar, name='d_listar'),
    path('departamentos/crear', views.d_crear, name='d_crear'),
    path('departamentos/editar/<int:id>/', views.d_editar, name='d_editar'),
    path('departamentos/eliminar/<int:id>/', views.d_eliminar, name='d_eliminar'),
    
    #Rutas para Reportes ---------------------------------------------------
    path('r_suministros', views.r_suministros, name='r_suministros'),
    path('r_despachos', views.r_despachos, name='r_despachos'),
    
    #Rutas para Catalogo ----------------------------------------------------
    path('categoria/listar', views.c_listar, name='c_listar'),
    path('categoria/crear', views.c_crear, name='c_crear'),
    path('categoria/editar/<int:id>/', views.c_editar, name='c_editar'),
    path('categoria/eliminar/<int:id>/', views.c_eliminar, name='c_eliminar'),
    
    path('formato/listar', views.f_listar, name='f_listar'),
    path('formato/crear', views.f_crear, name='f_crear'),
    path('formato/editar/<int:id>/', views.f_editar, name='f_editar'),
    path('formato/eliminar/<int:id>/', views.f_eliminar, name='f_eliminar'),
    
    path('piso/listar', views.p_listar, name='p_listar'),
    path('piso/crear', views.p_crear, name='p_crear'),
    path('piso/editar/<int:id>/', views.p_editar, name='p_editar'),
    path('piso/eliminar/<int:id>/', views.p_eliminar, name='p_eliminar'),
       
]
