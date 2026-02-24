# 🔍 PcComponentes Blog Audit Dashboard

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

Para generar el hash de una contraseña:
```python
import hashlib
hashlib.sha256("tu_contraseña".encode()).hexdigest()
```

## Seguridad

La app es pública pero tiene login con usuario/contraseña. Las contraseñas se almacenan como hash SHA-256 en los Secrets de Streamlit (nunca en texto plano).
