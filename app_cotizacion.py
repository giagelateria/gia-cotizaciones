#!/usr/bin/env python3
"""
GIA Gelateria — App Web de Cotizaciones
Ejecutar: streamlit run app_cotizacion.py
"""

import streamlit as st
import io
import os
from datetime import datetime
from reportlab.lib.pagesizes import letter
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Image,
    HRFlowable, Table, TableStyle
)
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.units import inch, cm
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_JUSTIFY
from reportlab.pdfgen import canvas as rl_canvas
from reportlab.lib.utils import ImageReader

# ── Rutas de assets ────────────────────────────────────────────────────────────
BASE_DIR    = os.path.dirname(os.path.abspath(__file__))
LOGO_PATH   = os.path.join(BASE_DIR, "logo_gia.png")
PATRON_PATH = os.path.join(BASE_DIR, "patron_dorado.png")
FOTO1_PATH  = os.path.join(BASE_DIR, "foto_gia_1.png")
FOTO2_PATH  = os.path.join(BASE_DIR, "foto_gia_2.jpeg")
FOTO3_PATH  = os.path.join(BASE_DIR, "foto_gia_3.png")

# ── Colores GIA ────────────────────────────────────────────────────────────────
NAVY   = colors.HexColor("#3D4A6B")
GOLD   = colors.HexColor("#B8A96A")
LIGHT  = colors.HexColor("#F7F5F0")
BLACK  = colors.HexColor("#1A1A1A")
GRAY   = colors.HexColor("#666666")

# ── Precios ────────────────────────────────────────────────────────────────────
PRECIO_100_CTG    = 2_500_000
COSTO_EMPLEADO    =   100_000
COSTO_TRANSPORTE  =   250_000
SURCHARGE_RURAL   =   400_000
FIJOS_CTG         = COSTO_EMPLEADO + COSTO_TRANSPORTE
PRECIO_POR_GELATO = (PRECIO_100_CTG - FIJOS_CTG) / 100   # 21,500

def calcular_precio(cantidad: int, es_rural: bool) -> int:
    fijos = FIJOS_CTG + (SURCHARGE_RURAL if es_rural else 0)
    return int(round((fijos + cantidad * PRECIO_POR_GELATO) / 50_000) * 50_000)

def fmt_precio(p: int) -> str:
    return "${:,.0f} COP".format(p).replace(",", ".")

# ── Textos por tipo de evento ──────────────────────────────────────────────────
TEXTOS = {
    "Boda": {
        "titulo_tipo": "BODA",
        "intro": "En una boda, el postre no es un detalle más: es uno de los últimos recuerdos que se llevan los invitados. Un momento de pausa, celebración y disfrute compartido. Nuestra propuesta está pensada para crear una experiencia fresca, elegante y memorable.",
        "subtitulo": "Propuesta GIA para su boda",
        "descripcion": "Servicio de gelato artesanal servido en sitio, diseñado para integrarse de manera armónica al ambiente del evento y sorprender a sus invitados con un momento distinto y especial.",
        "nota_reserva": "Debido a la alta demanda en temporada de bodas en Cartagena, las fechas se confirman únicamente con el abono correspondiente.",
        "cierre": "Con gusto coordinamos junto a ustedes la selección de sabores y el momento ideal del servicio dentro del cronograma de la boda, para que el gelato se convierta en uno de los momentos más especiales de la celebración.",
        "despedida": "Quedamos atentos para acompañarlos y hacer parte de este día tan especial.",
    },
    "Matrimonio": {
        "titulo_tipo": "MATRIMONIO",
        "intro": "En un matrimonio, el postre no es un detalle más: es uno de los últimos recuerdos que se llevan los invitados. Un momento de pausa, celebración y disfrute compartido. Nuestra propuesta está pensada para crear una experiencia fresca, elegante y memorable.",
        "subtitulo": "Propuesta GIA para su matrimonio",
        "descripcion": "Servicio de gelato artesanal servido en sitio, diseñado para integrarse de manera armónica al ambiente del evento y sorprender a sus invitados con un momento distinto y especial.",
        "nota_reserva": "Debido a la alta demanda en temporada de matrimonios en Cartagena, las fechas se confirman únicamente con el abono correspondiente.",
        "cierre": "Con gusto coordinamos junto a ustedes la selección de sabores y el momento ideal del servicio dentro del cronograma del matrimonio, para que el gelato se convierta en uno de los momentos más especiales de la celebración.",
        "despedida": "Quedamos atentos para acompañarlos y hacer parte de este día tan especial.",
    },
    "Cumpleaños": {
        "titulo_tipo": "CUMPLEAÑOS",
        "intro": "Un cumpleaños merece un momento de celebración auténtica. El gelato artesanal de GIA convierte cualquier reunión en una experiencia gastronómica que los invitados recordarán con cariño.",
        "subtitulo": "Propuesta GIA para su celebración",
        "descripcion": "Servicio de gelato artesanal servido en sitio, diseñado para deleitar a sus invitados y hacer de su cumpleaños un momento fresco, divertido y memorable.",
        "nota_reserva": "Las fechas se confirman únicamente con el abono correspondiente.",
        "cierre": "Con gusto coordinamos la selección de sabores y el momento ideal del servicio para que el gelato sea la sorpresa de la noche.",
        "despedida": "Quedamos atentos para acompañarlos y hacer de este cumpleaños algo verdaderamente especial.",
    },
    "Evento Corporativo": {
        "titulo_tipo": "EVENTO CORPORATIVO",
        "intro": "En los eventos corporativos, los detalles marcan la diferencia. Un servicio de gelato artesanal GIA añade un toque distintivo y sofisticado que eleva la experiencia de sus colaboradores e invitados.",
        "subtitulo": "Propuesta GIA para su evento",
        "descripcion": "Servicio de gelato artesanal servido en sitio, diseñado para integrarse al ambiente corporativo y ofrecer un momento de disfrute a todos los asistentes.",
        "nota_reserva": "Las fechas se confirman únicamente con el abono correspondiente.",
        "cierre": "Con gusto coordinamos la selección de sabores, el momento de servicio y la integración con el cronograma de su evento, para garantizar una experiencia impecable.",
        "despedida": "Quedamos atentos para acompañarlos y hacer parte de este evento.",
    },
    "Congreso": {
        "titulo_tipo": "CONGRESO",
        "intro": "En los congresos y encuentros profesionales, los espacios de networking cobran vida con experiencias gastronómicas únicas. El gelato artesanal GIA es el complemento perfecto para generar conversaciones y momentos de conexión.",
        "subtitulo": "Propuesta GIA para su congreso",
        "descripcion": "Servicio de gelato artesanal servido en sitio, diseñado para enriquecer los espacios de pausa y networking de su congreso con una experiencia memorable.",
        "nota_reserva": "Las fechas se confirman únicamente con el abono correspondiente.",
        "cierre": "Con gusto coordinamos la selección de sabores y el momento ideal del servicio dentro del programa del congreso.",
        "despedida": "Quedamos atentos para acompañarlos en este importante evento.",
    },
    "Quinceañero": {
        "titulo_tipo": "QUINCEAÑERO",
        "intro": "Los quince años son un momento único e irrepetible. El gelato artesanal de GIA añade un toque fresco y especial a esta celebración, creando un recuerdo dulce que perdurará para siempre.",
        "subtitulo": "Propuesta GIA para sus quince años",
        "descripcion": "Servicio de gelato artesanal servido en sitio, diseñado para sorprender y deleitar a todos los invitados en esta noche tan especial.",
        "nota_reserva": "Las fechas se confirman únicamente con el abono correspondiente.",
        "cierre": "Con gusto coordinamos la selección de sabores y el momento ideal del servicio para que el gelato sea uno de los momentos más recordados de la noche.",
        "despedida": "Quedamos atentos para acompañarlos y hacer parte de esta celebración tan especial.",
    },
    "Graduación": {
        "titulo_tipo": "GRADUACIÓN",
        "intro": "Una graduación es el cierre de un ciclo y el inicio de nuevos sueños. Celebrar con gelato artesanal GIA convierte este logro en un momento fresco, elegante y memorable para todos los presentes.",
        "subtitulo": "Propuesta GIA para su graduación",
        "descripcion": "Servicio de gelato artesanal servido en sitio, pensado para celebrar junto a sus seres queridos en un momento tan importante.",
        "nota_reserva": "Las fechas se confirman únicamente con el abono correspondiente.",
        "cierre": "Con gusto coordinamos la selección de sabores y el momento del servicio para que el gelato sea la nota especial de esta celebración.",
        "despedida": "Quedamos atentos para acompañarlos y celebrar juntos este gran logro.",
    },
    "Otro": {
        "titulo_tipo": "EVENTO ESPECIAL",
        "intro": "En GIA Gelateria nos especializamos en crear momentos únicos a través del gelato artesanal. Nuestra propuesta está diseñada para complementar su evento con una experiencia gastronómica memorable.",
        "subtitulo": "Propuesta GIA para su evento",
        "descripcion": "Servicio de gelato artesanal servido en sitio, diseñado para integrarse al ambiente del evento y sorprender a sus invitados con un momento distinto y especial.",
        "nota_reserva": "Las fechas se confirman únicamente con el abono correspondiente.",
        "cierre": "Con gusto coordinamos la selección de sabores y el momento ideal del servicio dentro del cronograma de su evento.",
        "despedida": "Quedamos atentos para acompañarlos y hacer parte de su evento.",
    },
}

# ── Header/Footer en cada página ──────────────────────────────────────────────
PAGE_W, PAGE_H = letter
MARGIN_X  = 1.1 * inch
LOGO_H    = 1.0 * inch   # altura del logo en header
LOGO_W    = 2.0 * inch
PATRON_H  = 0.42 * inch  # altura del patrón en footer
TOP_MARGIN    = LOGO_H + 0.3 * inch   # espacio reservado para header
BOTTOM_MARGIN = PATRON_H + 0.25 * inch  # espacio reservado para footer

def _dibujar_pagina(c, doc):
    """Dibuja logo (header) y patrón (footer) en cada página."""
    c.saveState()

    # ── HEADER: logo GIA centrado ──────────────────────────────────────────
    if os.path.exists(LOGO_PATH):
        logo_img = ImageReader(LOGO_PATH)
        x = (PAGE_W - LOGO_W) / 2
        y = PAGE_H - LOGO_H - 0.18 * inch
        c.drawImage(logo_img, x, y, width=LOGO_W, height=LOGO_H,
                    preserveAspectRatio=True, mask="auto")

    # línea dorada bajo el logo
    lx = MARGIN_X
    ly = PAGE_H - LOGO_H - 0.22 * inch
    c.setStrokeColor(GOLD)
    c.setLineWidth(0.9)
    c.line(lx, ly, PAGE_W - MARGIN_X, ly)

    # ── FOOTER: patrón dorado a ancho completo ─────────────────────────────
    if os.path.exists(PATRON_PATH):
        patron_img = ImageReader(PATRON_PATH)
        c.drawImage(patron_img, 0, 0, width=PAGE_W, height=PATRON_H,
                    preserveAspectRatio=False, mask="auto")

    c.restoreState()


# ── Generador de PDF ───────────────────────────────────────────────────────────
def generar_pdf(nombre: str, tipo: str, fecha: str, cantidad: int, es_rural: bool) -> bytes:
    texto  = TEXTOS[tipo]
    precio = calcular_precio(cantidad, es_rural)
    buf    = io.BytesIO()

    doc = SimpleDocTemplate(
        buf,
        pagesize=letter,
        leftMargin=MARGIN_X,
        rightMargin=MARGIN_X,
        topMargin=TOP_MARGIN,
        bottomMargin=BOTTOM_MARGIN,
    )

    ancho = PAGE_W - 2 * MARGIN_X

    # ── Estilos ────────────────────────────────────────────────────────────────
    def estilo(nombre_e, **kw):
        base = dict(
            fontName="Times-Roman", fontSize=10,
            textColor=BLACK, leading=16, spaceAfter=0,
        )
        base.update(kw)
        return ParagraphStyle(nombre_e, **base)

    s_titulo    = estilo("titulo",    fontName="Times-Bold",   fontSize=13,
                         textColor=NAVY, alignment=TA_CENTER, spaceAfter=4, leading=18)
    s_seccion   = estilo("seccion",   fontName="Times-Bold",   fontSize=10,
                         textColor=NAVY, spaceAfter=4, leading=14)
    s_body      = estilo("body",      alignment=TA_JUSTIFY,    leading=16, spaceAfter=6)
    s_item      = estilo("item",      leftIndent=14,           leading=15, spaceAfter=3)
    s_precio    = estilo("precio",    fontName="Times-Bold",   fontSize=11,
                         textColor=NAVY, spaceAfter=6, leading=16)
    s_firma     = estilo("firma",     fontName="Times-Bold",   fontSize=11,
                         textColor=NAVY, leading=16)
    s_firma_sub = estilo("firma_sub", fontSize=9, textColor=GRAY, leading=13)
    s_validez   = estilo("validez",   fontSize=9, textColor=GRAY,
                         alignment=TA_CENTER, leading=13)

    story = []

    # ── Título ─────────────────────────────────────────────────────────────────
    story.append(Paragraph(
        f"PROPUESTA GIA GELATERIA: {texto['titulo_tipo']} — {fecha.upper()}",
        s_titulo
    ))
    story.append(Spacer(1, 8))

    # ── Saludo ─────────────────────────────────────────────────────────────────
    story.append(Paragraph(f"Estimado/a <b>{nombre}</b>,", s_body))
    story.append(Spacer(1, 4))
    story.append(Paragraph(
        "Gracias por pensar en GIA Gelateria para acompañarlos en un día tan especial.",
        s_body
    ))
    story.append(Spacer(1, 4))
    story.append(Paragraph(texto["intro"], s_body))
    story.append(Spacer(1, 10))

    # ── Sección propuesta ──────────────────────────────────────────────────────
    story.append(Paragraph(texto["subtitulo"], s_seccion))
    story.append(Paragraph(texto["descripcion"], s_body))
    story.append(Spacer(1, 6))

    # ── Incluye ────────────────────────────────────────────────────────────────
    story.append(Paragraph("Incluye:", s_seccion))

    transporte_txt = (
        "Transporte ida y regreso (zona rural — fuera de Cartagena)"
        if es_rural else
        "Transporte ida y regreso dentro del Centro Histórico"
    )
    items = [
        f"Servicio de hasta <b>{cantidad} gelatos</b> artesanales (vasos de 4 oz)",
        "Estación móvil de gelato GIA, de estética clásica y cuidada",
        transporte_txt,
        "Servicio atendido por el equipo GIA, garantizando presentación y fluidez: 1 persona",
        "Vasos, cucharas y servilletas brandeadas GIA",
    ]
    for item in items:
        story.append(Paragraph(f"• {item}", s_item))

    story.append(Spacer(1, 8))

    # ── Línea dorada + Precio ──────────────────────────────────────────────────
    story.append(HRFlowable(width=ancho, thickness=0.6, color=GOLD, spaceAfter=8))
    story.append(Paragraph(f"Inversión total: {fmt_precio(precio)}", s_precio))
    story.append(HRFlowable(width=ancho, thickness=0.6, color=GOLD, spaceAfter=10))

    # ── Requerimientos técnicos ────────────────────────────────────────────────
    story.append(Paragraph("Requerimientos técnicos", s_seccion))
    for req in [
        "Punto de corriente 220V",
        "Espacio mínimo para instalación: 200 cm de alto, 160 cm de fondo y 80 cm de frente",
    ]:
        story.append(Paragraph(f"• {req}", s_item))
    story.append(Spacer(1, 8))

    # ── Condiciones de reserva ─────────────────────────────────────────────────
    story.append(Paragraph("Condiciones de reserva", s_seccion))
    for cond in [
        "Para confirmar la fecha, requerimos el 50% de la inversión total como anticipo.",
        "El 50% restante deberá cancelarse cinco (5) días antes del evento.",
        "La fecha quedará oficialmente reservada una vez recibido el anticipo.",
        texto["nota_reserva"],
    ]:
        story.append(Paragraph(f"• {cond}", s_item))
    story.append(Spacer(1, 6))
    story.append(Paragraph("Esta cotización tiene validez por 30 días.", s_validez))
    story.append(Spacer(1, 8))

    # ── Cierre ─────────────────────────────────────────────────────────────────
    story.append(Paragraph(texto["cierre"], s_body))
    story.append(Spacer(1, 14))

    # ── Fotos en fila ──────────────────────────────────────────────────────────
    story.append(Paragraph("Fotografías GIA", s_seccion))
    fotos = [p for p in [FOTO1_PATH, FOTO2_PATH, FOTO3_PATH] if os.path.exists(p)]
    if fotos:
        ancho_foto = (ancho - 0.15*inch * (len(fotos)-1)) / len(fotos)
        celdas = [[Image(f, width=ancho_foto, height=ancho_foto*1.25) for f in fotos]]
        tabla = Table(celdas, colWidths=[ancho_foto]*len(fotos), hAlign="CENTER")
        tabla.setStyle(TableStyle([
            ("ALIGN",        (0,0), (-1,-1), "CENTER"),
            ("VALIGN",       (0,0), (-1,-1), "MIDDLE"),
            ("LEFTPADDING",  (0,0), (-1,-1), 3),
            ("RIGHTPADDING", (0,0), (-1,-1), 3),
        ]))
        story.append(tabla)
    story.append(Spacer(1, 14))

    # ── Despedida y firma ──────────────────────────────────────────────────────
    story.append(HRFlowable(width=ancho, thickness=0.6, color=GOLD, spaceAfter=8))
    story.append(Paragraph(texto["despedida"], s_body))
    story.append(Spacer(1, 6))
    story.append(Paragraph("Cordialmente,", s_body))
    story.append(Spacer(1, 14))
    story.append(Paragraph("MELISSA GIL", s_firma))
    story.append(Paragraph("Co-fundadora & CEO", s_firma_sub))
    story.append(Paragraph("GIA Gelateria", s_firma_sub))

    doc.build(story, onFirstPage=_dibujar_pagina, onLaterPages=_dibujar_pagina)
    return buf.getvalue()


# ══════════════════════════════════════════════════════════════════════════════
# INTERFAZ STREAMLIT
# ══════════════════════════════════════════════════════════════════════════════
st.set_page_config(
    page_title="GIA Gelateria — Cotizaciones",
    page_icon="🍦",
    layout="centered",
    initial_sidebar_state="collapsed",
)

# ── CSS personalizado ──────────────────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Playfair+Display:wght@400;600;700&family=Lato:wght@300;400;500&display=swap');

html, body, [class*="css"] { font-family: 'Lato', sans-serif; }

.block-container { padding-top: 1.5rem; max-width: 720px; }

h1 { font-family: 'Playfair Display', serif !important; color: #3D4A6B !important; }
h2, h3 { font-family: 'Playfair Display', serif !important; color: #3D4A6B !important; }

.precio-box {
    background: linear-gradient(135deg, #3D4A6B 0%, #2a3550 100%);
    border-radius: 12px;
    padding: 20px 28px;
    text-align: center;
    margin: 12px 0;
}
.precio-label {
    color: #B8A96A;
    font-size: 13px;
    letter-spacing: 2px;
    text-transform: uppercase;
    font-weight: 500;
    margin-bottom: 4px;
}
.precio-valor {
    color: white;
    font-family: 'Playfair Display', serif;
    font-size: 32px;
    font-weight: 700;
    letter-spacing: 1px;
}

.escala-row {
    display: flex;
    justify-content: space-between;
    padding: 6px 0;
    border-bottom: 1px solid #eee;
    font-size: 13px;
}
.escala-header {
    display: flex;
    justify-content: space-between;
    padding: 6px 0;
    font-weight: 600;
    color: #3D4A6B;
    border-bottom: 2px solid #B8A96A;
    font-size: 13px;
}

div[data-testid="stSelectbox"] label,
div[data-testid="stTextInput"] label,
div[data-testid="stNumberInput"] label,
div[data-testid="stDateInput"] label {
    font-weight: 500;
    color: #3D4A6B;
}

.stButton > button {
    background: linear-gradient(135deg, #3D4A6B, #2a3550);
    color: white;
    border: none;
    border-radius: 8px;
    padding: 12px 28px;
    font-size: 15px;
    font-weight: 500;
    width: 100%;
    letter-spacing: 0.5px;
    transition: opacity 0.2s;
}
.stButton > button:hover { opacity: 0.88; }

.stDownloadButton > button {
    background: linear-gradient(135deg, #B8A96A, #a09058);
    color: white;
    border: none;
    border-radius: 8px;
    padding: 12px 28px;
    font-size: 15px;
    font-weight: 600;
    width: 100%;
    letter-spacing: 0.5px;
}

[data-testid="stRadio"] label { font-size: 14px; }

.gold-line {
    height: 2px;
    background: linear-gradient(to right, transparent, #B8A96A, transparent);
    margin: 16px 0;
}
</style>
""", unsafe_allow_html=True)

# ── Header ─────────────────────────────────────────────────────────────────────
if os.path.exists(PATRON_PATH):
    st.image(PATRON_PATH, use_container_width=True)

col_logo, col_titulo = st.columns([1, 2.5])
with col_logo:
    if os.path.exists(LOGO_PATH):
        st.image(LOGO_PATH, width=130)
with col_titulo:
    st.markdown("<br>", unsafe_allow_html=True)
    st.markdown("## Generador de Cotizaciones")
    st.markdown("<span style='color:#B8A96A;font-size:13px;letter-spacing:1px'>GELATO ARTESANAL · CARTAGENA</span>", unsafe_allow_html=True)

st.markdown("<div class='gold-line'></div>", unsafe_allow_html=True)

# ── Formulario ─────────────────────────────────────────────────────────────────
with st.form("cotizacion_form"):
    st.markdown("### Datos del evento")

    col1, col2 = st.columns(2)
    with col1:
        nombre = st.text_input("Nombre del cliente", placeholder="Ej: Paula Restrepo")
        tipo   = st.selectbox("Tipo de evento", list(TEXTOS.keys()))
    with col2:
        fecha    = st.text_input("Fecha del evento", placeholder="Ej: 18 de septiembre 2026")
        cantidad = st.number_input("Cantidad de gelatos", min_value=10, max_value=500,
                                   value=100, step=5)

    st.markdown("<br>", unsafe_allow_html=True)
    ubicacion = st.radio(
        "Ubicación del evento",
        ["Cartagena (ciudad / Centro Histórico)",
         "Rural / fuera de Cartagena  (+$400.000 transporte)"],
        horizontal=True,
    )
    es_rural = "Rural" in ubicacion

    submitted = st.form_submit_button("Calcular y generar cotización")

# ── Resultado ──────────────────────────────────────────────────────────────────
if submitted:
    if not nombre.strip():
        st.error("Por favor ingresa el nombre del cliente.")
    elif not fecha.strip():
        st.error("Por favor ingresa la fecha del evento.")
    else:
        precio = calcular_precio(cantidad, es_rural)

        st.markdown("<div class='gold-line'></div>", unsafe_allow_html=True)
        st.markdown("### Resumen de cotización")

        col_r1, col_r2 = st.columns(2)
        with col_r1:
            st.markdown(f"**Cliente:** {nombre}")
            st.markdown(f"**Evento:** {TEXTOS[tipo]['titulo_tipo']}")
            st.markdown(f"**Fecha:** {fecha}")
        with col_r2:
            st.markdown(f"**Gelatos:** {cantidad}")
            st.markdown(f"**Ubicación:** {'Rural / fuera de Cartagena' if es_rural else 'Cartagena'}")

        st.markdown(f"""
        <div class="precio-box">
            <div class="precio-label">Inversión total</div>
            <div class="precio-valor">{fmt_precio(precio)}</div>
        </div>
        """, unsafe_allow_html=True)

        # Anticipo
        anticipo = precio // 2
        st.markdown(
            f"<center style='color:#666;font-size:13px'>Anticipo 50%: <b>{fmt_precio(anticipo)}</b> · Saldo: <b>{fmt_precio(precio - anticipo)}</b></center>",
            unsafe_allow_html=True
        )

        st.markdown("<div class='gold-line'></div>", unsafe_allow_html=True)

        # PDF
        with st.spinner("Generando PDF..."):
            pdf_bytes = generar_pdf(nombre, tipo, fecha, cantidad, es_rural)

        nombre_archivo = f"Propuesta GIA - {TEXTOS[tipo]['titulo_tipo']} {nombre.replace(' ','_')}.pdf"

        st.download_button(
            label="⬇  Descargar Cotización PDF",
            data=pdf_bytes,
            file_name=nombre_archivo,
            mime="application/pdf",
        )

# ── Escala de precios ──────────────────────────────────────────────────────────
with st.expander("Ver escala de precios completa"):
    st.markdown("""
    <div class="escala-header">
        <span>Gelatos</span>
        <span>Cartagena</span>
        <span>Rural / Fuera CTG</span>
    </div>
    """, unsafe_allow_html=True)
    for qty in [25, 50, 75, 100, 125, 150, 200]:
        p_ctg   = calcular_precio(qty, False)
        p_rural = calcular_precio(qty, True)
        st.markdown(f"""
        <div class="escala-row">
            <span>{qty} gelatos</span>
            <span>{fmt_precio(p_ctg)}</span>
            <span>{fmt_precio(p_rural)}</span>
        </div>
        """, unsafe_allow_html=True)
    st.markdown("<br><small style='color:#999'>Precio base 100 gelatos Cartagena: $2.500.000 COP · Rural incluye +$400.000 transporte</small>", unsafe_allow_html=True)

# ── Footer ─────────────────────────────────────────────────────────────────────
st.markdown("<br>", unsafe_allow_html=True)
st.markdown(
    "<center style='color:#aaa;font-size:11px'>GIA Gelateria · Cartagena de Indias · gelato artesanal</center>",
    unsafe_allow_html=True
)
