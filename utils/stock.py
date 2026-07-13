import pandas as pd


def calculer_stock(matieres, entrees, sorties):

    stock = matieres[
        ["Designation"]
    ].copy()


    if not entrees.empty:

        entrees_calc = (
            entrees
            .groupby("Designation")["Quantite"]
            .sum()
        )

    else:

        entrees_calc = pd.Series()



    if not sorties.empty:

        sorties_calc = (
            sorties
            .groupby("Designation")["Quantite"]
            .sum()
        )

    else:

        sorties_calc = pd.Series()



    stock["Stock_Entree"] = (
        stock["Designation"]
        .map(entrees_calc)
        .fillna(0)
    )


    stock["Stock_Sortie"] = (
        stock["Designation"]
        .map(sorties_calc)
        .fillna(0)
    )


    stock["Stock_Disponible"] = (
        stock["Stock_Entree"]
        -
        stock["Stock_Sortie"]
    )


    return stock