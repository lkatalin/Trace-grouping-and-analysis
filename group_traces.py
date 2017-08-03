import re
import numpy as np
from make_dag import *
from decimal import *

# groups of traces based on structure
categories = {}

def depth_first_traversal(trace):
    """
    the DFT traverses DAG dict starting with 
    root node; returns a list indicating all
    nodes seen in order. no duplicates are
    kept in case of sync and full paths are 
    not kept.
    """
    from timer import Timer
    nodes = []
    stack = [trace.dag]
    while stack:
	with Timer() as t:
	    cur_node = stack[0]
	    stack = stack[1:]
	    if cur_node.id not in nodes: #do not duplicate in case of sync
		nodes.append(cur_node.id)
	    for child in cur_node.get_rev_children():
		stack.insert(0, child)
	    #print "=> time of start: %s" % t.start
    return nodes 

def hashval(trace):
    """
    hashval takes the list generated by DFT and 
    creates a meaningful string for the hash value
    of each trace (stored in trace object).
    """
    hashval = "".join(re.findall(r'(\d)\.1', "".join(depth_first_traversal(trace))))
    #hashval = "".join(re.findall(r'.(\d+)', "".join(depth_first_traversal(trace))))
    return hashval

def group_traces(trace):
    """
    traces with the same hash value (determined by
    hashval function) are in the same group. keys are
    hashvalues, values are lists of trace ids in that
    group.
    """
    maybe_key = categories.get(trace.hashval)
    if maybe_key is not None:
        categories[trace.hashval].append(trace.traceId)
    else:
        categories[trace.hashval] = [trace.traceId]

def trace_lookup(tid, tlist):
    for trace in tlist:
        if trace.traceId == tid:
            return trace
    return none

def process_groups(d, tlist):
    """
    calculates the average completion time of
    traces within a group, as well as variance 
    of each group.
    """
    group_info = {}

    for hashv, traceids in d.items():
        psum = 0
        lst = []
        numvals = len(traceids)
 
        # calculate average
        for tid in traceids:
            t = trace_lookup(tid, tlist)
            psum += float(t.response)
        avg = psum / numvals
        
        # calculate variance
        psum = 0
        for tid in traceids:
            t = trace_lookup(tid, tlist)
            curr = (float(t.response) - avg) ** 2            
            psum += curr
        if (numvals - 1) > 1:
            var = (1 / float(numvals - 1)) * psum
        else:
            var = 0

        group_info[hashv] = {'Average' : avg, 'Variance': var}
    return group_info

        


def edge_latencies(group, tlist):
    """
    assumes all traces in group have exact same structure
    ...
    possibly, we could group the edges by label instead of tid -> tid,
    which would give us more data per edge
    """
    traces = categories[group]
    edge_latencies = {}
    edge_averages = {}
    edge_variance = {}
    for traceid in traces:
        t = trace_lookup(traceid, tlist)
        for full_edge in t.fullEdges:
            #edge = re.search(r'(\d+.* -> \d+.*) \[', full_edge).group(1)
            #time = re.search(r'label="(.*)"', full_edge).group(1)
            edge = re.search(r'\d+.\d+ -> \d+.\d+', full_edge).group(0)
            time = re.search(r'(\d+.\d+) us', full_edge).group(1)
            if edge in edge_latencies:
                edge_latencies[edge].append(time)
            else: 
                edge_latencies[edge] = [time]

    # calculate averages
    for key, values in edge_latencies.items():
        psum = 0
        numvals = len(values)
        for value in values:
            psum += float(value)
        edge_averages[key] = psum / numvals

    # calculate variance
    for key, values in edge_latencies.items():
	if numvals < 2:
	    edge_variance[key] = 0
	else:
	    psum = 0
	    for value in values:
		avg = edge_averages[key]
		curr = (float(value) - avg) ** 2
		psum += curr
            edge_variance[key] = (1 / float(numvals - 1)) * psum

    #print "edges in group: "
    #print edge_latencies

    return (edge_latencies, edge_averages, edge_variance)

#    print "edge averages: "
#    print edge_averages

#    print "edge variances: "
#    print edge_variance


def cov_matrix(e_lat_dict, tlist):
    """
    returns covariance matrix for each pair of edges within a group.
    """
    if len(tlist) == 1:
        print "\ntoo few data points to create covariance matrix \n"
    else:
        lat_array = np.array([e_lat_dict[k] for k in e_lat_dict]).astype(np.float)
        print "\n array of latencies in group per edge: \n" 
        print  lat_array
	matrix = np.cov(lat_array)
        print "\n covariance matrix for group: \n"
	print matrix
	print "\n"
        return matrix
