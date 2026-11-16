# AeroDocs — sincronización compartida

## Qué hace
El servidor central guarda los 23 países y requisitos del respaldo del 13/11/2026 en SQLite. La página carga **siempre** el estado del servidor y consulta cambios cada **12 segundos** (y cuando vuelves a la pestaña). Un editor guarda desde Ajustes y los demás ven el cambio tras el siguiente sondeo. La edición simultánea usa un número de revisión: si otra persona guardó primero, el sistema bloquea la escritura conflictiva y solicita descargar respaldo y recargar. No se hace mezcla automática de ediciones divergentes.

## Ejecutar localmente (sin dependencias externas)
1. Instala Python 3.10 o superior y descomprime este proyecto.
2. En PowerShell, dentro de la carpeta:

```powershell
$env:AERODOCS_EDIT_TOKEN = "COLOCA_AQUI_UNA_CLAVE_LARGA_Y_ALEATORIA"
python server.py
```

3. Abre http://127.0.0.1:8080. La primera vez que guardes una edición se te pedirá la clave. La clave se almacena solo en `sessionStorage` del navegador, hasta cerrar la sesión/pestaña.
4. Para acceder desde varios equipos, TI debe desplegar **una sola instancia central** del servidor en infraestructura interna, con HTTPS, acceso restringido mediante autenticación corporativa, protección de acceso y copias de seguridad de `aerodocs.sqlite3`. No ejecutes varias instancias sobre archivos SQLite separados: cada una tendría datos distintos.

### Variables de entorno
- `AERODOCS_EDIT_TOKEN` (obligatoria; mínimo 16 caracteres).
- `AERODOCS_DB` (ruta del archivo SQLite persistente; por defecto `./aerodocs.sqlite3`).
- `AERODOCS_HOST` (por defecto `127.0.0.1`; configurar `0.0.0.0` solo detrás de un proxy interno seguro).
- `PORT` (por defecto `8080`).

### Publicación
GitHub Pages y el visor de archivos HTML de SharePoint **no ejecutan Python**, por lo que no pueden alojar esta versión sincronizada por sí solos. Para SharePoint real se requiere conectar una interfaz autorizada a **Microsoft Lists / SharePoint Lists**, por ejemplo usando Power Apps o SPFx con Microsoft Graph y Entra ID. La versión aquí entregada es un servidor independiente listo para instalar en un entorno de pruebas; **no está conectada** a SharePoint ni a una cuenta corporativa.

### Seguridad y operación
- No alojar esta versión directamente en Internet. El token compartido es un control básico para un prototipo y **no sustituye SSO/Entra ID ni permisos por usuario**.
- Ponerlo detrás de proxy HTTPS y autenticación corporativa, con control de red; leer datos también requiere protección al tratarse de información interna.
- No guardar nombres ni datos personales de candidatos: aquí solo se registran particularidades **por nacionalidad**.
- Crear backups regulares de la base de datos SQLite y probar restauraciones. La opción Exportar JSON también genera respaldos manuales.
- La validación normativa sigue siendo del área responsable; el sistema solo organiza la información.
- Si un guardado falla, el navegador conserva un respaldo temporal y se bloquea la sincronización para evitar sobrescribir el trabajo sin avisar. Exportar JSON y recargar una vez resuelto el problema.

### Prueba rápida de sincronización
Abre dos navegadores distintos apuntando al mismo servidor, edita una ficha en uno, guarda y observa el cambio en el otro en unos 12 segundos. Si ambos intentan guardar una misma versión, el segundo recibe una alerta de conflicto.
