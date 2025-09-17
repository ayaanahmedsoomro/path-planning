// lib/models/obstacle.dart

import 'package:latlong2/latlong.dart';
import 'package:uuid/uuid.dart';

enum ObstacleType { rectangle, circle }

class Obstacle {
  final String id;
  final ObstacleType type;
  List<LatLng> points;
  LatLng? center;
  double? radius; // Radius in meters

  Obstacle({
    required this.type,
    this.points = const [],
    this.center,
    this.radius,
  }) : id = const Uuid().v4();

  Map<String, dynamic> toJson() {
    final Map<String, dynamic> data = {
      'type': type.name,
    };
    if (type == ObstacleType.rectangle) {
      data['points'] = points.map((p) => {'latitude': p.latitude, 'longitude': p.longitude}).toList();
    } else if (type == ObstacleType.circle) {
      data['center'] = {'latitude': center!.latitude, 'longitude': center!.longitude};
      data['radius'] = radius;
    }
    return data;
  }
}