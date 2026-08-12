# Roles de repositorio

Fecha de vigencia: 2026-08-11.

## `/home/eze/omar`

Es el unico repositorio operativo del sistema de historias clinicas.

- El codigo canonico vive en `hhcc/`.
- Las pruebas, cambios, migraciones, imagenes Docker, QA y despliegues parten de este directorio.
- Toda decision tecnica debe contrastarse contra este codigo antes de implementarse.
- La documentacion operativa que describe comportamiento vigente debe vivir aqui, junto al codigo correspondiente.

## `/home/eze/omar-codex`

Es repositorio de memoria tecnica y espacio auxiliar de sesiones.

- Conserva reportes, capturas, scraping, evidencia, documentos historicos y notas de continuidad.
- Su arbol `hhcc/` es un snapshot legado y no es fuente de cambios ni de despliegue.
- No copiar codigo desde `omar-codex/hhcc/` a `omar` sin una decision explicita, comparacion contra el codigo vigente y pruebas en `omar`.
- Puede usarse para preparar analisis, scripts de inspeccion o documentacion, pero los cambios de la aplicacion se realizan en `omar`.

## Regla de sesion

1. Empezar en `/home/eze/omar`.
2. Leer `MAPA_TECNICO.md`, `ARRANQUE_SESION.md` y la documentacion del dominio involucrado.
3. Consultar `/home/eze/omar-codex` solo para antecedentes, evidencia o contexto historico.
4. Ejecutar pruebas y desplegar exclusivamente desde `/home/eze/omar`.

## Conservacion del legado

No se elimina ni se reorganiza masivamente `omar-codex/hhcc/` hasta hacer una auditoria independiente y conservar un snapshot Git recuperable. Su estado actual no debe contaminar los commits operativos de `omar`.
