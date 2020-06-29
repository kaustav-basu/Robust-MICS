from itertools import combinations
from gurobipy import *
from pulp import *
import math


class DCS:
    def __init__(self, num_nodes, num_transformers, graph):
        self.nodes = [i + 1 for i in range(num_transformers, num_nodes)]
        self.t_nodes = [i + 1 for i in range(num_transformers)]
        self.all_nodes = self.nodes + self.t_nodes
        self.graph = graph

    def get_k_di_mdcs(self, K, verbose=False):
        m = Model("MIQP")
        m.setParam("OutputFlag", 0)

        x = {}
        for i in self.all_nodes:
            for k in range(K):
                s = 'x_{}_{}'.format(i, k)
                x[s] = m.addVar(lb=0, ub=1, vtype=GRB.INTEGER, name=s)
        m.update()

        optimal_solution_size = m.addVar(
            lb=-GRB.INFINITY, ub=GRB.INFINITY, vtype=GRB.CONTINUOUS, name="opt_size"
        )
        m.update()

        for k in range(K):
            # Constraints to ensure that solution set sized for all graphs add up to the optimal solution size.
            solution_size = LinExpr()
            for i in self.nodes:
                s = 'x_{}_{}'.format(i, k)
                solution_size.add(x[s])
            m.addConstr(solution_size - optimal_solution_size == 0)

        for k in range(K):
            for i in self.t_nodes:
                # add has color constraints for node (i,k)
                has_color_constraint = LinExpr()
                for j in list(self.graph.neighbors(i)):
                    s = 'x_{}_{}'.format(j, k)
                    has_color_constraint.add(x[s])
                m.addConstr(has_color_constraint >= 1)

        for k in range(K):
            for n1, n2 in combinations(self.t_nodes, 2):
                # Add symmetric difference constraints for (n1, k) and (n2, k)
                has_unique_color = LinExpr()
                N_n1 = set(self.graph.neighbors(n1))
                N_n2 = set(self.graph.neighbors(n2))
                for node in N_n1.symmetric_difference(N_n2):
                    s = 'x_{}_{}'.format(node, k)
                    has_unique_color.add(x[s])
                m.addConstr(has_unique_color >= 1)

        for k1 in range(K):
            for k2 in range(k1 + 1, K):
                # Add constrains to ensure the solution for k1 and k2 have no common nodes
                diff_immune_solutions = QuadExpr()
                for i in self.nodes:
                    diff_immune_solutions.add(
                        (x['x_{}_{}'.format(i, k1)] - x['x_{}_{}'.format(i, k2)]) *
                        (x['x_{}_{}'.format(i, k1)] - x['x_{}_{}'.format(i, k2)])
                    )
                m.addConstr(diff_immune_solutions == 2 * optimal_solution_size)

        m.setObjective(optimal_solution_size, GRB.MINIMIZE)
        m.optimize()
        if m.status != 2:
            return None

        solution_dict = {}
        for v in m.getVars():
            if v.x == 1:
                #print("%s -> %g" % (v.varName, v.x))
                name, node, k = v.varName.split("_")
                try:
                    solution_dict[k].append(int(node))
                except KeyError:
                    solution_dict[k] = [int(node)]

        print("Obj -> %g" % m.objVal)
        return solution_dict.values()

    def get_k_di_mdcs_iterative(self, verbose=True):
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
        optimal_solution_size = math.inf
        all_opt_solutions_found = False
        while not all_opt_solutions_found:
            # Add constraints to ensure MICS nodes found should not be used in the new solution.
            # This guarantees solutions with differential immunity = 1.
            # TODO: Consider relaxing for solutions with 0 < differential immunity < 1
            for solution in solutions:
                for i in solution:
                    problem += x[i] == 0, ""

            new_solution = []
            problem.solve(GUROBI(msg=0))
            if LpStatus[problem.status] == "Optimal":
                for v in problem.variables():
                    if v.varValue == 1:
                        new_solution.append(int(v.name.split("_")[1]))
            else:
                all_opt_solutions_found = True
                continue

            # Break early if the solution set size becomes greater than the optimal value
            if len(new_solution) <= optimal_solution_size:
                optimal_solution_size = len(new_solution)
            else:
                break
            solutions.append(new_solution)

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
