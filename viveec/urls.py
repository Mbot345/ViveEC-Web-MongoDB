from django.urls import path
from . import views

urlpatterns = [

    # LOGIN USUARIO
    path('', views.login_usuario, name='login_usuario'),
    
    # LOGIN ARTISTA
    path('login-artista/', views.login_artista, name='login_artista'),
    
    # REGISTRO USUARIO
    path('registro-usuario/', views.registro_usuario, name='registro_usuario'),
    
    # REGISTRO ARTISTA
    path('registro-artista/', views.registro_artista, name='registro_artista'),
    
    # DASHBOARD DE INICIO DE USUARIO
    path('dashboard-usuario/',views.dashboard_usuario,name='dashboard_usuario'),

    # DASHBOARD DE INICIO DE ARTISTA
    path('dashboard-artista/',views.dashboard_artista,name='dashboard_artista'),

    # GESTION DE ALBUMES DEL ARTISTA
    path('gestion-albumes/', views.gestion_albumes, name='gestion_albumes'),
    
    # GESTION DE CANCIONES DEL ARTISTA
    path('gestion-canciones/',views.gestion_canciones,name='gestion_canciones'),

    # GESTION DE CANCIONES DEL ARTISTA SEGUN ALBUM
    path('gestion-canciones/<str:id_album>/', views.gestion_canciones, name='gestion_canciones'),

    # REGALIAS DEL ARTISTA
    path('regalias-artista/', views.regalias_artista, name='regalias_artista'),

    # REPORTES DEL ARTISTA
    path('reportes-artista/', views.reportes_artista, name='reportes_artista'),

    # REPRODUCCION DE UNA CANCION
    path('reproducir/<str:id_cancion>/', views.reproducir_cancion_detalle, name='reproducir_cancion_detalle'),
    
    # LIKE DE UNA CANCION
    path('alternar-like/', views.alternar_like_cancion, name='alternar_like_cancion'),
    
    # REGISTRO DE REPRODUCCION ESPECIFICA
    path('registrar-reproduccion/', views.registrar_reproduccion, name='registrar_reproduccion'),
    
    # ALBUMES DISPONIBLES
    path('descubrir-albumes/', views.descubrir_albumes, name='descubrir_albumes'),

    # DETALLE DE LOS ALBUMES
    path('album/<str:idAlbum>/', views.detalle_album, name='detalle_album'),
    
    # GARDADO DE ALBUMES
    path('toggle-album/', views.toggle_album, name='toggle_album'),

    # DETALLE DE LOS ARTISTAS
    path('artista/<str:idArtista>/', views.detalle_artista, name='detalle_artista'),
    
    # SEGUIMIENTO DE ARTISTAS
    path('toggle-seguir-artista/', views.toggle_seguir_artista, name='toggle_seguir_artista'),

    # BIBLIOTECA DE PLAYLIST DEL USUARIO
    path('biblioteca-usuario/', views.biblioteca_usuario, name='biblioteca_usuario'),

    # DETALLE DE LAS PLAYLIST
    path('playlist/<str:idPlaylist>/', views.playlist_detalle, name='playlist_detalle'),

    # CREACION DE LAS PLAYLIST
    path('crear-playlist/', views.crear_playlist, name='crear_playlist'),

    # GUARDADO DE PLAYLIST
    path('toggle-playlist/', views.toggle_playlist, name='toggle_playlist'),
    
    # BUSQUEDA DE CANCIONES
    path('buscar-canciones/', views.buscar_canciones, name='buscar_canciones'),

    # AGREGAR CANCIONES A LA PLAYLIST
    path('agregar-cancion/', views.agregar_cancion_a_playlist, name='agregar_cancion'),
    
    # ELIMINAR CANCIONES DE LA PLAYLIST
    path('eliminar-cancion/', views.eliminar_cancion, name='eliminar_cancion'),

    # SUSCRIPCIONES DE LOS USUARIOS
    path('suscripcion-usuario/', views.suscripcion_usuario, name='suscripcion_usuario'),

    #REPORTES DE LOS USUAIROS
    path('reportes-usuario/', views.reportes_usuario, name='reportes_usuario'),
]

