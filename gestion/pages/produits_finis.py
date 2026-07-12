import streamlit as st
import pandas as pd
from datetime import datetime

from utils.excel_produit import charger_donnees_production, sauvegarder_donnees_production
from utils.excel import charger_feuille  # Récupération de la fiche magasin d'origine


@st.dialog("🍳 Déclarer une Fabrication (Cuisine)")
def modal_nouvelle_fabrication(df_produits, df_fabrication):
    if df_produits.empty:
        st.warning("Veuillez d'abord ajouter des produits dans le catalogue.")
        if st.button("Fermer"): st.rerun()
        return

    produit = st.selectbox("Plat / Produit fabriqué *", df_produits["Produit"].tolist())
    date_fab = st.date_input("Date de fabrication", datetime.today())
    quantite = st.number_input("Quantité produite (Portions/Unités) *", min_value=1, step=1, value=1)

    col1, col2 = st.columns(2)
    with col1:
        if st.button("Confirmer la production", use_container_width=True, type="primary"):
            prochain_id = len(df_fabrication) + 1
            nouvelle_ligne = {
                "ID": prochain_id,
                "Date": date_fab.strftime("%Y-%m-%d"),
                "Produit": produit,
                "Quantité": quantite
            }
            df_nouveau = pd.concat([df_fabrication, pd.DataFrame([nouvelle_ligne])], ignore_index=True)
            sauvegarder_donnees_production(df_nouveau, "Fabrication")
            st.success(f"Production de {quantite} {produit} enregistrée !")
            st.rerun()
    with col2:
        if st.button("Annuler", use_container_width=True):
            st.rerun()


@st.dialog("➕ Ajouter un Produit au Catalogue")
def modal_nouveau_produit(df_produits):
    nom_produit = st.text_input("Nom du produit fini *")
    categorie = st.selectbox("Catégorie", ["Plats Rizerie", "Plats Grillades", "Boissons", "Desserts", "Autres"])
    prix_vente = st.number_input("Prix de vente (FCFA) *", min_value=0, step=50, value=0)

    col1, col2 = st.columns(2)
    with col1:
        if st.button("Enregistrer le produit", use_container_width=True, type="primary"):
            if not nom_produit:
                st.error("Le nom du produit est obligatoire.")
                return
            
            prochain_id = len(df_produits) + 1
            nouvelle_ligne = {
                "ID": prochain_id,
                "Produit": nom_produit,
                "Catégorie": categorie,
                "Prix vente": prix_vente
            }
            df_nouveau = pd.concat([df_produits, pd.DataFrame([nouvelle_ligne])], ignore_index=True)
            sauvegarder_donnees_production(df_nouveau, "Liste_Produits")
            st.success(f"Produit '{nom_produit}' ajouté au catalogue !")
            st.rerun()
    with col2:
        if st.button("Annuler", use_container_width=True):
            st.rerun()


def produit():
    st.title("🍳 Module Production & Fiches Recettes")

    df_produits = charger_donnees_production("Liste_Produits")
    df_recettes = charger_donnees_production("Recettes")
    df_fabrication = charger_donnees_production("Fabrication")

    # Lecture en direct depuis la fiche magasin d'origine
    df_matieres_magasin = charger_feuille("Liste_Matieres")

    if not df_matieres_magasin.empty:
        if "Statut" in df_matieres_magasin.columns:
            df_actives = df_matieres_magasin[df_matieres_magasin["Statut"] == "Actif"]
            liste_ingredients = df_actives["Désignation"].tolist() if not df_actives.empty else df_matieres_magasin["Désignation"].tolist()
        else:
            liste_ingredients = df_matieres_magasin["Désignation"].tolist()
    else:
        liste_ingredients = []

    onglet_fab, onglet_recette, onglet_catalogue = st.tabs([
        
        "📋 Catalogue Produits",
        "📖 Formules & Recettes", 
        "🍳 Suivi des Fabrications" 
    ])

    with onglet_fab:
        st.subheader("Suivi de la cuisine du jour")
        if st.button("🍳 Déclarer une nouvelle fabrication", type="primary"):
            modal_nouvelle_fabrication(df_produits, df_fabrication)

        st.write("### Historique des fabrications")
        if not df_fabrication.empty:
            st.dataframe(df_fabrication.sort_values(by="ID", ascending=False), hide_index=True, use_container_width=True)
        else:
            st.info("Aucune fabrication enregistrée pour le moment.")

    with onglet_recette:
        st.subheader("Gestion des fiches techniques")
        
        if df_produits.empty:
            st.warning("Ajoutez d'abord des produits dans le catalogue pour composer des recettes.")
        elif not liste_ingredients:
            st.warning("⚠️ Aucune matière première trouvée dans la fiche Magasin.")
        else:
            with st.expander("➕ Ajouter un ingrédient à une recette", expanded=False):
                with st.form("form_recette", clear_on_submit=True):
                    prod_recette = st.selectbox("Pour quel produit fini ?", df_produits["Produit"].tolist())
                    ing_choisi = st.selectbox("Sélectionner la matière première (du Magasin)", liste_ingredients)
                    
                    info_ing = df_matieres_magasin[df_matieres_magasin["Désignation"] == ing_choisi].iloc[0]
                    code_mat = info_ing["Code"] if "Code" in df_matieres_magasin.columns else "N/A"
                    unite_mat = info_ing["Unité"] if "Unité" in df_matieres_magasin.columns else "U"

                    quantite_besoin = st.number_input(f"Quantité nécessaire ({unite_mat})", min_value=0.0, step=0.01, format="%.2f")
                    
                    if st.form_submit_button("Ajouter à la formule", type="primary"):
                        prochain_id = len(df_recettes) + 1
                        nouvel_ingredient = {
                            "ID": prochain_id,
                            "Produit": prod_recette,
                            "Code Matière": code_mat,
                            "Matière": ing_choisi,
                            "Quantité": quantite_besoin,
                            "Unité": unite_mat
                        }
                        df_nouveau = pd.concat([df_recettes, pd.DataFrame([nouvel_ingredient])], ignore_index=True)
                        sauvegarder_donnees_production(df_nouveau, "Recettes")
                        st.success(f"Ingrédient {ing_choisi} ajouté à la recette de {prod_recette} !")
                        st.rerun()

        st.write("### Fiches techniques existantes")
        if not df_recettes.empty:
            produit_filtre = st.selectbox("Filtrer par plat :", ["Tous"] + df_produits["Produit"].tolist())
            df_recettes_aff = df_recettes.copy()
            if produit_filtre != "Tous":
                df_recettes_aff = df_recettes_aff[df_recettes_aff["Produit"] == produit_filtre]
            st.dataframe(df_recettes_aff, hide_index=True, use_container_width=True)
        else:
            st.info("Aucune recette enregistrée.")

    with onglet_catalogue:
        st.subheader("Catalogue des produits finis vendables")
        if st.button("➕ Ajouter un nouveau produit fini"):
            modal_nouveau_produit(df_produits)

        if not df_produits.empty:
            st.dataframe(df_produits, hide_index=True, use_container_width=True)
        else:
            st.info("Le catalogue est actuellement vide.")