import streamlit as st
import pandas as pd
import plotly.express as px  # Installé par défaut avec Streamlit pour des graphiques fluides
from datetime import datetime, timedelta

from utils.excel_produit import charger_donnees_production
from utils.excel import charger_feuille

def afficher():
    st.title("📈 Rapport d'Activité & Statistiques")

    # 1. Chargement unifié de toutes les bases de données
    df_ventes = charger_donnees_production("Ventes")
    df_fabrication = charger_donnees_production("Fabrication")
    df_produits = charger_donnees_production("Liste_Produits")
    df_recettes = charger_donnees_production("Recettes")
    df_matieres = charger_feuille("Liste_Matieres")

    if df_ventes.empty:
        st.info("💡 Aucune vente n'a encore été enregistrée. Les graphiques s'afficheront dès les premiers encaissements.")
        return

    # S'assurer que les dates sont bien lues au bon format
    df_ventes["Date"] = pd.to_datetime(df_ventes["Date"])
    
    # --- FILTRE TEMPOREL ---
    st.write("### 📅 Période d'analyse")
    col_f1, col_f2 = st.columns(2)
    with col_f1:
        date_debut = st.date_input("Date de début", datetime.today() - timedelta(days=30))
    with col_f2:
        date_fin = st.date_input("Date de fin", datetime.today())

    # Application du filtre temporel
    df_ventes_filtrees = df_ventes[
        (df_ventes["Date"].dt.date >= date_debut) & 
        (df_ventes["Date"].dt.date <= date_fin)
    ]

    if df_ventes_filtrees.empty:
        st.warning("Aucune donnée de vente sur la période sélectionnée.")
        return

    # --- CALCULS DES INDICES FINANCIERS ---
    chiffre_affaires = df_ventes_filtrees["Total"].sum()
    total_plats_vendus = df_ventes_filtrees["Quantité"].sum()
    panier_moyen = chiffre_affaires / len(df_ventes_filtrees) if len(df_ventes_filtrees) > 0 else 0

    # Affichage des indicateurs clés
    m1, m2, m3 = st.columns(3)
    with m1:
        st.metric("Chiffre d'Affaires", f"{chiffre_affaires:,.0f} FCFA".replace(",", " "))
    with m2:
        st.metric("Volume de Ventes", f"{total_plats_vendus} portions")
    with m3:
        st.metric("Panier Moyen par Ticket", f"{panier_moyen:,.0f} FCFA".replace(",", " "))

    st.write("---")

    # --- ZONE DES GRAPHIQUES ---
    st.write("### 📊 Analyses Graphiques")
    col_g1, col_g2 = st.columns(2)

    with col_g1:
        st.write("#### Évolution du Chiffre d'Affaires")
        # Regroupement des ventes par jour
        df_ca_quotidien = df_ventes_filtrees.groupby(df_ventes_filtrees["Date"].dt.date)["Total"].sum().reset_index()
        df_ca_quotidien.columns = ["Date", "Chiffre d'Affaires"]
        
        fig_ca = px.line(df_ca_quotidien, x="Date", y="Chiffre d'Affaires", 
                         labels={"Chiffre d'Affaires": "CA (FCFA)"},
                         template="plotly_white", line_shape="spline")
        st.plotly_chart(fig_ca, use_container_width=True)

    with col_g2:
        st.write("#### Palmarès des Ventes (Top Produits)")
        df_top_produits = df_ventes_filtrees.groupby("Produit")["Quantité"].sum().reset_index()
        df_top_produits = df_top_produits.sort_values(by="Quantité", ascending=False).head(8)
        
        fig_top = px.bar(df_top_produits, x="Quantité", y="Produit", orientation="h",
                         labels={"Quantité": "Portions vendues"},
                         template="plotly_white")
        fig_top.update_layout(yaxis={'categoryorder':'total ascending'})
        st.plotly_chart(fig_top, use_container_width=True)

    st.write("---")

    # --- ANALYSE AVANCÉE : RÉPARTITION ET COÛTS ---
    col_r1, col_r2 = st.columns(2)
    
    with col_r1:
        st.write("#### Ventes par mode de règlement")
        if "Mode Paiement" in df_ventes_filtrees.columns:
            df_mode = df_ventes_filtrees.groupby("Mode Paiement")["Total"].sum().reset_index()
            fig_pie = px.pie(df_mode, values="Total", names="Mode Paiement", hole=0.4)
            st.plotly_chart(fig_pie, use_container_width=True)
        else:
            st.info("Information sur les modes de paiement indisponible.")

    with col_r2:
        st.write("#### Consommation théorique des Matières Premières")
        # Calcul des ingrédients sortis de la cuisine d'après les recettes des plats vendus
        if not df_recettes.empty:
            ingredients_consommes = {}
            for _, ligne_vente in df_ventes_filtrees.iterrows():
                plat = ligne_vente["Produit"]
                qte_vendue = ligne_vente["Quantité"]
                
                # Trouver la recette du plat
                recette_plat = df_recettes[df_recettes["Produit"] == plat]
                for _, ing in recette_plat.iterrows():
                    nom_ing = ing["Matière"]
                    unite = ing["Unité"]
                    qte_unitaire = ing["Quantité"]
                    
                    total_besoin = qte_unitaire * qte_vendue
                    if nom_ing in ingredients_consommes:
                        ingredients_consommes[nom_ing]["Quantité"] += total_besoin
                    else:
                        ingredients_consommes[nom_ing] = {"Quantité": total_besoin, "Unité": unite}
            
            if ingredients_consommes:
                df_conso = pd.DataFrame.from_dict(ingredients_consommes, orient='index').reset_index()
                df_conso.columns = ["Matière Première", "Quantité Théorique Sortie", "Unité"]
                st.dataframe(df_conso, hide_index=True, use_container_width=True)
            else:
                st.info("Aucun ingrédient n'est rattaché aux plats vendus dans vos fiches recettes.")
        else:
            st.info("Configurez vos fiches techniques dans le module Production pour voir l'analyse des stocks consommés.")


# Alias pour votre fichier central stock.py
def rapport():
    afficher()