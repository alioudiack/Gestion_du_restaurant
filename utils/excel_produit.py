import os
import pandas as pd

# Base de données Excel globale pour la partie cuisine et comptoir de vente
FICHIER_EXCEL = "data/Produits.xlsx"

def initialiser_onglets_production():
    """S'assure que toutes les feuilles nécessaires existent avec leurs colonnes respectives."""
    structures_initiales = {
        "Liste_Matieres": pd.DataFrame(columns=["Code", "Désignation", "Unité", "Statut"]), # Sécurité d'alignement
        "Liste_Produits": pd.DataFrame(columns=["ID", "Produit", "Catégorie", "Prix vente"]),
        "Recettes": pd.DataFrame(columns=["ID", "Produit", "Code Matière", "Matière", "Quantité", "Unité"]),
        "Fabrication": pd.DataFrame(columns=["ID", "Date", "Produit", "Quantité"]),
        "Ventes": pd.DataFrame(columns=["ID", "Date", "Produit", "Quantité", "Prix Unitaire", "Total", "Mode Paiement"])
    }
    
    if not os.path.exists(FICHIER_EXCEL):
        # Si le fichier n'existe pas du tout, on crée tout à vide
        with pd.ExcelWriter(FICHIER_EXCEL, engine="openpyxl") as writer:
            for nom_feuille, df in structures_initiales.items():
                df.to_excel(writer, sheet_name=nom_feuille, index=False)
        return

    # Si le fichier existe, on vérifie onglet par onglet s'il manque quelque chose
    try:
        onglets_existants = pd.ExcelFile(FICHIER_EXCEL).sheet_names
    except Exception:
        onglets_existants = []

    for nom_feuille, df_initial in structures_initiales.items():
        if nom_feuille not in onglets_existants:
            # On ajoute l'onglet manquant sans écraser les autres
            with pd.ExcelWriter(FICHIER_EXCEL, engine="openpyxl", mode="a", if_sheet_exists="replace") as writer:
                df_initial.to_excel(writer, sheet_name=nom_feuille, index=False)


def charger_donnees_production(nom_feuille):
    """Charge une feuille spécifique en garantissant sa structure en cas d'absence."""
    initialiser_onglets_production()
    try:
        df = pd.read_excel(FICHIER_EXCEL, sheet_name=nom_feuille)
        df = df.dropna(how="all")
        return df
    except Exception:
        structures = {
            "Liste_Produits": pd.DataFrame(columns=["ID", "Produit", "Catégorie", "Prix vente"]),
            "Recettes": pd.DataFrame(columns=["ID", "Produit", "Code Matière", "Matière", "Quantité", "Unité"]),
            "Fabrication": pd.DataFrame(columns=["ID", "Date", "Produit", "Quantité"]),
            "Ventes": pd.DataFrame(columns=["ID", "Date", "Produit", "Quantité", "Prix Unitaire", "Total", "Mode Paiement"])
        }
        return structures.get(nom_feuille, pd.DataFrame())


def sauvegarder_donnees_production(df, nom_feuille):
    """Sauvegarde les données dans l'onglet spécifié sans altérer le reste du fichier Excel."""
    initialiser_onglets_production()
    try:
        with pd.ExcelWriter(FICHIER_EXCEL, engine="openpyxl", mode="a", if_sheet_exists="replace") as writer:
            df.to_excel(writer, sheet_name=nom_feuille, index=False)
        return True
    except Exception as e:
        print(f"Erreur lors de la sauvegarde de l'onglet {nom_feuille} : {e}")
        return False