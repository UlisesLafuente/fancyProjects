# Changelog

## [1.1.0]

### Añadido
- Nueva **vista global del proyecto**: cada página se representa como un rectángulo, al estilo de Scribus/InDesign.
- La vista global admite **páginas separadas** (a igual distancia) o **páginas enfrentadas** (la primera sola y después parejas 2-3, 4-5…, dejando sola la última impar).
- Las **tres visualizaciones** (proyecto, horas y global) se muestran **a la vez en tres columnas** redimensionables.
- Al hacer clic en una página de la vista global, las columnas de proyecto y horas hacen scroll hasta esa página.
- Icono de la aplicación en la barra superior.
- **Opciones del proyecto** (Archivo ▸ Opciones del proyecto…): permite cambiar el número de páginas y añadir o quitar tareas en el proyecto abierto.
- Aviso de **cambios sin guardar** al cerrar el proyecto, al crear/abrir/importar otro o al salir de la aplicación (Guardar / Salir sin guardar / Cancelar).

### Cambios
- Proyecto renombrado a **Fanzy Projects** (con z), incluyendo el repositorio, el identificador de la aplicación y los paquetes.
- El color de cada página (en la vista global y como fondo en la vista de proyecto) corresponde a la **última tarea totalmente completada** de la página; se muestra en gris si aún no hay ninguna.
- Interfaz traducida al español (menús **Archivo** y **Ver**, diálogos y mensajes).
- Las páginas de la vista global son más pequeñas para facilitar la visión de conjunto.
- Las columnas se pueden mostrar u ocultar desde **Ver ▸ Vista**.

## [1.0.0]
- Primera versión publicada: gestión de proyectos, páginas y tareas con horas estimadas, seguimiento de progreso, importación/exportación y empaquetados para Linux, macOS y Windows.
