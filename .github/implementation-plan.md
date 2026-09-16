# Implementation Plan: Gestión de Inventario (Activos de Nexova)

## Objetivo
Implementar una API de gestión de inventario con arquitectura de doble base de datos (TinyDB para Auth, Supabase para Inventario) para gestionar los activos físicos y digitales de los empleados de **Nexova Solutions**. 

## Entidades (Adaptación a Nexova Solutions)
Dado que Nexova es una consultora de recursos humanos y outsourcing, el "inventario" más crítico a gestionar son los **Activos Corporativos** (licencias de software, equipos para agentes de soporte, etc.).

- **Asset (Equivalente a Producto):** Representa un activo de la empresa (ej. Licencia de HubSpot, Laptop, Headset). 
  - Campos: `id`, `name`, `sku`, `department` (clave de partición definida en el contexto, ej. "Ventas", "Soporte al Cliente").
- **AssetAcquisition (Orden de Entrada):** Registro de compra o alta de nuevos activos.
- **AssetAssignment (Orden de Salida):** Registro de entrega de un activo a un empleado o departamento.

## Pasos de Implementación

### Paso 1: Configuración de Bases de Datos (`.env` y `database.py`)
- **.env:** Agregar cadena de conexión de Supabase (Transaction Pooler, tipo URI). Asegurar que está en `.gitignore`.
- **database.py:** Inicializar el motor `SQLModel` apuntando a Supabase, manteniendo el cliente TinyDB.
- **Inyección:** Crear la dependencia `get_db` usando `Depends()` para inyectar la sesión SQLModel en cada request. *Prohibido usar sesiones globales.*

### Paso 2: Modelos ORM (`models.py`)
- Crear el modelo `Asset` (`table=True`) con los campos definidos.
- Crear el modelo `AssetAcquisition` con `id`, `asset_id` (FK a Asset), `quantity`, `created_at`, y `user_uuid` (string, obtenida de TinyDB).
- Crear el modelo `AssetAssignment` con `id`, `asset_id` (FK a Asset), `quantity`, `created_at`, y `user_uuid`.
- Invocar `SQLModel.metadata.create_all(engine)` al inicio del ciclo de vida de la app (Lifespan o equivalente).

### Paso 3: Schemas Pydantic (`schemas.py`)
- Definir esquemas independientes para request y response (ej. `AssetCreate`, `AssetRead`, `AssetAcquisitionCreate`, etc.).
- Incluir obligatoriamente el campo calculado `current_stock` en el esquema `AssetRead`.
- Asegurar que estos archivos estén físicamente separados de `models.py`.

### Paso 4: Router y Endpoints (`routers/inventory.py`)
- Registrar `APIRouter(prefix="/inventory")`.
- **`GET /inventory/products`**: Retorna lista de `Asset`. El `current_stock` se calcula dinámicamente sumando adquisiciones y restando asignaciones.
- **`POST /inventory/products`**: Crea un `Asset`. *Requiere autenticación.*
- **`GET /inventory/products/{id}`**: Obtiene un `Asset` específico con su stock.
- **`POST /inventory/orders/inbound`**: Registra un `AssetAcquisition`. *Requiere autenticación (guarda el user_uuid).*
- **`POST /inventory/orders/outbound`**: Registra un `AssetAssignment`. *Requiere autenticación.* **Regla estricta:** Antes de persistir, debe validar que `quantity` no supere el stock actual en ese `department`. Si lo supera, devuelve `HTTP 400`.
- **`GET /inventory/orders`**: Lista todas las órdenes (inbound y outbound) con datos relacionales.

### Paso 5: Datos Semilla y Pruebas
- Crear un script semilla que introduzca activos reales de Nexova (ej. Licencias de software para el equipo de Ventas, Headsets para los 30 agentes de Soporte).
- Validar rigurosamente que una orden de salida mayor al stock lance HTTP 400.

---

## ⚙️ Métodos Aplicados (Code Refinement Suite)
- **Step-Back Prompting / Abstracción (PACK PLANNER):** Se analizó primero el contexto general de Nexova Solutions para determinar la entidad de inventario más lógica (Activos Corporativos) alejándonos de un modelo retail genérico.
- **Self-Refinement Loop (PACK PLANNER):** El plan fue estructurado asegurando el cumplimiento estricto de los "criterios de evaluación" de `STRATEGY.md` (separación de schemas/models, stock inmutable, Depends, rechazo HTTP 400).
- **Simulación de Seguridad (PACK AUDITOR / PRE-PLAN):** Se planificó explícitamente el control de stock negativo previo a la escritura en DB para prevenir condiciones de carrera lógicas en las salidas de inventario.
