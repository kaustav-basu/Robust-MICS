from itertools import combinations
from pulp import *


class DCS:
    def __init__(self, num_nodes, num_transformers, graph):
        self.nodes = [i + 1 for i in range(num_transformers, num_nodes)]
        self.t_nodes = [i + 1 for i in range(num_transformers)]
        self.all_nodes = self.nodes + self.t_nodes
        self.graph = graph

    def get_differentially_immune_solutions(self, verbose=True):
        print("Initializing Integer Linear Program ...")
        problem = LpProblem("IdentifyingCodes1", LpMinimize)

        # Adding binary node variables
        x = LpVariable.dict("x_%s", self.all_nodes, 0, 1, LpBinary)
        problem += sum(x[i] for i in self.nodes)

        print("Adding Coloring Constraints...")
        for i in self.t_nodes:
            val_color = 0
            neighbor = list(self.graph.neighbors(i))
            for j in neighbor:
                val_color += x[j]
            problem += val_color >= 1, "Coloring_Constraint_{}".format(i)

        print("Adding Uniqueness Constraints ...")
        for i in combinations(self.t_nodes, 2):
            val_unique = 0
            node1, node2 = list(i)
            set1 = set(self.graph.neighbors(node1))
            set2 = set(self.graph.neighbors(node2))
            unique = list(set1.symmetric_difference(set2))
            for k in unique:
                val_unique += x[k]
            problem += val_unique >= 1, "Uniqueness_Constraint_{}".format(i)

        print("Solving ...")
        solutions = []
        all_solutions_found = False
        while not all_solutions_found:
            # Add constraints to ensure MICS nodes found should not be used in the new solution.
            # This guarantees solutions with differential immunity = 1.
            # TODO: Consider relaxing for solutions with 0 < differential immunity < 1
            for solution in solutions:
                for i in solution:
                    problem += x[i] == 0, ""

            new_solution = []
            problem.solve(GUROBI())
            if LpStatus[problem.status] == "Optimal":
                for v in problem.variables():
                    if v.varValue == 1:
                        # print(v.name, "=", v.varValue)
                        new_solution.append(int(v.name.split("_")[1]))
                solutions.append(new_solution)
            else:
                print("No More Optimal Solutions with Differential Immunity = 1.")
                all_solutions_found = True

        if verbose:
            print("Solutions: ", solutions)
            print("Number of Alternate Solutions:", len(solution))
            print("-------------------------------------------------------")
            print(
                "Amount of Resources Required for Unique Monitoring: {}".format(
                    value(problem.objective)
                )
            )
            print(
                "Total Number of Nodes to be Uniquely Monitored: {}".format(
                    len(self.t_nodes)
                )
            )
            print(
                "% Savings: {}".format(
                    float(
                        100
                        * (len(self.t_nodes) - int(value(problem.objective)))
                        / len(self.t_nodes)
                    )
                )
            )
            print("-------------------------------------------------------")

        return solutions
