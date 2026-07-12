import streamlit as st
import pandas as pd
from datetime import datetime

from utils.excel import charger_feuille, sauvegarder_feuille

@st.dialog("🔄 Ajuster le Stock / Déclarer une Perte")
def modal_ajustement_stock(df_matieres, col_qte_trouvee):
    if df_matieres.empty:
        st.warning("Aucune matière première enregistrée dans le magasin.")
        if st.button("Fermer"): 
            st.rerun()
        return

    matiere_choisie = st.selectbox("Sélectionner la matière première *", df_matieres["Désignation"].tolist())
    info_mat = df_matieres[df_matieres["Désignation"] == matiere_choisie].iloc[0]
    
    unite = info_mat["Unité"] if "Unité" in df_matieres.columns else "U"
    stock_actuel = float(info_mat[col_qte_trouvee])
    
    st.info(f"📦 Stock théorique actuel : **{stock_actuel} {unite}**")
    
    type_ajustement = st.radio("Type d'opération *", ["Perte / Casse / Périmé", "Inventaire physique (Correction)"])
    
    if type_ajustement == "Perte / Casse / Périmé":
        quantite_perdue = st.number_input(f"Quantité perdue ou jetée ({unite}) *", min_value=0.01, step=0.1, format="%.2f")
        nouvelle_quantite = stock_actuel - quantite_perdue
    else:
        nouvelle_quantite = st.number_input(f"Nouvelle quantité réelle constatée ({unite}) *", min_value=0.0, step=0.1, value=stock_actuel, format="%.2f")

    motif = st.text_input("Motif de l'ajustement *", placeholder="Ex: Erreur pesée, sac déchiré, produit périmé...")

    col1, col2 = st.columns(2)
    with col1:
        if st.button("Valider l'ajustement", use_container_width=True, type="primary"):
            if not motif:
                st.error("Le motif est obligatoire pour justifier l'écart.")
                return
            
            if nouvelle_quantite < 0:
                st.error("Le stock final ne peut pas être négatif.")
                return

            # Mise à jour de la ligne dans le DataFrame principal
            df_matieres.loc[df_matieres["Désignation"] == matiere_choisie, col_qte_trouvee] = nouvelle_quantite
            
            if "Date" in df_matieres.columns:
                df_matieres.loc[df_matieres["Désignation"] == matiere_choisie, "Date"] = datetime.today().strftime("%Y-%m-%d")
                
            sauvegarder_feuille(df_matieres, "Liste_Matieres")
            st.success(f"Stock de {matiere_choisie} mis à jour avec succès !")
            st.rerun()
            
    with col2:
        if st.button("Annuler", use_container_width=True):
            st.rerun()


def afficher():
    st.title("📊 État des Stocks & Inventaire Magasin")
    
    df_matieres = charger_feuille("Liste_Matieres")
    
    if df_matieres.empty:
        st.info("💡 Aucune donnée disponible dans la liste des matières premières.")
        return

    # 1. Détection dynamique de la colonne quantité
    col_qte = None
    for col in ["Quantité", "Quantite", "Qte", "QUANTITE"]:
        if col in df_matieres.columns:
            col_qte = col
            break
            
    if not col_qte:
        st.error("⚠️ La colonne contenant les stocks (Quantité, Quantite ou Qte) n'a pas été trouvée dans votre fichier Excel.")
        return

    # S'assurer de la présence des autres colonnes indispensables
    colonnes_requises = ["Code", "Désignation", "Unité", "Prix Unitaire"]
    for col in colonnes_requises:
        if col not in df_matieres.columns:
            df_matieres[col] = 0 if "Prix" in col else "N/A"

    # Conversion propre des types numériques
    df_matieres[col_qte] = pd.to_numeric(df_matieres[col_qte], errors="coerce").fillna(0.0)
    df_matieres["Prix Unitaire"] = pd.to_numeric(df_matieres["Prix Unitaire"], errors="coerce").fillna(0)
    
    # Calcul de la valeur financière
    df_matieres["Valeur Stock"] = df_matieres[col_qte] * df_matieres["Prix Unitaire"]

    # --- ZONE MÉTRIQUES ---
    valeur_totale_magasin = df_matieres["Valeur Stock"].sum()
    nb_references = len(df_matieres)
    references_critiques = len(df_matieres[df_matieres[col_qte] <= 2])

    m_col1, m_col2, m_col3 = st.columns(3)
    with m_col1:
        st.metric("Valeur du Stock Magasin", f"{valeur_totale_magasin:,.0f} FCFA".replace(",", " "))
    with m_col2:
        st.metric("Total Références", f"{nb_references} ingrédients")
    with m_col3:
        st.metric("Alertes Stock Critique (≤ 2)", f"{references_critiques} articles", 
                  delta=f"-{references_critiques}" if references_critiques > 0 else None, delta_color="inverse")

    st.write("---")

    # --- BARRE D'ACTIONS ---
    col_btn, col_recherche = st.columns([1, 2])
    with col_btn:
        if st.button("🔄 Ajuster un Stock / Perte", use_container_width=True, type="primary"):
            modal_ajustement_stock(df_matieres, col_qte)
            
    with col_recherche:
        recherche = st.text_input("🔍 Rechercher un ingrédient dans le magasin :", "")

    # Filtrage de l'affichage
    df_affichage = df_matieres.copy()
    if recherche:
        df_affichage = df_affichage[df_affichage["Désignation"].str.contains(recherche, case=False, na=False)]

    # --- TABLEAU D'AFFICHAGE PRINCIPAL ---
    st.subheader("📋 Liste des Matières Premières en Stock")
    
    st.dataframe(
        df_affichage,
        hide_index=True,
        column_config={
            "Code": st.column_config.TextColumn("Code ID"),
            "Désignation": st.column_config.TextColumn("Matière Première"),
            col_qte: st.column_config.NumberColumn("Quantité en Stock", format="%.2f"),
            "Unité": st.column_config.TextColumn("Unité"),
            "Prix Unitaire": st.column_config.NumberColumn("Prix Unitaire (FCFA)", format="%d"),
            "Valeur Stock": st.column_config.NumberColumn("Valeur Totale (FCFA)", format="%d")
        },
        use_container_width=True
    )

    # --- ZONE D'ALERTES VISUELLES ---
    df_alertes = df_matieres[df_matieres[col_qte] <= 2]
    if not df_alertes.empty:
        with st.expander("⚠️ Liste détaillée des produits en rupture ou stock critique", expanded=True):
            for _, row in df_alertes.iterrows():
                st.warning(f"**{row['Désignation']}** : Il ne reste que **{row[col_qte]} {row['Unité']}** en réserve.")


def inventaire():
    afficher()