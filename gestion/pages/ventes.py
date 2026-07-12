import streamlit as st
import pandas as pd
from datetime import datetime
from utils.excel_produit import charger_donnees_production, sauvegarder_donnees_production

MODES_PAIEMENT = ["Espèces", "Wave", "Orange Money", "Chèque"]


@st.dialog("🛍️ Enregistrer une nouvelle vente")
def modal_nouvelle_vente(df_produits, df_fabrication, df_ventes):
    if df_produits.empty:
        st.warning("Aucun produit dans le catalogue pour effectuer une vente.")
        if st.button("Fermer"): 
            st.rerun()
        return

    produit_choisi = st.selectbox("Sélectionner le produit vendu *", df_produits["Produit"].tolist())
    
    # Correction de la variable info_produit
    if not df_produits[df_produits["Produit"] == produit_choisi].empty:
        info_produit = df_produits[df_produits["Produit"] == produit_choisi].iloc[0]
    else:
        info_produit = None
    
    prix_u = int(info_produit["Prix vente"]) if info_produit is not None else 0
    
    # Calcul des portions restantes (Fabriquées - Vendues)
    total_fabrique = df_fabrication[df_fabrication["Produit"] == produit_choisi]["Quantité"].sum() if not df_fabrication.empty else 0
    total_vendu = df_ventes[df_ventes["Produit"] == produit_choisi]["Quantité"].sum() if not df_ventes.empty else 0
    stock_dispo = total_fabrique - total_vendu
    
    st.info(f"💰 Prix unitaire : **{prix_u} FCFA** | 🍳 Portions en cuisine : `{stock_dispo}`")
    
    date_vente = st.date_input("Date de la transaction", datetime.today())
    quantite = st.number_input("Quantité vendue *", min_value=1, step=1, value=1)
    mode_paie = st.selectbox("Mode de règlement", MODES_PAIEMENT)
    
    total_facture = prix_u * quantite
    st.write(f"### Total à encaisser : `{total_facture:,} FCFA`".replace(",", " "))
    
    bloquer_vente = False
    if quantite > stock_dispo:
        st.warning("⚠️ Attention : Quantité supérieure au volume cuisiné disponible.")
        bloquer_vente = True

    col_v1, col_v2 = st.columns(2)
    with col_v1:
        soumettre = st.button("Confirmer la vente", use_container_width=True, type="primary", disabled=bloquer_vente)
    with col_v2:
        if st.button("Annuler", use_container_width=True):
            st.rerun()
        
    if soumettre:
        prochain_id = len(df_ventes) + 1
        nouvelle_ligne = {
            "ID": prochain_id,
            "Date": date_vente.strftime("%Y-%m-%d"),
            "Produit": produit_choisi,
            "Quantité": quantite,
            "Prix Unitaire": prix_u,
            "Total": total_facture,
            "Mode Paiement": mode_paie
        }
        df_nouveau = pd.concat([df_ventes, pd.DataFrame([nouvelle_ligne])], ignore_index=True)
        sauvegarder_donnees_production(df_nouveau, "Ventes")
        st.success("Vente enregistrée avec succès !")
        st.rerun()


def afficher():
    st.title("🛍️ Gestion des Ventes & Encaissements")
    
    df_produits = charger_donnees_production("Liste_Produits")
    df_fabrication = charger_donnees_production("Fabrication")
    df_ventes = charger_donnees_production("Ventes")
    
    # Métriques du Chiffre d'Affaires
    aujourdhui = datetime.today().strftime("%Y-%m-%d")
    df_ventes_jour = df_ventes[df_ventes["Date"] == aujourdhui] if not df_ventes.empty else pd.DataFrame()
    ca_jour = df_ventes_jour["Total"].sum() if not df_ventes_jour.empty else 0
    
    m_col1, m_col2 = st.columns(2)
    with m_col1:
        st.metric("Chiffre d'Affaires (Aujourd'hui)", f"{ca_jour:,} FCFA".replace(",", " "))
    with m_col2:
        ca_total = df_ventes["Total"].sum() if not df_ventes.empty else 0
        st.metric("Chiffre d'Affaires Global", f"{ca_total:,} FCFA".replace(",", " "))
        
    st.write("---")
    
    col_actions, col_filtre = st.columns([1, 2])
    with col_actions:
        if st.button("🛍️ Enregistrer un Ticket Vente", use_container_width=True, type="primary"):
            modal_nouvelle_vente(df_produits, df_fabrication, df_ventes)
            
    with col_filtre:
        recherche = st.text_input("🔍 Filtrer l'historique par produit :", "")
        
    df_affichage = df_ventes.copy() if not df_ventes.empty else pd.DataFrame(columns=["ID", "Date", "Produit", "Quantité", "Prix Unitaire", "Total", "Mode Paiement"])
    
    if recherche and not df_affichage.empty:
        df_affichage = df_affichage[df_affichage["Produit"].str.contains(recherche, case=False, na=False)]
        
    if not df_affichage.empty:
        df_affichage = df_affichage.sort_values(by="ID", ascending=False)
        
    st.dataframe(
        df_affichage,
        hide_index=True,
        column_config={
            "ID": None,
            "Prix Unitaire": st.column_config.NumberColumn("Prix (FCFA)", format="%d"),
            "Total": st.column_config.NumberColumn("Total (FCFA)", format="%d")
        },
        use_container_width=True
    )

# Alias pour éviter l'erreur de chargement dans stock.py
def vente():
    afficher()