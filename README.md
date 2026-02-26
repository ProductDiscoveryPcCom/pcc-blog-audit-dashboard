# PcComponentes Blog Audit Dashboard — v6 Modular

Dashboard interactivo con estética Metabase para auditoría SEO del blog de PcComponentes.

## Arquitectura

```
app.py                    ← Orquestador limpio (30 líneas de lógica)
state.py                  ← Estado centralizado con defaults explícitos
styles.py                 ← CSS Metabase + Altair theme + constantes de color
data.py                   ← Capa de datos con cache de dos niveles
requirements.txt
.streamlit/config.toml

components/
  auth.py                 ← Login con brute-force protection
  sidebar.py              ← Filtros con patrón pending/applied

pages/
  dashboard.py            ← KPIs + gráficos overview
  explorer.py             ← Tabla exploratoria + exportación
  alerts.py               ← Panel de alertas (st.fragment)
  analysis.py             ← Content gap, heatmap, timeline
  gsc.py                  ← 🆕 Google Search Console con drill-down

utils/
  helpers.py              ← Chart helpers + exportación CSV/Excel
```

## Optimizaciones aplicadas

### 1. Estado centralizado (`state.py`)
Todos los keys de `session_state` declarados en un solo lugar con defaults explícitos.
`init_state()` se llama una vez al inicio — nunca más `KeyError` por keys inexistentes.

### 2. Separar selección de aplicación de filtros (`sidebar.py`)
Los widgets del sidebar escriben en `pending_filters`. Los datos **solo se recalculan**
cuando el usuario pulsa **"Aplicar filtros"**, que copia pending → `applied_filters` e
invalida los caches de nivel 2. El botón se ilumina en naranja cuando hay filtros sin aplicar.

### 3. Cache de dos niveles (`data.py`)
- **Nivel 1 (pesado):** `fetch_all_sheets()` con `@st.cache_data(ttl=3600)` — I/O de red a Google Sheets. Se ejecuta como máximo 1 vez por hora.
- **Nivel 2 (ligero):** `get_filtered_master()` filtra en memoria y guarda resultado en `session_state`. Se invalida solo cuando `applied_filters` cambia.

### 4. Estructura modular
De un monolito de 1085 líneas a 13 archivos con responsabilidad única.
Cada archivo < 200 líneas. Añadir un nuevo tab = crear un archivo en `pages/`.

### 5. Drill-down interactivo (GSC)
En la pestaña GSC, seleccionar una fila de la tabla de URLs muestra sus top queries
en el panel lateral derecho. Usa `st.dataframe(on_select="rerun")` +
`session_state["detail_view"]`.

### 6. App.py como orquestador
`app.py` solo hace: init → auth → load → sidebar → routing. Toda la lógica
de presentación vive en `pages/`.

## Hojas de Google Sheets requeridas

| Hoja | Origen | Obligatoria |
|------|--------|-------------|
| `URLs_Master` | Colab Fase 1-2 | ✅ |
| `Alertas` | Colab Fase 3 | Opcional |
| `GSC_Performance` | Colab Fase 4 | Opcional |
| `GSC_Deltas` | Colab Fase 4 | Opcional |

## Secrets necesarios (Streamlit Cloud)

```toml
GCP_SERVICE_ACCOUNT = '{"type":"service_account", ...}'
SPREADSHEET_ID = "tu_spreadsheet_id"

[users]
admin = "sha256_hash_de_la_contraseña"
```

## Despliegue

1. Subir repo a GitHub
2. Conectar en [share.streamlit.io](https://share.streamlit.io)
3. Configurar Secrets en Settings
4. Main file: `app.py`
