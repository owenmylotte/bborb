import matplotlib.pyplot as plt  # for plotting
import pandas as pd
import numpy as np
from nusa import *


def test1():
    # These units make me sad but they were the defaults in the examples.
    # All the material parameters can be fixed later.
    # Input data
    E = 30e6  # psi
    A = 2.0  # in^2
    P = 10e3  # lbf

    # Model
    trussModel = TrussModel("Truss Model")

    # I would rather put in a yaml parser to define the elements and point locations.
    # That way we can clean this up.
    # Nodes
    n1 = Node((0, 0.05))  # Main pin connection
    n2 = Node((-1, 0))  # First truss end point, etc.
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
        trussModel.add_node(nd)
    for el in (b1, b2, b3, b4, b5, t1, t2, t3, t4):
        trussModel.add_element(el)

    # How we define the load depends on how we want to try modelling the snow
    # Getting the tarp sag accurate would require discretizing the tarp into a cloth sim
    # and I don't know if I'm up for that right now unless someone is feeling the heat.
    trussModel.add_force(n3, (0, -10))
    trussModel.add_force(n4, (0, -10))
    trussModel.add_force(n5, (0, -10))

    # Supports where it touches the ground. There are no horizontal forces (unless we want wind shear)
    # If we wanted to be more accurate, we could horizontally fix it at out anchor point.
    trussModel.add_constraint(n1, ux=0, uy=0)  # fixed
    trussModel.add_constraint(n2, uy=0)  # fixed
    trussModel.add_constraint(n6, uy=0)  # fixed

    plt.title("Deformed Truss Model for Car Shelter", fontsize=13)
    trussModel.plot_model()

    trussModel.solve()  # Solve model

    print(t1.f)  # Example of the force output from the beams

    trussModel.plot_deformed_shape()  # plot deformed shape
    plt.title("Deformed Truss Model for Car Shelter", fontsize=13)

    trussModel.show()

    return b1.f, b2.f, b3.f, b4.f, b5.f


def test2(forces=None):
    # Now create a model for the pin to analyze the forces on the pin

    # Input data
    E = 300
    I = 50.0
    P = 10e2
    L = 10

    pinModel = BeamModel("Pin Model")
    n1 = Node((0, 0))
    n2 = Node((1, 0))
    n3 = Node((2, 0))
    n4 = Node((3, 0))
    n5 = Node((4, 0))
    n6 = Node((5, 0))
    n7 = Node((6, 0))
    # forceNodes = [n2, n3, n4, n5, n6]
    # Elements
    e1 = Beam((n1, n2), E, I)
    e2 = Beam((n2, n3), E, I)
    e3 = Beam((n3, n4), E, I)
    e4 = Beam((n4, n5), E, I)
    e5 = Beam((n5, n6), E, I)
    e6 = Beam((n6, n7), E, I)
    # Add elements
    for nd in (n1, n2, n3, n4, n5, n6, n7): pinModel.add_node(nd)
    for el in (e1, e2, e3, e4, e5, e6): pinModel.add_element(el)

    # for i in range(len(forces)):
    #     pinModel.add_force(forceNodes[i], (0, forces[i]))  # Neglect horizontal force
    pinModel.add_force(n2, (forces[0],))
    pinModel.add_force(n3, (forces[1],))
    pinModel.add_force(n4, (forces[2],))
    pinModel.add_force(n5, (forces[3],))
    pinModel.add_force(n6, (forces[4],))

    # I'm not sure if this is how we want to define the forces on the bracket
    pinModel.add_constraint(n1, ux=0, uy=0)  # fixed
    pinModel.add_constraint(n7, uy=0)  # roller support

    pinModel.plot_model()
    plt.title("Pin Force Diagram", fontsize=13)

    pinModel.solve()  # Solve model
    print(n4.uy)  # Example output of the deflection along the pin

    pinModel.plot_disp(df=100)  # df = deformation factor
    plt.title("Pin Displacement Illustration", fontsize=13)
    pinModel.show()


if __name__ == '__main__':
    plt.rcParams["font.family"] = "Noto Serif CJK JP"

    f1, f2, f3, f4, f5 = test1()  # Run test one and give the outputs to the pin calculation
    test2([f1, f2, f3, f4, f5])  # Need to add geometric information about force direction
    # Preferably the geometry input would be automated through a yaml file for easy alteration
