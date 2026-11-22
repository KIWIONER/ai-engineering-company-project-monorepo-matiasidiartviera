---
name: ai-governance-nist
description: Gobernanza de IA, Seguridad por Diseño y cumplimiento NIST CSF 2.0 (Govern, Identify, Protect, Detect, Respond, Recover). Úsala al diseñar nuevas funciones con LLMs, mantener el inventario de sistemas de IA, evaluar responsabilidad compartida con proveedores, aplicar minimización RGPD/FIPA/FCRA/EU AI Act o redactar informes NIST.
---

# AI Governance & NIST Security-by-Design

Skill complementaria a `security-audit-suite`: mientras `security-audit-suite` audita vulnerabilidades técnicas (OWASP Web/LLM y servidor), **`ai-governance-nist`** gobierna el **diseño seguro**, el **inventario vivo**, la **responsabilidad compartida** y el **ciclo NIST CSF 2.0** de todo componente que toca un modelo de lenguaje.

---

## 🧠 Regla de Diseño Previo (Design-Time Governance)

Antes de escribir o modificar cualquier función que invoque un LLM o agente, responde estas 5 preguntas:

1. **¿Qué datos salen hacia el modelo?** Aplicar minimización estricta (solo campos necesarios, sin PII innecesaria).
2. **¿Pertenecen a una categoría regulada?** Mapear marco aplicable (p. ej. **RGPD** AEPD 72h, **Ley de IA de la UE** —empleo/scoring = Alto Riesgo—, **FIPA** 30 días, **FCRA**, **FERPA**, **HIPAA**).
3. **¿Qué permite el contrato del proveedor?** Verificar retención y cláusula de **no entrenamiento** con entradas.
4. **¿Qué acciones requieren confirmación humana (HITL)?** Toda acción irreversible o por encima del umbral de impacto (`BULK_THRESHOLD`) exige revisión humana con detalle concreto (destinatario, registro, impacto).
5. **¿Cuál es el peor resultado plausible si esta tool se invoca con los peores argumentos, y qué lo detiene?** Si la única defensa es "el prompt le dice que no lo haga", falta un control determinista en código.

---

## 🔄 Flujo de Trabajo en 4 Fases

### Fase 1 — Inventario Vivo y Responsabilidad Compartida (`Identify` + `Govern`)
- Registrar cada componente de IA usando [ai-inventory-template.md](resources/ai-inventory-template.md): propietario interno, proveedor/modelo/versión, datos de entrada, política de retención/entrenamiento, revisión humana y manejo de fallos.
- Documentar todos los **puntos de entrada de texto externo** al LLM (usuario, documentos RAG, respuestas de herramientas MCP, salidas de otros agentes).
- Definir la división de control (**Responsable / Desplegador** vs. **Encargado / Proveedor**): usar un proveedor externo nunca transfiere la responsabilidad sobre el propósito ni los datos enviados.

### Fase 2 — Seguridad por Diseño en los 2 Flujos No Confiables (`Protect`)
Aplicar los patrones de [security-by-design-patterns.md](references/security-by-design-patterns.md):
- **Secretos:** cero claves hardcoded; variables de entorno / vault con arranque *fail-secure*.
- **Entrada al modelo:** delimitación explícita (`---INICIO ENTRADA---` / `<external_data>`), minimización de PII y filtrado multi-tenant/rol *antes* de ensamblar el contexto RAG/MCP.
- **Salida del modelo:** tratar toda salida (texto, JSON, SQL, llamadas a tools) como entrada no confiable; validar mediante puerta determinista `review_action(action)` (*fail-secure* → `"allowed"` | `"confirm"` | `"denied"`).
- **Disponibilidad y costo:** rate limiting verificable en endpoints de IA, límites de entrada/salida, topes de iteración y timeouts.

### Fase 3 — Detección, Respuesta y Recuperación (`Detect` + `Respond` + `Recover`)
- **Detect:** logging forense estructurado de cada decisión de agente (modelo/versión, usuario, tool, argumentos saneados, veredicto y timestamp; redactando secretos y PII cruda) + alertas calibradas.
- **Respond:** roles preasignados (Líder de Respuesta, Oficial de Comunicaciones, Equipo Técnico), autoridad de contención y plazos legales de notificación.
- **Recover:** objetivos **RTO / RPO** definidos, pruebas periódicas de restauración y retroalimentación de lecciones aprendidas a `Identify` y `Protect`.

### Fase 4 — Informe NIST y Mantenimiento Continuo
- Generar o actualizar el informe usando [nist-report-template.md](resources/nist-report-template.md) cubriendo las **6 funciones NIST** con acciones priorizadas y brechas pendientes documentadas.
- Cada PR que agregue un modelo, cambie un prompt o conecte una nueva fuente de datos debe actualizar el inventario en el mismo ciclo.
