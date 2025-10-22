import json
import gurobipy as gp
from gurobipy import GRB
from pathlib import Path

# ----- Load data from JSON -----
with open("data/data/lot_sizing_data.json", "r") as f:
    data = json.load(f)

name = data["name"]
H    = int(data["H"])
d    = [float(val) for val in data["demand"]]
c    = [float(val) for val in data["var_cost"]]
f    = [float(val) for val in data["setup_cost"]]
h    = [float(val) for val in data["hold_cost"]]
Qmin = float(data["Qmin"])
Qmax = float(data["Qmax"])
I0   = float(data["I0"])

# Basic validation
assert len(d) == H and len(c) == H and len(f) == H and len(h) == H
assert 0 <= Qmin <= Qmax

# ----- Build model -----
with gp.Env() as env, gp.Model(name, env=env) as model:

    T = range(H)

    # Variables
    x = model.addVars(T, lb=0.0, name="x")                 # quantité produite en t
    y = model.addVars(T, vtype=gp.GRB.BINARY, name="y")    # 1 si on produit en t
    I = model.addVars(T, lb=0.0, name="I")                 # stock fin de période t

    # Objectif : coûts variables + setups + tenue en stock
    model.setObjective(
        gp.quicksum(c[t] * x[t] + f[t] * y[t] + h[t] * I[t] for t in T),
        gp.GRB.MINIMIZE
    )

    # Bilans de stock
    # I_0 = I0 + x_0 - d_0
    model.addConstr(I[0] == I0 + x[0] - d[0], name="balance_0")
    # I_t = I_{t-1} + x_t - d_t,  t=1..H-1
    model.addConstrs(
        (I[t] == I[t-1] + x[t] - d[t] for t in T if t >= 1),
        name="balance"
    )

    # Lot minimum et capacité si on produit
    model.addConstrs((x[t] <= Qmax * y[t] for t in T), name="cap")
    model.addConstrs((x[t] >= Qmin * y[t] for t in T), name="minbatch")

    # Optimize
    model.optimize()

    if model.SolCount:
        assert model.ObjVal == 1198.5
        print(f"Total cost = {model.ObjVal:.2f}")
        for t in range(H):
            print(f"t={t:2d}: y={int(y[t].X)} x={x[t].X:.1f} I={I[t].X:.1f}")
