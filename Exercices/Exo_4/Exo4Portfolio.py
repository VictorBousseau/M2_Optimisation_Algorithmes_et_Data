import json
import pandas as pd
import numpy as np
import gurobipy as gp
# from gurobipy import GRB  # optionnel; sinon utiliser gp.GRB

with open("data/data/portfolio-example.json", "r") as f:
    data = json.load(f)

n = data["num_assets"]
sigma = np.array(data["covariance"])
mu = np.array(data["expected_return"])
mu_0 = data["target_return"]
k = data["portfolio_max_size"]

assets = range(n)

with gp.Model("portfolio") as model:
    # Variables
    x = model.addVars(assets, lb=0.0, name="x")                    # poids du portefeuille
    y = model.addVars(assets, vtype=gp.GRB.BINARY, name="y")       # actif sélectionné ?

    # Objectif : minimiser le risque x' Sigma x
    model.setObjective(
        gp.quicksum(sigma[i, j] * x[i] * x[j] for i in assets for j in assets),
        gp.GRB.MINIMIZE,
    )

    # Contrainte de rendement (nommée "return" pour la récupérer après)
    model.addConstr(gp.quicksum(mu[i] * x[i] for i in assets) >= mu_0, name="return")

    # Budget : somme des poids = 1
    model.addConstr(gp.quicksum(x[i] for i in assets) == 1.0, name="budget")

    # Cardinalité : au plus k actifs
    model.addConstr(gp.quicksum(y[i] for i in assets) <= k, name="cardinality")

    # Lien x_i <= y_i (si non sélectionné, poids nul)
    model.addConstrs((x[i] <= y[i] for i in assets), name="link")

    model.optimize()

    # Écriture de la solution dans un DataFrame
    portfolio = [var.X for var in model.getVars() if "x" in var.VarName]
    risk = model.ObjVal
    expected_return = model.getRow(model.getConstrByName("return")).getValue()

    df = pd.DataFrame(
        data=portfolio + [risk, expected_return],
        index=[f"asset_{i}" for i in range(n)] + ["risk", "return"],
        columns=["Portfolio"],
    )
    print(df)
