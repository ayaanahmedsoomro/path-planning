# astar_modified.py

import math
import numpy as np
from find_intersect_line import *

class AStarPlanner:
    def __init__(self, start, goal, obstacles, boundary):
        self.start = start
        self.goal = goal
        self.obstacles = obstacles
        
        x_min, y_min = boundary['bottom_left']
        x_max, y_max = boundary['top_right']

        width = x_max - x_min
        height = y_max - y_min
        min_side = min(width, height) if min(width, height) > 0 else 100
        
        self.resolution = min_side * 0.02
        self.min_x = x_min
        self.min_y = y_min
        self.max_x = x_max
        self.max_y = y_max
        self.x_width = round((self.max_x - self.min_x) / self.resolution)
        self.y_width = round((self.max_y - self.min_y) / self.resolution)
        
        self.motion = self.get_motion_model()

    class Node:
        def __init__(self, x, y, cost, parent_index):
            self.x = x
            self.y = y
            self.cost = cost
            self.parent_index = parent_index

    def planning(self):
        start_node = self.Node(self.start[0], self.start[1], 0.0, -1)
        goal_node = self.Node(self.goal[0], self.goal[1], 0.0, -1)

        open_set, closed_set = dict(), dict()
        open_set[self.calc_grid_index(start_node)] = start_node

        while True:
            if len(open_set) == 0:
                print("Open set is empty..")
                break

            c_id = min(
                open_set,
                key=lambda o: open_set[o].cost + self.calc_heuristic(goal_node, open_set[o]),
            )
            current = open_set[c_id]

            dist_to_goal = self.calc_heuristic(goal_node, current)
            if dist_to_goal <= self.resolution:
                print("Goal is reached!")
                goal_node.parent_index = c_id
                goal_node.cost = current.cost
                # ================= FIX IS HERE =================
                # The final node must be added to the closed set for backtracking
                closed_set[c_id] = current
                # ===============================================
                break

            del open_set[c_id]
            closed_set[c_id] = current

            for i, _ in enumerate(self.motion):
                node = self.Node(
                    current.x + self.motion[i][0] * self.resolution,
                    current.y + self.motion[i][1] * self.resolution,
                    current.cost + self.motion[i][2] * self.resolution,
                    c_id,
                )
                n_id = self.calc_grid_index(node)

                if not self.verify_node(node):
                    continue
                if n_id in closed_set:
                    continue
                if n_id not in open_set:
                    open_set[n_id] = node
                else:
                    if open_set[n_id].cost > node.cost:
                        open_set[n_id] = node

        path = self.calc_final_path(goal_node, closed_set)
        p_path = self.prune_path(path)
        
        return [path, p_path]

    def calc_final_path(self, goal_node, closed_set):
        path = [[goal_node.x, goal_node.y]]
        parent_index = goal_node.parent_index
        while parent_index != -1:
            n = closed_set[parent_index]
            path.append([n.x, n.y])
            parent_index = n.parent_index
        return path[::-1]

    def prune_path(self, path):
        if not path or len(path) < 3:
            return path
        
        pruned_path = [path[0]]
        current_index = 0

        while current_index < len(path) - 1:
            best_next_index = current_index + 1  # Default to the next point
            
            # Try to find the farthest point we can reach without collision
            for next_index in range(len(path) - 1, current_index, -1):
                p1 = self.Node(path[current_index][0], path[current_index][1], 0, -1)
                p2 = self.Node(path[next_index][0], path[next_index][1], 0, -1)
                
                # Add intermediate checks to ensure the entire path is safe
                if self.is_collision_free(p1, p2):
                    # Additional check: verify that intermediate points don't get too close to obstacles
                    is_safe = True
                    for i in range(current_index + 1, next_index):
                        intermediate_node = self.Node(path[i][0], path[i][1], 0, -1)
                        if not self.verify_node(intermediate_node):
                            is_safe = False
                            break
                    
                    if is_safe:
                        best_next_index = next_index
                        break
            
            pruned_path.append(path[best_next_index])
            current_index = best_next_index
                    
        return pruned_path
    
    def is_point_inside_rectangle(self, point, rect_points):
        """Check if a point is inside a rectangle using the ray-casting algorithm."""
        x, y = point.x, point.y
        n = len(rect_points)
        inside = False
        p1x, p1y = rect_points[0]
        for i in range(n + 1):
            p2x, p2y = rect_points[i % n]
            if y > min(p1y, p2y):
                if y <= max(p1y, p2y):
                    if x <= max(p1x, p2x):
                        if p1y != p2y:
                            xinters = (y - p1y) * (p2x - p1x) / (p2y - p1y) + p1x
                        if p1x == p2x or x <= xinters:
                            inside = not inside
            p1x, p1y = p2x, p2y
        return inside

    def is_collision_free(self, start_node, end_node):
        is_point_check = (start_node.x == end_node.x and start_node.y == end_node.y)
        p1 = Point(start_node.x, start_node.y)
        q1 = Point(end_node.x, end_node.y)

        # Add a safety margin to avoid getting too close to obstacles
        safety_margin = self.resolution * 0.5
        
        for obs in self.obstacles:
            if obs['type'] == 'rectangle':
                if is_point_check:
                    if self.is_point_inside_rectangle(p1, obs['points']):
                        return False  # Point is inside a rectangle
                else:
                    rect_points = obs['points']
                    # Check if the line segment intersects with any edge of the rectangle
                    for i in range(4):
                        p2 = Point(rect_points[i][0], rect_points[i][1])
                        q2 = Point(rect_points[(i + 1) % 4][0], rect_points[(i + 1) % 4][1])
                        if doIntersect(p1, q1, p2, q2):
                            return False
                    
                    # Additional check: if the line is completely inside the obstacle
                    if self.is_point_inside_rectangle(p1, obs['points']) and self.is_point_inside_rectangle(q1, obs['points']):
                        return False

            elif obs['type'] == 'circle':
                center_x, center_y = obs['center']
                radius = obs['radius'] + safety_margin  # Add safety margin
                
                # Check if start point is inside the circle
                if ((p1.x - center_x)**2 + (p1.y - center_y)**2) <= radius**2:
                    return False
                    
                # Check if end point is inside the circle
                if ((q1.x - center_x)**2 + (q1.y - center_y)**2) <= radius**2:
                    return False

                if not is_point_check:
                    # Check if the line segment intersects the circle
                    dx = q1.x - p1.x
                    dy = q1.y - p1.y
                    fx = p1.x - center_x
                    fy = p1.y - center_y
                    a = dx*dx + dy*dy
                    b = 2 * (fx*dx + fy*dy)
                    c = fx*fx + fy*fy - radius*radius
                    
                    discriminant = b*b - 4*a*c
                    if discriminant >= 0:
                        discriminant = math.sqrt(discriminant)
                        t1 = (-b - discriminant) / (2*a) if a != 0 else -1
                        t2 = (-b + discriminant) / (2*a) if a != 0 else -1
                        
                        # Check if the intersection points are within the segment
                        if (0 <= t1 <= 1) or (0 <= t2 <= 1):
                            return False
        return True

    def verify_node(self, node):
        # Check if node is within boundaries
        if not (self.min_x <= node.x <= self.max_x and self.min_y <= node.y <= self.max_y):
            return False

        # Check if node is too close to any obstacle
        safety_margin = self.resolution * 0.5
        
        for obs in self.obstacles:
            if obs['type'] == 'rectangle':
                # Create a slightly expanded rectangle for safety check
                rect_points = obs['points']
                min_x = min(p[0] for p in rect_points) - safety_margin
                max_x = max(p[0] for p in rect_points) + safety_margin
                min_y = min(p[1] for p in rect_points) - safety_margin
                max_y = max(p[1] for p in rect_points) + safety_margin
                
                if min_x <= node.x <= max_x and min_y <= node.y <= max_y:
                    return False
                    
            elif obs['type'] == 'circle':
                center_x, center_y = obs['center']
                radius = obs['radius'] + safety_margin
                
                if ((node.x - center_x)**2 + (node.y - center_y)**2) <= radius**2:
                    return False
        
        return True

    def calc_grid_index(self, node):
        x_idx = round((node.x - self.min_x) / self.resolution)
        y_idx = round((node.y - self.min_y) / self.resolution)
        return y_idx * self.x_width + x_idx

    @staticmethod
    def calc_heuristic(n1, n2):
        return math.hypot(n1.x - n2.x, n1.y - n2.y)
    
    @staticmethod
    def get_motion_model():
        return [
            [1, 0, 1], [0, 1, 1], [-1, 0, 1], [0, -1, 1],
            [-1, -1, math.sqrt(2)], [-1, 1, math.sqrt(2)],
            [1, -1, math.sqrt(2)], [1, 1, math.sqrt(2)],
        ]