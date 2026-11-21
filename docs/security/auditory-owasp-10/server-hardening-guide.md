# Guía y Configuración de Endurecimiento de Servidor Linux — Nexova

> **Objetivo:** Cumplir los requisitos de endurecimiento de servidor de `.github/STRATEGY.md` y `docs/nexova-cybersecurity-BRIEFING.md` (§7) aplicando las 4 puertas de `skills/security-audit-suite/references/server-hardening.md`.

---

## 1. Usuario Dedicado No-Root (Operativa Diaria y Servicio)

- **Usuario administrativo de despliegue (`deployuser`):** reemplaza el uso diario de `root`.
  ```bash
  sudo adduser deployuser
  sudo usermod -aG sudo deployuser
  su - deployuser && sudo whoami   # Evidencia esperada: root
  ```
- **Cuenta de servicio de aplicación (`appuser`):** sin privilegios `sudo` ni shell interactiva.
  ```bash
  sudo adduser --system --no-create-home --group --shell /usr/sbin/nologin appuser
  ```

---

## 2. Restricción de Acceso SSH (`/etc/ssh/sshd_config`)

> **Regla operativa:** valida la clave SSH de `deployuser` en una segunda terminal antes de recargar el demonio SSH.

```text
PermitRootLogin no
PasswordAuthentication no
PubkeyAuthentication yes
AllowUsers deployuser
```

Verificación y recarga:
```bash
sudo sshd -t && sudo systemctl reload ssh
sudo grep -E "^(PermitRootLogin|PasswordAuthentication|AllowUsers)" /etc/ssh/sshd_config
```

---

## 3. Permisos Explícitos por Carpeta (Código, Logs y Secretos)

Separación de responsabilidades con principio de mínimo privilegio (cero `chmod 777`):

| Recurso | Propietario / Grupo | Permisos | Propósito |
| :--- | :--- | :---: | :--- |
| `/opt/nexova/app` (código) | `deployuser:appuser` | `750` / `640` | Código legible por el servicio, modificable solo por `deployuser` |
| `/var/log/nexova` (logs) | `appuser:appuser` | `750` / `640` | Solo el proceso de aplicación escribe logs |
| `/opt/nexova/.env` (secretos/API keys) | `appuser:appuser` | `600` | Solo el proceso de la app lee claves de LLM/ATS/JWT |

Comandos de aplicación y auditoría:
```bash
sudo mkdir -p /opt/nexova/app /var/log/nexova
sudo chown -R deployuser:appuser /opt/nexova/app
sudo chown -R appuser:appuser /var/log/nexova /opt/nexova/.env
sudo chmod 750 /opt/nexova/app /var/log/nexova
sudo chmod 600 /opt/nexova/.env

# Verificación: no debe devolver archivos world-writable (777)
find /opt/nexova -perm -0002 -ls
```

---

## 4. Firewall (`ufw`) — Política *Default-Deny*

Solo se permiten puertos estrictamente necesarios hacia el exterior; Redis (`6379`), Flower (`5555`) y Qdrant (`6333`/`6334`) quedan bloqueados al tráfico público.

```bash
sudo ufw default deny incoming
sudo ufw default allow outgoing
sudo ufw allow 22/tcp comment 'SSH administrativo'
sudo ufw allow 443/tcp comment 'HTTPS API y Frontend (reverse proxy)'
sudo ufw enable
```

Evidencia post-configuración:
```bash
sudo ufw status verbose
ss -tulpn
```
