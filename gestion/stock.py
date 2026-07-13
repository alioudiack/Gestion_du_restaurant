Python
import os
import sys

# Ajoute le dossier racine du projet au chemin de recherche de Python
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

# Le reste de vos imports...
import streamlit as st
from gestion.utils.excel import initialiser_base_donnees
from streamlit_option_menu import option_menu



from gestion.pages.accueil import accueil
from gestion.pages.magasin import magasin
from gestion.pages.produits_finis import produit
from gestion.pages.ventes import vente
from gestion.pages.inventaires import inventaire
from gestion.pages.rapports import rapport



# ==========================
# CONFIGURATION
# ==========================

st.set_page_config(
    page_title="Gestion Restaurant",
    page_icon="🍽️",
    layout="wide" 
)

initialiser_base_donnees()

# ==========================
# MENU
# ==========================

with st.sidebar:

    st.title("🍽️ Restaurant")

    menu = option_menu(
        menu_title="Navigation",

        options=[
            "Accueil",
            "Magasin",
            "Produits finis",
            "Ventes",
            "Inventaire",
            "Rapports"
        ],

        icons=[
            "house",
            "box-seam",
            "egg-fried",
            "cash-coin",
            "clipboard-check",
            "graph-up"
        ],

        default_index=0
    )


# ==========================
# ROUTAGE DES PAGES
# ==========================

if menu == "Accueil":


    accueil()


elif menu == "Magasin":

    
    magasin()


elif menu == "Produits finis":

    
    produit()


elif menu == "Ventes":

    
    vente()


elif menu == "Inventaire":

    
    inventaire()


elif menu == "Rapports":

    
    rapport()
