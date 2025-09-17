// lib/screens/main_screen.dart

import 'package:flutter/material.dart';
import 'package:flutter_map/flutter_map.dart';
import 'package:path_planning/models/obstacle.dart';
import 'package:path_planning/providers/map_provider.dart';
import 'package:path_planning/widgets/drawing_tools_widget.dart';
import 'package:path_planning/widgets/path_planning_widget.dart';
import 'package:path_planning/widgets/save_map_widget.dart';
import 'package:path_planning/widgets/saved_maps_widget.dart';
import 'package:provider/provider.dart';

class MainScreen extends StatelessWidget {
  const MainScreen({super.key});

  @override
  Widget build(BuildContext context) {
    final mapProvider = Provider.of<MapProvider>(context);

    return Scaffold(
      body: Row(
        children: [
          // Sidebar
          Container(
            width: 300,
            color: Colors.white,
            child: SingleChildScrollView(
              padding: const EdgeInsets.all(16.0),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  const Text(
                    'Path Planner',
                    style: TextStyle(fontSize: 24, fontWeight: FontWeight.bold),
                  ),
                  const SizedBox(height: 24),
                  const Divider(),
                  DrawingToolsWidget(),
                  const Divider(),
                  SaveMapWidget(),
                  const Divider(),
                  PathPlanningWidget(),
                  const Divider(),
                  SavedMapsWidget(),
                ],
              ),
            ),
          ),
          // Main Map View
          Expanded(
            child: FlutterMap(
              options: MapOptions(
                initialCenter: mapProvider.initialCenter,
                initialZoom: 15.0,
                onTap: (tapPosition, point) => mapProvider.handleMapTap(point),
              ),
              children: [
                TileLayer(
                  urlTemplate: 'https://tile.openstreetmap.org/{z}/{x}/{y}.png',
                  userAgentPackageName: 'com.example.path_planner_app',
                ),
                // Draw Boundary
                if (mapProvider.boundary != null)
                  PolygonLayer(polygons: [
                    Polygon(
                      points: mapProvider.boundary!.points,
                      color: Colors.green.withOpacity(0.2),
                      borderColor: Colors.green,
                      borderStrokeWidth: 2,
                    )
                  ]),
                // Draw Obstacles
                PolygonLayer(
                  polygons: mapProvider.obstacles
                      .where((o) => o.type == ObstacleType.rectangle)
                      .map((obs) => Polygon(
                            points: obs.points,
                            color: Colors.red.withOpacity(0.5),
                            borderColor: Colors.red,
                            borderStrokeWidth: 2,
                          ))
                      .toList(),
                ),
                CircleLayer(
                  circles: mapProvider.obstacles
                      .where((o) => o.type == ObstacleType.circle)
                      .map((obs) => CircleMarker(
                            point: obs.center!,
                            radius: obs.radius!,
                            color: Colors.red.withOpacity(0.5),
                            borderColor: Colors.red,
                            borderStrokeWidth: 2,
                            useRadiusInMeter: true,
                          ))
                      .toList(),
                ),

                // ================= FIX STARTS HERE =================
                // Draw Paths only if they exist
                if (mapProvider.unprunedPath.isNotEmpty ||
                    mapProvider.prunedPath.isNotEmpty)
                  PolylineLayer(
                    polylines: [
                      if (mapProvider.unprunedPath.isNotEmpty)
                        Polyline(
                            points: mapProvider.unprunedPath,
                            color: Colors.green.withOpacity(0.8),
                            strokeWidth: 4),
                      if (mapProvider.prunedPath.isNotEmpty)
                        Polyline(
                            points: mapProvider.prunedPath,
                            color: Colors.blue,
                            strokeWidth: 4),
                    ],
                  ),
                // ================= FIX ENDS HERE =================

                // Draw Start and End Points
                MarkerLayer(
                  markers: [
                    if (mapProvider.startPoint != null)
                      Marker(
                        point: mapProvider.startPoint!,
                        width: 80,
                        height: 80,
                        child: const Icon(Icons.location_on,
                            color: Colors.green, size: 40),
                      ),
                    if (mapProvider.endPoint != null)
                      Marker(
                        point: mapProvider.endPoint!,
                        width: 80,
                        height: 80,
                        child:
                            const Icon(Icons.flag, color: Colors.red, size: 40),
                      ),
                  ],
                ),
              ],
            ),
          ),
        ],
      ),
    );
  }
}