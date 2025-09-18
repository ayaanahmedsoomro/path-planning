from flask import Flask, request, jsonify
from flask_cors import CORS
from astar_modified import AStarPlanner
from dp_planner import DynamicProgrammingPlanner
import numpy as np
import os
import shutil

app = Flask(__name__)
CORS(app) # This will allow requests from your Flutter web app

def latlng_to_meters(lat, lon, ref_lat, ref_lon):
    """
    Approximate conversion from LatLng to meters.
    This is a simplified projection and works well for small areas.
    """
    m_per_deg_lat = 111132.954 - 559.822 * np.cos(2 * np.radians(ref_lat)) + 1.175 * np.cos(4 * np.radians(ref_lat))
    m_per_deg_lon = 111319.488 * np.cos(np.radians(ref_lat))
    
    x = (lon - ref_lon) * m_per_deg_lon
    y = (lat - ref_lat) * m_per_deg_lat
    return x, y

def meters_to_latlng(x, y, ref_lat, ref_lon):
    """
    Approximate conversion from meters to LatLng.
    """
    m_per_deg_lat = 111132.954 - 559.822 * np.cos(2 * np.radians(ref_lat)) + 1.175 * np.cos(4 * np.radians(ref_lat))
    m_per_deg_lon = 111319.488 * np.cos(np.radians(ref_lat))
    
    lon = x / m_per_deg_lon + ref_lon
    lat = y / m_per_deg_lat + ref_lat
    return lat, lon

def process_request_data(data):
    """Helper function to process incoming JSON data and convert to meters."""
    ref_lat = data['boundary']['points'][0]['latitude']
    ref_lon = data['boundary']['points'][0]['longitude']
    
    start_x, start_y = latlng_to_meters(data['start']['latitude'], data['start']['longitude'], ref_lat, ref_lon)
    goal_x, goal_y = latlng_to_meters(data['goal']['latitude'], data['goal']['longitude'], ref_lat, ref_lon)
    
    boundary_points_m = [latlng_to_meters(p['latitude'], p['longitude'], ref_lat, ref_lon) for p in data['boundary']['points']]
    
    min_x = min(p[0] for p in boundary_points_m)
    max_x = max(p[0] for p in boundary_points_m)
    min_y = min(p[1] for p in boundary_points_m)
    max_y = max(p[1] for p in boundary_points_m)
    
    boundary_m = {'bottom_left': (min_x, min_y), 'top_right': (max_x, max_y)}
    
    obstacles_m = []
    for obs in data['obstacles']:
        if obs['type'] == 'rectangle':
            points_m = [latlng_to_meters(p['latitude'], p['longitude'], ref_lat, ref_lon) for p in obs['points']]
            obstacles_m.append({'type': 'rectangle', 'points': points_m})
        elif obs['type'] == 'circle':
            center_x, center_y = latlng_to_meters(obs['center']['latitude'], obs['center']['longitude'], ref_lat, ref_lon)
            obstacles_m.append({'type': 'circle', 'center': (center_x, center_y), 'radius': obs['radius']})
            
    return (start_x, start_y), (goal_x, goal_y), obstacles_m, boundary_m, ref_lat, ref_lon

@app.route('/plan-path', methods=['POST'])
def plan_path():
    data = request.json
    start, goal, obstacles, boundary, ref_lat, ref_lon = process_request_data(data)

    # Initialize and run the A* planner
    planner = AStarPlanner(
        start=start,
        goal=goal,
        obstacles=obstacles,
        boundary=boundary
    )
    
    path, pruned_path = planner.planning()

    if not path:
        return jsonify({"error": "No path found"}), 404

    # Convert the resulting paths back to LatLng
    path_latlng = [{'latitude': lat, 'longitude': lon} for lat, lon in [meters_to_latlng(p[0], p[1], ref_lat, ref_lon) for p in path]]
    pruned_path_latlng = [{'latitude': lat, 'longitude': lon} for lat, lon in [meters_to_latlng(p[0], p[1], ref_lat, ref_lon) for p in pruned_path]]

    return jsonify({
        'path': path_latlng,
        'pruned_path': pruned_path_latlng
    })

@app.route('/plan-path-dp', methods=['POST'])
def plan_path_dp():
    data = request.json
    start, goal, obstacles, boundary, ref_lat, ref_lon = process_request_data(data)

    # Initialize and run the Dynamic Programming planner
    try:
        planner = DynamicProgrammingPlanner(
            start=start,
            goal=goal,
            obstacles=obstacles,
            boundary=boundary
        )
        path, pruned_path = planner.planning()
    except Exception as e:
        print(f"Error during DP planning: {e}")
        return jsonify({"error": "An error occurred during dynamic programming path planning."}), 500
    # finally:
    #     # Clean up the temporary decomposition directory
    #     if os.path.exists('decomposition_temp'):
    #         shutil.rmtree('decomposition_temp')

    if not path:
        return jsonify({"error": "No path found"}), 404

    # Convert the resulting paths back to LatLng
    path_latlng = [{'latitude': lat, 'longitude': lon} for lat, lon in [meters_to_latlng(p[0], p[1], ref_lat, ref_lon) for p in path]]
    pruned_path_latlng = [{'latitude': lat, 'longitude': lon} for lat, lon in [meters_to_latlng(p[0], p[1], ref_lat, ref_lon) for p in pruned_path]]

    return jsonify({
        'path': path_latlng,
        'pruned_path': pruned_path_latlng
    })

if __name__ == '__main__':
    app.run(debug=True)
