# ViveEC

Sistema de streaming musical desarrollado con Django y MongoDB.

## Requisitos

* Python 3.12 o superior
* MongoDB (Atlas o local)

## Instalación

### 1. Descargar el repositorio

Clonar o descargar este repositorio.

### 2. Crear y activar entorno virtual

Windows:

```bash
python -m venv venv
venv\Scripts\activate
```

### 3. Instalar dependencias

```bash
pip install -r requirements.txt
```

### 4. Configurar la conexión a MongoDB

Para conectar la aplicación con tu base de datos, localiza el archivo:

```text
viveec/views.py
```
Busca la variable de conexión y reemplaza la URI con la de tu instancia de MongoDB:

#### 5. Reemplaza con tu URI real de MongoDB

```python
client = MongoClient("mongodb+srv://<usuario>:<password>@clusterudla01.5ojogg0.mongodb.net/?appName=ClusterUDLA01")
db = client['NombreBaseDeDatos']
```
### 6. Ejecutar el proyecto

```bash
python manage.py runserver
```

### 7. Abrir en el navegador

```text
http://127.0.0.1:8000
```