import snap
import collections

# Read in the graph from a text file in the same directory
file_name = input("Input a directed graph from the SNAP database:\n")
graph = snap.LoadEdgeList(snap.PNGraph, file_name + ".txt", 0, 1)

node_map_SCC = {}  # Dictionary mapping each node to the super node that represents in the SCC graph
node_map_cmprss = {}  # Dictionary mapping each node to the super node that represents it in the compressed graph
sets_of_same_descendants = []  # List containing sets of nodes, where every node in that set has the same descendants
all_descendants = collections.OrderedDict()  # Dictionary that maps every node to a set of all its descendants
ancestors = collections.OrderedDict()  # Dictionary that maps every node to a set of all its ancestors
to_combine = []  # List containing sets of nodes, where every node in that set has the same ancestors and descendants
all_nodes = []   # List containing all nodes as Node data type rather than ints

Components = snap.TCnComV()
snap.GetSccs(graph, Components)

for CnCom in Components:

    # If the size of the connected component is greater than 1, create an empty set.
    # Add all nodes from CnCom into the set, and delete all edges between the nodes in CnCom.
    if CnCom.Len() > 1:
        nodes = set()
        MxScc = snap.GetMxScc(graph)
        for EI in MxScc.Edges():
            nodes.add(EI.GetSrcNId())
            nodes.add(EI.GetDstNId())
            graph.DelEdge(EI.GetSrcNId(), EI.GetDstNId())

        # Create a new node that will represent all nodes from CnCom and
        # map the new node to all nodes in CnCom
        num_nodes = graph.GetMxNId()
        graph.AddNode(num_nodes)

        # If an edge exists to or from a node in CnCom, connect that edge to the new representative node.
        for NI in graph.Nodes():
            if NI.GetId() in nodes:
                for Id_out in NI.GetOutEdges():
                    graph.AddEdge(num_nodes, Id_out)
                for Id_in in NI.GetInEdges():
                    graph.AddEdge(Id_in, num_nodes)

        # Delete all nodes in CnCom
        for NI in nodes:
            node_map_SCC[NI] = num_nodes
            graph.DelNode(NI)

# Delete all self loops and save graph as the SCC graph
snap.DelSelfEdges(graph)
graph.Defrag()
snap.SaveEdgeList(graph, file_name + "SCC.txt", "Save as tab-separated list of edges")

# Section of code responsible for computing sets of nodes that have the same descendants
# Create a bfs tree from every node and map each node to a set of all its descendants
for NI in graph.Nodes():
    BfsTree = snap.GetBfsTree(graph, NI.GetId(), True, False)
    nodes = set()
    for EI in BfsTree.Edges():
        nodes.add(EI.GetDstNId())
    all_descendants[NI.GetId()] = nodes

# Iterate over the list of all descendants to pair the nodes that have the same descendants
for k1, v1 in all_descendants.items():
    descendant_set = set()
    for k2, v2 in all_descendants.items():
        # Add nodes with the same descendants to a set and add that set to the final list
        if v1 == v2 and not k1 == k2:
            descendant_set.add(k1)
            descendant_set.add(k2)

    if not descendant_set == set():
        sets_of_same_descendants.append(descendant_set)
        # If the set we just added is a subset of another set, delete it from the final list
        if len(sets_of_same_descendants) > 1:
            for i in range(len(sets_of_same_descendants) - 2, -1, -1):
                if sets_of_same_descendants[len(sets_of_same_descendants) - 1].issubset(sets_of_same_descendants[i]):
                    sets_of_same_descendants.pop(len(sets_of_same_descendants) - 1)

# Section of code responsible for computing sets of nodes that have the same ancestors and descendants
# Create an inverted version of the SCC graph
graphT = snap.LoadEdgeList(snap.PNGraph, file_name + "SCC.txt", 1, 0)
# Create a bfs tree from every node and map each node to a set of all its ancestors
for NI in graphT.Nodes():
    BfsTree = snap.GetBfsTree(graphT, NI.GetId(), True, False)
    nodesT = set()
    for EI in BfsTree.Edges():
        nodesT.add(EI.GetDstNId())
    ancestors[NI.GetId()] = nodesT

# Iterate over every set in a list of sets, where every node in a set has the same descendants
for element in sets_of_same_descendants:
    marked = set()
    descendant_pairs = list(element)

    # Iterate over all nodes in the set, and group all the nodes that have the same set of ancestors and descendants
    for i in range(0, len(descendant_pairs), 1):
        ancestor_pairs = set()
        for j in range(i + 1, len(descendant_pairs), 1):
            if ancestors.get(descendant_pairs[i]) == ancestors.get(descendant_pairs[j]):
                ancestor_pairs.add(descendant_pairs[i])
                ancestor_pairs.add(descendant_pairs[j])

        # If a group of nodes has the same set of ancestors and descendants, and has not been marked, add it to a set
        if not ancestor_pairs == set() and not ancestor_pairs.issubset(marked):
            to_combine.append(ancestor_pairs)
            for pair_elt in ancestor_pairs:
                marked.add(pair_elt)

# Section of code responsible for merging nodes in the SCC graph into SuperNodes,
# and redirects corresponding edges to and from each SuperNode.
# Iterate over the list of sets in which each set contains nodes that have the same ancestors and descendants
for elt in to_combine:
    out_edges = set()
    in_edges = set()
    # Create two sets, each set contains all the vertices from the graph
    for nodes in graph.Nodes():
        out_edges.add(nodes.GetId())
        in_edges.add(nodes.GetId())
    # For each node in the set that contains only nodes with the same ancestors and descendants
    for NI in graph.Nodes():
        if NI.GetId() in elt:
            possible_out_edges = set()
            possible_in_edges = set()
            # For each outgoing edge, add all destination nodes to a set.
            # Remove all nodes not present in current set of outgoing edge destination nodes.
            for Id_out in NI.GetOutEdges():
                possible_out_edges.add(Id_out)
            out_edges.intersection_update(possible_out_edges)
            # For each incoming edge, add all source nodes to a set.
            # Remove all nodes not present in current set of incoming edge source nodes.
            for Id_in in NI.GetInEdges():
                possible_in_edges.add(Id_in)
            in_edges.intersection_update(possible_in_edges)
    # Add a new node that will be the SuperNode
    num_nodes = graph.GetMxNId()
    graph.AddNode(num_nodes)
    # Add edges from all nodes in the set of incoming edge source nodes to the new SuperNode
    for in_edge in in_edges:
        graph.AddEdge(in_edge, num_nodes)
    # Add edges from all nodes in the set of outgoing edge destination nodes to the new SuperNode
    for out_edge in out_edges:
        graph.AddEdge(num_nodes, out_edge)
    # Delete all nodes in the set of nodes with the same ancestors and descendants
    for node in elt:
        node_map_cmprss[node] = num_nodes
        graph.DelNode(node)

# Save the new compressed graph to a text file, and add each node mapped to its representative SuperNode
graph.Defrag()
snap.SaveEdgeList(graph, file_name + "Compressed.txt", "tab-separated list of edges, followed by a map of")
f = open(file_name + "Compressed.txt", "a")
f.write("\nlist of Nodes paired with the SuperNode that represents that Node in the compressed graph\n")
for elt in node_map_SCC.items():
    f.write(str(elt) + "\n")
for elt in node_map_cmprss.items():
    f.write(str(elt) + "\n")
f.close()


# Section of code responsible for computing reachability
# Use the original graph to double check whether our compressed graph computes reachability correctly
# graphConfirmation = snap.LoadEdgeList(snap.PNGraph, file_name + ".txt", 0, 1)
# number_nodes = graphConfirmation.GetMxNId() - 1

# while True:
#     valid = True  # Boolean variable to ensure that a valid input is given
#     src = int(input("Enter a source node to test for connectivity:\n"))
#     og_src = src
#     dst = int(input("Enter a destination node to test for connectivity:\n"))
#     og_dst = dst
#
#     # If the source is the same as the destination node, or if a SuperNode is entered, input is invalid
#     if src == dst or src > number_nodes or dst > number_nodes:
#         print("Please enter two valid nodes \n")
#         valid = False
#
#     # If the source node is not in the graph, find its SuperNode representation from the SCC or compression dictionary
#     if valid:
#         if graph.IsNode(src):
#             pass
#         elif src in node_map_cmprss.keys():
#             src = node_map_cmprss.get(src)
#         elif src in node_map_SCC.keys():
#             if node_map_SCC.get(src) not in node_map_cmprss.keys():
#                 src = node_map_SCC.get(src)
#             else:
#                 src = node_map_cmprss.get(node_map_SCC.get(src))
#         else:
#             print("Invalid source node entered, try again \n")
#             valid = False
#
#     # If the destination node is not in the graph, find its SuperNode representation from the SCC or compression dict
#     if valid:
#         if graph.IsNode(dst):
#             pass
#         elif dst in node_map_cmprss.keys():
#             dst = node_map_cmprss.get(dst)
#         elif dst in node_map_SCC.keys():
#             if node_map_SCC.get(dst) not in node_map_cmprss.keys():
#                 dst = node_map_SCC.get(dst)
#             else:
#                 dst = node_map_cmprss.get(node_map_SCC.get(dst))
#         else:
#             print("Invalid destination node entered, try again \n")
#             valid = False
#
#     # Find if there exists a path from src node to dst node.
#     if valid:
#         path = snap.GetShortPath(graph, src, dst, True)
#         if path == -1:
#             print("No connection from node %d to node %d" % (og_src, og_dst))
#         # If querying a SuperNode, find where the original nodes come from
#         elif path == 0:
#             if og_src in node_map_SCC and og_dst in node_map_SCC and node_map_SCC.get(og_src) == node_map_SCC.get(
#                     og_dst):
#                 print("Node %d is connected to node %d and both are represented by node %d" % (og_src, og_dst, src))
#             else:
#                 print("No connection from node %d to node %d" % (og_src, og_dst))
#         else:
#             print("Node %d is connected to node %d, represented by nodes (%d, %d)" % (og_src, og_dst, src, dst))
#
#     # Query the original graph to check the query from the compressed graph
#     if graphConfirmation.IsNode(og_src) and graphConfirmation.IsNode(og_dst) and valid:
#         Length = snap.GetShortPath(graphConfirmation, og_src, og_dst, True)
#         if Length > 0:
#             print("Node %d is connected to node %d in the original graph" % (og_src, og_dst) + "\n")
#         else:
#             print("No connection from node %d to node %d in the original graph" % (og_src, og_dst) + "\n")
