import json
import pandas as pd
import numpy as np
import gurobipy as gp
from gurobipy import GRB

with open("data/data/portfolio-example.json", "r") as f:
    data = json.load(f)

n = data["num_assets"]
sigma = np.array(data["covariance"])
mu = np.array(data["expected_return"])
mu_0 = data["target_return"]
k = data["portfolio_max_size"]

# Dans un problème d'optimisation de portefeuille, il y a n actifs.
# Chaque actif i est associé à un rendement espéré μi et chaque paire d'actifs (i, j) possède une covariance (risque) σij. 
# L'objectif est de trouver la fraction optimale du portefeuille investie dans chaque actif afin de minimiser le risque d'investissement,de sorte que 
# 1) le rendement espéré total de l'investissement dépasse le rendement cible minimal μ0 et 
# 2) le portefeuille investisse dans un maximum de k ≤ n actifs.
# xi : Investissement relatif dans l'actif
# yi : Variable binaire contrôlant la négociation de l'actif i


with gp.Model("portfolio") as model:
    # Name the modeling objects to retrieve them
    x = model.addVars(n, vtype=GRB.BINARY, name="x")                       # Decision variables: whether to include asset i in the portfolio
    y = model.addVars(n, lb=0.0,vtype=GRB.CONTINUOUS, name="y")            # Weight of asset i in the portfolio

    model.setObjective(
        gp.quicksum(sigma[i, j] * y[i] * y[j] for i in range(n) for j in range(n)) 
        ,GRB.MINIMIZE
    )  # Minimize risk x' Sigma x
    
    # Constraints
    model.addConstr(
        gp.quicksum(mu[i] * y[i] for i in range(n)) >= mu_0,
        name="return",
    )  # Return constraint // le rendement espéré total de l'investissement dépasse le rendement cible minimal μ0

    model.addConstr(
        gp.quicksum(y[i] for i in range(n)) == 1.0,
        name="budget",
    )  # Budget: sum of weights = 1 // utiliser tous les fonds disponibles

    model.addConstr(
        gp.quicksum(x[i] for i in range(n)) <= k,
        name="cardinality",
    )  # Cardinality: at most k assets // le portefeuille investisse dans un maximum de k ≤ n actifs

    model.addConstrs(
        (y[i] <= x[i] for i in range(n)),
        name="link",
    )  # Link x_i <= y_i (if not selected, weight is zero) // si un actif n'est pas sélectionné, son poids dans le portefeuille est nul
    
    model.optimize()

    # Write the solution into a DataFrame
    portfolio = [var.X for var in model.getVars() if "x" in var.VarName]
    risk = model.ObjVal
    expected_return = model.getRow(model.getConstrByName("return")).getValue()
    df = pd.DataFrame(
        data=portfolio + [risk, expected_return],
        index=[f"asset_{i}" for i in range(n)] + ["risk", "return"],
        columns=["Portfolio"],
    )
    print(df)