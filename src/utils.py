from collections import deque, defaultdict

def topologically_sort_lesson_nodes(nodes, edges):
    """
    Sorts nodes in a lesson based on prerequisite relationships using Kahn's algorithm.
    
    Args:
        nodes (list): A list of node dictionaries.
        edges (list): A list of edge dictionaries.
        
    Returns:
        list: A list of node dictionaries in topologically sorted order.
    """
    if not nodes:
        return []

    in_degree = {node['id']: 0 for node in nodes}
    adj = defaultdict(list)
    
    for edge in edges:
        if edge.get('type') == 'PREREQUISITE_FOR':
            source_id = edge['source']
            target_id = edge['target']
            if source_id in in_degree and target_id in in_degree:
                adj[source_id].append(target_id)
                in_degree[target_id] += 1

    queue = deque([node_id for node_id, degree in in_degree.items() if degree == 0])
    sorted_order = []
    
    while queue:
        u = queue.popleft()
        sorted_order.append(u)
        
        for v in adj[u]:
            in_degree[v] -= 1
            if in_degree[v] == 0:
                queue.append(v)
    
    if len(sorted_order) != len(nodes):
        # Cycle detected or disconnected components not handled by simple Kahn's
        # Add remaining nodes that were part of a cycle to the end
        remaining_nodes = set(in_degree.keys()) - set(sorted_order)
        sorted_order.extend(list(remaining_nodes))

    # Create a map of node_id to node object
    node_map = {node['id']: node for node in nodes}
    
    # Return the full node objects in the sorted order
    return [node_map[node_id] for node_id in sorted_order]