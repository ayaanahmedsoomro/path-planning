// lib/api/api_service.dart

import 'dart:convert';
import 'package:http/http.dart' as http;
import 'package:latlong2/latlong.dart';
import 'package:path_planning/models/map_data.dart';


class ApiService {
  final String _baseUrl = 'http://127.0.0.1:5000';

  Future<Map<String, dynamic>> getPath(MapData mapData) async {
    final url = Uri.parse('$_baseUrl/plan-path');
    final headers = {"Content-Type": "application/json"};
    final body = json.encode(mapData.toJson());

    try {
      final response = await http.post(url, headers: headers, body: body);

      if (response.statusCode == 200) {
        final Map<String, dynamic> data = json.decode(response.body);
        
        List<LatLng> path = (data['path'] as List)
            .map((p) => LatLng(p['latitude'], p['longitude']))
            .toList();
        
        List<LatLng> prunedPath = (data['pruned_path'] as List)
            .map((p) => LatLng(p['latitude'], p['longitude']))
            .toList();

        return {'path': path, 'pruned_path': prunedPath};
      } else {
        throw Exception(
            'Failed to get path. Status code: ${response.statusCode}');
      }
    } catch (e) {
      throw Exception('Error connecting to the server: $e');
    }
  }
}