# 🔍 PcComponentes Blog Audit Dashboard

Dashboard interactivo para auditar y monitorizar el blog de PcComponentes.

## Qué muestra

- **KPIs**: total URLs, status codes, alertas activas, artículos con carrusel
- **Explorador**: tabla interactiva con filtros, exportable a CSV
- **Alertas**: panel priorizado por severidad (años obsoletos, noindex, canonical, etc.)
- **Análisis**: content gaps, distribución de longitud, mapa categoría × tipo

## Setup en Streamlit Cloud

1. Crea un repo en GitHub y sube estos archivos
2. Ve a [share.streamlit.io](https://share.streamlit.io/) → New app → conecta el repo
3. En Settings → Secrets, añade:

```toml
SPREADSHEET_ID = "tu_spreadsheet_id"
GCP_SERVICE_ACCOUNT = '{"type":"service_account","project_id":"...","private_key":"...","client_email":"..."}'
```

4. La app se desplegará automáticamente

## Datos

Los datos se cargan de Google Sheets (hoja `URLs_Master` y `Alertas`). Se alimentan desde el notebook de Google Colab.
