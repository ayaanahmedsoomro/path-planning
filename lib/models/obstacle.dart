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

  // Convert Obstacle object to a JSON map
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

  // Create an Obstacle object from a JSON map (NEW)
  factory Obstacle.fromJson(Map<String, dynamic> json) {
    var type = ObstacleType.values.firstWhere((e) => e.name == json['type']);
    List<LatLng> points = [];
    LatLng? center;
    double? radius;

    if (type == ObstacleType.rectangle) {
      points = (json['points'] as List)
          .map((p) => LatLng(p['latitude'], p['longitude']))
          .toList();
    } else if (type == ObstacleType.circle) {
      center = LatLng(json['center']['latitude'], json['center']['longitude']);
      radius = json['radius'];
    }

    return Obstacle(
      type: type,
      points: points,
      center: center,
      radius: radius,
    );
  }
}