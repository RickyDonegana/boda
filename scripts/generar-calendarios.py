#!/usr/bin/env python3
"""
Genera los archivos de calendario de la boda a partir del CONFIG de index.html:

  public/boda.ics        -> la fecha de la boda, con avisos 1 semana, 1 día y 1 hora antes
  public/cronograma.ics  -> cada momento del cronograma como evento, con alarma a la hora
                            justa, más avisos 1 semana y 1 día antes (y 1 hora antes de la recepción)

Correr cada vez que cambie el cronograma o la fecha:
  python3 scripts/generar-calendarios.py
"""
import re
from datetime import datetime, timedelta, timezone
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
html = (RAIZ / "index.html").read_text(encoding="utf-8")

AR = timezone(timedelta(hours=-3))


def campo(nombre):
    m = re.search(nombre + r':\s*"([^"]+)"', html)
    if not m:
        raise SystemExit(f"No encontré {nombre} en CONFIG")
    return m.group(1)


inicio = datetime.fromisoformat(campo("inicio"))
fin = datetime.fromisoformat(campo("fin"))
lugar_nombre = campo("nombre")
lugar_dir = campo("direccion")
dia = inicio.date()

bloque = re.search(r"cronograma:\s*\[(.*?)\n\s*\],", html, re.S).group(1)
items = []
for linea in re.findall(r"\{[^{}]*\}", bloque):
    hora = re.search(r'hora:\s*"([^"]+)"', linea).group(1)
    que = re.search(r'que:\s*"([^"]+)"', linea).group(1)
    sub = re.search(r'sub:\s*"([^"]+)"', linea)
    items.append({"hora": hora, "que": que, "sub": sub.group(1) if sub else ""})


def a_dt(hhmm):
    h, m = map(int, hhmm.split(":"))
    return datetime(dia.year, dia.month, dia.day, h, m, tzinfo=AR)


for i, it in enumerate(items):
    partes = [p.strip() for p in it["hora"].split(" a ")]
    it["ini"] = a_dt(partes[0])
    if len(partes) > 1:
        it["fin"] = a_dt(partes[1])
    elif i + 1 < len(items):
        it["fin"] = a_dt(items[i + 1]["hora"].split(" a ")[0])
    else:
        it["fin"] = it["ini"] + timedelta(minutes=30)


def utc(dt):
    return dt.astimezone(timezone.utc).strftime("%Y%m%dT%H%M%SZ")


def esc(t):
    return t.replace("\\", "\\\\").replace(";", "\\;").replace(",", "\\,").replace("\n", "\\n")


def plegar(linea):
    """Las líneas de un .ics no deben pasar de 75 bytes."""
    b = linea.encode("utf-8")
    if len(b) <= 75:
        return linea
    out, actual = [], b""
    for ch in linea:
        c = ch.encode("utf-8")
        if len(actual) + len(c) > (75 if not out else 74):
            out.append(actual.decode("utf-8"))
            actual = b""
        actual += c
    out.append(actual.decode("utf-8"))
    return "\r\n ".join(out)


def alarma(trigger, texto):
    return ["BEGIN:VALARM", f"TRIGGER:{trigger}", "ACTION:DISPLAY", f"DESCRIPTION:{esc(texto)}", "END:VALARM"]


SELLO = utc(datetime.now(timezone.utc))
UBIC = esc(f"{lugar_nombre}, {lugar_dir}")


def evento(uid, titulo, ini, fin_, desc, alarmas):
    lineas = ["BEGIN:VEVENT", f"UID:{uid}", f"DTSTAMP:{SELLO}", f"DTSTART:{utc(ini)}", f"DTEND:{utc(fin_)}",
              f"SUMMARY:{esc(titulo)}", f"DESCRIPTION:{esc(desc)}", f"LOCATION:{UBIC}", "STATUS:CONFIRMED"]
    for a in alarmas:
        lineas += a
    lineas.append("END:VEVENT")
    return lineas


def calendario(nombre, eventos):
    lineas = ["BEGIN:VCALENDAR", "VERSION:2.0", "PRODID:-//Cami y Ricky//Boda//ES", "CALSCALE:GREGORIAN",
              "METHOD:PUBLISH", f"X-WR-CALNAME:{esc(nombre)}", "X-WR-TIMEZONE:America/Argentina/Buenos_Aires"]
    for e in eventos:
        lineas += e
    lineas.append("END:VCALENDAR")
    return "\r\n".join(plegar(l) for l in lineas) + "\r\n"


WEB = "https://camiyricky.vercel.app"

# ---------- boda.ics: un solo evento con tres avisos ----------
boda = evento(
    "boda-cami-ricky-20270417@camiyricky",
    "Boda de Cami y Ricky",
    inicio, fin,
    f"¡Nos casamos! Recepción 13 hs, ceremonia 14 hs puntual.\nToda la info: {WEB}",
    [alarma("-P7D", "En una semana es la boda de Cami y Ricky"),
     alarma("-P1D", "Mañana es la boda de Cami y Ricky"),
     alarma("-PT1H", "En una hora empieza la boda de Cami y Ricky")],
)
(RAIZ / "public" / "boda.ics").write_text(calendario("Boda de Cami y Ricky", [boda]), encoding="utf-8")

# ---------- cronograma.ics: un evento por momento, con alarma a la hora justa ----------
# Primero el evento general con los avisos de 1 semana y 1 día antes
eventos = [evento(
    "cronograma-general-cami-ricky-20270417@camiyricky",
    "Boda de Cami y Ricky",
    inicio, fin,
    f"¡Nos casamos! Recepción 13 hs, ceremonia 14 hs puntual.\nToda la info: {WEB}",
    [alarma("-P7D", "En una semana es la boda de Cami y Ricky"),
     alarma("-P1D", "Mañana es la boda de Cami y Ricky")],
)]
for i, it in enumerate(items):
    sig = items[i + 1] if i + 1 < len(items) else None
    titulo = it["que"] + (f" · {it['sub']}" if it["sub"] else "")
    desc = f"Boda de Cami y Ricky.\nAhora: {titulo}."
    if sig:
        desc += f"\nDespués, a las {sig['hora'].split(' a ')[0]} hs: {sig['que']}."
    desc += f"\n{WEB}"
    alarmas = [alarma("PT0M", f"Ahora: {titulo}")]
    if i == 0:
        # La recepción además avisa una hora antes
        # (el iPhone admite hasta 2 avisos por evento, por eso los avisos se reparten)
        alarmas = [alarma("-PT1H", "En una hora empieza la boda de Cami y Ricky")] + alarmas
    eventos.append(evento(f"cronograma-{i:02d}-cami-ricky-20270417@camiyricky",
                          f"Boda C&R · {titulo}", it["ini"], it["fin"], desc, alarmas))

(RAIZ / "public" / "cronograma.ics").write_text(calendario("Cronograma · Boda de Cami y Ricky", eventos), encoding="utf-8")
print(f"OK: boda.ics y cronograma.ics ({len(eventos) - 1} momentos + evento general)")
