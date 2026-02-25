# Revisión del Repositorio — pcc-blog-audit-dashboard

**Fecha:** 2026-02-25 (actualizado)
**Alcance:** Revisión completa tras 4 rondas de optimización + mejoras de calidad.

---

## Estado Actual

El dashboard ha pasado por múltiples iteraciones de mejora:

1. **Migración Plotly → Altair** — Reducción de ~3.5MB → ~400KB en payload JS (9x más ligero)
2. **Renderizado condicional** — `st.radio` + `if/elif` en lugar de `st.tabs` (solo se renderiza la pestaña activa)
3. **`@st.fragment`** en Alertas — Los filtros internos no provocan rerun completo
4. **Columnas pre-computadas** — Máscaras booleanas `_ne_*` y columnas `_*_lower` en `load_data()`
5. **Autenticación multi-usuario con SHA-256** — Protección brute-force incluida
6. **Tema Altair personalizado** — Estilo visual Metabase consistente

---

## Hallazgos Actuales y Mejoras Aplicadas

### Corregidos en esta revisión

| Problema | Solución |
|----------|----------|
| `timedelta` importado inline (PEP 8) | Movido a importaciones de nivel superior |
| `altair` no explícito en requirements.txt | Añadido `altair>=5.0.0,<6.0.0` |
| Filtros de carrusel/alertas sin check de columna | Añadidos `if col in df.columns` defensivos |
| `.head(25)` hardcodeado en contenido antiguo | Reemplazado por slider configurable (10–100) |
| Sin exportación en pestaña Alertas | Añadidos botones CSV/Excel |
| Sin indicador de carga al recargar | Añadido `st.spinner` al botón Recargar |
| Sin filtro por fecha de publicación | Añadido `st.date_input` con rango en sidebar |

---

## Mejoras Pendientes (Recomendadas)

### P1 — Corto plazo
1. **Persistir filtros en URL** — Usar `st.query_params` para que los filtros sobrevivan recargas
2. **Paginación en Explorador** — Con datasets >5000 URLs, considerar paginación o límite con "cargar más"
3. **Tests unitarios** — Al menos para `load_data()`, chart helpers y autenticación

### P2 — Medio plazo
4. **Modularizar** — Separar auth, data loading, componentes de UI en ficheros independientes
5. **CI/CD** — GitHub Actions para lint (ruff) y tests automáticos
6. **Expiración de sesión** — Timeout de inactividad configurable

### P3 — Mejoras UX
7. **Estados vacíos** — Mensajes consistentes cuando un gráfico no tiene datos
8. **Descarga de gráficos** — Habilitar exportación SVG/PNG desde Altair
9. **Modo oscuro** — Alternativa al tema claro actual

---

## Fortalezas del Proyecto

- Autenticación robusta (SHA-256, multi-usuario, brute-force)
- Rendimiento optimizado (Altair, renderizado condicional, @st.fragment)
- Esquema de datos documentado en README
- Manejo de errores granular en carga de datos
- CSS personalizado coherente (tema Metabase)
- Dependencias versionadas con límites superiores
