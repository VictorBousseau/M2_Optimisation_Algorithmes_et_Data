import gurobipy as gp
from gurobipy import GRB    

# 24 Hour Load Forecast (MW)
load_forecast = [
     4,  4,  4,  4,  4,  4,   6,   6,
    12, 12, 12, 12, 12,  4,   4,   4,
     4, 16, 16, 16, 16,  6.5, 6.5, 6.5,
]

# solar energy forecast (MW)
solar_forecast = [
    0,   0,   0,   0,   0,   0,   0.5, 1.0,
    1.5, 2.0, 2.5, 3.5, 3.5, 2.5, 2.0, 1.5,
    1.0, 0.5, 0,   0,   0,   0,   0,   0,
]

# global number of time intervals
nTimeIntervals = len(load_forecast)

# thermal units
thermal_units = ["gen1", "gen2", "gen3"]

# thermal units' costs  (a + b*p + c*p^2), (startup and shutdown costs)
thermal_units_cost, a, b, c, sup_cost, sdn_cost = gp.multidict(
    {
        "gen1": [5.0, 0.5, 1.0, 2, 1],
        "gen2": [5.0, 0.5, 0.5, 2, 1],
        "gen3": [5.0, 3.0, 2.0, 2, 1],
    }
)

# thernal units operating limits
thermal_units_limits, pmin, pmax = gp.multidict(
    {"gen1": [1.5, 5.0], "gen2": [2.5, 10.0], "gen3": [1.0, 3.0]}
)

# thermal units dynamic data (initial commitment status)
thermal_units_dyn_data, init_status = gp.multidict(
    {"gen1": [0], "gen2": [0], "gen3": [0]}
)


def show_results():
    obj_val_s = model.ObjVal
    print(f" OverAll Cost = {round(obj_val_s, 2)}	")
    print("\n")
    print("%5s" % "time", end=" ")
    for t in range(nTimeIntervals):
        print("%4s" % t, end=" ")
    print("\n")

    for g in thermal_units:
        print("%5s" % g, end=" ")
        for t in range(nTimeIntervals):
            print("%4.1f" % thermal_units_out_power[g, t].X, end=" ")
        print("\n")

    print("%5s" % "Solar", end=" ")
    for t in range(nTimeIntervals):
        print("%4.1f" % solar_forecast[t], end=" ")
    print("\n")

    print("%5s" % "Load", end=" ")
    for t in range(nTimeIntervals):
        print("%4.1f" % load_forecast[t], end=" ")
    print("\n")


pi_max = pmax       # Maximum Power for unit i (MW)
pi_min = pmin       # Minimum Power for unit i (MW)
αi = a              # Fixed Cost for unit i ($/h)
βi = b              # Linear Cost for unit i ($/MWh)
γi = c              # Quadratic Cost for unit i ($/MWh/MWh)
δi = sup_cost       # Start Up Cost for unit i ($)
ζi = sdn_cost       # Shutdown Cost for unit i ($)
Lt = load_forecast  # Load Forecast at time interval t (MW)
St = solar_forecast # Solar Energy Forecast at time interval t (MW)


with gp.Env() as env, gp.Model(env=env) as model:

    # add variables for thermal units (power and statuses for commitment, startup and shutdown)
    # p[g,t] ≥ 0 : puissance produite par l’unité g à l’instant t
    thermal_units_out_power = model.addVars(
        thermal_units, nTimeIntervals, lb=0.0, name="p"
    )

    # v[g,t] ∈ {0,1} : l’unité g démarre à l’instant t ?
    thermal_units_startup_status = model.addVars(
        thermal_units, nTimeIntervals, vtype=GRB.BINARY, name="v"
    )

    # w[g,t] ∈ {0,1} : l’unité g s’arrête à l’instant t ?
    thermal_units_shutdown_status = model.addVars(
        thermal_units, nTimeIntervals, vtype=GRB.BINARY, name="w"
    )

    # u[g,t] ∈ {0,1} : l’unité g est en marche à l’instant t ?
    thermal_units_comm_status = model.addVars(
        thermal_units, nTimeIntervals, vtype=GRB.BINARY, name="u"
    )

    # define objective function as an empty quadratic construct and add terms
    obj_fun_expr = gp.QuadExpr(0)
    for t in range(nTimeIntervals):
        for g in thermal_units:
            p_gt = thermal_units_out_power[g, t]
            u_gt = thermal_units_comm_status[g, t]
            v_gt = thermal_units_startup_status[g, t]
            w_gt = thermal_units_shutdown_status[g, t]
            obj_fun_expr.add( γi[g]*p_gt*p_gt + βi[g]*p_gt + αi[g]*u_gt + δi[g]*v_gt + ζi[g]*w_gt )

    model.setObjective(obj_fun_expr, GRB.MINIMIZE)

    # Power balance equations
    for t in range(nTimeIntervals):
        model.addConstr(
            gp.quicksum(thermal_units_out_power[g, t] for g in thermal_units) + solar_forecast[t]
            == load_forecast[t],
            name="power_balance_" + str(t),
        )

    # Thermal units logical constraints
    for t in range(nTimeIntervals):
        for g in thermal_units:
            u_gt = thermal_units_comm_status[g, t]        # u[g,t] ∈ {0,1} 1 si l’unité g est en marche à l’instant t, 0 sinon
            v_gt = thermal_units_startup_status[g, t]     # v[g,t] ∈ {0,1} 1 si l’unité g démarre à l’instant t, 0 sinon
            w_gt = thermal_units_shutdown_status[g, t]    # w[g,t] ∈ {0,1} 1 si l’unité g s’arrête à l’instant t, 0 sinon
            if t == 0:
                # u[g,0] - init_status[g] = v[g,0] - w[g,0]
                model.addConstr(
                    u_gt - init_status[g] == v_gt - w_gt,
                    name=f"logical1_{g}_{t}",
                )
            else:
                model.addConstr(
                    u_gt - thermal_units_comm_status[g, t - 1] == v_gt - w_gt,
                    name="logical1_" + g + "_" + str(t),
                )

            model.addConstr(
                thermal_units_out_power[g, t] <= pi_max[g] * u_gt,
                name="logical2_" + g + "_" + str(t),
            )

    # Thermal units physical constraints, using indicator constraints
    for t in range(nTimeIntervals):
        for g in thermal_units:
            p_gt = thermal_units_out_power[g, t]          # p[g,t] ≥ 0
            u_gt = thermal_units_comm_status[g, t]        # u[g,t] ∈ {0,1}

            # Si u=0 -> p=0
            model.addGenConstrIndicator(
                u_gt, 0, p_gt == 0.0,
                name=f"phys_off_{g}_{t}"
            )

            # Si u=1 -> p >= Pmin
            model.addGenConstrIndicator(
                u_gt, 1, p_gt >= pi_min[g],
                name=f"phys_min_{g}_{t}"
            )

            # Si u=1 -> p <= Pmax
            model.addGenConstrIndicator(
                u_gt, 1, p_gt <= pi_max[g],
                name=f"phys_max_{g}_{t}"
            )

    model.optimize()
    show_results()