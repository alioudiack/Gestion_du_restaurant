from pathlib import Path
import os
import pandas as pd

# Calcul dynamique de la racine du projet
BASE_DIR = Path(__file__).resolve().parent.parent

# Définition des chemins absolus sécurisés
DOSSIER_DATA = BASE_DIR / "data"
DB_PRODUITS_PATH = DOSSIER_DATA / "Produits.xlsx"

def initialiser_base_produits():
    """Crée le fichier Excel des produits finis et ses feuilles si elles n'existent pas."""
    # Création du dossier 'data' s'il n'existe pas
    if not DOSSIER_DATA.exists():
        DOSSIER_DATA.mkdir(parents=True, exist_ok=True)
        
    if not DB_PRODUITS_PATH.exists():
        with pd.ExcelWriter(DB_PRODUITS_PATH, engine="openpyxl") as writer:
            # 1. Liste_Produits
            df_produits = pd.DataFrame(columns=["ID", "Code", "Désignation", "Catégorie", "Prix_Vente", "Statut"])
            df_produits.to_excel(writer, sheet_name="Liste_Produits", index=False)
            
            # 2. Ventes
            df_ventes = pd.DataFrame(columns=["ID", "Date", "Code", "Désignation", "Quantité", "Prix_Unitaire", "Montant", "Serveur"])
            df_ventes.to_excel(writer, sheet_name="Ventes", index=False)
            
            # 3. Stock_Produits
            df_stock_p = pd.DataFrame(columns=["Code", "Désignation", "Initial", "Ventes", "Disponible"])
            df_stock_p.to_excel(writer, sheet_name="Stock_Produits", index=False)

def charger_feuille_produit(nom_feuille):
    initialiser_base_produits()
    try:
        return pd.read_excel(DB_PRODUITS_PATH, sheet_name=nom_feuille)
    except Exception as e:
        # Si le fichier est corrompu, réinitialisation complète de sécurité
        if DB_PRODUITS_PATH.exists():
            try:
                os.remove(DB_PRODUITS_PATH)
                initialiser_base_produits()
                return pd.read_excel(DB_PRODUITS_PATH, sheet_name=nom_feuille)
            except Exception:
                pass
        
        # Structure de secours si tout échoue
        structures = {
            "Liste_Produits": pd.DataFrame(columns=["ID", "Code", "Désignation", "Catégorie", "Prix_Vente", "Statut"]),
            "Ventes": pd.DataFrame(columns=["ID", "Date", "Code", "Désignation", "Quantité", "Prix_Unitaire", "Montant", "Serveur"]),
            "Stock_Produits": pd.DataFrame(columns=["Code", "Désignation", "Initial", "Ventes", "Disponible"])
        }
        return structures.get(nom_feuille, pd.DataFrame())

def sauvegarder_feuille_produit(df, nom_feuille):
    initialiser_base_produits()
    # Met à jour la feuille ciblée sans altérer les autres structures du classeur Excel
    with pd.ExcelWriter(DB_PRODUITS_PATH, engine="openpyxl", mode="a", if_sheet_exists="replace") as writer:
        df.to_excel(writer, sheet_name=nom_feuille, index=False)
