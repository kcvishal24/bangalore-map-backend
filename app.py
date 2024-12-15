import osmnx as ox
import networkx as nx
from flask import Flask, request, jsonify
from flask_cors import CORS  # Importing CORS

app = Flask(__name__)

# Enable CORS for all routes
CORS(app)

# Load Bengaluru graph data once
graph = ox.graph_from_place('Bengaluru, India', network_type='drive')

@app.route('/get_shortest_path', methods=['POST'])
def get_shortest_path():
    data = request.json
    origin = tuple(map(float, data['from'].split(',')))  # Parse origin (lat,lng)
    destination = tuple(map(float, data['to'].split(',')))  # Parse destination (lat,lng)

    # Find nearest network nodes to origin and destination
    orig_node = ox.distance.nearest_nodes(graph, origin[1], origin[0])  # Lat/Lng reversed
    dest_node = ox.distance.nearest_nodes(graph, destination[1], destination[0])

    # Compute the shortest path
    shortest_path = nx.shortest_path(graph, orig_node, dest_node, weight='length')

    # Extract the lat/lng for the nodes in the shortest path
    path_coords = [(graph.nodes[node]['y'], graph.nodes[node]['x']) for node in shortest_path]

    # Calculate total distance
    total_distance = sum(
        nx.shortest_path_length(graph, u, v, weight='length') for u, v in zip(shortest_path[:-1], shortest_path[1:])
    )

    # Convert distance to km if it's >= 1 km, otherwise in meters
    if total_distance >= 1:
        total_distance = round(total_distance / 1000, 2)  # Convert to kilometers and round
    else:
        total_distance = round(total_distance, 2)  # Keep in meters if < 1 km

    # Calculate estimated duration (in minutes)
    estimated_duration = total_distance / 18 * 60  # Assuming an average speed of 18 km/h

    # Convert estimated duration to hours and minutes if greater than 60 minutes
    if estimated_duration > 60:
        hours = int(estimated_duration // 60)
        minutes = int(estimated_duration % 60)
        estimated_duration = f"{hours} h {minutes} m"
    else:
        estimated_duration = f"{round(estimated_duration, 1)} m"

    # Return the response in the specified order
    response = {
        "estimated_duration": estimated_duration,
        "total_distance": f"{total_distance} km" if total_distance >= 1 else f"{total_distance} m",
        "path_coords": path_coords
    }

    return jsonify(response)

if __name__ == '__main__':
    # Use the PORT environment variable, or fallback to port 5000 for local testing
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
