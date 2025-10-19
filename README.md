# codex-ai

## Descripción del proyecto
Este repositorio contiene un backend modular construido con FastAPI y Python 3.12. La aplicación expone endpoints REST para gestionar usuarios y tareas, utiliza JWT para autenticación, persiste datos con SQLAlchemy y SQLite/PostgreSQL, y ofrece scripts y workflows para pruebas automatizadas, integración continua y despliegue en Google Cloud Run.

### Características principales
- Arquitectura organizada en módulos (`routers`, `services`, `models`, `core`).
- Autenticación basada en JWT con endpoints de registro, inicio de sesión y refresco.
- CRUD completos para usuarios y tareas con control de acceso por propietario.
- Integración con SQLAlchemy y compatibilidad con SQLite (desarrollo/tests) y PostgreSQL (producción).
- Dockerfile y `docker-compose.yml` para orquestar backend, base de datos y Redis.
- Workflows de GitHub Actions para pruebas, linting, build de contenedor y despliegue en Cloud Run.

## Estructura de carpetas
```text
app/
  core/           # Configuración, dependencias y utilidades de seguridad
  models/         # Modelos ORM y esquemas Pydantic
  routers/        # Endpoints organizados por recurso
  services/       # Lógica de negocio desacoplada de los controladores
  main.py         # Punto de entrada de la aplicación FastAPI
stubs/             # Stubs de tipado para dependencias externas
tests/             # Fixtures y pruebas de integración con pytest
Dockerfile         # Imagen de producción basada en Python 3.12
run_tests.sh       # Script para ejecutar pytest con cobertura
pyproject.toml     # Configuración de herramientas (mypy, black, flake8)
requirements.txt   # Dependencias de ejecución y desarrollo
.env               # Variables de entorno de ejemplo
```

## Requisitos e instalación
1. **Requisitos previos**
   - Python 3.12
   - `pip` y `virtualenv` (recomendado)
   - Docker y Docker Compose (opcional para despliegues locales)

2. **Clonar el repositorio y crear un entorno virtual**
   ```bash
   git clone <url-del-repositorio>
   cd codex-ai
   python3.12 -m venv .venv
   source .venv/bin/activate  # En Windows: .venv\\Scripts\\activate
   ```

3. **Instalar dependencias**
   ```bash
   pip install -r requirements.txt
   ```

## Variables de entorno
Todas las variables se cargan desde `.env`. Ajusta los valores según el entorno donde despliegues la aplicación.

| Variable | Descripción | Valor por defecto |
| --- | --- | --- |
| `SECRET_KEY` | Clave secreta para firmar JWT. | `super-secret-key-change-me` |
| `ALGORITHM` | Algoritmo de firma para JWT. | `HS256` |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | Minutos de validez del access token. | `15` |
| `REFRESH_TOKEN_EXPIRE_MINUTES` | Minutos de validez del refresh token. | `10080` |
| `DATABASE_URL` | Cadena de conexión para SQLite (desarrollo/tests). | `sqlite+aiosqlite:///./app.db` |
| `POSTGRES_DB` | Nombre de la base de datos PostgreSQL. | `app_db` |
| `POSTGRES_USER` | Usuario de la base de datos PostgreSQL. | `app_user` |
| `POSTGRES_PASSWORD` | Contraseña de la base de datos PostgreSQL. | `app_password` |
| `POSTGRES_HOST` | Host del servicio PostgreSQL (Docker Compose). | `db` |
| `POSTGRES_PORT` | Puerto del servicio PostgreSQL. | `5432` |
| `POSTGRES_DATABASE_URL` | URL asíncrona para PostgreSQL usada en producción. | `postgresql+asyncpg://app_user:app_password@db:5432/app_db` |
| `REDIS_URL` | Cadena de conexión para Redis. | `redis://redis:6379/0` |
| `GCP_PROJECT` | ID del proyecto de Google Cloud (usado en workflows). | _sin valor_ |
| `GCP_REGION` | Región de despliegue en Google Cloud. | _sin valor_ |
| `GCP_SERVICE_NAME` | Nombre del servicio en Cloud Run. | _sin valor_ |

> Sustituye las credenciales por valores seguros antes de desplegar en entornos reales.

## Uso de la API
La aplicación expone un conjunto de endpoints REST protegidos por JWT (excepto los de salud y autenticación). Todas las rutas autenticadas requieren el encabezado `Authorization: Bearer <access_token>`.

### Salud
| Método | Ruta | Descripción |
| --- | --- | --- |
| `GET` | `/health` | Comprueba que la API está disponible.

### Autenticación
| Método | Ruta | Descripción | Cuerpo |
| --- | --- | --- | --- |
| `POST` | `/auth/signup` | Registra un nuevo usuario. | `{ "name": str, "email": str, "password": str }`
| `POST` | `/auth/login` | Inicia sesión y devuelve tokens JWT. | `{ "email": str, "password": str }`
| `POST` | `/auth/refresh` | Emite un nuevo par de tokens usando el refresh token. | `{ "refresh_token": str }`

### Usuarios (requieren JWT)
| Método | Ruta | Descripción |
| --- | --- | --- |
| `GET` | `/users` | Lista todos los usuarios registrados.
| `POST` | `/users` | Crea un usuario (solo para administradores o flujos internos).
| `GET` | `/users/{user_id}` | Obtiene la información de un usuario específico.
| `PUT` | `/users/{user_id}` | Actualiza los datos de un usuario.
| `DELETE` | `/users/{user_id}` | Elimina un usuario.

### Tareas (requieren JWT)
| Método | Ruta | Descripción |
| --- | --- | --- |
| `GET` | `/tasks` | Lista las tareas del usuario autenticado.
| `POST` | `/tasks` | Crea una nueva tarea para el usuario autenticado.
| `GET` | `/tasks/{task_id}` | Obtiene una tarea del usuario si le pertenece.
| `PUT` | `/tasks/{task_id}` | Actualiza una tarea propia.
| `DELETE` | `/tasks/{task_id}` | Elimina una tarea propia.

### Resumen de texto
| Método | Ruta | Descripción | Cuerpo |
| --- | --- | --- | --- |
| `POST` | `/summarize` | Genera un resumen breve usando GPT-5 y OpenAI. | `{ "text": str }`

> **Requisitos**: Debes establecer la variable de entorno `OPENAI_API_KEY` con una clave válida de OpenAI antes de iniciar la API. Si el valor está ausente, el servicio de resumen no podrá inicializarse.

Ejemplo de consumo con `curl`:

```bash
curl -X POST "http://localhost:8000/summarize" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer <TOKEN_JWT>" \
  -d '{"text": "Texto largo que deseas resumir."}'
```

Respuesta esperada:

```json
{
  "summary": "Resumen generado por GPT-5"
}
```

## Cómo correr los tests
1. Asegúrate de tener las dependencias instaladas (`pip install -r requirements.txt`).
2. Ejecuta el script de pruebas con cobertura:
   ```bash
   ./run_tests.sh
   ```
   El script invoca `pytest` con `--cov` para garantizar al menos 80% de cobertura sobre los módulos de la aplicación.

## Hooks de pre-commit
Automatiza los chequeos de formato, linting y pruebas instalando [pre-commit](https://pre-commit.com/).

1. Instala la herramienta:
   ```bash
   pip install pre-commit
   ```
2. Registra los hooks definidos en `.pre-commit-config.yaml`:
   ```bash
   pre-commit install
   ```
3. (Opcional) Ejecuta todos los hooks sobre el repositorio completo:
   ```bash
   pre-commit run --all-files
   ```

Los hooks configurados validan el formato con Black e isort, aplican reglas de linting con Flake8 y ejecutan `./run_tests.sh` antes de cada commit. Todos los hooks basados en Python se fijan a la versión 3.12 para permanecer alineados con el runtime del proyecto.

## Versionado semántico y releases
La automatización de releases utiliza etiquetas git con formato `vX.Y.Z` y genera un changelog actualizado en cada versión.

1. Cada push a `main` o una ejecución manual del workflow **release** dispara [Release Please](https://github.com/googleapis/release-please).
2. La acción analiza los mensajes de commit (Convencional Commit recomendado) y propone un incremento de versión semántica.
3. Al fusionar la Pull Request de release, se crea automáticamente la etiqueta (`v1.0.0`, `v1.1.0`, etc.), la entrada correspondiente en `CHANGELOG.md` y la Release en GitHub.
4. También puedes lanzar el proceso manualmente desde la pestaña **Actions** seleccionando el workflow "release" y pulsando **Run workflow**.

Consulta `CHANGELOG.md` para conocer el historial de cambios generado automáticamente.

## Estándares de documentación
- Todo el código incluye docstrings con formato Google para facilitar el mantenimiento y la generación futura de documentación.
- Se recomienda mantener este estilo al añadir nuevas funciones o clases.

## Despliegue

### Desarrollo local con Docker Compose
1. Copia `.env` y ajusta las variables según sea necesario.
2. Construye y levanta los servicios:
   ```bash
   docker-compose up --build
   ```
3. La API quedará disponible en `http://localhost:8000` y la documentación interactiva en `http://localhost:8000/docs`.

### Despliegue en Cloud Run
Sigue estos pasos para desplegar el backend en Google Cloud Run utilizando Artifact Registry como registro de imágenes.

1. **Preparar el entorno local**
   - Instala y autentícate con la [CLI de Google Cloud](https://cloud.google.com/sdk/docs/install).
   - Habilita las APIs necesarias:
     ```bash
     gcloud services enable run.googleapis.com artifactregistry.googleapis.com
     ```

2. **Definir variables comunes**
   ```bash
   export GCP_PROJECT="tu-proyecto"
   export GCP_REGION="us-central1"
   export GCP_SERVICE_NAME="codex-ai-backend"
   export GAR_REPOSITORY="codex-ai"
   export IMAGE="${GCP_REGION}-docker.pkg.dev/${GCP_PROJECT}/${GAR_REPOSITORY}/${GCP_SERVICE_NAME}:latest"
   ```

3. **Crear el repositorio en Artifact Registry (una sola vez)**
   ```bash
   gcloud artifacts repositories create "$GAR_REPOSITORY" \
     --repository-format=docker \
     --location="$GCP_REGION"
   ```
   > Si el repositorio ya existe, omite este paso.

4. **Construir y enviar la imagen Docker**
   ```bash
   docker build -t "$IMAGE" .
   docker push "$IMAGE"
   ```

5. **Configurar variables de entorno de la aplicación**
   - Crea un archivo `.env` con las variables definidas anteriormente.
   - Convierte su contenido a un formato compatible con Cloud Run:
     ```bash
     export CLOUD_RUN_ENV_VARS="$(grep -v '^#' .env | xargs | tr ' ' ',')"
     ```

6. **Desplegar en Cloud Run**
   ```bash
   gcloud run deploy "$GCP_SERVICE_NAME" \
     --image="$IMAGE" \
     --region="$GCP_REGION" \
     --platform=managed \
     --allow-unauthenticated \
     --set-env-vars "$CLOUD_RUN_ENV_VARS"
   ```

7. **Verificar el despliegue**
   - Google Cloud Run mostrará la URL pública del servicio al finalizar.
   - Comprueba la salud del servicio:
     ```bash
     curl https://<tu-url-de-cloud-run>/health
     ```

Estas mismas variables (`GCP_PROJECT`, `GCP_REGION` y `GCP_SERVICE_NAME`) se utilizan como secretos en los workflows de GitHub Actions para automatizar el despliegue.
