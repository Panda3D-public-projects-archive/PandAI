
////////////////////////////////////////////////////////////////////////
//! Filename :		meshGen.h 
//! Created by :	Deepak, John, Navin
//! Date:					8 Sep 09
//!
////////////////////////////////////////////////////////////////////////
//!
//! PANDA3D SOFTWARE
//! Copyright(c) Carnegie Mellon University. All rights reserved.
//!
//!	All use of this software is subjest to the terms of the revised BSD
//!	license. You should have received a copy of this license along with this source code in a file named "LICENSE"
			
////////////////////////////////////////////////////////////////////////

#include<iostream>
#include<fstream>

#include "aiMeshGenerator.h"

// This structure holds all the Plain Old Data types from the Node class.
// Members like _score, _cost, _heuristic are not written to the .csv file
// as they are computed later on during path finding.
struct NodePOD {
	// Indicates if a node is NULL.
  bool _is_null;

	// 0 - current node
  // 1 - neighbor node
  int _node_type;

	int _grid_x, _grid_y;
	float _width, _length ,_height;
  LVecBase3f _position;
};

int main(int argc, char * argv[]) {
  // Check to ensure enough number of arguments are passed at command line.
  if(argc < 3) {
    cout<<"Error: Insufficient arguments!"<<endl;
    cout<<"Usage: meshgen <mesh_plane egg file> <mesh_collision_plane egg file>"<<endl;
    cout<<"   eg: meshgen plane_mesh.egg plane_col_mesh.egg"<<endl;
    exit(0);
  }

  // Variables to hold the 2 command line arguments.
  const char * mesh_plane = argv[1];
  const char * mesh_col_plane = argv[2];

	// Holds the mesh data in a navmesh.csv
	ofstream navmesh_datafile ("navmesh.csv");

	// This one dimensional vector is used to store all the relevant mesh PODs.
  vector<NodePOD> nodePOD_array;

	// Creates the nodes on the mesh and also all the other dependencies.
  MeshGenerator *mesh_generator = new MeshGenerator(mesh_col_plane, mesh_plane);

	cout<<"Step 6: Storing POD data from mesh...."<<endl;

  for(unsigned int i = 0; i < mesh_generator->_node_array.size(); ++i) {
    for(unsigned j = 0; j < mesh_generator->_node_array[i].size(); ++j) {
			// Loop through all the main nodes and then through their correspodning neighbor nodes.
      if(mesh_generator->_node_array[i][j] != NULL) {
        NodePOD main_nodepod;
        main_nodepod._is_null = false;
        main_nodepod._node_type = 0;
        main_nodepod._grid_x = mesh_generator->_node_array[i][j]->_grid_x;
        main_nodepod._grid_y = mesh_generator->_node_array[i][j]->_grid_y;
        main_nodepod._length = mesh_generator->_node_array[i][j]->_length;
        main_nodepod._width = mesh_generator->_node_array[i][j]->_width;
        main_nodepod._height = mesh_generator->_node_array[i][j]->_height;
        main_nodepod._position = mesh_generator->_node_array[i][j]->_position;
        nodePOD_array.push_back(main_nodepod);

				// Looping through the 8 neighbors begins here.
        for(unsigned k=0; k<8; k++) {
          if(mesh_generator->_node_array[i][j]->_neighbours[k] != NULL) {
            NodePOD neighbor_nodepod;
            neighbor_nodepod._is_null = false;
            neighbor_nodepod._node_type = 1;
            neighbor_nodepod._grid_x = mesh_generator->_node_array[i][j]->_neighbours[k]->_grid_x;
            neighbor_nodepod._grid_y = mesh_generator->_node_array[i][j]->_neighbours[k]->_grid_y;
            neighbor_nodepod._length = mesh_generator->_node_array[i][j]->_neighbours[k]->_length;
            neighbor_nodepod._width = mesh_generator->_node_array[i][j]->_neighbours[k]->_width;
            neighbor_nodepod._height = mesh_generator->_node_array[i][j]->_neighbours[k]->_height;
            neighbor_nodepod._position = mesh_generator->_node_array[i][j]->_neighbours[k]->_position;
            nodePOD_array.push_back(neighbor_nodepod);
          }
          else {
            // If the node is NULL do the following.
						// Note: It is necessary to preserve the NULL nodes to maintain grid coordinates.
            NodePOD null_nodepod_n;
            null_nodepod_n._is_null = true;
            null_nodepod_n._node_type = 1;
            null_nodepod_n._grid_x = 0;
            null_nodepod_n._grid_y = 0;
            null_nodepod_n._length = 0.0;
            null_nodepod_n._width = 0.0;
            null_nodepod_n._height = 0.0;
            null_nodepod_n._position = LVecBase3f(0.0 ,0.0, 0.0);
            nodePOD_array.push_back(null_nodepod_n);
          }
        }
      }
      else {
        // If the node is NULL do the following.
				// Note: It is necessary to preserve the NULL nodes to maintain grid coordinates.
        NodePOD null_nodepod;
        null_nodepod._is_null = true;
        null_nodepod._node_type = 0;
        null_nodepod._grid_x = 0;
        null_nodepod._grid_y = 0;
        null_nodepod._length = 0.0;
        null_nodepod._width = 0.0;
        null_nodepod._height = 0.0;
        null_nodepod._position = LVecBase3f(0.0 ,0.0, 0.0);
        nodePOD_array.push_back(null_nodepod);
      }
    }
  }

  if(navmesh_datafile.is_open()) {
		cout<<"Step 7: Writing mesh data into navmesh.csv...."<<endl;

		// The Grid size is specfied at the beginning of the .csv file.
    navmesh_datafile << "Grid Size,"<<sqrt(float(mesh_generator->_full_grid_size)) << endl;

		// Header for the file.
    navmesh_datafile << "NULL,NodeType,GridX,GridY,Length,Width,Height,PosX,PosY,PosZ" << endl;
    for(unsigned int i = 0; i<nodePOD_array.size(); i++) {
      navmesh_datafile <<nodePOD_array[i]._is_null<<","<<nodePOD_array[i]._node_type<<","<<nodePOD_array[i]._grid_x<<","<<nodePOD_array[i]._grid_y<<","
				<<nodePOD_array[i]._length<<","<<nodePOD_array[i]._width<<","<<nodePOD_array[i]._height<<","<<nodePOD_array[i]._position.get_x()<<","<<nodePOD_array[i]._position.get_y()<<","<<nodePOD_array[i]._position.get_z()<<endl;
    }
    navmesh_datafile.close();
		cout<<"Process Complete!"<<endl;
  }
  else {
    cout<<"error opening navmesh.csv file!"<<endl;
		exit(0);
  }
}