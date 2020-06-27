from itertools import combinations
import networkx as nx
import configparser
from dcs import DCS
from nash import Nash
from pulp import *
import random
import time

config = configparser.ConfigParser()
config.read("graph_config.ini")
seed = int(config["GRAPH"]["SEED"])
random.seed(seed)


def gen_graph(edge_file):
    G = nx.Graph()
    G = nx.read_edgelist(edge_file, nodetype=int)
    return G


def read_node_weights():
    f = open(config["GRAPH"]["NODE_WEIGHTS_FILE"])
    node_weights = dict()
    for line in f:
        x = line.replace("\n", "").split(" ")
        node_weights[int(x[0])] = int(x[1])
    return node_weights


def generating_node_weights(t_nodes):
    node_weights = dict()
    max_value_t_nodes = max(t_nodes)
    for i in range(1, len(t_nodes) + 1):
        node_weights[i] = random.randint(1, max_value_t_nodes + 10)

    s = ""
    for k, v in node_weights.items():
        s += str(k) + " " + str(v) + "\n"
    f = open(config["GRAPH"]["NODE_WEIGHTS_FILE"], "w+")
    f.write(s)
    f.close()


def get_color_codes(solution, attack, t_nodes, G):
    color = ["0" for i in range(len(t_nodes))]
    for i in solution:
        if not i == attack:
            neighbor = list(G.neighbors(i))
            for node in neighbor:
                color[node - 1] = color[node - 1] + "+" + str(i)
    return color


def check_uniqueness(color):
    node_weights = read_node_weights()
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


def generate_game_matrix(def_actions, attacks, t_nodes, graph, write_file):
    game_matrix = dict()

    index = 1
    for a_D in def_actions:
        for a_A in attacks:
            color_codes = get_color_codes(a_D, a_A, t_nodes, graph)
            total_sum, r_D = check_uniqueness(color_codes)
            game_matrix["{}_{}".format(index, a_A)] = (r_D, total_sum - r_D)
        index += 1

    for a_A in attacks:
        r_A = random.randint(0, total_sum)
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

    with open(write_file, "w") as f:
        f.write(s)

    return game_matrix


def model():
    num_nodes = int(config["GRAPH"]["NUM_NODES"])
    num_transformers = int(config["GRAPH"]["NUM_TRANSFORMER_NODES"])
    edge_file = config["GRAPH"]["EDGE_FILE"]
    write_file = config["GRAPH"]["WRITE_FILE"]

    G = gen_graph(edge_file)

    dcs = DCS(num_nodes, num_transformers, G)

    solutions = []

    start = time.time()
    i = 1
    while i < num_nodes - num_transformers:
        new_solutions = dcs.get_k_di_mdcs(K=i, verbose=False)
        if new_solutions is None:
            if i % 2 == 1:
                break
            else:
                i -= 3
        solutions = new_solutions
        i += 2
    one_shot_end = time.time()
    solutions_iterative = dcs.get_k_di_mdcs_iterative(verbose=False)
    iterative_end = time.time()

    print(one_shot_end - start, iterative_end - one_shot_end)
    print(len(solutions), len(solutions_iterative))
    print([len(i) for i in solutions], [len(i) for i in solutions_iterative])

    # All possible nodes where sensors can be deployed can be attacked.
    attacks = set()
    for solution in solutions:
        for node in solution:
            attacks.add(node)

    print("Number of Defender's Strategies: {}".format(len(solutions)))
    print("Number of Attacker's Strategies: {}".format(len(attacks)))
    generating_node_weights(dcs.t_nodes)
    generate_game_matrix(solutions, list(attacks), dcs.t_nodes, G, write_file)


if __name__ == "__main__":
    model()
