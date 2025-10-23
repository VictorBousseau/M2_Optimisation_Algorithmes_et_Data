import gurobipy as gp
from gurobipy import GRB
import numpy as np


load_forecast = [
     4,  4,  4,  4,  4,  4,   6,   6,
    12, 12, 12, 12, 12,  4,   4,   4,
     4, 16, 16, 16, 16,  6.5, 6.5, 6.5,
]
solar_forecast = [
    0,   0,   0,   0,   0,   0,   0.5, 1.0,
    1.5, 2.0, 2.5, 3.5, 3.5, 2.5, 2.0, 1.5,
    1.0, 0.5, 0,   0,   0,   0,   0,   0,
]
thermal_units = ["gen1", "gen2", "gen3"]

thermal_units_cost, a, b, c, sup_cost, sdn_cost = gp.multidict(
    {"gen1": [5.0, 0.5, 1.0, 2, 1],
     "gen2": [5.0, 0.5, 0.5, 2, 1],
     "gen3": [5.0, 3.0, 2.0, 2, 1]}
)
thermal_units_limits, pmin, pmax = gp.multidict(
    {"gen1": [1.5, 5.0], "gen2": [2.5, 10.0], "gen3": [1.0, 3.0]}
)
thermal_units_dyn_data, init_status = gp.multidict(
    {"gen1": [0], "gen2": [0], "gen3": [0]}
)

T = len(load_forecast)         # nb d'heures
G = len(thermal_units)         # nb d'unités
rngG = range(G)
rngT = range(T)

# Convertis les params en vecteurs numpy bien typés (G,) ou (T,)
a_vec   = np.array([a[g]        for g in thermal_units], dtype=float)
b_vec   = np.array([b[g]        for g in thermal_units], dtype=float)
c_vec   = np.array([c[g]        for g in thermal_units], dtype=float)
sup_vec = np.array([sup_cost[g] for g in thermal_units], dtype=float)
sdn_vec = np.array([sdn_cost[g] for g in thermal_units], dtype=float)
pmin_vec= np.array([pmin[g]     for g in thermal_units], dtype=float)
pmax_vec= np.array([pmax[g]     for g in thermal_units], dtype=float)

init_vec= np.array([init_status[g] for g in thermal_units], dtype=float)
Lt      = np.array(load_forecast, dtype=float)
St      = np.array(solar_forecast, dtype=float)

# --------------------------------
# Modèle Matrix API (addMVar)
# --------------------------------
with gp.Env() as env, gp.Model("UC_matrix", env=env) as model:

    # Variables matrices (G x T)
    # p ≥ 0 (puissance); u,v,w binaires
    p = model.addMVar((G, T), name="p")
    u = model.addMVar((G, T), vtype=GRB.BINARY, name="u")
    v = model.addMVar((G, T), vtype=GRB.BINARY, name="v")
    w = model.addMVar((G, T), vtype=GRB.BINARY, name="w")

    # -------------------------
    # Objectif (somme g,t)
    # -------------------------
    # On itère sur t (vectorisation en g via produits scalaires)
    obj = gp.QuadExpr(0.0)
    for t in rngT:
        # parties linéaires : a·u[:,t] + b·p[:,t] + sup·v[:,t] + sdn·w[:,t]
        obj += a_vec @ u[:, t] + b_vec @ p[:, t] + sup_vec @ v[:, t] + sdn_vec @ w[:, t]
        # partie quadratique : somme_g c[g] * p[g,t]^2
        # -> produit quadratique diagonal : p[:,t] @ diag(c) @ p[:,t]
        # on crée Q_t = diag(c_vec)
        Qt = np.diag(c_vec)
        obj += p[:, t] @ Qt @ p[:, t]
    model.setObjective(obj, GRB.MINIMIZE)

    # --------------------------------
    # 1) Équilibre de puissance (par t)
    #     sum_g p[g,t] + S_t = L_t
    # --------------------------------
    for t in rngT:
        model.addConstr(p[:, t].sum() + St[t] == Lt[t], name=f"balance_{t}")

    # --------------------------------
    # 2) Logique u - u_prev = v - w
    #    (vectorisée en g, petite boucle en t)
    # --------------------------------
    # t=0 : u[:,0] - init = v[:,0] - w[:,0]
    model.addConstr(u[:, 0] - init_vec == v[:, 0] - w[:, 0], name="logic_t0")

    # t>=1 : u[:,t] - u[:,t-1] = v[:,t] - w[:,t]
    for t in range(1, T):
        model.addConstr(u[:, t] - u[:, t-1] == v[:, t] - w[:, t], name=f"logic_t{t}")

    # Pas start & stop simultanés : v + w ≤ 1
    # (vectorisé en g, boucle sur t)
    for t in rngT:
        model.addConstr(v[:, t] + w[:, t] <= 1, name=f"no_simul_{t}")

    # --------------------------------------------------------
    # 3) Contraintes physiques via indicateurs (exception)
    #    Pour chaque (g,t) :
    #      u=0 -> p=0
    #      u=1 -> p ≥ pmin[g]
    #      u=1 -> p ≤ pmax[g]
    # --------------------------------------------------------
    for g in rngG:
        for t in rngT:
            model.addGenConstrIndicator(u[g, t], False, p[g, t] == 0.0,
                                        name=f"off_zero_{g}_{t}")
            model.addGenConstrIndicator(u[g, t], True,  p[g, t] >= pmin_vec[g],
                                        name=f"min_when_on_{g}_{t}")
            model.addGenConstrIndicator(u[g, t], True,  p[g, t] <= pmax_vec[g],
                                        name=f"max_when_on_{g}_{t}")

    # Résolution
    model.optimize()

    # -------------------------
    # Petit affichage
    # -------------------------
    if model.SolCount:
        print(f"Total cost = {model.ObjVal:.3f}\n")
        header = "      " + " ".join([f"{t:>4d}" for t in rngT])
        print(header)
        for gi, g in enumerate(thermal_units):
            row = "p " + g + " " + " ".join(f"{p[gi, t].X:>4.1f}" for t in rngT)
            print(row)
        print("\nSolar:", " ".join(f"{St[t]:>4.1f}" for t in rngT))
        print("Load :", " ".join(f"{Lt[t]:>4.1f}" for t in rngT))
