
#include "meshNode.h"

Node::Node(int grid_x, int grid_y, LVecBase3f pos, float w, float l, float h) {

	for(int i=0; i<8; i++) {
		_neighbours[i] = NULL;
	}

	_position = pos;
	_width = w;
	_length = l;
	_height = h;
	_grid_x = grid_x;
	_grid_y = grid_y;

  _status = neutral;

	_type = true;
	_score = 0;
	_cost = 0;
	_heuristic = 0;
	_next = NULL;
	_prv_node =  NULL;

}

Node::~Node() {

}

////////////////////////////////////////////////////////////////////////////////////////
//! Function : contains
//! Description : Checks whether a particular point x, y (z is not considered yet since
//!               right now we are developing for a flat terrain with tweaks) is within
//!								the Square node.

///////////////////////////////////////////////////////////////////////////////////////

bool Node::contains(float x, float y) {

	if(_position[0]-_width/2 <= x && _position[0]+_width/2 >= x &&
					_position[1]-_length/2 <= y && _position[1]+_length/2 >= y)
			return true;

	return false;
}

