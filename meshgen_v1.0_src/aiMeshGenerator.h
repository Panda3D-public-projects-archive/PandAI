
////////////////////////////////////////////////////////////////////////
//! Filename :		aiMeshGenerator.h 
//! Created by :	Deepak, John, Navin
//! Date:					6 Dec 09
//!
////////////////////////////////////////////////////////////////////////
//!
//! PANDA3D SOFTWARE
//! Copyright(c) Carnegie Mellon University. All rights reserved.
//!
//!	All use of this software is subjest to the terms of the revised BSD
//!	license. You should have received a copy of this license along with this source code in a file named "LICENSE"

////////////////////////////////////////////////////////////////////////

#include "meshNode.h"
#include <fstream>
#include <string>

// Note: The header file given below is use only if you want to draw the nodes.
//#include "linesegs.h"

typedef vector<Node *> NODE_ARRAY;

// Helper functions which aids the MeshGenerator
bool exists(Node* head ,int y, int x);
bool compare(LVecBase3f v[], LVecBase3f val);
float find_min(LVecBase3f v[], char type);
float find_max(LVecBase3f v[], char type);

//////////////////////////////////////////////////////////////////////////////////
//! Class : MeshGenerator
//! Description : This class parses the egg files and generates the nodes.

/////////////////////////////////////////////////////////////////////////////////

class MeshGenerator {
private:
	  // For the collision mesh
		vector<LVecBase3f> _vertices;
		vector<LVecBase3f> _triangles;
		
		// For the full mesh
		vector<LVecBase3f> _vertices_full;
		vector<LVecBase3f> _triangles_full;

		// For drawing the mesh
		//vector<LineSegs *> _line_draw;
		//vector<GeomNode *> _parent_geom_node;

		// For the 2d grid array of the mesh (1 - node, 0 - collision)
		int **_grid_map;
		int _coll_grid_size;

		Node *_prev_node;

public:
		int _full_grid_size;
		Node *_head; // For the collision mesh
		Node *_head_full; // For the full mesh

		vector<NODE_ARRAY> _node_array;  // The node array which is used by the Pathfinder

	  MeshGenerator(const char* coll_file_name, const char* full_file_name);
		~MeshGenerator();
		
		void read_file(const char* file_name, const char* mesh_file_name);

		void create_nodes();
		void attach_node(LVecBase3f v[], int node_no, const char* type);
		void create_neighbors();
		Node* find_node(int x, int y);
		void create_node_array();

		void draw_mesh();
};
