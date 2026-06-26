from django.shortcuts import render, redirect
from django.http import HttpResponse 
from django.conf import settings
from pymongo import MongoClient
import random
from bson import ObjectId
from collections import Counter, defaultdict
from datetime import datetime, timedelta
import calendar
import json
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt

client = MongoClient("mongodb+srv://<usuario>:<password>@clusterudla01.5ojogg0.mongodb.net/?appName=ClusterUDLA01") # user: Admin, psswd: UDLA
db = client['NombreBaseDeDatos']  #Nombre: ViveEC

# LOGIN USUARIO
def login_usuario(request):
    if request.method == 'POST':
        correo = request.POST.get('correo')
        password = request.POST.get('password')

        
        usuario = db.Usuario.find_one({
            'correoUsuario': correo,
            'contraseñaUsuario': password
        })

        if usuario:
            
            request.session['usuario_nombre'] = usuario.get('nombreUsuario')
            return redirect('dashboard_usuario') # Usamos el nombre del path
            
        else:
            return render(request, 'viveec/login_usuario.html', {
                'error': 'Correo o contraseña incorrectos'
            })

    return render(request, 'viveec/login_usuario.html')

# LOGIN ARTISTA
def login_artista(request):
    if request.method == 'POST':
        correo = request.POST.get('correo')
        password = request.POST.get('password')

        
        artista = db.Artista.find_one({
            'correoArtista': correo,
            'contraseñaArtista': password
        })

        if artista:
            
            request.session['artista_nombre'] = artista.get('nombreArtista')
            return redirect('dashboard_artista') 
            
        else:
            return render(request, 'viveec/login_artista.html', {
                'error': 'Correo o contraseña incorrectos'
            })

    return render(request, 'viveec/login_artista.html')

# REGISTRO USUARIO
def registro_usuario(request):
    if request.method == 'POST':
        nombre = request.POST.get('nombre')
        correo = request.POST.get('correo')
        password = request.POST.get('password')
        pais = request.POST.get('pais')

        
        if db.Usuario.find_one({'correoUsuario': correo}):
            return render(request, 'viveec/registro_usuario.html', {
                'error': 'El correo ya se encuentra registrado'
            })

        
        ultimo_usuario = db.Usuario.find().sort('_id', -1).limit(1)
        ultimo_usuario = list(ultimo_usuario)

        if ultimo_usuario:
            
            ultimo_id_str = ultimo_usuario[0].get('_id')
            numero = int(ultimo_id_str[1:])
            nuevo_id = f'U{numero + 1:03}'
        else:
            nuevo_id = 'U001'

        
        nuevo_usuario = {
            '_id': nuevo_id,           
            'nombreUsuario': nombre,
            'correoUsuario': correo,
            'contraseñaUsuario': password,
            'pais': pais,
            'likes': [],               
            'albumesGuardados': [],
            'ArtistasSeguidos': []
        }
        
        db.Usuario.insert_one(nuevo_usuario)
        print(f"DEBUG: Registro guardado en: {client.address}")

        return render(request, 'viveec/registro_usuario.html', {'registro_exitoso': True})

    return render(request, 'viveec/registro_usuario.html')

def registro_artista(request):
    
    discograficas_cursor = db.Discografica.find({})
    discograficas = []
    for d in discograficas_cursor:
        discograficas.append({
            'id': d['_id'],
            'nombre': d['nombreDiscografica']
        })

    if request.method == 'POST':
        nombre = request.POST.get('nombre')
        correo = request.POST.get('correo')
        password = request.POST.get('password')
        discografica_id = request.POST.get('discografica_id') or None

        
        if db.Artista.find_one({'correoArtista': correo}):
            return render(request, 'viveec/registro_artista.html', {
                'error': 'El correo ya se encuentra registrado',
                'discograficas': discograficas
            })

        
        ultimo_artista = db.Artista.find().sort('_id', -1).limit(1)
        ultimo_artista = list(ultimo_artista)

        if ultimo_artista:
            ultimo_id_str = ultimo_artista[0].get('_id')
            numero = int(ultimo_id_str[1:])
            nuevo_id = f'A{numero + 1:03}'
        else:
            nuevo_id = 'A001'

        
        nuevo_artista = {
            '_id': nuevo_id,
            'nombreArtista': nombre,
            'correoArtista': correo,
            'contraseñaArtista': password,
            'discografica_id': discografica_id
        }
        
        db.Artista.insert_one(nuevo_artista)

        return render(request, 'viveec/registro_artista.html', {
            'registro_exitoso': True, 
            'discograficas': discograficas
        })

    return render(request, 'viveec/registro_artista.html', {'discograficas': discograficas})

def dashboard_usuario(request):
    nombre_usuario = request.session.get('usuario_nombre')
    if not nombre_usuario:
        return redirect('/login-usuario/')

    usuario = db.Usuario.find_one({'nombreUsuario': nombre_usuario})
    if not usuario:
        return redirect('/login-usuario/')

    
    ids_albumes = usuario.get('albumesGuardados', [])
    pipeline_albumes = [
        {'$match': {'_id': {'$in': ids_albumes}}},
        {'$lookup': {'from': 'Artista', 'localField': 'artista_id', 'foreignField': '_id', 'as': 'artista_info'}},
        {'$unwind': {'path': '$artista_info', 'preserveNullAndEmptyArrays': True}}
    ]
    albumes_guardados = [
        {
            'id_album': a['_id'],
            'nombre_album': a.get('nombreAlbum'),
            'artista': a.get('artista_info', {}).get('nombreArtista', 'Desconocido')
        } for a in db.Album.aggregate(pipeline_albumes)
    ]

    
    ids_artistas = usuario.get('ArtistasSeguidos', [])
    artistas_favoritos = [
        {'id_artista': art['_id'], 'nombre_artista': art['nombreArtista']} 
        for art in db.Artista.find({'_id': {'$in': ids_artistas}})
    ]

    
    reproducciones = list(db.Reproduccion.find({'usuario_id': usuario['_id']}))
    ids_escuchados = [r.get('cancion_id') for r in reproducciones]

    generos_favoritos = {}
    albumes_con_historial = db.Album.find({'canciones.id_cancion': {'$in': ids_escuchados}})
    
    for alb in albumes_con_historial:
        for cancion in alb.get('canciones', []):
            if cancion.get('id_cancion') in ids_escuchados:
                for gen in cancion.get('generos', []):
                    generos_favoritos[gen] = generos_favoritos.get(gen, 0) + 1
    
    generos_top = sorted(generos_favoritos, key=generos_favoritos.get, reverse=True)[:3]

    
    recomendaciones = []
    if generos_top:
        pipeline_rec = [
            {'$match': {'canciones.generos': {'$in': generos_top}}},
            {'$unwind': '$canciones'},
            {'$match': {
                'canciones.generos': {'$in': generos_top},
                'canciones.id_cancion': {'$nin': ids_escuchados}
            }},
            {'$lookup': {'from': 'Artista', 'localField': 'artista_id', 'foreignField': '_id', 'as': 'artista_info'}},
            {'$unwind': '$artista_info'},
            {'$limit': 5}
        ]
        
        for item in db.Album.aggregate(pipeline_rec):
            recomendaciones.append({
                'idCancion': item['canciones'].get('id_cancion'),
                'Recomendacion': item['canciones'].get('nombreCancion'),
                'Artista': item['artista_info'].get('nombreArtista', 'Desconocido')
            })

    return render(request, 'viveec/dashboard_usuario.html', {
        'nombre': nombre_usuario,
        'recomendaciones': recomendaciones,
        'albumes': albumes_guardados,
        'artistas': artistas_favoritos
    })
    
# DASHBOARD ARTISTAS
def dashboard_artista(request):
    nombre_artista = request.session.get('artista_nombre')
    
    artista = db.Artista.find_one({'nombreArtista': nombre_artista})
    
    if not artista:
        return redirect('/login-artista/')
    
    id_artista = artista['_id']

    total_seguidores = db.Usuario.count_documents({'ArtistasSeguidos': id_artista})

    albumes_artista = list(db.Album.find({'artista_id': id_artista}))
    total_albumes = len(albumes_artista)
    
    total_canciones = 0
    for alb in albumes_artista:
        total_canciones += len(alb.get('canciones', []))

    return render(request, 'viveec/dashboard_artista.html', {
        'nombre': nombre_artista,
        'total_seguidores': total_seguidores,
        'total_albumes': total_albumes,
        'total_canciones': total_canciones
    })

def gestion_albumes(request):
    nombre_artista = request.session.get('artista_nombre')
    artista = db.Artista.find_one({'nombreArtista': nombre_artista})
    
    if not artista:
        return redirect('/login-artista/')

    error_formulario = None

    if request.method == 'POST':
        accion = request.POST.get('accion')

        try:
            if accion == 'agregar':
                
                total_albumes = db.Album.count_documents({})
                nuevo_id_formateado = f"AL{total_albumes + 1:02d}"
                
                nuevo_album = {
                    '_id': nuevo_id_formateado, 
                    'artista_id': artista['_id'],
                    'nombreAlbum': request.POST.get('nombreAlbum'),
                    'fechaLanzamientoAlbum': request.POST.get('fechaLanzamiento'),
                    'canciones': [] 
                }
                db.Album.insert_one(nuevo_album)

            elif accion == 'editar':
                id_album = request.POST.get('idAlbum')
                db.Album.update_one(
                    {'_id': id_album},
                    {'$set': {
                        'nombreAlbum': request.POST.get('nombreAlbum'),
                        'fechaLanzamientoAlbum': request.POST.get('fechaLanzamiento')
                    }}
                )

            elif accion == 'eliminar':
                id_album = request.POST.get('idAlbum')
                db.Album.delete_one({'_id': id_album})
        
        except Exception as e:
            error_formulario = f"Error al procesar: {str(e)}"
        
        if not error_formulario:
            return redirect('/gestion-albumes/')

    # LISTADO
    albumes_cursor = db.Album.find({'artista_id': artista['_id']})
    albumes = []
    for alb in albumes_cursor:
        fecha_raw = alb.get('fechaLanzamientoAlbum', '')
        albumes.append({
            'id_album': str(alb['_id']),
            'nombreAlbum': alb.get('nombreAlbum'),
            'fecha_completa': fecha_raw,
            'anio_album': fecha_raw[:4] if fecha_raw else '',
            'total_canciones': len(alb.get('canciones', []))
        })

    return render(request, 'viveec/gestion_albumes.html', {
        'albumes': albumes,
        'nombre': nombre_artista,
        'error_formulario': error_formulario
    })


def gestion_canciones(request, id_album):
    nombre_artista = request.session.get('artista_nombre')
    if not nombre_artista:
        return redirect('/login-artista/')

    error_formulario = None
    
    
    if request.method == 'POST':
        accion = request.POST.get('accion')
        try:
            if accion == 'agregar':
                
                todos_los_albumes = db.Album.find()
                max_id = 0
                for alb in todos_los_albumes:
                    for c in alb.get('canciones', []):
                        id_c = c.get('id_cancion', 'C000')
                        try:
                            num = int(id_c[1:]) 
                            if num > max_id:
                                max_id = num
                        except:
                            continue
                
                nuevo_id = f"C{max_id + 1:03d}"
                # -------------------------------------------------------

                nueva_cancion = {
                    'id_cancion': nuevo_id,
                    'nombreCancion': request.POST.get('nombre'),
                    'duracionCancion': int(request.POST.get('duracion', 0)),
                    'fechaLanzamientoCancion': request.POST.get('fechaLanzamiento'),
                    'calidadAudio': request.POST.get('calidad'),
                    'estadoCancion': request.POST.get('estado'),
                    'generos': [request.POST.get('genero')] 
                }
                db.Album.update_one({'_id': id_album}, {'$push': {'canciones': nueva_cancion}})

            elif accion == 'editar':
                id_canc = request.POST.get('idCancion')
                db.Album.update_one(
                    {'_id': id_album, 'canciones.id_cancion': id_canc},
                    {'$set': {
                        'canciones.$.nombreCancion': request.POST.get('nombre'),
                        'canciones.$.duracionCancion': int(request.POST.get('duracion', 0)),
                        'canciones.$.fechaLanzamientoCancion': request.POST.get('fechaLanzamiento'),
                        'canciones.$.calidadAudio': request.POST.get('calidad'),
                        'canciones.$.estadoCancion': request.POST.get('estado'),
                        'canciones.$.generos': [request.POST.get('genero')]
                    }}
                )

            elif accion == 'eliminar':
                id_canc = request.POST.get('idCancion')
                db.Album.update_one({'_id': id_album}, {'$pull': {'canciones': {'id_cancion': id_canc}}})
            
            return redirect(f'/gestion-canciones/{id_album}/')
        except Exception as e:
            error_formulario = str(e)

    # --- PREPARACIÓN DE DATOS PARA RENDER ---
    album = db.Album.find_one({'_id': id_album})
    if not album:
        return redirect('/gestion-albumes/')

    mapa_generos = {g['_id']: g['nombreGenero'] for g in db.Genero.find()}
    lista_canciones = album.get('canciones', [])
    canciones_render = []

    for c in lista_canciones:
        id_cancion = c.get('id_cancion')
        id_gen = c.get('generos', [None])[0]
        
        
        total_reps = db.Reproduccion.count_documents({'cancion_id': id_cancion})
        
        canciones_render.append({
            'id': id_cancion,
            'nombre': c.get('nombreCancion'),
            'duracion': c.get('duracionCancion'),
            'fecha': c.get('fechaLanzamientoCancion'),
            'calidad': c.get('calidadAudio'),
            'estado': c.get('estadoCancion'),
            'genero_nombre': mapa_generos.get(id_gen, "Sin género"),
            'genero_id': id_gen,
            'reproducciones': total_reps
        })

    generos_render = [{'id': g['_id'], 'nombre': g['nombreGenero']} for g in db.Genero.find()]

    return render(request, 'viveec/gestion_canciones.html', {
        'canciones': canciones_render,
        'info_album': [album.get('nombreAlbum'), album.get('fechaLanzamientoAlbum', '')[:4]],
        'id_album': id_album,
        'nombre': nombre_artista,
        'error_formulario': error_formulario,
        'generos_disponibles': generos_render
    })

def regalias_artista(request):
    nombre_artista = request.session.get('artista_nombre')
    artista = db.Artista.find_one({'nombreArtista': nombre_artista})
    
    if not artista:
        return redirect('/login-artista/')
    
    id_artista = artista['_id']
    
    
    db.Regalia.delete_many({'artista_id': id_artista})

    hoy = datetime.now()
    str_inicio = hoy.replace(day=1).strftime('%Y-%m-%d')
    ultimo_dia = calendar.monthrange(hoy.year, hoy.month)[1]
    str_fin = hoy.replace(day=ultimo_dia).strftime('%Y-%m-%d')

    try:
        
        albumes = list(db.Album.find({'$or': [{'idArtista': id_artista}, {'artista_id': id_artista}]}))
        ids_canciones = [c.get('id_cancion') for alb in albumes for c in alb.get('canciones', [])]

        
        total_reps = db.Reproduccion.count_documents({
            'cancion_id': {'$in': ids_canciones},
            'fechaReproduccion': {'$gte': str_inicio, '$lte': str_fin}
        })

        
        if total_reps > 0:
            
            ultimo_r = db.Regalia.find().sort([('_id', -1)]).limit(1)
            ultimo_r = list(ultimo_r)
            
            if ultimo_r and isinstance(ultimo_r[0].get('_id'), str) and ultimo_r[0]['_id'].startswith('R'):
                num = int(ultimo_r[0]['_id'][1:]) + 1
            else:
                num = 1
            nuevo_id = f"R{num:03d}"
            
            db.Regalia.insert_one({
                '_id': nuevo_id,
                'idRegalia': nuevo_id,
                'artista_id': id_artista,
                'fechaInicio': str_inicio,
                'fechaFin': str_fin,
                'totalReproducciones': total_reps,
                'montoTotal': total_reps * 0.05,
                'fechaPago': hoy.strftime('%Y-%m-%d')
            })
            
    except Exception as e:
        print(f"DEBUG ERROR: {e}")

    
    regalias_db = list(db.Regalia.find({'artista_id': id_artista}).sort([('fechaInicio', -1)]))
    
    return render(request, 'viveec/regalias_artista.html', {
        'nombre': nombre_artista,
        'regalias': regalias_db,
        'total_ganado': sum(r.get('montoTotal', 0) for r in regalias_db),
        'total_reproducciones': sum(r.get('totalReproducciones', 0) for r in regalias_db)
    })

# REPORTES ARTISTA 
def reportes_artista(request):
    nombre_artista = request.session.get('artista_nombre')
    if not nombre_artista:
        return redirect('/login-artista/')

    artista = db.Artista.find_one({'nombreArtista': nombre_artista})
    if not artista:
        return redirect('/login-artista/')

    id_artista = artista['_id']

    
    albumes_artista = list(db.Album.find({'artista_id': id_artista}))

    mapa_canciones = {}  
    ids_canciones = []
    for alb in albumes_artista:
        for c in alb.get('canciones', []):
            id_c = c.get('id_cancion')
            mapa_canciones[id_c] = c.get('nombreCancion')
            ids_canciones.append(id_c)

    
    datos_reproducciones = []
    datos_top_canciones = []
    oyentes_mensuales = 0
    pais_mas_escuchado = "N/A"
    oyentes_pais = 0
    lista_canciones_nombres = []
    lista_canciones_repros = []

    if ids_canciones:
        
        reproducciones = list(db.Reproduccion.find({'cancion_id': {'$in': ids_canciones}}))

        
        conteo_por_cancion = Counter(r.get('cancion_id') for r in reproducciones)

        for id_c, nombre_c in mapa_canciones.items():
            total = conteo_por_cancion.get(id_c, 0)
            datos_reproducciones.append((nombre_c, total))
            lista_canciones_nombres.append(nombre_c)
            lista_canciones_repros.append(total)

        
        top3 = sorted(datos_reproducciones, key=lambda x: x[1], reverse=True)[:3]
        datos_top_canciones = [{'nombre': nombre, 'total': total} for nombre, total in top3]

        
        hoy = datetime.now()
        usuarios_mes = set()
        for r in reproducciones:
            fecha_str = r.get('fechaReproduccion')  
            if not fecha_str:
                continue
            try:
                fecha = datetime.strptime(fecha_str, '%Y-%m-%d')
            except ValueError:
                continue
            if fecha.month == hoy.month and fecha.year == hoy.year:
                usuarios_mes.add(r.get('usuario_id'))
        oyentes_mensuales = len(usuarios_mes)

        
        usuarios_por_pais = defaultdict(set)
        for r in reproducciones:
            pais = r.get('paisReproduccion')
            usuarios_por_pais[pais].add(r.get('usuario_id'))

        if usuarios_por_pais:
            pais_top = max(usuarios_por_pais.items(), key=lambda x: len(x[1]))
            pais_mas_escuchado = pais_top[0]
            oyentes_pais = len(pais_top[1])

    return render(request, 'viveec/reportes_artista.html', {
        'nombre': nombre_artista,
        'datos_reproducciones': datos_reproducciones,
        'datos_top_canciones': datos_top_canciones,
        'oyentes_mensuales': oyentes_mensuales,
        'pais_mas_escuchado': pais_mas_escuchado,
        'oyentes_pais': oyentes_pais,

        'lista_canciones_nombres': lista_canciones_nombres,
        'lista_canciones_repros': lista_canciones_repros,
    })

@csrf_exempt
def reproducir_cancion_detalle(request, id_cancion):
    nombre_usuario = request.session.get('usuario_nombre')
    if not nombre_usuario:
        return redirect('/login-usuario/')
    
    
    usuario = db.Usuario.find_one({'nombreUsuario': nombre_usuario})
    if not usuario:
        return redirect('/dashboard-usuario/')
    
    
    cancion_info = None
    album = db.Album.find_one({'canciones.id_cancion': id_cancion})
    
    if album:
        cancion_data = next((c for c in album['canciones'] if c['id_cancion'] == id_cancion), None)
        if cancion_data:
            artista = db.Artista.find_one({'_id': album['artista_id']})
            cancion_info = {
                'id': id_cancion,
                'nombre': cancion_data['nombreCancion'],
                'artista': artista['nombreArtista'] if artista else "Desconocido",
                'duracion': cancion_data['duracionCancion']
            }

    if not cancion_info:
        return redirect('/dashboard-usuario/')

    
    lista_likes = usuario.get('likes', [])
    esta_en_array = id_cancion in lista_likes
    
    
    en_coleccion = db.LikeCancion.find_one({'idCancion': id_cancion, 'idUsuario': usuario['_id']}) is not None
    
    
    tiene_like = esta_en_array or en_coleccion

    return render(request, 'viveec/reproductor_detalle.html', {
        'cancion': cancion_info,
        'nombre_usuario': nombre_usuario,
        'tiene_like': tiene_like
    })

@csrf_exempt
def alternar_like_cancion(request):
    if request.method == 'POST':
        nombre_usuario = request.session.get('usuario_nombre')
        data = json.loads(request.body)
        id_cancion = data.get('idCancion')
        
        # 1. Buscar al usuario
        usuario = db.Usuario.find_one({'nombreUsuario': nombre_usuario})
        if not usuario:
            return JsonResponse({'status': 'error', 'message': 'No autenticado'}, status=401)
            
        uid = usuario['_id']
        
        
        if 'likes' in usuario and id_cancion in usuario['likes']:
            
            db.Usuario.update_one({'_id': uid}, {'$pull': {'likes': id_cancion}})
            estado = 'removido'
        else:
            
            db.Usuario.update_one({'_id': uid}, {'$push': {'likes': id_cancion}})
            estado = 'agregado'
            
        return JsonResponse({'status': 'success', 'estado': estado})
    
@csrf_exempt
def registrar_reproduccion(request):
    if request.method == 'POST':
        nombre_usuario = request.session.get('usuario_nombre')
        data = json.loads(request.body)
        
        usuario = db.Usuario.find_one({'nombreUsuario': nombre_usuario})
        
        
        db.Reproduccion.insert_one({
            'cancion_id': data.get('idCancion'),
            'usuario_id': usuario['_id'],
            'paisReproduccion': usuario.get('pais', 'N/A'),
            'duracionReproduccion': int(data.get('tiempo')), 
            'fechaReproduccion': datetime.now().strftime('%Y-%m-%d')
        })
        
        return JsonResponse({'status': 'success'})

def descubrir_albumes(request):
    nombre_usuario = request.session.get('usuario_nombre')
    if not nombre_usuario: 
        return redirect('/login-usuario/')

    
    pipeline = [
        {
            "$lookup": {
                "from": "Artista",          
                "localField": "artista_id", 
                "foreignField": "_id",      
                "as": "artista_info"        
            }
        },
        {
            "$unwind": {
                "path": "$artista_info",
                "preserveNullAndEmptyArrays": True 
            }
        }
    ]

    
    resultado = list(db.Album.aggregate(pipeline))

   
    albumes = [
        {
            'idAlbum': alb.get('_id'),
            'nombre': alb.get('nombreAlbum'),
            'artista': {'nombre': alb.get('artista_info', {}).get('nombreArtista', "Desconocido")}
        } for alb in resultado
    ]
        
    
    cursor_artistas = db.Artista.find()
    artistas = [{'id': art.get('_id'), 'nombre': art.get('nombreArtista')} for art in cursor_artistas]
        
    return render(request, 'viveec/descubrir.html', {
        'albumes': albumes,
        'artistas': artistas,
        'nombre': nombre_usuario
    })

def detalle_album(request, idAlbum):
    nombre_usuario = request.session.get('usuario_nombre')
    if not nombre_usuario: return redirect('/login-usuario/')
    
    usuario = db.Usuario.find_one({'nombreUsuario': nombre_usuario})
    
    
    pipeline = [
        {'$match': {'_id': idAlbum}},
        {'$lookup': {'from': 'Artista', 'localField': 'artista_id', 'foreignField': '_id', 'as': 'artista_info'}},
        {'$unwind': {'path': '$artista_info', 'preserveNullAndEmptyArrays': True}}
    ]
    album = list(db.Album.aggregate(pipeline))
    if not album: return redirect('/dashboard-usuario/')
    
    alb = album[0]
    info_album = [
        alb.get('nombreAlbum'), 
        alb.get('artista_info', {}).get('nombreArtista', 'Desconocido'),
        alb.get('fechaLanzamientoAlbum', 'N/A')[:4],
        alb.get('_id')
    ]
    
    
    canciones_procesadas = [
        {
            'id': c.get('id_cancion'), 
            'nombre': c.get('nombreCancion'), 
            'duracion': f"{int(c.get('duracionCancion', 0))//60}:{int(c.get('duracionCancion', 0))%60:02d}"
        } 
        for c in alb.get('canciones', [])
    ]
    
    
    ya_agregado = idAlbum in usuario.get('albumesGuardados', [])
    
    return render(request, 'viveec/detalle_album.html', {
        'info_album': info_album, 
        'canciones': canciones_procesadas,
        'idAlbum': idAlbum,
        'ya_agregado': ya_agregado
    })

@csrf_exempt
def toggle_album(request):
    data = json.loads(request.body)
    id_album = data.get('idAlbum')
    nombre_usuario = request.session.get('usuario_nombre')
    
    usuario = db.Usuario.find_one({'nombreUsuario': nombre_usuario})
    if not usuario:
        return JsonResponse({'error': 'No autenticado'}, status=401)
    
    uid = usuario['_id']
    lista_guardados = usuario.get('albumesGuardados', [])
    
    if id_album in lista_guardados:
        # Remover
        db.Usuario.update_one({'_id': uid}, {'$pull': {'albumesGuardados': id_album}})
        estado = 'removido'
    else:
        # Agregar
        db.Usuario.update_one({'_id': uid}, {'$push': {'albumesGuardados': id_album}})
        estado = 'agregado'
        
    return JsonResponse({'estado': estado})

def detalle_artista(request, idArtista):
    nombre_usuario = request.session.get('usuario_nombre')
    if not nombre_usuario: return redirect('/login-usuario/')
    
    
    artista = db.Artista.find_one({'_id': idArtista})
    if not artista: return redirect('/dashboard-usuario/')
    
    
    usuario = db.Usuario.find_one({'nombreUsuario': nombre_usuario})
    
    
    lista_seguidos = usuario.get('ArtistasSeguidos', [])
    ya_sigue = idArtista in lista_seguidos

    return render(request, 'viveec/detalle_artista.html', {
        'artista': {'id': artista['_id'], 'nombre': artista['nombreArtista']},
        'ya_sigue': ya_sigue
    })

@csrf_exempt
def toggle_seguir_artista(request):
    data = json.loads(request.body)
    id_artista = data.get('idArtista')
    nombre_usuario = request.session.get('usuario_nombre')
    
    usuario = db.Usuario.find_one({'nombreUsuario': nombre_usuario})
    if not usuario:
        return JsonResponse({'error': 'No autenticado'}, status=401)
    
    uid = usuario['_id']
    lista_seguidos = usuario.get('ArtistasSeguidos', [])
    
    if id_artista in lista_seguidos:
        
        db.Usuario.update_one({'_id': uid}, {'$pull': {'ArtistasSeguidos': id_artista}})
        estado = 'no_seguido'
    else:
        
        db.Usuario.update_one({'_id': uid}, {'$push': {'ArtistasSeguidos': id_artista}})
        estado = 'seguido'
        
    return JsonResponse({'estado': estado})

def biblioteca_usuario(request):
    nombre_usuario = request.session.get('usuario_nombre')
    
    if not nombre_usuario:
        return redirect('/login-usuario/')

    usuario = db.Usuario.find_one({'nombreUsuario': nombre_usuario})
    if not usuario:
        return redirect('/login-usuario/')
    
    id_usuario = usuario['_id']

    
    pipeline = [
        {
            "$lookup": {
                "from": "Usuario",
                "localField": "propietario_id",
                "foreignField": "_id",
                "as": "info_propietario"
            }
        },
        {"$unwind": {"path": "$info_propietario", "preserveNullAndEmptyArrays": True}}
    ]

    todas_las_playlists = list(db.Playlist.aggregate(pipeline))

    mis_playlists = []
    comunidad_playlists = []

    for p in todas_las_playlists:
        
        if p.get('propietario_id') == id_usuario:
            mis_playlists.append({
                'idPlaylist': p['_id'],
                'nombrePlaylist': p.get('nombrePlaylist'),
                'visibilidad': p.get('visibilidad', 'Privada')
            })
        elif p.get('visibilidad') == 'Pública':
            comunidad_playlists.append({
                'idPlaylist': p['_id'],
                'nombrePlaylist': p.get('nombrePlaylist'),
                'propietario': p.get('info_propietario', {}).get('nombreUsuario', 'Desconocido')
            })

    return render(request, 'viveec/biblioteca_usuario.html', {
        'nombre': nombre_usuario,
        'mis_playlists': mis_playlists,
        'comunidad_playlists': comunidad_playlists
    })

def playlist_detalle(request, idPlaylist):
    nombre_usuario = request.session.get('usuario_nombre')
    if not nombre_usuario:
        return redirect('/login-usuario/')

    # 1. Obtener usuario actual
    usuario = db.Usuario.find_one({'nombreUsuario': nombre_usuario})
    if not usuario:
        return redirect('/login-usuario/')
    
    id_usuario_actual = usuario['_id']

    
    pipeline = [
        {'$match': {'_id': idPlaylist}},
        {
            '$lookup': {
                'from': 'Usuario',
                'localField': 'propietario_id',
                'foreignField': '_id',
                'as': 'info_propietario'
            }
        },
        {'$unwind': {'path': '$info_propietario', 'preserveNullAndEmptyArrays': True}}
    ]
    
    playlist_data = list(db.Playlist.aggregate(pipeline))
    
    if not playlist_data:
        return redirect('/biblioteca-usuario/')
    
    p = playlist_data[0]
    
    
    playlist = {
        'idPlaylist': p['_id'],
        'nombrePlaylist': p.get('nombrePlaylist'),
        'descripcionPlaylist': p.get('descripcionPlaylist', ''),
        'propietario': {'nombre': p.get('info_propietario', {}).get('nombreUsuario', 'Desconocido')},
        'idUsuarioPropietario': p.get('propietario_id')
    }
    
    
    es_propietario = (p.get('propietario_id') == id_usuario_actual)
    
    ya_guardado = (id_usuario_actual in p.get('colaboradores', []))

    
    ids_canciones_playlist = p.get('canciones', [])
    canciones = []
    
    if ids_canciones_playlist:
        
        albumes_con_canciones = db.Album.find({'canciones.id_cancion': {'$in': ids_canciones_playlist}})
        
        
        for alb in albumes_con_canciones:
            for c in alb.get('canciones', []):
                if c.get('id_cancion') in ids_canciones_playlist:
                    canciones.append({
                        'id': c.get('id_cancion'),
                        'nombre': c.get('nombreCancion'),
                        'duracion': int(c.get('duracionCancion', 0))
                    })

    
    todas_las_canciones = []
    cursor_todas = db.Album.find({}, {'canciones': 1})
    for alb in cursor_todas:
        for c in alb.get('canciones', []):
            todas_las_canciones.append({'id': c['id_cancion'], 'nombre': c['nombreCancion']})

    return render(request, 'viveec/playlist_detalle.html', {
        'playlist': playlist,
        'canciones': canciones,
        'todas_las_canciones': todas_las_canciones,
        'nombre': nombre_usuario,
        'es_propietario': es_propietario,
        'ya_guardado': ya_guardado
    })

def crear_playlist(request):
    if request.method == 'POST':
        nombre = request.POST.get('nombre')
        descripcion = request.POST.get('descripcion')
        visibilidad = request.POST.get('visibilidad')
        
        nombre_usuario = request.session.get('usuario_nombre')
        if not nombre_usuario:
            return redirect('/')

        
        usuario = db.Usuario.find_one({'nombreUsuario': nombre_usuario})
        if not usuario:
            return redirect('/')
        id_usuario = usuario['_id']

        
        ultimo_registro = db.Playlist.find().sort('_id', -1).limit(1)
        ultimo = list(ultimo_registro)
        
        if ultimo:
            
            numero = int(ultimo[0]['_id'][1:]) + 1
            nuevo_id = f"P{numero:03d}"
        else:
            nuevo_id = "P001"

        
        nueva_playlist = {
            '_id': nuevo_id,
            'nombrePlaylist': nombre,
            'descripcionPlaylist': descripcion,
            'visibilidad': visibilidad,
            'propietario_id': id_usuario,
            'colaboradores': [], 
            'canciones': []      
        }
        
        db.Playlist.insert_one(nueva_playlist)
        
        return redirect('/biblioteca-usuario/')
    
    return redirect('/biblioteca-usuario/')

@csrf_exempt
def toggle_playlist(request):
    data = json.loads(request.body)
    id_playlist = data.get('idPlaylist')
    nombre_usuario = request.session.get('usuario_nombre')
    
    usuario = db.Usuario.find_one({'nombreUsuario': nombre_usuario})
    id_user = usuario['_id']
    
    
    playlist = db.Playlist.find_one({'_id': id_playlist, 'colaboradores': id_user})
    
    if playlist:
        
        db.Playlist.update_one({'_id': id_playlist}, {'$pull': {'colaboradores': id_user}})
        estado = 'no_guardado'
    else:
        
        db.Playlist.update_one({'_id': id_playlist}, {'$addToSet': {'colaboradores': id_user}})
        estado = 'guardado'
        
    return JsonResponse({'estado': estado})

def buscar_canciones(request):
    query = request.GET.get('q', '')
    
    pipeline = [
        {"$unwind": "$canciones"},
        {"$match": {"canciones.nombreCancion": {"$regex": query, "$options": "i"}}},
        {"$limit": 5},
        {"$project": {"_id": 0, "id": "$canciones.id_cancion", "nombre": "$canciones.nombreCancion"}}
    ]
    canciones = list(db.Album.aggregate(pipeline))
    return JsonResponse({'canciones': canciones})

@csrf_exempt
def agregar_cancion_a_playlist(request):
    if request.method == 'POST':
        data = json.loads(request.body)
        
        db.Playlist.update_one(
            {'_id': data['idPlaylist']}, 
            {'$addToSet': {'canciones': data['idCancion']}}
        )
        return JsonResponse({'status': 'ok'})

@csrf_exempt
def eliminar_cancion(request):
    if request.method == 'POST':
        data = json.loads(request.body)
        
        db.Playlist.update_one(
            {'_id': data['idPlaylist']}, 
            {'$pull': {'canciones': data['idCancion']}}
        )
        return JsonResponse({'status': 'eliminado'})

def suscripcion_usuario(request):
    nombre_usuario = request.session.get('usuario_nombre')
    usuario = db.Usuario.find_one({'nombreUsuario': nombre_usuario})
    
    if not usuario:
        return redirect('/login-usuario/')
    
    id_usuario = usuario['_id']
    hoy = datetime.now()
    
    
    fecha_hoy_str = hoy.strftime('%Y-%m-%d')
    suscripcion_actual = db.Suscripcion.find_one({
        'usuario_id': id_usuario,
        'estadoSuscripcion': 'Activa',
        'fechaFinSuscripcion': {'$gte': fecha_hoy_str}
    })
    
    
    suscripciones_usuario = list(db.Suscripcion.find({'usuario_id': id_usuario}))
    lista_suscripcion_ids = [s['_id'] for s in suscripciones_usuario]
    
    
    pagos = list(db.Pago.find({'suscripcion_id': {'$in': lista_suscripcion_ids}}).sort('fechaPago', -1))
    historial = []
    for p in pagos:
        susc = db.Suscripcion.find_one({'_id': p['suscripcion_id']})
        if susc:
            historial.append({
                'tipoSuscripcion': susc.get('tipoSuscripcion'),
                'monto': p.get('monto'),
                'fechaInicioSuscripcion': susc.get('fechaInicioSuscripcion'),
                'fechaFinSuscripcion': susc.get('fechaFinSuscripcion')
            })
    
    error_formulario = None
    
    if request.method == 'POST' and not suscripcion_actual:
        tipo = request.POST.get('tipoSuscripcion')
        monto = float(request.POST.get('monto', 0))
        metodo = request.POST.get('metodoPago')
        
        if monto <= 0:
            error_formulario = "El monto debe ser mayor a 0."
        elif tipo not in ['Individual', 'Estudiante', 'Familiar']:
            error_formulario = "Tipo de suscripción inválido."
        else:
            # Generar ID para Suscripción
            ultimo_s = db.Suscripcion.find().sort('_id', -1).limit(1)
            lista_s = list(ultimo_s)
            num_s = int(lista_s[0]['_id'][1:]) + 1 if lista_s else 1
            nuevo_id_s = f"S{num_s:03d}"
            
            # Generar ID para Pago
            ultimo_p = db.Pago.find().sort('_id', -1).limit(1)
            lista_p = list(ultimo_p)
            num_p = int(lista_p[0]['_id'][1:]) + 1 if lista_p else 1
            nuevo_id_p = f"P{num_p:03d}"
            
            try:
                fecha_fin = (hoy + timedelta(days=30)).strftime('%Y-%m-%d')
                
                db.Suscripcion.insert_one({
                    '_id': nuevo_id_s,
                    'tipoSuscripcion': tipo,
                    'fechaInicioSuscripcion': fecha_hoy_str,
                    'fechaFinSuscripcion': fecha_fin,
                    'estadoSuscripcion': 'Activa',
                    'usuario_id': id_usuario
                })
                
                db.Pago.insert_one({
                    '_id': nuevo_id_p,
                    'monto': monto,
                    'fechaPago': fecha_hoy_str,
                    'metodoPago': metodo,
                    'resultadoPago': 'Aprobado',
                    'suscripcion_id': nuevo_id_s
                })
                return redirect('/suscripcion-usuario/')
            except Exception as e:
                error_formulario = f"Error al procesar suscripción: {str(e)}"

    return render(request, 'viveec/suscripcion.html', {
        'nombre': nombre_usuario,
        'tiene_suscripcion': suscripcion_actual is not None,
        'nombre_plan': suscripcion_actual.get('tipoSuscripcion') if suscripcion_actual else None,
        'error_formulario': error_formulario,
        'planes': [('Individual', '9.99'), ('Estudiante', '4.99'), ('Familiar', '14.99')],
        'historial_pagos': historial
    })

def formatear_tiempo(segundos):
    if not segundos:
        return "0:00"
    minutos = int(segundos) // 60
    segundos_restantes = int(segundos) % 60
    return f"{minutos}:{segundos_restantes:02d}"



def reportes_usuario(request):
    nombre_usuario = request.session.get('usuario_nombre')
    if not nombre_usuario:
        return redirect('/login-usuario/')

    usuario = db.Usuario.find_one({'nombreUsuario': nombre_usuario})
    if not usuario:
        return redirect('/login-usuario/')

    id_usuario = usuario['_id']

    data = {'nombre': nombre_usuario}

    
    reproducciones = list(db.Reproduccion.find({'usuario_id': id_usuario}))

    
    mapa_cancion_nombre = {}
    mapa_cancion_generos = {}     
    mapa_cancion_artista = {}     

    for alb in db.Album.find():
        artista_id = alb.get('artista_id')
        for c in alb.get('canciones', []):
            id_c = c.get('id_cancion')
            mapa_cancion_nombre[id_c] = c.get('nombreCancion')
            mapa_cancion_generos[id_c] = c.get('generos', [])
            mapa_cancion_artista[id_c] = artista_id

    
    mapa_generos = {g['_id']: g['nombreGenero'] for g in db.Genero.find()}

    
    mapa_artistas = {a['_id']: a['nombreArtista'] for a in db.Artista.find()}

    
    conteo_canciones = Counter(r.get('cancion_id') for r in reproducciones)
    top_canciones_raw = conteo_canciones.most_common(3) 

    top_canciones = []
    for id_c, total in top_canciones_raw:
        nombre_c = mapa_cancion_nombre.get(id_c, 'Desconocida')
        top_canciones.append((nombre_c, total))

    data['top_canciones'] = top_canciones
    data['nombres_canciones'] = [x[0] for x in top_canciones]
    data['repros_canciones'] = [x[1] for x in top_canciones]

    
    conteo_generos = Counter()
    for r in reproducciones:
        id_c = r.get('cancion_id')
        for id_g in mapa_cancion_generos.get(id_c, []):
            conteo_generos[id_g] += 1

    generos_data = [
        (mapa_generos.get(id_g, 'Desconocido'), total)
        for id_g, total in sorted(conteo_generos.items(), key=lambda x: x[1], reverse=True)
    ]
    data['generos_tabla'] = generos_data

    
    hoy = datetime.now()
    segundos_mes = 0
    for r in reproducciones:
        fecha_str = r.get('fechaReproduccion')
        if not fecha_str:
            continue
        try:
            fecha = datetime.strptime(fecha_str, '%Y-%m-%d')
        except ValueError:
            continue
        if fecha.month == hoy.month and fecha.year == hoy.year:
            segundos_mes += r.get('duracionReproduccion', 0)
    data['tiempo_mes'] = formatear_tiempo(segundos_mes)

    
    semana_actual = hoy.isocalendar()[1]
    segundos_semana = 0
    for r in reproducciones:
        fecha_str = r.get('fechaReproduccion')
        if not fecha_str:
            continue
        try:
            fecha = datetime.strptime(fecha_str, '%Y-%m-%d')
        except ValueError:
            continue
        if fecha.isocalendar()[1] == semana_actual and fecha.year == hoy.year:
            segundos_semana += r.get('duracionReproduccion', 0)
    data['tiempo_semana'] = formatear_tiempo(segundos_semana)

    
    duracion_por_artista = defaultdict(int)
    for r in reproducciones:
        fecha_str = r.get('fechaReproduccion')
        if not fecha_str:
            continue
        try:
            fecha = datetime.strptime(fecha_str, '%Y-%m-%d')
        except ValueError:
            continue
        if fecha.month == hoy.month and fecha.year == hoy.year:
            id_c = r.get('cancion_id')
            id_artista = mapa_cancion_artista.get(id_c)
            if id_artista:
                duracion_por_artista[id_artista] += r.get('duracionReproduccion', 0)

    artistas_ordenados = sorted(duracion_por_artista.items(), key=lambda x: x[1], reverse=True)
    artistas_formateados = [
        (mapa_artistas.get(id_artista, 'Desconocido'), formatear_tiempo(segundos))
        for id_artista, segundos in artistas_ordenados
    ]
    data['artistas_top'] = artistas_formateados

    
    historial_ordenado = sorted(
        reproducciones,
        key=lambda r: r.get('fechaReproduccion', '')
    )
    historial_formateado = []
    for r in historial_ordenado:
        id_c = r.get('cancion_id')
        nombre_c = mapa_cancion_nombre.get(id_c, 'Desconocida')
        duracion_fmt = formatear_tiempo(r.get('duracionReproduccion', 0))
        fecha_str = r.get('fechaReproduccion')
        try:
            fecha_obj = datetime.strptime(fecha_str, '%Y-%m-%d') if fecha_str else None
        except ValueError:
            fecha_obj = None
        historial_formateado.append((nombre_c, duracion_fmt, fecha_obj))
    data['historial'] = historial_formateado

    
    ids_likes = usuario.get('likes', [])
    data['likes'] = [mapa_cancion_nombre.get(id_c, 'Desconocida') for id_c in ids_likes]

    return render(request, 'viveec/reportes_usuario.html', data)
