# Revisión Crítica del Repositorio — pcc-blog-audit-dashboard

**Fecha:** 2026-02-25
**Alcance:** Revisión completa de seguridad, arquitectura, calidad de código, infraestructura y UX.

---

## Resumen Ejecutivo

El repositorio contiene un dashboard Streamlit de 904 líneas en un solo archivo (`app.py`) para auditar el blog de PcComponentes. Aunque el producto final tiene buena presentación visual (tema Metabase), presenta **problemas críticos de seguridad**, **inconsistencias entre documentación y código**, y **carencias significativas de infraestructura**.

---

## 1. SEGURIDAD — Problemas Críticos

### 1.1 Autenticación en texto plano (CRÍTICO)
**Archivo:** `app.py:239`
```python
if password == st.secrets.get("APP_PASSWORD", ""):
```
La contraseña se compara directamente en texto plano. **El README afirma** que se usa SHA-256 con hashes por usuario (`[users]` section), pero el código real usa un único `APP_PASSWORD` sin hashear. Esto es una contradicción grave entre documentación y realidad.

### 1.2 Contraseña vacía permite acceso (CRÍTICO)
**Archivo:** `app.py:239`
```python
st.secrets.get("APP_PASSWORD", "")
```
Si `APP_PASSWORD` no está configurado en los Secrets, el valor por defecto es `""`. Un usuario podría autenticarse enviando una contraseña vacía. Esto es una **puerta trasera accidental**.

### 1.3 Sin protección contra fuerza bruta
No hay rate limiting, captcha, ni bloqueo temporal tras intentos fallidos. Un atacante puede probar contraseñas indefinidamente.

### 1.4 Sin expiración de sesión
Una vez autenticado, `st.session_state['authenticated']` permanece `True` indefinidamente. No hay timeout de inactividad ni expiración de sesión.

### 1.5 Uso extensivo de `unsafe_allow_html=True`
Se usa en **10+ ocasiones** a lo largo del código. Aunque el contenido inyectado es mayormente estático, este patrón abre la puerta a vulnerabilidades XSS si algún valor dinámico se inyecta en el futuro sin sanitizar.

---

## 2. ARQUITECTURA Y CALIDAD DE CÓDIGO

### 2.1 Monolito de 904 líneas
Todo el código (CSS, autenticación, carga de datos, filtros, 4 tabs con visualizaciones) está en un solo archivo. Esto dificulta:
- Mantenimiento y modificaciones
- Testing unitario
- Reutilización de componentes
- Code review efectivo

**Estructura recomendada:**
```
├── app.py              (punto de entrada, ~50 líneas)
├── auth.py             (autenticación)
├── data.py             (carga y transformación de datos)
├── components/
│   ├── dashboard.py
│   ├── explorer.py
│   ├── alerts.py
│   └── analysis.py
├── styles/
│   └── metabase.py     (CSS y tema Plotly)
└── utils.py            (funciones comunes)
```

### 2.2 Lógica duplicada
La conversión de booleanos se repite idénticamente en dos lugares:
- **`app.py:282-284`** (carga de datos)
- **`app.py:617-618`** (alertas)

```python
lambda x: str(x).strip().upper() in ('TRUE', 'VERDADERO', '1', 'YES')
```

### 2.3 Magic strings dispersos
Valores como `'caduco'`, `'evergreen_actualizable'`, `'ALTA'`, `'MEDIA'`, `'BAJA'`, `'URLs_Master'`, `'Alertas'` aparecen como strings literales sin definir constantes. Cualquier typo pasaría desapercibido.

### 2.4 Patrón de filtrado repetido
La expresión `df['col'].astype(str).str.strip() != ''` se repite **9 veces** (líneas 322, 330, 335, 341, 346, 464, 485, 509, 744, 867, 868). Debería extraerse a una función utilidad.

### 2.5 Sin logging
Cero líneas de logging en toda la aplicación. Imposible diagnosticar problemas en producción.

### 2.6 Manejo de errores genérico
```python
except Exception as e:
    st.error(f"Error conectando con Google Sheets: {e}")
```
Un solo `except` genérico (línea 299) captura errores de autenticación GCP, errores de red, errores de schema y errores de parsing con el mismo mensaje.

---

## 3. INFRAESTRUCTURA — Carencias Significativas

| Elemento | Estado |
|----------|--------|
| `.gitignore` | **AUSENTE** — riesgo de commit accidental de `__pycache__`, `.env`, etc. |
| Tests | **INEXISTENTES** — cero tests, cero framework de testing |
| CI/CD | **INEXISTENTE** — sin GitHub Actions ni checks automatizados |
| Linting/Formatting | **INEXISTENTE** — sin ruff, flake8, black, ni isort |
| Docker | **AUSENTE** — sin Dockerfile para desarrollo local |
| `.streamlit/config.toml` | **AUSENTE** — sin configuración local de Streamlit |
| `pyproject.toml` / `setup.py` | **AUSENTE** — sin configuración estándar de proyecto Python |
| Pre-commit hooks | **AUSENTE** |

---

## 4. DEPENDENCIAS

### 4.1 Versiones no fijadas
```
streamlit>=1.30.0
pandas>=2.0.0
```
Usar `>=` sin límite superior significa que una futura versión de Streamlit (ej. 2.0) podría romper la app. Builds no son reproducibles.

**Recomendación:** Usar versiones fijadas o rangos acotados:
```
streamlit>=1.30.0,<2.0.0
pandas>=2.0.0,<3.0.0
```
O mejor aún, generar un `requirements.txt` con `pip freeze` para reproducibilidad total.

### 4.2 Dependencia implícita
El README menciona `hashlib` para generar hashes SHA-256, pero el código nunca importa ni usa `hashlib`. La funcionalidad de hashing documentada no existe en el código.

---

## 5. MANEJO DE DATOS

### 5.1 `get_all_records()` sin paginación
**Archivo:** `app.py:263`
```python
df = pd.DataFrame(ws_master.get_all_records())
```
Carga **todos** los registros de la hoja en memoria. Para hojas grandes (10k+ filas), esto puede causar timeouts o problemas de memoria.

### 5.2 NaN silenciosamente convertidos a 0
**Archivo:** `app.py:277`
```python
df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0).astype(int)
```
Un `status_code` vacío o inválido se convierte en `0`, que no es un código HTTP válido. Esto enmascara problemas de calidad de datos.

### 5.3 Sin validación de schema
No se valida que las columnas esperadas existan en el Google Sheet. Si alguien renombra una columna, la app puede crashear con un `KeyError` en la sección de filtros (línea 360: `df['status_code'].unique()`) que no está protegida con verificación de columna.

### 5.4 Cache de 5 minutos sin configuración
El TTL de 300 segundos está hardcodeado. No hay forma de ajustarlo sin modificar el código.

---

## 6. UX / INTERFAZ

### 6.1 Sin paginación en el explorador
El dataframe muestra todos los resultados filtrados a la vez. Con miles de URLs, la experiencia será degradada.

### 6.2 Límite hardcodeado de 25 items
**Archivo:** `app.py:847`
```python
df_old[old_available].head(25)
```
La tabla de "contenido prioritario para actualizar" muestra solo 25 items sin opción de ver más.

### 6.3 Filtros no persisten entre recargas
Los filtros del sidebar se resetean cada vez que se recarga la página. No se guardan en URL params ni session state.

### 6.4 Sin estados vacíos consistentes
Algunos gráficos no muestran mensaje cuando no hay datos. La experiencia varía entre tabs.

---

## 7. DOCUMENTACIÓN

### 7.1 README contradice el código (CRÍTICO)
El README describe:
- Sistema multi-usuario con sección `[users]`
- Contraseñas hasheadas con SHA-256
- Ejemplo de hash: `240be518fabd2724ddb6f04eeb1da5967448d7e831c08c8fa822809f74c720a9`

El código implementa:
- Un solo `APP_PASSWORD` en texto plano
- Sin soporte multi-usuario
- Sin hasheo alguno

### 7.2 Sin documentación del schema de datos
No hay documentación de las columnas esperadas en `URLs_Master` ni en `Alertas`. Un nuevo desarrollador no sabría qué campos necesita el Google Sheet.

### 7.3 Sin docstrings
Solo una función (`load_data`) tiene docstring, y es genérica. Las secciones del código solo tienen comentarios decorativos con `═══`.

---

## 8. HISTORIAL GIT

- Solo **4 commits**, todos con mensajes genéricos ("Add files via upload", "Update app.py")
- Sin convención de mensajes de commit
- Sin uso de branches de feature (todo directamente en main)
- Indica desarrollo vía upload directo en GitHub UI, no flujo profesional

---

## Priorización de Correcciones

### P0 — Inmediato (Seguridad)
1. Corregir autenticación: implementar hashing SHA-256 como dice el README, o actualizar el README
2. Eliminar fallback de contraseña vacía
3. Agregar `.gitignore`

### P1 — Corto plazo (Estabilidad)
4. Agregar validación de schema de datos
5. Mejorar manejo de errores con mensajes específicos
6. Fijar versiones de dependencias
7. Agregar logging básico

### P2 — Medio plazo (Mantenibilidad)
8. Refactorizar en módulos separados
9. Extraer funciones de utilidad (filtrado de vacíos, conversión de booleanos)
10. Definir constantes para magic strings
11. Agregar tests unitarios

### P3 — Mejoras (UX/DevOps)
12. CI/CD con GitHub Actions
13. Linting y formatting automáticos
14. Persistencia de filtros
15. Paginación en explorador
