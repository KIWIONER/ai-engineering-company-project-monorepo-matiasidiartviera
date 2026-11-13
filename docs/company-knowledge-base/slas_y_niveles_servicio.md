# Nexova Solutions — Acuerdos de Nivel de Servicio (SLAs) y Matriz de Escalamiento

## Matriz de Prioridad y Tiempos de Respuesta
Las incidencias reportadas se clasifican objetivamente en cuatro niveles de criticidad con tiempos máximos garantizados:
- Severidad 1 (Crítica / P1): Interrupción total del servicio o indisponibilidad de la plataforma de producción del cliente. Tiempo de primera respuesta menor a 15 minutos; tiempo máximo de resolución o mitigación operativa menor a 4 horas.
- Severidad 2 (Alta / P2): Degradación sustancial de funciones críticas sin parada total, afectando a múltiples usuarios. Tiempo de primera respuesta menor a 1 hora; tiempo máximo de resolución menor a 8 horas.
- Severidad 3 (Media / P3): Anomalías o fallos que permiten el trabajo alternativo (workaround) y no bloquean el flujo de negocio. Tiempo de primera respuesta menor a 4 horas; resolución comprometida en un plazo máximo de 24 horas laborables.
- Severidad 4 (Baja / P4): Consultas de información, cambios de configuración menores o peticiones administrativas. Tiempo de respuesta menor a 8 horas; resolución en 48 horas laborables.

## Protocolo de Escalamiento Operativo
Si un incidente P1 no cuenta con un diagnóstico preliminar tras 60 minutos de la apertura del ticket, se activa el escalado automático:
1. Notificación inmediata al Service Delivery Manager (SDM) y al Líder de Operaciones (Roberto Díaz).
2. Apertura de una sala de crisis virtual (War Room) con el equipo técnico de guardia y los interlocutores del cliente.
3. Actualización de estado al cliente cada 30 minutos hasta la normalización del servicio.

## Penalizaciones y Créditos de Servicio (Service Credits)
En caso de incumplimiento de los niveles de servicio comprometidos por causas atribuibles exclusivamente a Nexova Solutions, el cliente tendrá derecho a compensación vía créditos de servicio aplicables en la siguiente factura mensual:
- Disponibilidad mensual inferior al 99.5% pero superior al 98.0%: crédito del 5% del valor mensual del contrato.
- Disponibilidad mensual inferior al 98.0%: crédito del 15% del valor mensual del contrato.
- Incumplimiento reiterado de resolución en tickets P1 (más de 2 incidencias en el mes): crédito del 20% del valor mensual.