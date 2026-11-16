# AeroDocs — sincronización compartida

## Qué hace
El servidor central guarda los 23 países y requisitos del respaldo del 13/11/2026 en SQLite. La página carga **siempre** el estado del servidor y consulta cambios cada **12 segundos** (y cuando vuelves a la pestaña). Un editor guarda desde Ajustes y los demás ven el cambio tras el siguiente sondeo. La edición simultánea usa un número de revisión: si otra persona guardó primero, el sistema bloquea la escritura conflictiva y solicita descargar respaldo y recargar. No se hace mezcla automática de ediciones divergentes.

### Prueba rápida de sincronización
Abre dos navegadores distintos apuntando al mismo servidor, edita una ficha en uno, guarda y observa el cambio en el otro en unos 12 segundos. Si ambos intentan guardar una misma versión, el segundo recibe una alerta de conflicto.
