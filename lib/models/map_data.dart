// lib/models/map_data.dart


import 'package:latlong2/latlong.dart';
import 'package:path_planning/models/obstacle.dart';

class MapData {
  String name;
  Obstacle boundary;
  List<Obstacle> obstacles;
  LatLng? startPoint;
  LatLng? endPoint;

  MapData({
    required this.name,
    required this.boundary,
    required this.obstacles,
    this.startPoint,
    this.endPoint,
  });

  Map<String, dynamic> toJson() {
    return {
      'boundary': boundary.toJson(),
      'obstacles': obstacles.map((o) => o.toJson()).toList(),
      'start': {
        'latitude': startPoint!.latitude,
        'longitude': startPoint!.longitude
      },
      'goal': {
        'latitude': endPoint!.latitude,
        'longitude': endPoint!.longitude
      },
    };
  }
}