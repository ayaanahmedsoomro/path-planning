import numpy as np
import cv2
import dill
import os
from copy import deepcopy

from astar_modified import AStarPlanner
from decomposition import Boustrophedon_Cellular_Decomposition

class DynamicProgrammingPlanner:
    """
    Implements a path planning strategy using Boustrophedon cellular decomposition
    and dynamic programming (memoization) to speed up repeated calculations.
    """
    def __init__(self, start, goal, obstacles, boundary):
        self.start = start
        self.goal = goal
        self.obstacles_meters = obstacles
        self.boundary_meters = boundary
        
        # Setup properties for map decomposition
        self.map_size = [
            self.boundary_meters['bottom_left'][0],
            self.boundary_meters['top_right'][0],
            self.boundary_meters['bottom_left'][1],
            self.boundary_meters['top_right'][1]
        ]
        self.decomposition_dir = 'decomposition_temp'
        if not os.path.exists(self.decomposition_dir):
            os.makedirs(self.decomposition_dir)
            
        self.decomposed = None
        self.total_cells_number = 0
        self.cells = None
        self.memory_table = None
        
        # Perform decomposition upon initialization
        self._perform_decomposition()

    def _perform_decomposition(self):
        """
        Creates a binary image of the map, runs the decomposition algorithm,
        and loads the resulting cell data.
        """
        min_x, max_x, min_y, max_y = self.map_size
        width = int(max_x - min_x)
        height = int(max_y - min_y)

        # Ensure dimensions are positive
        if width <= 0: width = 1
        if height <= 0: height = 1
        
        map_img = np.zeros((height, width), np.uint8)

        # Convert obstacle coordinates to image coordinates relative to map origin
        obstacles_for_cv2 = []
        for obs in self.obstacles_meters:
            if obs['type'] == 'rectangle':
                points = np.array(obs['points'], dtype=np.int32)
                points[:, 0] -= int(min_x)
                points[:, 1] -= int(min_y)
                obstacles_for_cv2.append(points)

        if obstacles_for_cv2:
             cv2.fillPoly(map_img, pts=obstacles_for_cv2, color=(255, 255, 255))
        
        # Invert image so free space is white
        cv2.bitwise_not(map_img, map_img)
        map_image_path = os.path.join(self.decomposition_dir, "map.jpg")
        cv2.imwrite(map_image_path, map_img)

        # Run the Boustrophedon decomposition
        Boustrophedon_Cellular_Decomposition(self.decomposition_dir)
        
        # Load the decomposition results
        result_path = os.path.join(self.decomposition_dir, "decomposed_result")
        decomposed, total_cells_number, cells = dill.load(open(result_path, "rb"))

        # Adjust cell center coordinates from image space back to original map space
        for i in range(1, len(cells)):
            if cells[i] is not None:
                x_center, y_center = cells[i].center
                cells[i].center = (x_center + min_x, y_center + min_y)

        self.decomposed = decomposed
        self.total_cells_number = total_cells_number
        self.cells = cells
        # Initialize memory table for storing paths between cell centers
        self.memory_table = [[-1] * total_cells_number for _ in range(total_cells_number)]

    def planning(self):
        """
        Main planning function that orchestrates the pathfinding process.
        """
        # Convert start/goal coordinates to image coordinates to find their cells
        start_img_x = int(self.start[0] - self.map_size[0])
        start_img_y = int(self.start[1] - self.map_size[2])
        goal_img_x = int(self.goal[0] - self.map_size[0])
        goal_img_y = int(self.goal[1] - self.map_size[2])

        # Clamp coordinates to be within image bounds
        h, w = self.decomposed.shape
        start_img_y = max(0, min(start_img_y, h - 1))
        start_img_x = max(0, min(start_img_x, w - 1))
        goal_img_y = max(0, min(goal_img_y, h - 1))
        goal_img_x = max(0, min(goal_img_x, w - 1))

        start_cell_num = self.decomposed[start_img_y, start_img_x]
        goal_cell_num = self.decomposed[goal_img_y, goal_img_x]
        
        # Handle cases where start or goal is inside an obstacle (cell 0)
        if start_cell_num == 0 or goal_cell_num == 0:
            print("Start or goal point is inside an obstacle. Cannot plan path.")
            return [], []
            
        start_cell_idx = start_cell_num - 1
        goal_cell_idx = goal_cell_num - 1

        # If start and goal are in the same cell, plan a direct A* path
        if start_cell_num == goal_cell_num:
            planner = AStarPlanner(self.start, self.goal, self.obstacles_meters, self.boundary_meters)
            return planner.planning()

        start_cell_center = self.cells[start_cell_num].center
        goal_cell_center = self.cells[goal_cell_num].center

        path_between_centers = []
        # Check memory table for a pre-calculated path
        if self.memory_table[start_cell_idx][goal_cell_idx] != -1:
            print("Path between cell centers found in memory.")
            path_between_centers = deepcopy(self.memory_table[start_cell_idx][goal_cell_idx])
        else:
            print("Path not in memory, calculating A* between cell centers...")
            planner = AStarPlanner(start_cell_center, goal_cell_center, self.obstacles_meters, self.boundary_meters)
            path, _ = planner.planning()
            path_between_centers = path
            
            # Store the new path in the memory table for future use
            self.memory_table[start_cell_idx][goal_cell_idx] = deepcopy(path_between_centers)
            self.memory_table[goal_cell_idx][start_cell_idx] = deepcopy(path_between_centers[::-1])

        # Plan path from the actual start point to the start of the center-path
        planner_start = AStarPlanner(self.start, path_between_centers[0], self.obstacles_meters, self.boundary_meters)
        start_segment, _ = planner_start.planning()
        
        # Plan path from the end of the center-path to the actual goal point
        planner_goal = AStarPlanner(path_between_centers[-1], self.goal, self.obstacles_meters, self.boundary_meters)
        goal_segment, _ = planner_goal.planning()

        # Combine the three path segments, avoiding duplicate points
        full_path = start_segment[:-1] + path_between_centers + goal_segment[1:]

        # Perform a final pruning on the combined path to smooth it
        temp_planner = AStarPlanner(self.start, self.goal, self.obstacles_meters, self.boundary_meters)
        pruned_full_path = temp_planner.prune_path(full_path)

        return full_path, pruned_full_path
