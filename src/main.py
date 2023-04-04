import pathlib
import yaml
import matplotlib.pyplot as plt  # for plotting
import pandas as pd
import numpy as np
import argparse
from nusa import *


class Pin(yaml.YAMLObject):
    YAMLTag = u"!Pin"

    def __init__(self, name, elements, length, E, I):
        self.name = name
        self.elements = elements
        self.elasticModulus = E
        self.secondMoment = I
        self.length = length


class Force(yaml.YAMLObject):
    YAMLTag = u"!Force"

    def __init__(self, name, point, x, y):
        self.name = name
        self.point = point
        self.x = x
        self.y = y

    # # This can be used to write out optimized geometries. Save for later
    # def __repr__(self):
    #     return "%s(name=%r, point=%r, x=%r, y=%r)" % (self.__class__.__name__, self.name, self.point, self.x, self.y)


class Constraint(yaml.YAMLObject):
    YAMLTag = u"!Constraint"

    def __init__(self, name, point, x, y):
        self.name = name
        self.point = point
        self.x = bool(x)
        self.y = bool(y)


class Element(yaml.YAMLObject):
    YAMLTag = u"!Element"

    def __init__(self, name, start, end, E, A):
        self.name = name
        self.start = start
        self.end = end
        self.elasticModulus = E
        self.sectionArea = A
        self.truss = Truss((self.start.node, self.end.node), self.elasticModulus, self.sectionArea)


class Tarp(yaml.YAMLObject):
    YAMLTag = u"!Tarp"

    def __init__(self, name, start, end, E, A, nodecount, load):
        self.name = name
        self.start = start
        self.end = end
        self.elasticModulus = E
        self.sectionArea = A
        self.truss = np.zeros(nodecount + 1, Truss)  # Elements in the tarp
        self.nodes = np.zeros(nodecount, Node)  # Points in between the tarp ends
        for i in range(nodecount):  # Create all the nodes in between the input start and end
            self.nodes[i].x = self.start.x + (self.end.x - self.start.x) * (i + 1 / self.nodecount + 2)
            self.nodes[i].y = self.start.y + (self.end.y - self.start.y) * (i + 1 / self.nodecount + 2)

        self.truss[0] = Truss((self.start.node, self.end.node), self.elasticModulus, self.sectionArea)
        for i in range(1, nodecount - 1):
            self.truss[i] = Truss((self.start.node, self.end.node), self.elasticModulus, self.sectionArea)

            # Put the load on each of the nodes


class Point(yaml.YAMLObject):
    YAMLTag = u"!Point"

    def __init__(self, name, x, y):
        self.name = name
        self.x = x
        self.y = y
        self.node = Node((self.x, self.y))


def constraint_constructor(loader: yaml.SafeLoader, node: yaml.nodes.MappingNode) -> Constraint:
    return Constraint(**loader.construct_mapping(node))


def point_constructor(loader: yaml.SafeLoader, node: yaml.nodes.MappingNode) -> Point:
    return Point(**loader.construct_mapping(node))


def element_constructor(loader: yaml.SafeLoader, node: yaml.nodes.MappingNode) -> Element:
    return Element(**loader.construct_mapping(node))


def force_constructor(loader: yaml.SafeLoader, node: yaml.nodes.MappingNode) -> Force:
    return Force(**loader.construct_mapping(node))


def pin_constructor(loader: yaml.SafeLoader, node: yaml.nodes.MappingNode) -> Pin:
    return Pin(**loader.construct_mapping(node))


def get_loader():
    """Add constructors to PyYAML loader."""
    loader = yaml.SafeLoader
    loader.add_constructor("!Constraint", constraint_constructor)
    loader.add_constructor("!Point", point_constructor)
    loader.add_constructor("!Element", element_constructor)
    loader.add_constructor("!Force", force_constructor)
    loader.add_constructor("!Pin", pin_constructor)
    return loader


def trussSolve(data):
    # Model
    trussModel = TrussModel("Truss Model")

    # Add elements
    for nd in data['points']:
        trussModel.add_node(nd.node)
    for el in data['elements']:
        trussModel.add_element(el.truss)

    # How we define the load depends on how we want to try modelling the snow
    # Getting the tarp sag accurate would require discretizing the tarp into a cloth sim
    # and I don't know if I'm up for that right now unless someone is feeling the heat.
    for fc in data['forces']:
        trussModel.add_force(fc.point.node, (fc.x, fc.y))

    for tarp in data["tarps"]:
        for i in range(tarp.nodecount):
            trussModel.add_force(tarp.nodes[i], (0, tarp.load / tarp.nodecount))  # Apply portion of tarp load to nodes

    for cnst in data['constraints']:
        if ((cnst.x == True) and (cnst.y == True)):
            trussModel.add_constraint(cnst.point.node, ux=0, uy=0)  # fixed in both x and y
        elif (cnst.x == True):
            trussModel.add_constraint(cnst.point.node, ux=0)  # fixed in x
        elif (cnst.y == True):
            trussModel.add_constraint(cnst.point.node, uy=0)  # fixed in y
        else:
            raise ValueError("Null constraint enforces nothing.")

    trussModel.plot_model()
    plt.title("Truss Car Shelter Model", fontsize=13)

    trussModel.show()

    trussModel.solve()  # Solve model

    options = {"headers": "firstrow",
               "tablefmt": "rst",
               "numalign": "right"}

    r1 = 0.0127 * 0.5
    r2 = 0.0127
    length = 1
    for el in data['elements']:
        Ielem = np.pi * 0.5 * (r2 * r2 - r1 * r1)
        Fcrit = (np.pi * np.pi * el.truss.E * Ielem) / (length)
        print(el.name + ": " + str(el.truss.s) + " : Buckling Failure? : " + str(Fcrit < abs(el.truss.f)))

    trussModel.plot_deformed_shape()  # plot deformed shape
    plt.title("Truss Model Deformation", fontsize=13)

    trussModel.show()


def pinSolve(data):
    # Now create a model for the pin to analyze the forces on the pin

    pinModel = BeamModel("Pin Model")

    nodes = np.zeros((len(data['pin'].elements) + 2), dtype=Node)
    elements = np.zeros(len(nodes) - 1, dtype=Element)
    nodePositions = np.linspace(0, data['pin'].length, (len(data['pin'].elements) + 2),
                                dtype=float)  # Leave room for the end
    for i in range(1, len(nodes) - 1):
        nodes[i] = Node((nodePositions[i], 0))
    nodes[0] = Node((0, 0))
    nodes[len(nodes) - 1] = Node((data['pin'].length, 0))

    for i in range(len(nodePositions) - 1):
        elements[i] = Beam((nodes[i], nodes[i + 1]), data['pin'].elasticModulus, data['pin'].secondMoment)

    # Add elements
    for nd in range(len(nodes)):
        pinModel.add_node(nodes[nd])
    for el in range(len(elements)):
        pinModel.add_element(elements[el])

    for i in range(len(data['pin'].elements)):
        pinModel.add_force(nodes[i + 1], (data['pin'].elements[i].truss.f,))

    # I'm not sure if this is how we want to define the constraints on the bracket?
    pinModel.add_constraint(nodes[0], ux=0, uy=0)  # fixed
    pinModel.add_constraint(nodes[len(nodes) - 1], uy=0)  # roller support

    pinModel.plot_model()
    plt.title("Beam Pin Model", fontsize=13)

    pinModel.solve()  # Solve model

    pinModel.plot_disp(df=100)  # df = deformation factor
    pinModel.plot_shear_diagram()  # df = deformation factor
    pinModel.plot_moment_diagram()  # df = deformation factor
    plt.title("Beam Model Deformation", fontsize=13)
    pinModel.show()


if __name__ == '__main__':
    # Input argument parser used to point to a yaml file.
    parser = argparse.ArgumentParser(
        description='Structural analysis tool for portable car shelter. '
                    'See https://github.com/owenmylotte/bborb'
                    ' for details.  ')
    parser.add_argument('--input', dest='input_file', type=pathlib.Path, required=True,
                        help='The path to the yaml input file containing the design geometry.')
    args = parser.parse_args()

    data = yaml.load(open(args.input_file, "rb"), Loader=get_loader())  # Open the input file

    plt.rcParams["font.family"] = "Noto Serif CJK JP"  # Set the font for plotting.

    trussSolve(data)  # Runs the truss model of the strut and tarp system
    pinSolve(data)  # Solves the pin beam problem

    # TODO: Eventually we will want to solve for a factor of safety and run multiple benchmark cases.
    # TODO: This includes snow loading, wind shear, and other cases potentially.
    # TODO: Implementing an optimization / solve on the component parameters is also an option.
