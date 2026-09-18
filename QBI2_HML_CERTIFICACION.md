# QBI2 / RCTA: datos de certificación HML

Fuente: correo de Innovamed del 13/05/2026, archivo local
`Contacto RCTA integraciones.eml`.

Para certificar la integración antes de solicitar las claves de producción,
Innovamed indicó estas dos pruebas de receta:

- OSDE: número de afiliado `23200126801`.
- Accord Salud: número de afiliado `23256785`.

Los identificadores del financiador deben resolverse contra
`GET /apirecipe/GetFinanciadores` en el ambiente HML. Al 16/09/2026, el
catálogo devolvió:

- OSDE: `idFinanciador = 28`.
- ACCORDSALUD: `idFinanciador = 96`.

El correo no exige un plan para estas pruebas. No se debe inferir uno desde la
ficha clínica local. La emisión documentada debajo usó ese juego de
certificación. El cliente simplificado `_2` posteriormente pasó a seleccionar
pacientes de HHCC y a enviar los datos reales guardados en su ficha; no
reemplaza automáticamente esos datos por el afiliado de certificación.

No guardar en este documento tokens, contraseñas ni otras credenciales.

## Verificación del cliente `_2` — 16/09/2026

La primera solicitud, armada con el afiliado real de la ficha clínica
`62333891101`, fue rechazada por HML con `QBI184` y no generó una receta.

Después de reemplazarlo por el afiliado de certificación OSDE y omitir el plan,
se emitió una sola receta de homologación:

- Paciente: Bergonzi Ezequiel, DNI `23101065`.
- Medicamento: LOTRIAL / enalapril 10 mg, `regNo = 34959`.
- Diagnóstico: `I10`, hipertensión esencial (primaria).
- Número de receta: `880006621509`.
- Hash: `KKH5QW7XCK9X6YNFO8K2PY66VP7OAD`.
- Estado: `OK`, sin errores.
- Vigencia informada: 16/09/2026 a 16/10/2026.

El PDF se verificó visualmente: incluye el paciente, la credencial HML, el
medicamento, la firma rasterizada, el sello con MN/MP y el logo profesional.
La receta no fue anulada.

## Agrupación observada de medicamentos — 18/09/2026

Una emisión HML enviada en una única llamada con diez medicamentos confirmó
un comportamiento que no figuraba en la documentación disponible: RCTA
respondió `OK`, sin errores, y devolvió cuatro elementos en `recetas`, agrupados
en `3 + 3 + 3 + 1` medicamentos. Cada elemento incluyó su propio `idReceta`,
hash, CUIR, enlace PDF y verificador.

Por lo tanto, la integración no debe dividir localmente el pedido ni interpretar
solamente el primer elemento de `recetas`. Debe enviar el arreglo completo y
persistir todos los documentos devueltos por RCTA.
