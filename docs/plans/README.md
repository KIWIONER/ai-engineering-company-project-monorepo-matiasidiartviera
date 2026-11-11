# 📚 Índice Cronológico de Planes de Implementación (`docs/plans/`)

Este documento recopila y ordena cronológicamente todos los planes de implementación técnica desarrollados para el proyecto monorepo de **Nexova Solutions**, desde los módulos fundacionales de la plataforma hasta el agente de soporte orquestado con LangGraph.

---

| # | Fecha | Plan de Implementación | Módulo / Área Técnica | Descripción Clave |
| :-: | :---: | :--- | :--- | :--- |
| **01** | `2026-10-08` | [error-handling-plan.md](file:///workspaces/ai-engineering-company-project-monorepo-matiasidiartviera/docs/plans/error-handling-plan.md) | Backend Core | Manejo global y centralizado de excepciones y errores HTTP. |
| **02** | `2026-10-08` | [frontend-performance-audit-plan.md](file:///workspaces/ai-engineering-company-project-monorepo-matiasidiartviera/docs/plans/frontend-performance-audit-plan.md) | Frontend / UX | Auditoría WPO, Core Web Vitals y accesibilidad WCAG 2.1 AA. |
| **03** | `2026-10-08` | [optimizacion-rendimiento-caching-plan.md](file:///workspaces/ai-engineering-company-project-monorepo-matiasidiartviera/docs/plans/optimizacion-rendimiento-caching-plan.md) | Rendimiento | Estrategias de caching y optimización de latencia en consultas. |
| **04** | `2026-10-08` | [plan-autenticacion-frontend.md](file:///workspaces/ai-engineering-company-project-monorepo-matiasidiartviera/docs/plans/plan-autenticacion-frontend.md) | Seguridad / UI | Flujo de login, gestión de tokens JWT y guardas de navegación. |
| **05** | `2026-10-08` | [plan-inventario-activos-nexova.md](file:///workspaces/ai-engineering-company-project-monorepo-matiasidiartviera/docs/plans/plan-inventario-activos-nexova.md) | Dominio de Negocio | Modelo de datos y operaciones CRUD para inventario corporativo. |
| **06** | `2026-10-08` | [plan-inventario-backoffice-nexova.md](file:///workspaces/ai-engineering-company-project-monorepo-matiasidiartviera/docs/plans/plan-inventario-backoffice-nexova.md) | UI Backoffice | Vistas de administración de activos y stock en Next.js. |
| **07** | `2026-10-08` | [serilization-plan.md](file:///workspaces/ai-engineering-company-project-monorepo-matiasidiartviera/docs/plans/serilization-plan.md) | Backend Core | Validación y serialización estricta de datos con esquemas Pydantic. |
| **08** | `2026-10-08` | [telemetry-event-envelope-plan.md](file:///workspaces/ai-engineering-company-project-monorepo-matiasidiartviera/docs/plans/telemetry-event-envelope-plan.md) | Telemetría | Definición del estándar de sobres (envelopes) de eventos telemétricos. |
| **09** | `2026-10-14` | [pipeline-design-plan.md](file:///workspaces/ai-engineering-company-project-monorepo-matiasidiartviera/docs/plans/pipeline-design-plan.md) | Data Engineering | Arquitectura fundacional de pipelines de extracción y transformación. |
| **10** | `2026-10-14` | [telemetry-event-storage-plan.md](file:///workspaces/ai-engineering-company-project-monorepo-matiasidiartviera/docs/plans/telemetry-event-storage-plan.md) | Telemetría | Almacenamiento persistente y estructurado de trazas telemétricas. |
| **11** | `2026-10-14` | [telemetry-implementation-plan.md](file:///workspaces/ai-engineering-company-project-monorepo-matiasidiartviera/docs/plans/telemetry-implementation-plan.md) | Telemetría | Integración del middleware de telemetría y endpoints de ingesta. |
| **12** | `2026-10-15` | [resilient-business-performance-pipeline-plan.md](file:///workspaces/ai-engineering-company-project-monorepo-matiasidiartviera/docs/plans/resilient-business-performance-pipeline-plan.md) | Data Pipelines | Pipeline resiliente para cálculo de KPIs y métricas de desempeño. |
| **13** | `2026-10-20` | [pipeline-subflows-tests-dashboard-plan.md](file:///workspaces/ai-engineering-company-project-monorepo-matiasidiartviera/docs/plans/pipeline-subflows-tests-dashboard-plan.md) | Orquestación | Subflujos en Prefect, suite de tests unitarios y visualización. |
| **14** | `2026-10-20` | [nightly-export-background-jobs-plan.md](file:///workspaces/ai-engineering-company-project-monorepo-matiasidiartviera/docs/plans/nightly-export-background-jobs-plan.md) | Automatización | Tareas nocturnas programadas para exportación y consolidación. |
| **15** | `2026-11-09` | [async-tasks-redis-celery-plan.md](file:///workspaces/ai-engineering-company-project-monorepo-matiasidiartviera/docs/plans/async-tasks-redis-celery-plan.md) | Backend Asíncrono | Configuración de colas distribuidas con Redis y Celery. |
| **16** | `2026-11-09` | [redis-celery-async-tasks-plan.md](file:///workspaces/ai-engineering-company-project-monorepo-matiasidiartviera/docs/plans/redis-celery-async-tasks-plan.md) | Backend Asíncrono | Procesamiento en background de tareas pesadas y monitoreo con Flower. |
| **17** | `2026-11-09` | [sales-forecast-regression-plan.md](file:///workspaces/ai-engineering-company-project-monorepo-matiasidiartviera/docs/plans/sales-forecast-regression-plan.md) | Machine Learning | Modelos de regresión para predicción y estimación de ventas. |
| **18** | `2026-11-09` | [sales-forecast-strategy.md](file:///workspaces/ai-engineering-company-project-monorepo-matiasidiartviera/docs/plans/sales-forecast-strategy.md) | Machine Learning | Estrategia de features, split temporal y métricas de error. |
| **19** | `2026-11-10` | [regression-model-evaluation-timeseries-plan.md](file:///workspaces/ai-engineering-company-project-monorepo-matiasidiartviera/docs/plans/regression-model-evaluation-timeseries-plan.md) | Machine Learning | Evaluación temporal con validación cruzada (Expanding Window CV). |
| **20** | `2026-11-11` | [rag-knowledge-base-qdrant-fastapi-plan.md](file:///workspaces/ai-engineering-company-project-monorepo-matiasidiartviera/docs/plans/rag-knowledge-base-qdrant-fastapi-plan.md) | RAG / Vectores | Sistema RAG con FastEmbed, base vectorial Qdrant y endpoint seguro. |
| **21** | `2026-11-11` | [langgraph-support-agent-base-plan.md](file:///workspaces/ai-engineering-company-project-monorepo-matiasidiartviera/docs/plans/langgraph-support-agent-base-plan.md) | Agente IA / Grafos | Agente de soporte orquestado con LangGraph, checkpointing y evals. |
| **22** | `2026-11-11` | [langgraph-agent-external-tools-plan.md](file:///workspaces/ai-engineering-company-project-monorepo-matiasidiartviera/docs/plans/langgraph-agent-external-tools-plan.md) | Agente IA / Tools | Herramientas externas (incidentes en vivo), enrutador autónomo y evals. |

---

> 💡 *Para consultar los planes directamente en la terminal ordenados por fecha de modificación:*  
> ```bash
> ls -lt docs/plans/
> ```

