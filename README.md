# graph-compression
Algorithm for compressing directed graphs in a way that allows you to compute reachability through the compressed graph.


To run the algorithm, must first install the snap.py interface.
Instructions on how to install and use the snap.py interface are on the snap stanford website: 
http://snap.stanford.edu/snappy/index.html#pip

Run the algorithm by inputting the graph you want to compress via a command line argument.
The graph must be a text file that has all edges listed as a tab-separated list of edges,
where the first column is the source node and the last column is the destination node.
Graph must be directed.

For example, a graph with 4 nodes and 3 edges would appear in a text file as:
# Nodes: 4 Edges: 3
1   2
1   3
2   3
4   1
