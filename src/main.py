import matplotlib.pyplot as plt  # for plotting
import pandas as pd
import numpy as np
from nusa import *


# import nusa.mesh as nmsh


def test1():
    # Input data
    E = 30e6  # psi
    A = 2.0  # in^2
    P = 10e3  # lbf

    # Model
    m = TrussModel("Truss Model")

    # Nodes
    n1 = Node((0, 0))  # Main pin connection
    n2 = Node((-1, 0))  # First
    n3 = Node((-1 * np.cos(45 * np.pi / 180.), 1 * np.sin(45 * np.pi / 180.)))
    n4 = Node((0, 1))
    n5 = Node((1 * np.cos(45 * np.pi / 180.), 1 * np.sin(45 * np.pi / 180.)))
    n6 = Node((1, 0))

    # Elements
    b1 = Truss((n1, n2), E, A)
    b2 = Truss((n1, n3), E, A)
    b3 = Truss((n1, n4), E, A)
    b4 = Truss((n1, n5), E, A)
    b5 = Truss((n1, n6), E, A)
    t1 = Truss((n2, n3), E, A)
    t2 = Truss((n3, n4), E, A)
    t3 = Truss((n4, n5), E, A)
    t4 = Truss((n5, n6), E, A)

    # Add elements
    for nd in (n1, n2, n3, n4, n5, n6):
        m.add_node(nd)
    for el in (b1, b2, b3, b4, b5, t1, t2, t3, t4):
        m.add_element(el)

    m.add_force(n3, (0, -10))
    m.add_force(n4, (0, -10))
    m.add_force(n5, (0, -10))

    m.add_constraint(n1, ux=0, uy=0)  # fixed
    m.add_constraint(n2, uy=0)  # fixed
    m.add_constraint(n6, uy=0)  # fixed

    m.plot_model()

    m.solve()  # Solve model

    print(t1.f)

    m.plot_deformed_shape()  # plot deformed shape
    plt.title("Truss Model for Car Shelter")

    m.show()


if __name__ == '__main__':
    test1()
