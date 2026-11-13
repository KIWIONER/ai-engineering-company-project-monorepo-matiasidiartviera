# Documentación de la Skill: `fastapi-enterprise-api-builder`

## 🎯 Propósito y Alcance
Esta skill proporciona el estándar de ingeniería para diseñar y desplegar **APIs REST de grado empresarial con FastAPI**. 

Elimina cualquier dependencia en bases de datos embebidas de prototipado (como TinyDB) y establece una arquitectura pura en capas que utiliza **SQLModel / PostgreSQL**, contratos fuertemente tipados con **Pydantic V2**, seguridad centralizada (**Auth Guard Standard**) y pruebas automatizadas rigurosas.

---

## 🏛️ Casos de Uso Empresariales

### 1. Construcción de Nuevos Recursos y Microservicios
**Escenario:** Se requiere exponer un nuevo recurso de negocio (ej. `Invoices`, `Tasks`, `Tickets`, `Profiles`).
**Cómo actúa la skill:**
- Define los 4 DTOs Pydantic V2 (`Base`, `Create`, `Update`, `Response`).
- Desacopla la lógica de base de datos en repositorios con sesiones SQLModel.
- Implementa endpoints con verbos REST canónicos (`POST`, `GET`, `PATCH`, `DELETE`).
- Registra el router con prefijos y etiquetas OpenAPI para Swagger/ReDoc.

### 2. Cumplimiento de Seguridad y Zero-Trust
**Escenario:** Proteger datos corporativos sensibles contra accesos no autenticados.
**Cómo actúa la skill:**
- Inyecta obligatoriamente `Depends(get_current_user)` en todos los endpoints de negocio.
- Asegura que cualquier intento de acceso anónimo devuelva `401 Unauthorized`.

### 3. Blindaje de Excepciones y OWASP API Security
**Escenario:** Fallos de conexión a la base de datos o violaciones de integridad referencial.
**Cómo actúa la skill:**
- Captura errores en la capa de servicio/controlador y los traduce a respuestas HTTP estandarizadas.
- Oculta detalles internos de la base de datos, evitando fugas de información sensible en stack traces.

### 4. Ciclo de Desarrollo y Testing con UV
**Escenario:** Incorporar librerías o correr pruebas continuas en CI/CD.
**Cómo actúa la skill:**
- Exige el uso exclusivo del gestor `uv`: `uv add <paquete>` y `uv run pytest`.
