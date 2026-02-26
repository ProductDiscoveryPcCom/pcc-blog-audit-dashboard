"""
Authentication module — SHA‑256 hashed, multi‑user, brute‑force protection.
"""

import streamlit as st
import hashlib
import logging
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)

MAX_LOGIN_ATTEMPTS = 5
LOGIN_LOCKOUT_SECONDS = 300


def hash_password(password: str) -> str:
    return hashlib.sha256(password.encode()).hexdigest()


def _authenticate(username: str, password: str) -> bool:
    users = st.secrets.get("users", {})
    if not users:
        logger.warning("No users configured in secrets")
        st.error("No hay usuarios configurados. Añade la sección [users] en Secrets.")
        return False
    stored_hash = users.get(username)
    if stored_hash is None:
        return False
    return hash_password(password) == stored_hash


def render_login() -> bool:
    """Show login form.  Returns True if user is now authenticated."""
    if st.session_state.get("authenticated"):
        return True

    now = datetime.now()
    lockout_until = st.session_state.get("lockout_until")
    is_locked = lockout_until is not None and now < lockout_until

    st.markdown('<div class="login-container">', unsafe_allow_html=True)
    st.markdown('<div class="login-title">Blog Audit</div>', unsafe_allow_html=True)
    st.markdown(
        '<div class="login-subtitle">PcComponentes — Dashboard de contenido</div>',
        unsafe_allow_html=True,
    )

    if is_locked:
        remaining = int((lockout_until - now).total_seconds())
        st.error(f"Demasiados intentos. Espera {remaining}s antes de reintentar.")
    else:
        username = st.text_input("Usuario", placeholder="Tu nombre de usuario")
        password = st.text_input(
            "Contraseña", type="password", placeholder="Introduce tu contraseña"
        )
        if st.button("Entrar", use_container_width=True):
            if not username or not password:
                st.warning("Introduce usuario y contraseña")
            elif _authenticate(username, password):
                st.session_state["authenticated"] = True
                st.session_state["current_user"] = username
                st.session_state["login_attempts"] = 0
                logger.info("User '%s' logged in", username)
                st.rerun()
            else:
                st.session_state["login_attempts"] += 1
                attempts = st.session_state["login_attempts"]
                logger.warning("Failed login #%d for '%s'", attempts, username)
                if attempts >= MAX_LOGIN_ATTEMPTS:
                    st.session_state["lockout_until"] = now + timedelta(
                        seconds=LOGIN_LOCKOUT_SECONDS
                    )
                    st.error(
                        f"Demasiados intentos. Bloqueado {LOGIN_LOCKOUT_SECONDS // 60} min."
                    )
                else:
                    st.error(
                        f"Credenciales incorrectas. {MAX_LOGIN_ATTEMPTS - attempts} intentos."
                    )

    st.markdown("</div>", unsafe_allow_html=True)
    return False
