import streamlit as st
import pandas as pd
from datetime import datetime
from utils.excel import charger_feuille, sauvegarder_feuille

# Définition des listes de contrôle strictes (Catégories et Unités)
CATEGORIES = ["Alimentaire", "Boisson", "Épices", "Laitier", "Viande", "Volaille", "Poisson", "Légume", "Fruit", "Emballage", "Produit d'entretien", "Autre"]
UNITES = ["kg", "g", "L", "ml", "pièce", "paquet", "carton", "sac", "bidon"]
DESTINATIONS = ["Cuisine", "Perte / Gaspillage", "Commande client", "Autre"]

def calculer_stock_actuel(code, df_entrees, df_sorties):
    """Calcule le stock disponible actuel pour un code article donné."""
    total_entrees = 0.0
    total_sorties = 0.0
    
    if not df_entrees.empty and "Code" in df_entrees.columns:
        total_entrees = df_entrees[df_entrees["Code"] == code]["Quantité"].sum()
        
    if not df_sorties.empty and "Code" in df_sorties.columns:
        total_sorties = df_sorties[df_sorties["Code"] == code]["Quantité"].sum()
        
    return float(total_entrees - total_sorties)


def synchroniser_et_sauvegarder_stock(df_matieres, df_entrees, df_sorties):
    """Calcule le stock complet et synchronise la feuille 'Stock' de votre fichier Excel."""
    if df_matieres.empty:
        return pd.DataFrame()
        
    donnees_stock = []
    for _, matiere in df_matieres.iterrows():
        code = matiere["Code"]
        designation = matiere["Désignation"]
        categorie = matiere["Catégorie"]
        unite = matiere["Unité"]
        seuil = float(matiere["Seuil"])
        statut_art = matiere["Statut"]
        
        stock_restant = calculer_stock_actuel(code, df_entrees, df_sorties)
        
        # Gestion du PUMP et valorisation
        p_moyen = 0.0
        if not df_entrees.empty and "Code" in df_entrees.columns:
            entrees_art = df_entrees[df_entrees["Code"] == code]
            total_q_achetee = entrees_art["Quantité"].sum()
            if total_q_achetee > 0:
                p_moyen = entrees_art["Montant"].sum() / total_q_achetee
        
        valeur_stock = stock_restant * p_moyen if stock_restant > 0 else 0.0
        alerte_visuelle = "🚨 Alerte Stock Bas" if stock_restant <= seuil else "✅ Suffisant"
            
        donnees_stock.append({
            "Code": code,
            "Désignation": designation,
            "Catégorie": categorie,
            "Stock Actuel": round(stock_restant, 2),
            "Unité": unite,
            "Seuil Alerte": seuil,
            "Alerte": alerte_visuelle,
            "Prix Moyen (FCFA)": round(p_moyen, 2),
            "Valeur Stock (FCFA)": round(valeur_stock, 0),
            "Statut Article": statut_art
        })
        
    df_stock_final = pd.DataFrame(donnees_stock)
    
    # Écriture physique dans le fichier Excel (Feuille "Stock")
    sauvegarder_feuille(df_stock_final, "Stock")
    return df_stock_final


@st.dialog("➕ Ajouter une nouvelle matière première")
def modal_ajouter_matiere(df_matieres):
    if not df_matieres.empty and "Code" in df_matieres.columns:
        df_matieres['num'] = df_matieres['Code'].str.extract('(\d+)').astype(float).fillna(0).astype(int)
        prochain_id = df_matieres['num'].max() + 1
        df_matieres.drop(columns=['num'], inplace=True)
    else:
        prochain_id = 1
    code_auto = f"MP{prochain_id:04d}"
    
    st.info(f"Le code généré automatiquement sera : **{code_auto}**")
    
    designation = st.text_input("Désignation *")
    categorie = st.selectbox("Catégorie", CATEGORIES)
    unite = st.selectbox("Unité de mesure", UNITES)
    seuil = st.number_input("Seuil d'alerte (Stock minimum)", min_value=0.0, step=1.0, value=10.0)
    
    col_form1, col_form2 = st.columns(2)
    with col_form1:
        soumettre = st.button("Enregistrer", use_container_width=True)
    with col_form2:
        annuler = st.button("Annuler", use_container_width=True)
        
    if soumettre:
        if designation:
            nouvel_id = len(df_matieres) + 1
            nouvelle_ligne = {
                "ID": nouvel_id,
                "Code": code_auto,
                "Désignation": designation,
                "Catégorie": categorie,
                "Unité": unite,
                "Seuil": seuil,
                "Statut": "Actif"
            }
            df_nouveau = pd.concat([df_matieres, pd.DataFrame([nouvelle_ligne])], ignore_index=True)
            sauvegarder_feuille(df_nouveau, "Liste_Matieres")
            
            # Recalcul et mise à jour de la feuille "Stock"
            df_e = charger_feuille("Entrees")
            df_s = charger_feuille("Sorties")
            synchroniser_et_sauvegarder_stock(df_nouveau, df_e, df_s)
            
            st.success(f"Matière '{designation}' ajoutée avec succès et stock mis à jour !")
            st.rerun()
        else:
            st.error("La désignation est obligatoire.")
    elif annuler:
        st.rerun()


@st.dialog("📥 Enregistrer une nouvelle entrée de stock")
def modal_nouvelle_entrée(df_matieres, df_entrees):
    df_actives = df_matieres[df_matieres["Statut"] == "Actif"]
    if df_actives.empty:
        st.warning("Veuillez d'abord ajouter des matières premières actives.")
        if st.button("Fermer"): st.rerun()
        return

    liste_designations = df_actives["Désignation"].tolist()
    choix_designation = st.selectbox("Sélectionner la matière première *", liste_designations, key="sel_entree")
    
    ligne_matiere = df_actives[df_actives["Désignation"] == choix_designation].iloc[0]
    code_associe = ligne_matiere["Code"]
    unite_associee = ligne_matiere["Unité"]
    
    st.caption(f"Code : **{code_associe}** | Unité : **{unite_associee}**")
    
    date_entree = st.date_input("Date de réception", datetime.today(), key="date_entree")
    quantite = st.number_input(f"Quantité reçue ({unite_associee}) *", min_value=0.01, step=0.1, value=1.0)
    prix_unitaire = st.number_input("Prix unitaire (FCFA) *", min_value=0.0, step=50.0, value=0.0)
    
    montant_total = quantite * prix_unitaire
    st.write(f"**Montant total :** {montant_total:,.0f} FCFA")
    observation = st.text_input("Observation / Fournisseur (Optionnel)", "")
    
    col_e1, col_e2 = st.columns(2)
    with col_e1:
        soumettre = st.button("Confirmer l'entrée", use_container_width=True)
    with col_e2:
        annuler = st.button("Annuler", use_container_width=True)
        
    if soumettre:
        nouvel_id = len(df_entrees) + 1
        nouvelle_entree = {
            "ID": nouvel_id,
            "Date": date_entree.strftime("%Y-%m-%d"),
            "Code": code_associe,
            "Désignation": choix_designation,
            "Quantité": quantite,
            "Prix unitaire": prix_unitaire,
            "Montant": montant_total,
            "Observation": observation
        }
        df_nouveau_entrees = pd.concat([df_entrees, pd.DataFrame([nouvelle_entree])], ignore_index=True)
        sauvegarder_feuille(df_nouveau_entrees, "Entrees")
        
        # Mouvement d'entrée -> Mise à jour forcée de la feuille "Stock"
        df_sorties_actuelles = charger_feuille("Sorties")
        synchroniser_et_sauvegarder_stock(df_matieres, df_nouveau_entrees, df_sorties_actuelles)
        
        st.success(f"Entrée de '{choix_designation}' validée et stock synchronisé !")
        st.rerun()
    elif annuler:
        st.rerun()


@st.dialog("📤 Enregistrer une sortie de stock")
def modal_nouvelle_sortie(df_matieres, df_entrees, df_sorties):
    df_actives = df_matieres[df_matieres["Statut"] == "Actif"]
    if df_actives.empty:
        st.warning("Aucune matière première active disponible.")
        if st.button("Fermer"): st.rerun()
        return

    liste_designations = df_actives["Désignation"].tolist()
    choix_designation = st.selectbox("Sélectionner la matière première *", liste_designations, key="sel_sortie")
    
    ligne_matiere = df_actives[df_actives["Désignation"] == choix_designation].iloc[0]
    code_associe = ligne_matiere["Code"]
    unite_associee = ligne_matiere["Unité"]
    
    stock_dispo = calculer_stock_actuel(code_associe, df_entrees, df_sorties)
    
    st.caption(f"Code : **{code_associe}** | Unité : **{unite_associee}**")
    if stock_dispo <= 0:
        st.error(f"🚨 Rupture de stock ! Solde actuel : **{stock_dispo} {unite_associee}**. Sortie impossible.")
    else:
        st.warning(f"📦 Stock théorique disponible en réserve : **{stock_dispo} {unite_associee}**")

    date_sortie = st.date_input("Date de sortie", datetime.today(), key="date_sortie")
    quantite = st.number_input(f"Quantité à sortir ({unite_associee}) *", min_value=0.01, step=0.1, value=1.0)
    destination = st.selectbox("Destination *", DESTINATIONS)
    observation = st.text_input("Observation / Motif (Optionnel)", "")
    
    col_s1, col_s2 = st.columns(2)
    with col_s1:
        soumettre = st.button("Confirmer la sortie", use_container_width=True, disabled=(stock_dispo <= 0))
    with col_s2:
        annuler = st.button("Annuler", use_container_width=True)
        
    if soumettre:
        if quantite > stock_dispo:
            st.error(f"Action refusée : Vous essayez de sortir {quantite} {unite_associee}, mais vous n'avez que {stock_dispo} {unite_associee} en magasin.")
        else:
            nouvel_id = len(df_sorties) + 1
            nouvelle_sortie = {
                "ID": nouvel_id,
                "Date": date_sortie.strftime("%Y-%m-%d"),
                "Code": code_associe,
                "Désignation": choix_designation,
                "Quantité": quantite,
                "Destination": destination,
                "Observation": observation
            }
            df_nouveau_sorties = pd.concat([df_sorties, pd.DataFrame([nouvelle_sortie])], ignore_index=True)
            sauvegarder_feuille(df_nouveau_sorties, "Sorties")
            
            # Mouvement de sortie -> Mise à jour forcée de la feuille "Stock"
            synchroniser_et_sauvegarder_stock(df_matieres, df_entrees, df_nouveau_sorties)
            
            st.success(f"Sortie enregistrée et feuille 'Stock' mise à jour.")
            st.rerun()
    elif annuler:
        st.rerun()


def magasin():
    st.title("📦 Gestion du Magasin")
    
    onglet_matieres, onglet_entrees, onglet_sorties, onglet_stock = st.tabs([
        "📝 Matières premières", 
        "📥 Entrées", 
        "📤 Sorties", 
        "📊 Stock Actuel"
    ])

    df_matieres = charger_feuille("Liste_Matieres")
    df_entrees = charger_feuille("Entrees")
    df_sorties = charger_feuille("Sorties")

    # ==========================================
    # 1. ONGLET : MATIÈRES PREMIÈRES
    # ==========================================
    with onglet_matieres:
        st.subheader("Catalogue des matières premières")
        col_recherche, col_bouton = st.columns([3, 1])
        with col_recherche:
            recherche = st.text_input("🔍 Rechercher une matière (Code ou Désignation) :", "", key="recherche_mp")
        with col_bouton:
            st.write("##")
            if st.button("➕ Nouvelle matière", use_container_width=True):
                modal_ajouter_matiere(df_matieres)

                df_affichage = df_matieres.copy()

        # ============================
        # Nettoyage et correction types
        # compatible Streamlit Cloud
        # ============================

        if "ID" in df_affichage.columns:
            df_affichage["ID"] = df_affichage["ID"].astype(str)

        if "Code" in df_affichage.columns:
            df_affichage["Code"] = df_affichage["Code"].astype(str)

        if "Désignation" in df_affichage.columns:
            df_affichage["Désignation"] = (
                df_affichage["Désignation"]
                .fillna("")
                .astype(str)
            )

        if "Catégorie" in df_affichage.columns:
            df_affichage["Catégorie"] = (
                df_affichage["Catégorie"]
                .fillna(CATEGORIES[0])
                .astype(str)
            )

        if "Unité" in df_affichage.columns:
            df_affichage["Unité"] = (
                df_affichage["Unité"]
                .fillna(UNITES[0])
                .astype(str)
            )

        if "Seuil" in df_affichage.columns:
            df_affichage["Seuil"] = pd.to_numeric(
                df_affichage["Seuil"]
                .astype(str)
                .str.replace(",", "."),
                errors="coerce"
            ).fillna(0).astype(float)

        if "Statut" in df_affichage.columns:
            df_affichage["Statut"] = (
                df_affichage["Statut"]
                .fillna("Actif")
                .astype(str)
            )


        # ============================
        # Contrôle des valeurs Selectbox
        # ============================

        df_affichage["Catégorie"] = df_affichage["Catégorie"].apply(
            lambda x: x if x in CATEGORIES else CATEGORIES[0]
        )

        df_affichage["Unité"] = df_affichage["Unité"].apply(
            lambda x: x if x in UNITES else UNITES[0]
        )

        df_affichage["Statut"] = df_affichage["Statut"].apply(
            lambda x: x if x in ["Actif", "Inactif"] else "Actif"
        )


        # ============================
        # Recherche
        # ============================

        if recherche:
            df_affichage = df_affichage[
                df_affichage["Désignation"]
                .str.contains(recherche, case=False, na=False)
                |
                df_affichage["Code"]
                .str.contains(recherche, case=False, na=False)
            ]


        # ============================
        # Colonne sélection
        # ============================

        if "Sélection" not in df_affichage.columns:
            df_affichage.insert(0, "Sélection", False)

        df_affichage["Sélection"] = (
            df_affichage["Sélection"]
            .astype(bool)
        )


        st.write("---")


        # ============================
        # Data Editor
        # ============================

        editeur_reponse = st.data_editor(
            df_affichage,
            hide_index=True,

            column_config={

                "Sélection": st.column_config.CheckboxColumn(
                    "Sélectionner"
                ),

                "ID": None,

                "Code": st.column_config.TextColumn(
                    "Code"
                ),

                "Désignation": st.column_config.TextColumn(
                    "Désignation"
                ),

                "Catégorie": st.column_config.SelectboxColumn(
                    "Catégorie",
                    options=CATEGORIES
                ),

                "Unité": st.column_config.SelectboxColumn(
                    "Unité",
                    options=UNITES
                ),

                "Seuil": st.column_config.NumberColumn(
                    "Seuil Alerte"
                ),

                "Statut": st.column_config.SelectboxColumn(
                    "Statut",
                    options=["Actif", "Inactif"]
                )
            },

            disabled=["Code"],

            use_container_width=True,

            key="editeur_matieres_unique"
        )

        col_act1, col_act2, col_act3 = st.columns([1.5, 1.5, 1])
        with col_act1:
            modifier_bouton = st.button("✏️ Enregistrer les modifications", use_container_width=True)
        with col_act2:
            desactiver_bouton = st.button("🚫 Désactiver la sélection", use_container_width=True)

        if modifier_bouton and "editeur_matieres_unique" in st.session_state:
            state_edits = st.session_state["editeur_matieres_unique"].get("edited_rows", {})
            if state_edits:
                for idx_affiche, modifs in state_edits.items():
                    code_cible = df_affichage.iloc[idx_affiche]["Code"]
                    idx_principal = df_matieres[df_matieres["Code"] == code_cible].index
                    if not idx_principal.empty:
                        for cle, valeur in modifs.items():
                            df_matieres.loc[idx_principal, cle] = valeur
                
                sauvegarder_feuille(df_matieres, "Liste_Matieres")
                # Changement de fiche -> Re-calcul de la feuille Stock globale
                synchroniser_et_sauvegarder_stock(df_matieres, df_entrees, df_sorties)
                st.success("Modifications enregistrées et stocks synchronisés !")
                st.rerun()

        if desactiver_bouton and editeur_reponse is not None:
            lignes_selectionnees = editeur_reponse[editeur_reponse["Sélection"] == True]
            if not lignes_selectionnees.empty:
                codes_a_desactiver = lignes_selectionnees["Code"].tolist()
                df_matieres.loc[df_matieres["Code"].isin(codes_a_desactiver), "Statut"] = "Inactif"
                sauvegarder_feuille(df_matieres, "Liste_Matieres")
                synchroniser_et_sauvegarder_stock(df_matieres, df_entrees, df_sorties)
                st.success(f"{len(codes_a_desactiver)} matière(s) désactivée(s) et stock synchronisé.")
                st.rerun()

    # ==========================================
    # 2 & 3. ONGLETS ENTRÉES ET SORTIES (Restent inchangés pour le rendu visuel)
    # ==========================================
    with onglet_entrees:
        # [... Vos filtres et affichage df_entrees_filtrees ...]
        st.subheader("📥 Mouvements d'approvisionnement (Entrées)")
        col_entree_btn, col_date_debut, col_date_fin, col_recherche_e = st.columns([1.5, 1, 1, 1.5])
        with col_entree_btn:
            st.write("##")
            if st.button("📥 Nouvelle entrée de stock", use_container_width=True, type="primary"):
                modal_nouvelle_entrée(df_matieres, df_entrees)
        with col_date_debut: date_deb = st.date_input("Du :", datetime(datetime.today().year, 1, 1), key="deb_e")
        with col_date_fin: date_fin = st.date_input("Au :", datetime.today(), key="fin_e")
        with col_recherche_e: recherche_e = st.text_input("🔍 Filtrer (Code, Désignation, Obs) :", "", key="recherche_entree")
        df_entrees_filtrees = df_entrees.copy()
        if not df_entrees_filtrees.empty:
            df_entrees_filtrees["Date"] = pd.to_datetime(df_entrees_filtrees["Date"]).dt.date
            df_entrees_filtrees = df_entrees_filtrees[(df_entrees_filtrees["Date"] >= date_deb) & (df_entrees_filtrees["Date"] <= date_fin)]
            if recherche_e:
                df_entrees_filtrees = df_entrees_filtrees[df_entrees_filtrees['Désignation'].str.contains(recherche_e, case=False, na=False) | df_entrees_filtrees['Code'].str.contains(recherche_e, case=False, na=False)]
        st.write("---")
        st.dataframe(df_entrees_filtrees, hide_index=True, use_container_width=True)

    with onglet_sorties:
        # [... Vos filtres et affichage df_sorties_filtrees ...]
        st.subheader("📤 Mouvements de consommation (Sorties)")
        col_sortie_btn, col_date_debut_s, col_date_fin_s, col_recherche_s = st.columns([1.5, 1, 1, 1.5])
        with col_sortie_btn:
            st.write("##")
            if st.button("📤 Nouvelle sortie / Déstockage", use_container_width=True, type="primary"):
                modal_nouvelle_sortie(df_matieres, df_entrees, df_sorties)
        with col_date_debut_s: date_deb_s = st.date_input("Du :", datetime(datetime.today().year, 1, 1), key="deb_s")
        with col_date_fin_s: date_fin_s = st.date_input("Au :", datetime.today(), key="fin_s")
        with col_recherche_s: recherche_s = st.text_input("🔍 Filtrer (Code, Désignation, Destination) :", "", key="recherche_sortie")
        df_sorties_filtrees = df_sorties.copy()
        if not df_sorties_filtrees.empty:
            df_sorties_filtrees["Date"] = pd.to_datetime(df_sorties_filtrees["Date"]).dt.date
            df_sorties_filtrees = df_sorties_filtrees[(df_sorties_filtrees["Date"] >= date_deb_s) & (df_sorties_filtrees["Date"] <= date_fin_s)]
            if recherche_s:
                df_sorties_filtrees = df_sorties_filtrees[df_sorties_filtrees['Désignation'].str.contains(recherche_s, case=False, na=False) | df_sorties_filtrees['Code'].str.contains(recherche_s, case=False, na=False)]
        st.write("---")
        st.dataframe(df_sorties_filtrees, hide_index=True, use_container_width=True)

    # ==========================================
    # 4. ONGLET : STOCK ACTUEL (LECTURE SIMPLIFIÉE)
    # ==========================================
    with onglet_stock:
        st.subheader("📊 État des stocks en temps réel et Valorisation")
        
        # Lecture directe depuis la feuille Excel mise à jour par événements
        df_stock_final = charger_feuille("Stock")
        
        if df_stock_final.empty:
            # Premier lancement ou fichier vide -> Génération initiale automatique
            df_stock_final = synchroniser_et_sauvegarder_stock(df_matieres, df_entrees, df_sorties)
            
        if df_stock_final.empty:
            st.info("Le catalogue de matières premières est vide. Aucun stock disponible.")
        else:
            # Indicateurs KPI directeurs
            total_articles_valeurs = df_stock_final[df_stock_final["Stock Actuel"] > 0]["Code"].nunique()
            valeur_globale_magasin = df_stock_final["Valeur Stock (FCFA)"].sum()
            alertes_actives = df_stock_final[(df_stock_final["Alerte"].str.contains("🚨")) & (df_stock_final["Statut Article"] == "Actif")].shape[0]
            
            kpi1, kpi2, kpi3 = st.columns(3)
            with kpi1: st.metric("Articles en Stock", f"{total_articles_valeurs}")
            with kpi2: st.metric("Valeur Totale Magasin", f"{valeur_globale_magasin:,.0f} FCFA")
            with kpi3: st.metric("Articles en Alerte Seuil", f"{alertes_actives}", delta="- Attention" if alertes_actives > 0 else None, delta_color="inverse")
            
            st.write("---")
            
            col_f_cat, col_f_alt = st.columns(2)
            with col_f_cat: choix_cat = st.multiselect("Filtrer par Catégorie :", CATEGORIES)
            with col_f_alt: choix_alt = st.radio("Affichage des alertes :", ["Tous les articles", "Uniquement les alertes stock bas"], horizontal=True)
                
            if choix_cat: df_stock_final = df_stock_final[df_stock_final["Catégorie"].isin(choix_cat)]
            if choix_alt == "Uniquement les alertes stock bas": df_stock_final = df_stock_final[df_stock_final["Alerte"].str.contains("🚨")]
                
            st.dataframe(
                df_stock_final,
                hide_index=True,
                column_config={
                    "Code": st.column_config.TextColumn("Code"),
                    "Désignation": st.column_config.TextColumn("Désignation"),
                    "Catégorie": st.column_config.TextColumn("Catégorie"),
                    "Stock Actuel": st.column_config.NumberColumn("Stock Actuel", format="%.2f"),
                    "Unité": st.column_config.TextColumn("Unité"),
                    "Seuil Alerte": st.column_config.NumberColumn("Seuil Alerte", format="%.2f"),
                    "Alerte": st.column_config.TextColumn("Statut Alerte"),
                    "Prix Moyen (FCFA)": st.column_config.NumberColumn("PUMP (FCFA)", format="%d"),
                    "Valeur Stock (FCFA)": st.column_config.NumberColumn("Valeur (FCFA)", format="%d"),
                    "Statut Article": None 
                },
                use_container_width=True
            )
