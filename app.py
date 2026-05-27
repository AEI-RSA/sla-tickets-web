import streamlit as st
import pandas as pd
import re
from datetime import datetime, timedelta

st.set_page_config(page_title="SLA Tickets", layout="wide")

SLA_TABLA = {1:6, 2:8, 3:10, 4:12, 5:24, 6:48, 7:96}

# ---------- CARGAR PERIMETRO ----------
@st.cache_data
def cargar_perimetro():
    return pd.read_excel("PERIMETRO MAYO.xlsx", header=None)

df_perimetro = cargar_perimetro()

# ---------- FUNCION SITE ----------
def obtener_datos_site(site):
    site = site.strip().upper()

    for i in range(len(df_perimetro)):
        if str(df_perimetro.iloc[i,0]).strip().upper() == site:

            texto_cluster = str(df_perimetro.iloc[i,11]).upper()
            match = re.search(r"\d+", texto_cluster)
            cluster = int(match.group()) if match else None

            return {
                "cluster": cluster,
                "departamento": df_perimetro.iloc[i,1],
                "provincia": df_perimetro.iloc[i,2],
                "distrito": df_perimetro.iloc[i,3],
                "centro": df_perimetro.iloc[i,4],
                "nodo": df_perimetro.iloc[i,5],
                "latitud": df_perimetro.iloc[i,9],
                "longitud": df_perimetro.iloc[i,10],
                "concesionaria": df_perimetro.iloc[i,34],
                "suministro": df_perimetro.iloc[i,35]
            }

    return None

# ---------- TITULO ----------
st.title("📡 SLA TICKETS ONLINE")

col1, col2 = st.columns(2)

# =========================================================
# IZQUIERDA SLA
# =========================================================

with col1:

    st.header("🎯 TICKETS SLA")

    texto = st.text_area("Pega el ticket")

    if st.button("CALCULAR SLA"):

        try:
            partes = texto.strip().split("\t")

            ticket = partes[0]
            site = partes[3]
            fecha = datetime.strptime(partes[-1], "%d/%m/%Y %I:%M %p")

            info = obtener_datos_site(site)

            if not info:
                st.error("SITE no encontrado")
            else:

                cluster = info["cluster"]
                sla = SLA_TABLA[cluster]

                vence = fecha + timedelta(hours=sla)
                ahora = datetime.now()

                trans = (ahora - fecha).total_seconds()/3600
                rest = sla - trans

                estado = "🟢 EN TIEMPO" if rest > 0 else "🔴 VENCIDO"

                st.success(estado)

                st.text(f"""
TICKET: {ticket}
SITE: {site}
CLUSTER: {cluster}
SLA: {sla}h

UBICACIÓN
{info['departamento']} / {info['provincia']} / {info['distrito']}

Centro: {info['centro']}
Nodo: {info['nodo']}

Concesionaria: {info['concesionaria']}
Suministro: {info['suministro']}

Latitud: {info['latitud']}
Longitud: {info['longitud']}

Salida: {fecha}
Vence: {vence}

Transcurridas: {trans:.2f}h
Restantes: {rest:.2f}h
""")

        except Exception as e:
            st.error(str(e))

# =========================================================
# DERECHA ANALISIS
# =========================================================

with col2:

    st.header("📊 ANALISIS DE TICKETS")

    archivo = st.file_uploader("Subir Excel", type=["xlsx"])

    if archivo:

        try:

            df = pd.read_excel(archivo)

            df["empresa"] = df.iloc[:,61].astype(str)
            df["estado_sup"] = df.iloc[:,40].astype(str)
            df["estado_ticket"] = df.iloc[:,50].astype(str)

            df["empresa"] = df["empresa"].str.upper().str.strip()

            pendientes = df[df["estado_ticket"] != "Finalizado"]

            def resumen_empresa(nombre):

                emp = pendientes[
                    pendientes["empresa"].str.contains(nombre, na=False)
                ]

                pendientes_cant = len(emp)

                en_atencion = len(
                    emp[emp["estado_sup"] == "En atención"]
                )

                atendidos = len(
                    emp[emp["estado_sup"] == "Atendido"]
                )

                libres = len(
                    emp[emp["estado_sup"] == "Libre"]
                )

                return pendientes_cant, en_atencion, atendidos, libres

            indra = resumen_empresa("INDRA")
            comfica = resumen_empresa("COMFICA")

            st.text(f"""
INDRA PERU S.A.
Pendientes: {indra[0]}
En atención real: {indra[1]}
Atendidos: {indra[2]}
Libres: {indra[3]}

COMFICA PERU S.A.C.
Pendientes: {comfica[0]}
En atención real: {comfica[1]}
Atendidos: {comfica[2]}
Libres: {comfica[3]}
""")

        except Exception as e:
            st.error(str(e))