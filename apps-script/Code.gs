/**
 * Boda Cami & Ricky · Backend en Google Apps Script
 *
 * Recibe las confirmaciones de asistencia y los comprobantes de regalos
 * desde la página, y devuelve el total del fondo común.
 *
 * Se instala dentro de la planilla "Lista de Invitados - Casamiento"
 * (Extensiones > Apps Script). Ver LEEME.md.
 */

const HOJA_CONFIRMACIONES = "Confirmaciones";
const HOJA_REGALOS = "Regalos";
const CARPETA_COMPROBANTES = "Comprobantes Boda Cami y Ricky";

const COLUMNAS_CONFIRMACIONES = ["Fecha", "Nombre", "Asiste", "Acompañantes", "Menú", "Mensaje"];
const COLUMNAS_REGALOS = ["Fecha", "Nombre", "Moneda", "Monto", "Monto en pesos", "Estado", "Comprobante", "Mensaje"];

/** GET ?accion=fondo → { ok, recaudado } (suma de "Monto en pesos" de los regalos aprobados) */
function doGet(e) {
  const accion = (e && e.parameter && e.parameter.accion) || "";
  if (accion === "fondo") {
    return json_({ ok: true, recaudado: totalAprobado_() });
  }
  return json_({ ok: true });
}

/** POST con JSON (Content-Type text/plain) */
function doPost(e) {
  try {
    const datos = JSON.parse(e.postData.contents);
    if (datos.tipo === "confirmacion") return json_(guardarConfirmacion_(datos));
    if (datos.tipo === "regalo") return json_(guardarRegalo_(datos));
    return json_({ ok: false, error: "Tipo desconocido" });
  } catch (err) {
    return json_({ ok: false, error: String(err) });
  }
}

function guardarConfirmacion_(d) {
  if (!d.nombre || !d.asiste) return { ok: false, error: "Faltan datos" };
  const hoja = hoja_(HOJA_CONFIRMACIONES, COLUMNAS_CONFIRMACIONES);
  hoja.appendRow([new Date(), limpiar_(d.nombre), limpiar_(d.asiste), limpiar_(d.acompanantes),
                  limpiar_(d.menu), limpiar_(d.mensaje)]);
  return { ok: true };
}

function guardarRegalo_(d) {
  const monto = Number(d.monto);
  if (!d.nombre || !(monto > 0) || !d.archivo || !d.archivo.base64) return { ok: false, error: "Faltan datos" };

  const bytes = Utilities.base64Decode(d.archivo.base64);
  if (bytes.length > 5 * 1024 * 1024) return { ok: false, error: "Archivo muy grande" };

  const nombreArchivo = Utilities.formatDate(new Date(), "America/Argentina/Buenos_Aires", "yyyy-MM-dd HHmm")
    + " - " + limpiar_(d.nombre) + " - " + (d.archivo.nombre || "comprobante");
  const blob = Utilities.newBlob(bytes, d.archivo.tipo || "application/octet-stream", nombreArchivo);
  const archivo = carpeta_().createFile(blob);

  const moneda = d.moneda === "USD" ? "USD" : "ARS";
  const hoja = hoja_(HOJA_REGALOS, COLUMNAS_REGALOS);
  // En pesos se completa solo. En dólares, completar "Monto en pesos" a mano con la cotización.
  hoja.appendRow([new Date(), limpiar_(d.nombre), moneda, monto, moneda === "ARS" ? monto : "",
                  "Pendiente", archivo.getUrl(), limpiar_(d.mensaje)]);
  return { ok: true };
}

/** Suma "Monto en pesos" de las filas con Estado = "Aprobado". */
function totalAprobado_() {
  const hoja = hoja_(HOJA_REGALOS, COLUMNAS_REGALOS);
  const valores = hoja.getDataRange().getValues();
  const iMonto = COLUMNAS_REGALOS.indexOf("Monto en pesos");
  const iEstado = COLUMNAS_REGALOS.indexOf("Estado");
  let total = 0;
  for (let i = 1; i < valores.length; i++) {
    if (String(valores[i][iEstado]).trim().toLowerCase() === "aprobado") total += Number(valores[i][iMonto]) || 0;
  }
  return total;
}

/* ---------- auxiliares ---------- */

function hoja_(nombre, columnas) {
  const libro = SpreadsheetApp.getActiveSpreadsheet();
  let hoja = libro.getSheetByName(nombre);
  if (!hoja) {
    hoja = libro.insertSheet(nombre);
    hoja.appendRow(columnas);
    hoja.setFrozenRows(1);
    hoja.getRange(1, 1, 1, columnas.length).setFontWeight("bold");
    if (nombre === HOJA_REGALOS) {
      const regla = SpreadsheetApp.newDataValidation().requireValueInList(["Pendiente", "Aprobado", "Rechazado"], true).build();
      hoja.getRange(2, columnas.indexOf("Estado") + 1, 1000, 1).setDataValidation(regla);
    }
  }
  return hoja;
}

function carpeta_() {
  const it = DriveApp.getFoldersByName(CARPETA_COMPROBANTES);
  return it.hasNext() ? it.next() : DriveApp.createFolder(CARPETA_COMPROBANTES);
}

/** Evita que un texto se interprete como fórmula en la planilla. */
function limpiar_(v) {
  const s = String(v == null ? "" : v).slice(0, 1000).trim();
  return /^[=+\-@]/.test(s) ? "'" + s : s;
}

function json_(obj) {
  return ContentService.createTextOutput(JSON.stringify(obj)).setMimeType(ContentService.MimeType.JSON);
}
