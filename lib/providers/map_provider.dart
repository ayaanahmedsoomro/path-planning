// lib/providers/map_provider.dart

import 'package:flutter/material.dart';
import 'package:latlong2/latlong.dart';
import 'package:geolocator/geolocator.dart';
import 'package:path_planning/api/api_service.dart';
import 'package:path_planning/models/map_data.dart';
import 'package:path_planning/models/obstacle.dart';
import 'package:path_planning/utils/geo_utils.dart';

enum DrawingMode { none, boundary, obstacleRect, obstacleCircle, setStart, setEnd }

class MapProvider extends ChangeNotifier {
  DrawingMode _drawingMode = DrawingMode.none;
  DrawingMode get drawingMode => _drawingMode;

  Obstacle? _boundary;
  Obstacle? get boundary => _boundary;

  List<Obstacle> _obstacles = [];
  List<Obstacle> get obstacles => _obstacles;

  LatLng? _startPoint;
  LatLng? get startPoint => _startPoint;

  LatLng? _endPoint;
  LatLng? get endPoint => _endPoint;

  List<LatLng> _unprunedPath = [];
  List<LatLng> get unprunedPath => _unprunedPath;

  List<LatLng> _prunedPath = [];
  List<LatLng> get prunedPath => _prunedPath;

  bool _isLoading = false;
  bool get isLoading => _isLoading;

  String _errorMessage = '';
  String get errorMessage => _errorMessage;

  LatLng _initialCenter = const LatLng(51.509364, -0.128928); // Default to London
  LatLng get initialCenter => _initialCenter;
  
  Map<String, MapData> _savedMaps = {};
  Map<String, MapData> get savedMaps => _savedMaps;

  // Temporary points for drawing
  LatLng? _tempStartPoint;

  final ApiService _apiService = ApiService();

  MapProvider() {
    _determinePosition();
  }

  Future<void> _determinePosition() async {
    bool serviceEnabled;
    LocationPermission permission;

    serviceEnabled = await Geolocator.isLocationServiceEnabled();
    if (!serviceEnabled) {
      return;
    }

    permission = await Geolocator.checkPermission();
    if (permission == LocationPermission.denied) {
      permission = await Geolocator.requestPermission();
      if (permission == LocationPermission.denied) {
        return;
      }
    }

    if (permission == LocationPermission.deniedForever) {
      return;
    }

    try {
      Position position = await Geolocator.getCurrentPosition();
      _initialCenter = LatLng(position.latitude, position.longitude);
      notifyListeners();
    } catch (e) {
      print("Could not get location: $e");
    }
  }

  void setDrawingMode(DrawingMode mode) {
    _drawingMode = mode;
    _tempStartPoint = null;
    notifyListeners();
  }

  void handleMapTap(LatLng point) {
    switch (_drawingMode) {
      case DrawingMode.boundary:
      case DrawingMode.obstacleRect:
        _handleRectDrawing(point);
        break;
      case DrawingMode.obstacleCircle:
        _handleCircleDrawing(point);
        break;
      case DrawingMode.setStart:
        _startPoint = point;
        _drawingMode = DrawingMode.none;
        break;
      case DrawingMode.setEnd:
        _endPoint = point;
        _drawingMode = DrawingMode.none;
        break;
      case DrawingMode.none:
        break;
    }
    notifyListeners();
  }

  void _handleRectDrawing(LatLng point) {
    if (_tempStartPoint == null) {
      _tempStartPoint = point;
    } else {
      final corner1 = _tempStartPoint!;
      final corner2 = point;
      _tempStartPoint = null;

      final rectPoints = [
        corner1,
        LatLng(corner1.latitude, corner2.longitude),
        corner2,
        LatLng(corner2.latitude, corner1.longitude),
      ];
      
      final newObstacle = Obstacle(type: ObstacleType.rectangle, points: rectPoints);
      
      if (_drawingMode == DrawingMode.boundary) {
        _boundary = newObstacle;
      } else {
        _obstacles.add(newObstacle);
      }
      _drawingMode = DrawingMode.none;
    }
  }
  
  void _handleCircleDrawing(LatLng point) {
    if (_tempStartPoint == null) {
      _tempStartPoint = point; // This is the center
    } else {
      final center = _tempStartPoint!;
      final radiusPoint = point;
      _tempStartPoint = null;
      
      final radius = GeoUtils.calculateDistance(center, radiusPoint);
      final newObstacle = Obstacle(type: ObstacleType.circle, center: center, radius: radius);
      
      _obstacles.add(newObstacle);
      _drawingMode = DrawingMode.none;
    }
  }
  
  void saveMap(String name) {
    if (name.isEmpty || _boundary == null) return;
    final mapData = MapData(
        name: name, boundary: _boundary!, obstacles: List.from(_obstacles));
    _savedMaps[name] = mapData;
    notifyListeners();
  }
  
  void loadMap(String name) {
    if (!_savedMaps.containsKey(name)) return;
    final mapData = _savedMaps[name]!;
    _boundary = mapData.boundary;
    _obstacles = List.from(mapData.obstacles);
    clearPathAndPoints();
    notifyListeners();
  }

  void calculatePath() async {
    if (_startPoint == null || _endPoint == null || _boundary == null) {
      _errorMessage = 'Please set a boundary, start, and end point.';
      notifyListeners();
      return;
    }

    _isLoading = true;
    _errorMessage = '';
    _unprunedPath = [];
    _prunedPath = [];
    notifyListeners();

    final mapData = MapData(
      name: 'current',
      boundary: _boundary!,
      obstacles: _obstacles,
      startPoint: _startPoint,
      endPoint: _endPoint,
    );
    
    try {
      final result = await _apiService.getPath(mapData);
      _unprunedPath = result['path']!;
      _prunedPath = result['pruned_path']!;
    } catch (e) {
      _errorMessage = e.toString();
    } finally {
      _isLoading = false;
      notifyListeners();
    }
  }
  
  void clearPathAndPoints() {
    _startPoint = null;
    _endPoint = null;
    _unprunedPath = [];
    _prunedPath = [];
    _drawingMode = DrawingMode.none;
    notifyListeners();
  }

  void clearAll() {
    _drawingMode = DrawingMode.none;
    _boundary = null;
    _obstacles = [];
    _startPoint = null;
    _endPoint = null;
    _unprunedPath = [];
    _prunedPath = [];
    _tempStartPoint = null;
    _isLoading = false;
    _errorMessage = '';
    notifyListeners();
  }
}