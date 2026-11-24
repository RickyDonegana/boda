# Conectar la página con la planilla

Este código guarda las **confirmaciones de asistencia** y los **comprobantes de regalos** en la planilla "Lista de Invitados - Casamiento", y le pasa a la página el **total del fondo común**.

## Instalación (una sola vez, unos 5 minutos)

1. Abrí la planilla **Lista de Invitados - Casamiento** en Google Sheets.
2. Andá a **Extensiones → Apps Script**.
3. Borrá lo que haya en `Código.gs` y pegá todo el contenido de `Code.gs`.
4. Guardá (ícono del disquete).
5. Arriba a la derecha: **Implementar → Nueva implementación**.
   - Tipo: **Aplicación web**.
   - Ejecutar como: **Yo**.
   - Quién tiene acceso: **Cualquier usuario**.
6. Tocá **Implementar** y aceptá los permisos que pide Google (planilla y Drive).
7. Copiá la **URL de la aplicación web** (termina en `/exec`).
8. En `index.html`, buscá `appsScriptUrl: ""` y pegá la URL entre las comillas.

La primera vez que alguien confirme o mande un comprobante, se crean solas las pestañas **Confirmaciones** y **Regalos**, y la carpeta de Drive **Comprobantes Boda Cami y Ricky**.

## Cómo se actualiza el fondo

- Cada comprobante entra en la pestaña **Regalos** con estado **Pendiente**.
- Revisan que el dinero haya llegado y cambian el estado a **Aprobado**.
- Si es en dólares, completan a mano la columna **Monto en pesos** con la cotización que quieran usar.
- La página suma solo los regalos **Aprobados** y muestra el total en la barra del fondo.

## Si cambian el código más adelante

Después de pegar una versión nueva: **Implementar → Administrar implementaciones → editar (lápiz) → Versión: Nueva versión → Implementar**. Así la URL sigue siendo la misma.
