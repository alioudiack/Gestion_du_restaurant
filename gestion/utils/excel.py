import os
import pandas as pd

DB_PATH = "data/matieres.xlsx"

def initialiser_base_donnees():
    """Crée le fichier Excel et les 4 feuilles si elles n'existent pas."""
    if not os.path.exists("data"):
        os.makedirs("data")
        
    if not os.path.exists(DB_PATH):
        with pd.ExcelWriter(DB_PATH, engine="openpyxl") as writer:
            # 1. Liste_Matieres
            df_matieres = pd.DataFrame(columns=["ID", "Code", "Désignation", "Catégorie", "Unité", "Seuil", "Statut"])
            df_matieres.to_excel(writer, sheet_name="Liste_Matieres", index=False)
            
            # 2. Entrees
            df_entrees = pd.DataFrame(columns=["ID", "Date", "Code", "Désignation", "Quantité", "Prix unitaire", "Montant", "Observation"])
            df_entrees.to_excel(writer, sheet_name="Entrees", index=False)
            
            # 3. Sorties
            df_sorties = pd.DataFrame(columns=["ID", "Date", "Code", "Désignation", "Quantité", "Destination", "Observation"])
            df_sorties.to_excel(writer, sheet_name="Sorties", index=False)
            
            # 4. Stock
            df_stock = pd.DataFrame(columns=["Code", "Désignation", "Entrées", "Sorties", "Stock", "Unité", "Seuil", "Statut"])
            df_stock.to_excel(writer, sheet_name="Stock", index=False)

def charger_feuille(nom_feuille):
    initialiser_base_donnees()
    try:
        return pd.read_excel(DB_PATH, sheet_name=nom_feuille)
    except Exception as e:
        # Si le fichier est corrompu (BadZipFile, etc.), on le supprime et on le recrée
        import os
        if os.path.exists(DB_PATH):
            try:
                os.remove(DB_PATH)
                initialiser_base_donnees()
                return pd.read_excel(DB_PATH, sheet_name=nom_feuille)
            except Exception:
                pass
        
        # Structure de secours si tout échoue
        structures = {
            "Liste_Matieres": pd.DataFrame(columns=["ID", "Code", "Désignation", "Catégorie", "Unité", "Seuil", "Statut"]),
            "Entrees": pd.DataFrame(columns=["ID", "Date", "Code", "Désignation", "Quantité", "Prix unitaire", "Montant", "Observation"]),
            "Sorties": pd.DataFrame(columns=["ID", "Date", "Code", "Désignation", "Quantité", "Destination", "Observation"]),
            "Stock": pd.DataFrame(columns=["Code", "Désignation", "Entrées", "Sorties", "Stock", "Unité", "Seuil", "Statut"])
        }
        return structures.get(nom_feuille, pd.DataFrame())

def sauvegarder_feuille(df, nom_feuille):
    initialiser_base_donnees()
    # On utilise ExcelWriter pour mettre à jour une feuille sans écraser les autres
    with pd.ExcelWriter(DB_PATH, engine="openpyxl", mode="a", if_sheet_exists="replace") as writer:
        df.to_excel(writer, sheet_name=nom_feuille, index=False)