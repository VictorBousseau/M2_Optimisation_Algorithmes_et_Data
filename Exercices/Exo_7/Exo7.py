from functools import partial
import gurobipy as gp
from gurobipy import GRB
import math

class CallbackData:
    def __init__(self):
        self.last_gap_change_time = -GRB.INFINITY
        self.last_gap = GRB.INFINITY


def callback(model, where, *, cbdata):
    if where != GRB.Callback.MIP:
        return
    if model.cbGet(GRB.Callback.MIP_SOLCNT) == 0:
        return

    # Temps courant
    current_time = model.cbGet(GRB.Callback.RUNTIME)
    # Reconstruire le gap courant: |bestobj - bestbnd| / (|bestobj| + eps)
    bestobj = model.cbGet(GRB.Callback.MIP_OBJBST)  # meilleure solution entière
    bestbnd = model.cbGet(GRB.Callback.MIP_OBJBND)  # meilleure borne

    if math.isinf(bestobj) or math.isinf(bestbnd):
        current_gap = GRB.INFINITY
    else:
        denom = abs(bestobj) + 1e-10
        current_gap = abs(bestobj - bestbnd) / denom

    # Logique d'arrêt si le gap n'a pas baissé d'au moins epsilon
    if (current_time - cbdata.last_gap_change_time > max_time_between_gap_updates and
            abs(cbdata.last_gap - current_gap) < epsilon_to_compare_gap):
        print(f"Terminating optimization: gap has not changed significantly "
              f"in the last {max_time_between_gap_updates} seconds. "
              f"(gap ~ {current_gap:.6g})")
        model.terminate()
    elif abs(cbdata.last_gap - current_gap) >= epsilon_to_compare_gap:
        cbdata.last_gap = current_gap
        cbdata.last_gap_change_time = current_time

with gp.read("data/data/mkp.mps") as model:
    # Global variables used in the callback function
    max_time_between_gap_updates = 15
    epsilon_to_compare_gap = 1e-4

    # Initialize data passed to the callback function
    callback_data = CallbackData()
    callback_func = partial(callback, cbdata=callback_data)

    model.optimize(callback_func)