import json
import gurobipy as gp
from gurobipy import GRB, nlfunc
from pathlib import Path
import math

with gp.Model("Cone") as model:
    r = model.addVar(lb=0.0,ub=10,vtype=GRB.CONTINUOUS, name="r")
    R = model.addVar(lb=0.0,ub=10,vtype=GRB.CONTINUOUS, name="R")
    h = model.addVar(lb=0.0,ub=10,vtype=GRB.CONTINUOUS, name="h")
    Objectif = model.addVar(lb=0.0,vtype=GRB.CONTINUOUS, name="Objectif")
    Surface = model.addVar(lb=1,ub=1,vtype=GRB.CONTINUOUS, name="Surface")

    model.setObjective(
        Objectif,
        GRB.MAXIMIZE
    )

    model.addConstr(
        Surface == (math.pi*r**2 + math.pi*(R + r)* nlfunc.sqrt((R-r)**2+h**2)) ,
        name="Surface use"
    )

    model.addConstr(
        Objectif == ((math.pi*h)/3)*(R**2+R*r+r**2)
    )

    model.optimize()
    
    if model.SolCount > 0:
        r_opt = r.X
        R_opt = R.X
        h_opt = h.X
        obj_opt = Objectif.X
        S_opt = Surface.X

        # Recalculs pour vérification numérique (avec les valeurs optimales)
        S_check = math.pi*r_opt**2 + math.pi*(R_opt + r_opt)*math.sqrt((R_opt - r_opt)**2 + h_opt**2)
        V_check = (math.pi*h_opt/3.0)*(R_opt**2 + R_opt*r_opt + r_opt**2)

        print("\n=== Solution optimale ===")
        print(f"r         = {r_opt:.6f}")
        print(f"R         = {R_opt:.6f}")
        print(f"h         = {h_opt:.6f}")
        print(f"Surface   = {S_opt:.6f}")
        print(f"Objectif  = {obj_opt:.6f}  (volume)")

        # Contrôles rapides (écarts numériques très petits attendus)
        print("\n--- Vérifications ---")
        print(f"Surface (recalcul) = {S_check:.6f}   | écart = {abs(S_opt - S_check):.3e}")
        print(f"Volume  (recalcul) = {V_check:.6f}   | écart = {abs(obj_opt - V_check):.3e}")
    else:
        print("Aucune solution trouvée (SolCount=0). Statut:", model.Status)