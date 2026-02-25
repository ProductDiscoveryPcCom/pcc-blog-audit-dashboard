# PcComponentes Blog Audit Dashboard

Dashboard interactivo con autenticación para auditar y monitorizar el blog de PcComponentes.

## Setup en Streamlit Cloud

1. Crea un repo en GitHub y sube estos archivos
2. Ve a [share.streamlit.io](https://share.streamlit.io/) → New app → conecta el repo
3. Marca la app como **pública** (requisito del plan gratuito)
4. En Settings → Secrets, configura:

```toml
SPREADSHEET_ID = "tu_spreadsheet_id"
GCP_SERVICE_ACCOUNT = '{"type":"service_account","project_id":"...","private_key":"...","client_email":"..."}'

[users]
admin = "240be518fabd2724ddb6f04eeb1da5967448d7e831c08c8fa822809f74c720a9"
maria = "hash_de_la_contraseña_de_maria"
```

## Gestión de usuarios

Las contraseñas se almacenan como hash SHA-256 en la sección `[users]` de los Secrets de Streamlit. Cada clave es el nombre de usuario y el valor es el hash SHA-256 de la contraseña.

Para generar el hash de una contraseña:
```python
import hashlib
hashlib.sha256("tu_contraseña".encode()).hexdigest()
```

## Seguridad

- Login con usuario/contraseña, hashes SHA-256 (nunca texto plano)
- Protección contra fuerza bruta: bloqueo tras 5 intentos fallidos (5 minutos)
- Sesiones gestionadas por Streamlit session state

## Schema de datos

### Hoja `URLs_Master` (obligatoria)

| Columna | Tipo | Obligatoria | Descripción |
|---------|------|-------------|-------------|
| `url` | texto | Sí | URL del artículo |
| `meta_title` | texto | No | Título meta del artículo |
| `categoria` | texto | Sí | Categoría principal |
| `subcategoria` | texto | No | Subcategoría |
| `tipo_contenido` | texto | No | Tipo de contenido (guía, review, etc.) |
| `vigencia` | texto | No | `evergreen`, `evergreen_actualizable` o `caduco` |
| `status_code` | entero | Sí | Código HTTP (200, 301, 404...) |
| `has_noindex` | booleano | No | Tiene meta noindex |
| `has_product_carousel` | booleano | No | Tiene carrusel de producto |
| `has_alerts` | booleano | No | Tiene alertas activas |
| `word_count` | entero | No | Número de palabras |
| `h2_count` | entero | No | Número de encabezados H2 |
| `product_count` | entero | No | Número de productos |
| `year_in_title` | numérico | No | Año mencionado en el título |
| `pub_date` | fecha | No | Fecha de publicación |
| `lastmod` | fecha | No | Fecha de última modificación |
| `sitemap_title` | texto | No | Título en el sitemap |

### Hoja `Alertas` (opcional)

| Columna | Tipo | Descripción |
|---------|------|-------------|
| `url` | texto | URL afectada |
| `alert_type` | texto | Tipo de alerta |
| `severity` | texto | `ALTA`, `MEDIA` o `BAJA` |
| `detail` | texto | Descripción de la alerta |
| `detected_date` | fecha | Fecha de detección |
| `resolved` | booleano | Si la alerta ha sido resuelta |
