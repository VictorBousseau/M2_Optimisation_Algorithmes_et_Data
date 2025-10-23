import math
import gurobipy as gp
from gurobipy import GRB, nlfunc as nl


# Parameters
L1, L2 = 1.0, 0.8             # Lengths of the links
x_star, y_star = 1.20, 0.60   # Point to reach
xo, yo, r = 0.50, 0.00, 0.20  # Disk to avoid

# Joint limits
theta1_min, theta1_max = -math.pi, math.pi
theta2_min, theta2_max = -0.75*math.pi, 0.75*math.pi


# Build model
m = gp.Model("robot_arm_nlfunc")

# Decision variables (angles)
theta1 = m.addVar(lb=theta1_min, ub=theta1_max, name="theta1")
theta2 = m.addVar(lb=theta2_min, ub=theta2_max, name="theta2")

# Kinematics variables (end-effector and mid-link point)
x  = m.addVar(lb=-GRB.INFINITY, name="x")
y  = m.addVar(lb=-GRB.INFINITY, name="y")
xm = m.addVar(lb=-GRB.INFINITY, name="xm")
ym = m.addVar(lb=-GRB.INFINITY, name="ym")

# Nonlinear trig expressions via nlfunc
# These are NLExpr objects that you can use directly in constraints/objective
c1  = nl.cos(theta1)
s1  = nl.sin(theta1)
th12 = theta1 + theta2
c12 = nl.cos(th12)
s12 = nl.sin(th12)

# Forward kinematics using nonlinear expressions
m.addConstr(x  == L1 * c1  + L2 * c12, name="x_def")
m.addConstr(y  == L1 * s1  + L2 * s12, name="y_def")
m.addConstr(xm == 0.5 * L1 * c1,       name="xm_def")
m.addConstr(ym == 0.5 * L1 * s1,       name="ym_def")

# Obstacle avoidance: keep mid-link outside circle
m.addQConstr((xm - xo)**2 + (ym - yo)**2 >= r**2, name="mid_outside")

# Objective: reach target
obj = (x - x_star)**2 + (y - y_star)**2
m.setObjective(obj, GRB.MINIMIZE)

m.optimize()

sol = None
if m.Status == GRB.OPTIMAL:
    sol = {
        "theta1": theta1.X, "theta2": theta2.X,
        "x": x.X, "y": y.X, "xm": xm.X, "ym": ym.X,
        "obj": m.ObjVal,
    }
    print("Optimal objective:", m.ObjVal)
    print(sol)
else:
    print("Optimization status:", m.Status)


import matplotlib.pyplot as plt

def draw_arm(ax, L1, L2, th1, th2, xo, yo, r, x_star, y_star, title):
    x1 = L1*math.cos(th1); y1 = L1*math.sin(th1)
    x2 = x1 + L2*math.cos(th1 + th2); y2 = y1 + L2*math.sin(th1 + th2)

    ax.plot([0, x1], [0, y1], linewidth=3)
    ax.plot([x1, x2], [y1, y2], linewidth=3)
    ax.scatter([0, x1, x2], [0, y1, y2], s=40)

    # obstacle
    t = [i*2*math.pi/300 for i in range(301)]
    cx = [xo + r*math.cos(tt) for tt in t]
    cy = [yo + r*math.sin(tt) for tt in t]
    ax.plot(cx, cy, linewidth=2)

    # target
    ax.scatter([x_star], [y_star], marker='x', s=80)

    ax.set_aspect('equal', adjustable='box')
    ax.set_xlim(-0.5, L1+L2+0.2)
    ax.set_ylim(-0.5, L1+L2+0.2)
    ax.grid(True, linestyle=':')
    ax.set_title(title)

if sol is not None:
    fig, ax = plt.subplots(figsize=(6,6))
    draw_arm(ax, L1, L2, sol['theta1'], sol['theta2'], xo, yo, r, x_star, y_star,
             title=f"Robot Arm (nlfunc)\nobj={sol['obj']:.4g}")
    # Save as PNG instead of showing
    plt.savefig("images/robot-arm.png", dpi=100, bbox_inches="tight")
    plt.close(fig)
else:
    print("No solution available to plot yet.")