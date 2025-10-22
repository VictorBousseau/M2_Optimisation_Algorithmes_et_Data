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
    x = model.addVars(H, lb=0.0,vtype=GRB.INTEGER, name="x")
    y = model.addVars(H, vtype=GRB.BINARY,name="y")
    I = model.addVars(H, lb=0.0,vtype=GRB.INTEGER, name="I")

    #objectif
    model.setObjective(
        gp.quicksum(x[t]*c[t]+ f[t]*y[t]+ h[t]* I[t] for t in range (H)),
        GRB.MINIMIZE
    )

    # Constraints
    model.addConstr(I[0] == I0 + x[0] - d[0], name="balance_0")

    model.addConstrs(
        (I[t] == I[t-1] + x[t] - d[t] for t in range (1,H)) ,
        name="Inventory_Balance"
    ) 

    model.addConstrs(
        (x[t] <= Qmax*y[t] for t in range (H)),
        name="Ne pas dépassé la quantité de production max"
    )

    model.addConstrs(
        (x[t] >= Qmin*y[t] for t in range (H)),
        name="Minimum de prod si on produit"
    )

    model.addConstrs(
        (x[t] >= 0 for t in range (H)),
        name="Quantité produite >= 0"
    )
    model.addConstr(
        (I[t] >= 0 for t in range (H)),
        name="Stock >= 0"
    )

    # Optimize
    model.optimize()

    if model.SolCount:
        assert model.ObjVal == 1198.5
        print(f"Total cost = {model.ObjVal:.2f}")
        for t in range(H):
            print(f"t={t:2d}: y={int(y[t].X)} x={x[t].X:.1f} I={I[t].X:.1f}")