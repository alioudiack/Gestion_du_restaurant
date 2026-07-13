import streamlit as st
import os
import pandas as pd
from datetime import datetime

from utils.excel_produit import charger_donnees_production
from utils.excel import charger_feuille


def afficher():
    # --- EN-TÊTE ET LOGO ---
    col_logo, col_titre = st.columns([1, 4])
    
    with col_logo:
        dossier_image = "images"
        logo_charge = False
        
        if os.path.exists(dossier_image):
            for fichier in os.listdir(dossier_image):
                if fichier.lower().startswith("logo") and fichier.lower().endswith((".png", ".jpg", ".jpeg")):
                    chemin_logo = os.path.join(dossier_image, fichier)
                    st.image(chemin_logo, width=120)
                    logo_charge = True
                    break
        
        if not logo_charge:
            st.title("🍽️")

    with col_titre:
        st.title("Gestion de Restaurant")
        st.subheader("Tableau de bord de pilotage")
        st.write(f"📅 **Date du jour :** {datetime.today().strftime('%d/%m/%Y')}")

    st.write("---")

    # --- CHARGEMENT DES DONNÉES EN DIRECT POUR LES ALERTES/RÉSUMÉS ---
    df_ventes = charger_donnees_production("Ventes")
    df_fabrication = charger_donnees_production("Fabrication")
    df_matieres = charger_feuille("Liste_Matieres")

    # 1. Calcul du chiffre d'affaires du jour
    aujourdhui = datetime.today().strftime("%Y-%m-%d")
    if not df_ventes.empty:
        df_ventes_jour = df_ventes[df_ventes["Date"] == aujourdhui] if "Date" in df_ventes.columns else pd.DataFrame()
        ca_jour = df_ventes_jour["Total"].sum() if "Total" in df_ventes_jour.columns else 0
        nb_ventes_jour = df_ventes_jour["Quantité"].sum() if "Quantité" in df_ventes_jour.columns else (df_ventes_jour["Quantite"].sum() if "Quantite" in df_ventes_jour.columns else 0)
    else:
        ca_jour = 0
        nb_ventes_jour = 0

    # 2. Calcul des fabrications (portions cuisinées) aujourd'hui
    if not df_fabrication.empty:
        df_fab_jour = df_fabrication[df_fabrication["Date"] == aujourdhui] if "Date" in df_fabrication.columns else pd.DataFrame()
        fab_jour = df_fab_jour["Quantité"].sum() if "Quantité" in df_fab_jour.columns else (df_fab_jour["Quantite"].sum() if "Quantite" in df_fab_jour.columns else 0)
    else:
        fab_jour = 0

    # 3. Calcul sécurisé des alertes de stock critique
    alertes_stock = 0
    if not df_matieres.empty:
        # Trouver dynamiquement la colonne quantité (gère 'Quantité', 'Quantite', 'Qte')
        col_qte = None
        for col in ["Quantité", "Quantite", "Qte", "QUANTITE"]:
            if col in df_matieres.columns:
                col_qte = col
                break
        
        if col_qte:
            df_matieres[col_qte] = pd.to_numeric(df_matieres[col_qte], errors="coerce").fillna(0.0)
            alertes_stock = len(df_matieres[df_matieres[col_qte] <= 2])
        else:
            # Si aucune colonne n'est trouvée, on évite le plantage
            alertes_stock = 0

    # --- SECTION VUE D'ENSEMBLE (METRICS) ---
    st.markdown("### 📊 Activité du jour")
    m1, m2, m3, m4 = st.columns(4)
    
    with m1:
        st.metric("Recettes du Jour", f"{ca_jour:,} FCFA".replace(",", " "))
    with m2:
        st.metric("Plats Vendus", f"{nb_ventes_jour} portions")
    with m3:
        st.metric("Cuisiné ce Jour", f"{fab_jour} portions")
    with m4:
        st.metric("Alertes Stock Magasin", f"{alertes_stock} articles", 
                  delta=f"{alertes_stock} à réapprovisionner" if alertes_stock > 0 else None, 
                  delta_color="inverse" if alertes_stock > 0 else "normal")

    st.write("---")

    # --- RACCOURCIS ET ACCÈS RAPIDE ---
    st.markdown("### 🚀 Raccourcis de navigation rapides")
    col_r1, col_r2, col_r3 = st.columns(3)
    
    with col_r1:
        st.info("🛒 **Côté Magasin**\n\nAllez dans l'onglet **Magasin** pour enregistrer vos entrées de marchandises ou créer de nouveaux ingrédients.")
        
    with col_r2:
        st.success("🍳 **Côté Cuisine**\n\nDéclarez vos fiches techniques et validez les portions produites par la cuisine depuis l'onglet **Production**.")
        
    with col_r3:
        st.warning("🛍️ **Côté Comptoir**\n\nEnregistrez instantanément les commandes clients et gérez la caisse depuis le menu **Ventes**.")


def accueil():
    afficher()