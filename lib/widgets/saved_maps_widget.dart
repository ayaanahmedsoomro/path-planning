// lib/widgets/saved_maps_widget.dart

import 'package:flutter/material.dart';
import 'package:path_planning/providers/map_provider.dart';
import 'package:provider/provider.dart';

class SavedMapsWidget extends StatelessWidget {
  const SavedMapsWidget({super.key});

  @override
  Widget build(BuildContext context) {
    return Consumer<MapProvider>(
      builder: (context, mapProvider, child) {
        final savedMapKeys = mapProvider.savedMaps.keys.toList();

        return Padding(
          padding: const EdgeInsets.symmetric(vertical: 8.0),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              const Text('List of Saved Obstacles',
                  style: TextStyle(fontSize: 18, fontWeight: FontWeight.w600)),
              const SizedBox(height: 12),
              if (savedMapKeys.isEmpty)
                const Text('No maps saved yet.')
              else
                ListView.builder(
                  shrinkWrap: true,
                  physics: const NeverScrollableScrollPhysics(),
                  itemCount: savedMapKeys.length,
                  itemBuilder: (context, index) {
                    final mapName = savedMapKeys[index];
                    return Card(
                      elevation: 1,
                      margin: const EdgeInsets.only(bottom: 8),
                      child: ListTile(
                        title: Text(mapName),
                        onTap: () => mapProvider.loadMap(mapName),
                        trailing: const Icon(Icons.arrow_forward_ios, size: 16),
                      ),
                    );
                  },
                ),
            ],
          ),
        );
      },
    );
  }
}