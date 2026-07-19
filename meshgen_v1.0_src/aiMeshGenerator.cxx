
#include "aiMeshGenerator.h"

MeshGenerator::MeshGenerator(const char* coll_file_name, const char* full_file_name) {
	_head = NULL;
	_head_full = NULL;
	_prev_node = NULL;

  cout<<"Step 1: Begin reading file...."<<endl;
	read_file(coll_file_name, full_file_name);
  cout<<"Step 2: Creating nodes on the mesh...."<<endl;
	create_nodes();
  cout<<"Step 3: Identifying neighbor nodes for each node on the mesh...."<<endl;
	create_neighbors();
  cout<<"Step 4: Creating the array of nodes...."<<endl;
	create_node_array();
  cout<<"Step 5: Navmesh generation complete!"<<endl;
}

MeshGenerator::~MeshGenerator() {
	// Clear the vectors
	_vertices_full.clear();
	_triangles_full.clear();
	_vertices.clear();
	_triangles.clear();
	//_parent_geom_node.clear();
}

/*
/////////////////////////////////////////////////////////////////////////////////
//! Function : draw_mesh()
//! Description : This function draws the mesh using the triangles and vertices 
//!								from the parsed input file. (used for testing the created mesh)
//! Note: This function cannot be used here unless the code in meshGen.cxx is
//!       changed so that it opens a window to display the models.

/////////////////////////////////////////////////////////////////////////////////

  void MeshGenerator::draw_mesh() {
  //Initializations for line drawing
	for(unsigned int i=0; i<_triangles.size() * 3; i++) {
		_line_draw.insert(_line_draw.end(),new LineSegs("line of sight"));
		_line_draw[i]->set_color(1.0, 0.0, 0.0);
		_line_draw[i]->set_thickness(2.0);
		_parent_geom_node.insert(_parent_geom_node.end(),_line_draw[i]->create());
	}


	//Drawing the triangles
	int k = 0;
	for (unsigned int i=0; i<_triangles.size() ; i++) {
		k = i * 3;
		for(unsigned int j=0; j<3; j++) {
			_line_draw[k+j]->move_to(_vertices[_triangles[i][j]]);
			if(j<2) {
				_line_draw[k+j]->draw_to(_vertices[int(_triangles[i][j+1])]);
			}
			else {
				_line_draw[k+j]->draw_to(_vertices[int(_triangles[i][0])]);
			}
			_parent_geom_node[k+j] = _line_draw[k+j]->create();
		}
	}
}*/


/////////////////////////////////////////////////////////////////////////////////
//! Function : read_file()
//! Description : This function reads the input file and parses it to get the
//!								triangles and vertices and stores them.

/////////////////////////////////////////////////////////////////////////////////

void MeshGenerator::read_file(const char* coll_file_name, const char* mesh_file_name) {
	float position[3];
	string str;
	ifstream coll_mesh_file, full_mesh_file;
	
	coll_mesh_file.open(coll_file_name);
	full_mesh_file.open(mesh_file_name);

	if(!coll_mesh_file || !full_mesh_file) {
		cout<<"error reading file"<<endl;
		exit(0);
	}

	// Processing full mesh to get the grid
	full_mesh_file >> str;
	while(!full_mesh_file.eof()) {
		if(str == "<Vertex>") {
			full_mesh_file >> str; // avoids "vertex number"
			full_mesh_file >> str; // avoids "{"
			// Vertex numbers
			full_mesh_file >> str;
			position[0] = atof(str.c_str()); 
			full_mesh_file >> str;
			position[1] = atof(str.c_str()); 
			full_mesh_file >> str;
			position[2] = atof(str.c_str()); 

			_vertices_full.insert(_vertices_full.end(), LVecBase3f(position[0], position[1], position[2]));
		}

		if(str == "<VertexRef>") {
			full_mesh_file >> str; // avoids "{"
			// Triangle numbers
			full_mesh_file >> str;
			position[0] = atof(str.c_str()); 
			full_mesh_file >> str;
			position[1] = atof(str.c_str()); 
			full_mesh_file >> str;
			position[2] = atof(str.c_str()); 

			_triangles_full.insert(_triangles_full.end(),LVecBase3f(position[0],position[1],position[2]));
		}

		full_mesh_file >> str;
	}

	_full_grid_size = _triangles_full.size() / 2;

	// Initializing grid map
	int grid_size = sqrt(float(_full_grid_size));
	_grid_map = new int*[grid_size];
	for(int i = 0; i < grid_size; ++i) {
		_grid_map[i] = new int[grid_size];
	}

	// setting all cells in grid map = 1
	for(int i = 0; i < grid_size; ++i) {
		for(int j = 0; j < grid_size; ++j) {
			_grid_map[i][j] = 1;
		}
	}

	// Processing collision mesh
	coll_mesh_file >> str;
	while(!coll_mesh_file.eof()) {
		if(str == "<Vertex>") {
			coll_mesh_file >> str; // avoids "vertex number"
			coll_mesh_file >> str; // avoids "{"
			//Vertex numbers
			coll_mesh_file >> str;
			position[0] = atof(str.c_str()); 
			coll_mesh_file >> str;
			position[1] = atof(str.c_str()); 
			coll_mesh_file >> str;
			position[2] = atof(str.c_str()); 

			_vertices.insert(_vertices.end(), LVecBase3f(position[0], position[1], position[2]));
		}

		if(str == "<VertexRef>") {
			coll_mesh_file >> str; // avoids "{"
			//Triangle numbers
			coll_mesh_file >> str;
			position[0] = atof(str.c_str()); 
			coll_mesh_file >> str;
			position[1] = atof(str.c_str()); 
			coll_mesh_file >> str;
			position[2] = atof(str.c_str()); 

			_triangles.insert(_triangles.end(), LVecBase3f(position[0], position[1], position[2]));
		}

		coll_mesh_file >> str;
	}

	_coll_grid_size = _triangles.size() / 2;

	full_mesh_file.close();
	coll_mesh_file.close();
}


/////////////////////////////////////////////////////////////////////////////////
//! Function : create_nodes()
//! Description : This function makes nodes out of each square (2 triangles) of the mesh

/////////////////////////////////////////////////////////////////////////////////

void MeshGenerator::create_nodes() {
	LVecBase3f vertex[4];
	int k = 0;

	// For the full mesh
	for (unsigned int i = 0; i < _triangles_full.size() ; ++i) {
		// 1st triangle
		for(int j = 0; j < 3; ++j) {
			vertex[j] = _vertices_full[_triangles_full[i][j]];
		}
		++i; // 2nd triangle
		for(int j = 0; j < 3; ++j) {
			//returns a true if the vertex is not part of the first array
			if(compare(vertex, _vertices_full[_triangles_full[i][j]]))
				vertex[3] = _vertices_full[_triangles_full[i][j]];
		}	
		attach_node(vertex, i/2, "full");
	}

	k = 0;
	// For the collision mesh
	for (unsigned int i = 0; i < _triangles.size() ; ++i) {
		// 1st triangle
		for(int j = 0; j < 3; ++j) {
			vertex[j] = _vertices[_triangles[i][j]];
		}
		++i; // 2nd triangle
		for(int j = 0; j < 3; ++j) {
			//returns a true if the vertex is not part of the first array
			if(compare(vertex, _vertices[_triangles[i][j]]))
				vertex[3] = _vertices[_triangles[i][j]];
		}	
		attach_node(vertex, i/2, "collision");
	}

}

/////////////////////////////////////////////////////////////////////////////////
//! Function : attach_node()
//! Description : This function creates the node and attaches it to the head node

/////////////////////////////////////////////////////////////////////////////////

void MeshGenerator::attach_node(LVecBase3f v[], int node_no, const char* type) {

	float x1 = find_min(v, 'x');
	float x2 = find_max(v, 'x');

	float y1 = find_min(v, 'y');
	float y2 = find_max(v, 'y');

	float z1 = find_min(v, 'z');
	float z2 = find_max(v, 'z');

	int grid_x, grid_y, grid_length;

	LVecBase3f pos = LVecBase3f((x2 + x1) / 2, (y2 + y1) / 2, (z2 + z1) / 2);

	// Grid x,y calculations for the Full Mesh
	if(type == "full") {
		grid_length = sqrt(float(_full_grid_size));
		if(node_no <  grid_length) {
			grid_x = node_no;
			grid_y = 0;
		}
		else {
			grid_x = node_no % grid_length;
			grid_y = int(node_no / grid_length);
		}
	}
	// Grid x,y calculations for the Collision Mesh
	if(type == "collision") {
		grid_length = sqrt(float(_full_grid_size));

		Node *temp = _head_full;

		while(temp!=NULL) {
			if(temp->_position == pos) {
				grid_x = temp->_grid_x;
				grid_y = temp->_grid_y;
			}
			temp = temp->_next;
		}
	}

	// Making the new node at the center of the square with y = row, x = coloumn
  Node *nnode = new Node(grid_y, grid_x, pos, (x2 - x1), (y2 - y1), (z2 - z1));

	// Assigning the node to the full and collision heads of their linked lists
	if(type == "full") {
		if(_head_full == NULL) {
			_head_full = nnode;
		}
		else {
			_prev_node->_next = nnode;
		}
	}

	if(type == "collision") {
		if(_head == NULL) {
			_head = nnode;
		}
		else {
			_prev_node->_next = nnode;
		}
	}

	nnode->_next = NULL;
	_prev_node = nnode;
}

/////////////////////////////////////////////////////////////////////////////////
//! Function : create_neighbors()
//! Description : This function creates the appropriate neighbors in the collision nodes

/////////////////////////////////////////////////////////////////////////////////

void MeshGenerator::create_neighbors() {

	int grid_size = sqrt(float(_full_grid_size));

	// Initialize all the Null elements in the grid map to 0
	for(int i = 0; i < grid_size; ++i) {
		for(int j = 0; j < grid_size; ++j) {
			if(!exists(_head, i, j)) {
				_grid_map[i][j] = 0;	
			}
		}
	}

	// Update neighbors in the collision mesh node links
	// based on the grid map and boundary checks of the mesh size
	// done for all the 8 neighbors of each node.
	Node *temp = _head;

	while(temp!=NULL) {
		// left
		if(temp->_grid_x - 1 < 0) 
			temp->_neighbours[0] = temp->_neighbours[1] = temp->_neighbours[2] = NULL;
		else {
			if(temp->_grid_y + 1 < grid_size) {
				if(!_grid_map[temp->_grid_y + 1][temp->_grid_x - 1])
					temp->_neighbours[0] = NULL;
				else
					temp->_neighbours[0] = find_node(temp->_grid_x - 1, temp->_grid_y + 1);
			}
			
			if(!_grid_map[temp->_grid_y][temp->_grid_x - 1])
				temp->_neighbours[1] = NULL;
			else
				temp->_neighbours[1] = find_node(temp->_grid_x - 1, temp->_grid_y);

			if(temp->_grid_y - 1 > -1)
				if(!_grid_map[temp->_grid_y - 1][temp->_grid_x - 1])
					temp->_neighbours[2] = NULL;
				else
					temp->_neighbours[2] = find_node(temp->_grid_x - 1, temp->_grid_y - 1);
		}

		//bottom
		if(temp->_grid_y - 1 < 0) 
			temp->_neighbours[2] = temp->_neighbours[3] = temp->_neighbours[4] = NULL;
		else {
			if(!_grid_map[temp->_grid_y - 1][temp->_grid_x])
				temp->_neighbours[3] = NULL;
			else
				temp->_neighbours[3] = find_node(temp->_grid_x, temp->_grid_y - 1);

			if(temp->_grid_x + 1 < grid_size)
				if(!_grid_map[temp->_grid_y - 1][temp->_grid_x + 1])
					temp->_neighbours[4] = NULL;
				else
					temp->_neighbours[4] = find_node(temp->_grid_x + 1, temp->_grid_y - 1);
		}

		//right
		if(temp->_grid_x + 1 >= grid_size) 
			temp->_neighbours[4] = temp->_neighbours[5] = temp->_neighbours[6] = NULL;
		else {
			if(temp->_grid_y + 1 < grid_size)
				if(!_grid_map[temp->_grid_y + 1][temp->_grid_x + 1])
					temp->_neighbours[6] = NULL;
				else
					temp->_neighbours[6] = find_node(temp->_grid_x + 1, temp->_grid_y + 1);

			if(!_grid_map[temp->_grid_y][temp->_grid_x + 1])
				temp->_neighbours[5] = NULL;
			else
				temp->_neighbours[5] = find_node(temp->_grid_x + 1, temp->_grid_y);
		}

		//top
		if(temp->_grid_y + 1 >= grid_size) 
			temp->_neighbours[0] = temp->_neighbours[7] = temp->_neighbours[6] = NULL;
		else {
			if(!_grid_map[temp->_grid_y + 1][temp->_grid_x])
				temp->_neighbours[7] = NULL;
			else
				temp->_neighbours[7] = find_node(temp->_grid_x, temp->_grid_y + 1);
		}

		temp = temp->_next;
	}
}


/////////////////////////////////////////////////////////////////////////////////
//! Function : find_node(int, int)
//! Description : Helper Function that returns the Node array with x and y
//!								representing the grid_x and grid_y

/////////////////////////////////////////////////////////////////////////////////


Node* MeshGenerator::find_node(int x, int y) {
	Node* temp = _head;

	while(temp!=NULL) {
		if(temp->_grid_x == x && temp->_grid_y == y)
				return temp;

		temp = temp->_next;
	}

	return NULL;
}

/////////////////////////////////////////////////////////////////////////////////
//! Function : create_node_array()
//! Description : Helper Function that creates the node array which is going to be
//!								exported for use by the pathfinder in AiBehaviors

/////////////////////////////////////////////////////////////////////////////////

void MeshGenerator::create_node_array() {
	int grid_size = sqrt(float(_full_grid_size));
	int row_count = grid_size;
	int col_count = grid_size;

	// Initialize the 2d vector of nodes
	for(int r = 0; r < row_count; ++r) {
		_node_array.push_back(vector<Node*>());
		for(int c = 0; c < col_count; ++c) {
			_node_array[r].push_back(NULL);
		}
	}

	Node* temp = _head;

	for(int r = 0; r < row_count; ++r) {
		for(int c = 0; c < col_count; ++c) {
			if((_grid_map[r][c] == 1) && (temp != NULL)) {
					_node_array[r][c] = temp;
					temp = temp->_next;
			}
		}
	}
}

//////////////////////////////////////////////////////////////////////////////////
//! Functions : exists(Node*, int, int)
//! Description : Checks whether a particular node exists in the collision linked list

/////////////////////////////////////////////////////////////////////////////////

bool exists(Node* head ,int y, int x) {
	Node *temp = head;

	while(temp!=NULL) {
		if(temp->_grid_x == x && temp->_grid_y == y) {
			return true;			
		}
		temp = temp->_next;
	}

	return false;
}

//////////////////////////////////////////////////////////////////////////////////
//! Functions : compare(LVecBase3f[], LVecBase3f)
//! Description : Compares whether a vertex is part of a triangle set of vertices

/////////////////////////////////////////////////////////////////////////////////

bool compare(LVecBase3f v[], LVecBase3f val) {
	
	for(int i = 0; i < 3; ++i) {
		if(v[i] == val) {
			return false;
		}
	}

	return true;
}

//////////////////////////////////////////////////////////////////////////////////
//! Functions : find_min(LVecBase3f[], char)
//! Description : Returns the minimum x,y or z values in a triangle set of vertices

/////////////////////////////////////////////////////////////////////////////////

float find_min(LVecBase3f v[], char type) {
   
	if(type == 'x') {
		float min_x = v[0][0];
		for(int i = 1; i < 4; ++i) {
			if(v[i][0] <= min_x)		
						min_x = v[i][0];
		}
		return min_x;
	}

	if(type == 'y') {
		float min_y = v[0][1];
		for(int i = 1; i < 4; ++i) {
			if(v[i][1] <= min_y)		
						min_y = v[i][1];
		}
		return min_y;
	}

	if(type == 'z') {
		float min_z = v[0][2];
		for(int i = 1; i < 4; ++i) {
			if(v[i][2] <= min_z)		
						min_z = v[i][2];
		}
		return min_z;
	}

	return 0;
}

//////////////////////////////////////////////////////////////////////////////////
//! Functions : find_max(LVecBase3f[], char)
//! Description : Returns the maximum x,y or z values in a triangle set of vertices

/////////////////////////////////////////////////////////////////////////////////

float find_max(LVecBase3f v[], char type) {
	
	if(type == 'x') {
		float max_x = v[0][0];
		for(int i = 1; i < 4; ++i) {
			if(v[i][0] >= max_x)		
						max_x = v[i][0];
		}
		return max_x;
	}

	if(type == 'y') {
		float max_y = v[0][1];
		for(int i = 1; i < 4; ++i) {
			if(v[i][1] >= max_y)		
						max_y = v[i][1];
		}
		return max_y;
	}

	if(type == 'z') {
		float max_z = v[0][2];
		for(int i = 1; i < 4; ++i) {
			if(v[i][2] >= max_z)		
						max_z = v[i][2];
		}
		return max_z;
	}

	return 0;
}