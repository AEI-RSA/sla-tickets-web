import streamlit as st
import pandas as pd
import re
from datetime import datetime, timedelta
import pytz

# ---------------- CONFIG ----------------

st.set_page_config(
    page_title="SLA Tickets PRO",
    layout="wide"
)

SLA_TABLA = {
    1: 6,
    2: 8,
    3: 10,
    4: 12,
    5: 24,
    6: 48,
    7: 96
}

# ---------------- LEER PERIMETRO ----------------

@st.cache_data
def cargar_perimetro():
    return pd.read_excel("PERIMETRO MAYO.xlsx", header=None)

df_perimetro = cargar_perimetro()

# ---------------- BUSCAR SITE ----------------

def obtener_datos_site(site):

    site = str(site).strip().upper()

    for i in range(len(df_perimetro)):

        if str(df_perimetro.iloc[i, 0]).strip().upper() == site:

            texto_cluster = str(df_perimetro.iloc[i, 11]).upper()

            match = re.search(r"\d+", texto_cluster)

            cluster = int(match.group()) if match else None

            return {
                "cluster": cluster,
                "departamento": df_perimetro.iloc[i, 1],
                "provincia": df_perimetro.iloc[i, 2],
                "distrito": df_perimetro.iloc[i, 3],
                "centro": df_perimetro.iloc[i, 4],
                "nodo": df_perimetro.iloc[i, 5],
                "latitud": df_perimetro.iloc[i, 9],
                "longitud": df_perimetro.iloc[i, 10],
                "concesionaria": df_perimetro.iloc[i, 34],
                "suministro": df_perimetro.iloc[i, 35]
            }

    return None

# ---------------- TITULO ----------------

st.title("⚡ SLA TICKETS PRO")
st.caption("Sistema de monitoreo NOC")

# ---------------- COLUMNAS ----------------

col1, col2 = st.columns(2)

# =========================================================
# ================== IZQUIERDA SLA ========================
# =========================================================

with col1:

    st.header("🎯 TICKETS SLA")

    texto = st.text_area(
        "Pega aquí el ticket",
        height=220
    )

    if st.button("CALCULAR SLA"):

        try:

            # Acepta tabs y saltos de línea
            partes = re.split(r'[\t\n]+', texto.strip())

            # Validación mínima
            if len(partes) < 4:
                st.error("Formato de ticket inválido")
                st.stop()

            ticket = partes[0].strip()

            site = partes[3].strip()

            fecha = datetime.strptime(
                partes[-1].strip(),
                "%d/%m/%Y %I:%M %p"
            )

            info = obtener_datos_site(site)

            if not info:
                st.error("SITE no encontrado")

            else:

                cluster = info["cluster"]

                sla = SLA_TABLA[cluster]

                vence = fecha + timedelta(hours=sla)

                # HORA PERÚ
                zona_peru = pytz.timezone("America/Lima")
                ahora = datetime.now(zona_peru).replace(tzinfo=None)

                trans = (ahora - fecha).total_seconds() / 3600

                rest = sla - trans

                estado = (
                    "🟢 EN TIEMPO"
                    if rest > 0
                    else "🔴 VENCIDO"
                )

                st.success(estado)

                st.code(f"""
TICKET: {ticket}

SITE: {site}
CLUSTER: {cluster}
SLA: {sla}h

━━━━━━━━ UBICACIÓN ━━━━━━━━
{info['departamento']} / {info['provincia']} / {info['distrito']}

Centro: {info['centro']}
Nodo: {info['nodo']}

━━━━━━━━ DATOS ELÉCTRICOS ━━━━━━━━
Concesionaria: {info['concesionaria']}
Suministro: {info['suministro']}

━━━━━━━━ COORDENADAS ━━━━━━━━
Latitud: {info['latitud']}
Longitud: {info['longitud']}

━━━━━━━━ TIEMPOS ━━━━━━━━
Salida: {fecha}
Vence: {vence}

Transcurridas: {trans:.2f}h
Restantes: {rest:.2f}h

━━━━━━━━ ESTADO ━━━━━━━━
{estado}
""")

        except Exception as e:
            st.error(str(e))

# =========================================================
# ================= DERECHA ANALISIS ======================
# =========================================================

with col2:

    st.header("📊 ANÁLISIS DE TICKETS")

    archivo = st.file_uploader(
        "Sube Excel de tickets",
        type=["xlsx"]
    )

    if archivo is not None:

        try:

            df = pd.read_excel(archivo)

            empresa = df.iloc[:, 61]
            estado_sup = df.iloc[:, 40]
            estado_ticket = df.iloc[:, 50]

            df_t = pd.DataFrame({
                "empresa": empresa,
                "estado_sup": estado_sup,
                "estado_ticket": estado_ticket
            })

            pendientes = df_t[
                df_t["estado_ticket"] != "Finalizado"
            ]

            # ---------------- INDRA ----------------

            indra = pendientes[
                pendientes["empresa"]
                .astype(str)
                .str.contains("INDRA", case=False, na=False)
            ]

            indra_en_atencion = len(
                indra[
                    indra["estado_sup"]
                    .astype(str)
                    .str.contains("En atención", case=False, na=False)
                ]
            )

            indra_atendidos = len(
                indra[
                    indra["estado_sup"]
                    .astype(str)
                    .str.contains("Atendido", case=False, na=False)
                ]
            )

            indra_libres = len(
                indra[
                    indra["estado_sup"]
                    .astype(str)
                    .str.contains("Libre", case=False, na=False)
                ]
            )

            # ---------------- COMFICA ----------------

            comfica = pendientes[
                pendientes["empresa"]
                .astype(str)
                .str.contains("COMFICA", case=False, na=False)
            ]

            comfica_en_atencion = len(
                comfica[
                    comfica["estado_sup"]
                    .astype(str)
                    .str.contains("En atención", case=False, na=False)
                ]
            )

            comfica_atendidos = len(
                comfica[
                    comfica["estado_sup"]
                    .astype(str)
                    .str.contains("Atendido", case=False, na=False)
                ]
            )

            comfica_libres = len(
                comfica[
                    comfica["estado_sup"]
                    .astype(str)
                    .str.contains("Libre", case=False, na=False)
                ]
            )

            st.code(f"""
INDRA PERU S.A.

Pendientes: {len(indra)}
En atención real: {indra_en_atencion}
Atendidos: {indra_atendidos}
Libres: {indra_libres}


COMFICA PERU S.A.C.

Pendientes: {len(comfica)}
En atención real: {comfica_en_atencion}
Atendidos: {comfica_atendidos}
Libres: {comfica_libres}
""")

        except Exception as e:
            st.error(str(e))
