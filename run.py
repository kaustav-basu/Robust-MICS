from itertools import combinations
import networkx as nx
import configparser
from dcs import DCS
from pulp import *
import random
import time
import statistics

config = configparser.ConfigParser()
config.read("graph_config.ini")
#seed = int(config["GRAPH"]["SEED"])
#random.seed(seed)
att_opt = dict()
att_iter = dict()


def gen_graph(edge_file):
    G = nx.Graph()
    G = nx.read_edgelist(edge_file, nodetype=int)
    return G


def read_node_weights(graph):
    f = open(config["GRAPH_{}".format(graph)]["NODE_WEIGHTS_FILE"])
    node_weights = dict()
    for line in f:
        x = line.replace("\n", "").split(" ")
        node_weights[int(x[0])] = int(x[1])
    return node_weights


def generating_node_weights(graph, t_nodes, attacks_optimal, attacks_iterative):
    node_weights = dict()
    #max_value_t_nodes = max(t_nodes)
    for i in range(1, len(t_nodes) + 1):
        node_weights[i] = random.randint(1, 10)

    s = ""
    for k, v in node_weights.items():
        s += str(k) + " " + str(v) + "\n"
    f = open(config["GRAPH_{}".format(graph)]["NODE_WEIGHTS_FILE"], "w+")
    f.write(s)
    f.close()
    
    common_list = list(attacks_optimal.intersection(attacks_iterative))
    
    for common in common_list:
        val = random.randint(1, 10)
        att_opt[common] = val
        att_iter[common] = val
    
    for att in list(attacks_optimal.difference(attacks_iterative)):
        att_opt[att] = random.randint(1, 10)
    
    for att in list(attacks_iterative.difference(attacks_optimal)):
        att_iter[att] = random.randint(1, 10)


def get_color_codes(solution, attack, t_nodes, G):
    color = ["0" for i in range(len(t_nodes))]
    for i in solution:
        if not i == attack:
            neighbor = list(G.neighbors(i))
            for node in neighbor:
                color[node - 1] = color[node - 1] + "+" + str(i)
    return color


def check_uniqueness(graph, color):
    node_weights = read_node_weights(graph)
    total_sum = sum(node_weights.values())

    r_D = 0
    unique = []
    # If all nodes have unique non zero color
    if len(color) == len(set(color)) and "0" not in color:
        r_D = total_sum

    # Otherwise
    else:
        counter = collections.Counter(color)
        for k, v in counter.items():
            if v == 1 and k != "0":
                unique.append(k)
        for i in unique:
            ind = color.index(i)
            r_D += node_weights[ind + 1]

    return total_sum, r_D


def generate_game_matrix_optimal(seed, graph, def_actions, attacks, t_nodes, G, write_file_opt):
    game_matrix = dict()

    index = 1
    for a_D in def_actions:
        for a_A in attacks:
            color_codes = get_color_codes(a_D, a_A, t_nodes, G)
            total_sum, r_D = check_uniqueness(graph, color_codes)
            game_matrix["{}_{}".format(index, a_A)] = (r_D, total_sum - r_D)
        index += 1

    for a_A in attacks:
        r_A = att_opt[a_A]
        for key in game_matrix.keys():
            if str(a_A) in key:
                val = game_matrix[key]
                game_matrix[key] = (val[0], val[1] - r_A)

    s = ""
    s += str(len(def_actions)) + "\n"
    s += str(1) + "\n"
    s += str(1) + "\n"
    s += str(len(attacks)) + "\n"

    attackString = [str(a) for a in attacks]
    s += "|".join(attackString) + "\n"

    count = 0
    for k, v in game_matrix.items():
        s += "{},{} ".format(v[0], v[1])
        count += 1
        if count % len(attacks) == 0:
            s += "\n"

    with open("GameMatrix/" + str(seed) + "_" + write_file_opt, "w+") as f:
        f.write(s)

    #return game_matrix

    
def generate_game_matrix_iterative(seed, graph, def_actions, attacks, t_nodes, G, write_file_it):
    game_matrix = dict()

    index = 1
    for a_D in def_actions:
        for a_A in attacks:
            color_codes = get_color_codes(a_D, a_A, t_nodes, G)
            total_sum, r_D = check_uniqueness(graph, color_codes)
            game_matrix["{}_{}".format(index, a_A)] = (r_D, total_sum - r_D)
        index += 1

    for a_A in attacks:
        r_A = att_iter[a_A]
        for key in game_matrix.keys():
            if str(a_A) in key:
                val = game_matrix[key]
                game_matrix[key] = (val[0], val[1] - r_A)

    s = ""
    s += str(len(def_actions)) + "\n"
    s += str(1) + "\n"
    s += str(1) + "\n"
    s += str(len(attacks)) + "\n"

    attackString = [str(a) for a in attacks]
    s += "|".join(attackString) + "\n"

    count = 0
    for k, v in game_matrix.items():
        s += "{},{} ".format(v[0], v[1])
        count += 1
        if count % len(attacks) == 0:
            s += "\n"

    with open("GameMatrix/" + str(seed) + "_" + write_file_it, "w+") as f:
        f.write(s)

    return game_matrix


def model(graph, seed):
    num_nodes = int(config["GRAPH_{}".format(graph)]["NUM_NODES"])
    num_transformers = int(config["GRAPH_{}".format(graph)]["NUM_TRANSFORMER_NODES"])
    edge_file = config["GRAPH_{}".format(graph)]["EDGE_FILE"]
    write_file_opt = config["GRAPH_{}".format(graph)]["WRITE_FILE_OPT"]
    write_file_it = config["GRAPH_{}".format(graph)]["WRITE_FILE_IT"]

    G = gen_graph(edge_file)

    dcs = DCS(num_nodes, num_transformers, G)

    solutions = []
    start = time.time()
    i = 1
    while i < num_nodes - num_transformers:
        try:
            new_solutions = list(dcs.get_k_di_mdcs(K=i, verbose=False))
        except TypeError:
            new_solutions = None

        # The ILP is infeasible and thus no solutions were returned.
        if new_solutions is None:
            break

        # The ILP was feasible but did not return a Minimum DCS.
        if solutions != [] and len(solutions[0]) < len(new_solutions[0]):
            break

        solutions = new_solutions
        i += 1

    one_shot_end = time.time()
    solutions_iterative = dcs.get_k_di_mdcs_iterative(verbose=False)
    iterative_end = time.time()

    #print(one_shot_end - start, iterative_end - one_shot_end)
    #print([len(i) for i in solutions], [len(i) for i in solutions_iterative])

    #print(solutions)
    #print(solutions_iterative)
    # All possible nodes where sensors can be deployed can be attacked.
    attacks_optimal = set()
    for solution in solutions:
        for node in solution:
            attacks_optimal.add(node)
    
    attacks_iterative = set()
    for solution in solutions_iterative:
        for node in solution:
            attacks_iterative.add(node)

    #print("Number of Defender's Optimal Strategies: {}".format(len(solutions)))
    #print("Number of Defender's Iterative Strategies: {}".format(len(solutions_iterative)))
    #print("Number of Attacker's Optimal Strategies: {}".format(len(attacks_optimal)))
    #print("Number of Attacker's Iterative Strategies: {}".format(len(attacks_iterative)))
    
    generating_node_weights(graph, dcs.t_nodes, attacks_optimal, attacks_iterative)
    generate_game_matrix_optimal(seed, graph, solutions, list(attacks_optimal), dcs.t_nodes, G, write_file_opt)
    generate_game_matrix_iterative(seed, graph, solutions_iterative, list(attacks_iterative), dcs.t_nodes, G, write_file_it)
    return one_shot_end - start, iterative_end - one_shot_end

    
def main():
    num_graphs = int(sys.argv[1])
    for graph in range(1, num_graphs + 1):
        seeds = [42 * i for i in range(1, 11)]
        total_time_optimal = []
        total_time_iterative = []
        for seed in seeds:
            print("Seed = {}".format(seed))
            random.seed(seed)
            opt_time, iter_time = model(graph, seed)
            total_time_optimal.append(opt_time)
            total_time_iterative.append(iter_time)

        print("Optimal Total Run Time = {}s".format(statistics.mean(total_time_optimal)))
        print("Iterative Total Run Time = {}s".format(statistics.mean(total_time_iterative)))
        print("Optimal Time Standard Deviation = {}s".format(statistics.pstdev(total_time_optimal)))
        print("Iterative Time Standard Deviation = {}s".format(statistics.pstdev(total_time_iterative)))
        results = ""
        results += str(statistics.mean(total_time_optimal)) + ", " + str(statistics.mean(total_time_iterative)) + "\n"
        results += str(statistics.pstdev(total_time_optimal)) + ", " + str(statistics.pstdev(total_time_iterative)) + "\n"

        with open(config["GRAPH_{}".format(graph)]["WRITE_RESULTS"], "w+") as f:
            f.write(results)


if __name__ == "__main__":
    main()
