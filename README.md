# DSLIA

Bot de Discord para gestión de archivos, entregas y recursos académicos.

## Tabla de Contenidos
- [Requisitos](#requisitos)
- [Instalación](#instalación)
- [Configuración](#configuración)
- [Ejecución](#ejecución)
- [Uso y Comandos](#uso-y-comandos)
- [Roles y Permisos](#roles-y-permisos)
- [Ejemplos de Comandos](#ejemplos-de-comandos)

---

## Requisitos
- Hasta Python 3.11.9
- pip (gestor de paquetes de Python)
- Acceso a un servidor de Discord donde tengas permisos de administrador

## Instalación
1. **Clona o descarga este repositorio** en tu máquina local.
2. Abre una terminal en la carpeta del proyecto.
3. Instala las dependencias ejecutando:
   ```powershell
   pip install -r requirements.txt
   ```

## Configuración
1. Crea un bot en el [Portal de Desarrolladores de Discord](https://discord.com/developers/applications) y copia el token.
2. En el archivo `dst.py` (si no lo tiene generelo), agrega una variable llamada `TOKEN` con tu token de bot:
   ```python
   TOKEN = "TU_TOKEN_AQUI"
   ```
3. (Opcional) Configura los roles en tu servidor de Discord. El bot utiliza el rol `Docente` para comandos administrativos.

## Ejecución
En la terminal, ejecuta:
```powershell
python main.py
```
El bot se conectará a tu servidor de Discord.

## Uso y Comandos
El bot responde a los siguientes comandos (prefijo `!`):
- `!help`: Muestra la ayuda de comandos.
- `!prueba <texto>`: Repite el texto que escribas.
- `!saludo`: El bot te saluda.
- `!subir`: (Docente) Sube un archivo de teoría, TP o bibliografía.
- `!ver_archivos [filtro]`: Muestra los archivos subidos. Puedes filtrar por 'teoria', 'tp', 'bibliografia'.
- `!descargar <categoria>`: Muestra los archivos de la categoría elegida y permite descargarlos con botones interactivos.
- `!buscar [filtros]`: Busca materiales por tipo, fecha o autor. Ejemplo: `!buscar tipo=teoria fecha=2025-06-01 autor=Juan`
- `!eliminar_archivo <nombre>`: (Docente) Elimina un archivo por nombre.
- `!enviar_archivo <criterio>`: Envía archivos por privado según nombre, tipo o 'todo'.
- `!agregar_entrega`: (Docente) Agrega una entrega y programa recordatorios automáticos.
- `!listar_entregas`: Muestra la lista de entregas próximas.

## Roles y Permisos
- El rol `Docente` es necesario para usar comandos administrativos como `!subir`, `!eliminar_archivo` y `!agregar_entrega`.
- Los estudiantes pueden usar los comandos de consulta y descarga.

## Ejemplos de Comandos
- `!subir` → Sube un archivo (solo Docente). El bot te guiará paso a paso.
- `!ver_archivos teoria` → Muestra todos los archivos de teoría.
- `!descargar tp` → Descarga archivos de trabajos prácticos.
- `!agregar_entrega` → Agrega una nueva entrega (solo Docente). El bot pedirá nombre, fecha, hora y canal.
- `!listar_entregas` → Lista todas las entregas próximas.
- `!buscar tipo=tp fecha=2025-06-10` → Busca archivos de TP subidos en una fecha específica.

---

Para dudas o problemas, consulta el código fuente o abre un issue.
