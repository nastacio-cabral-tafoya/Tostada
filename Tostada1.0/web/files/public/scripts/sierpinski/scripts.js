dimensions = 3;

function getRandomVerticie(verticies)
{// Selects a random point in the triangle.
	let start    = (Math.floor(Math.random() * dimensions) * dimensions); // Determines the starting index of the verticie that was selected.
	let verticie = new Array(); // Initializes a new empty array.
	
	for (let i = start; (i < (start + dimensions)); i++)
	{// Iterates from the starting index to the number of dimensions past the starting index. In this case (start + 3).
		verticie.push(verticies[i]);
	}
	
	return verticie; // Returns the x,y,z coordinates of the selected verticie of the triangle.
}

function generateSierpinskiVerticies(verticies, iterations)
{// Generates points to overlay onto the triangle to draw a Sierpinski Triangle.
	let v1           = [0.0, 0.0, 0.0]; // Starting point is at middle of the canvas or middle of the triangle.
	let v2           = getRandomVerticie(verticies, dimensions); // Gets a random triangle verticie.
	let retVerticies = new Array();
	
	for (let i = 0; (i < iterations); i++)
	{// Iterates the specified number of times.
		v1 = [((v2[0] + v1[0]) / 2), ((v2[1] + v1[1]) / 2), 0]; // Sets v1 to be the mid point between v1 and v2.
		
		for (let j = 0; (j < v1.length); j++)
		{// Pushes each element in the v1 array into the retVeriticies array.
			retVerticies.push(v1[j]);
		}
		
		//Selects another random triangle verticie.
		v2 = getRandomVerticie(verticies, dimensions);
	}
	
	// Returns the list of verticies to draw.
	return retVerticies;
}

function drawSierpinskiTriangle()
{// Draws the black triangle shape, and the green verticies for the sierpinski overlay.
	let iterations = document.getElementById("iterations_txbx").value; // Gets the number of iterations the user entered into the textbox.
	
	/*============== Creating a canvas ====================*/
	let canvas = document.getElementById('triangle');
	let gl = canvas.getContext('experimental-webgl');

	/*======== Defining and storing the geometry ===========*/

	let triangleVerticies = [
		-1.0, -1.0, 0.0, // Point 1
		0.0, 1.0, 0.0,   // Point 2
		1.0, -1.0, 0.0   // Point 3
	];
	
	let indices = [0,1,2];

	// Create an empty buffer object to store vertex buffer
	let vertex_buffer = gl.createBuffer();

	// Bind appropriate array buffer to it
	gl.bindBuffer(gl.ARRAY_BUFFER, vertex_buffer);

	// Pass the vertex data to the buffer
	gl.bufferData(gl.ARRAY_BUFFER, new Float32Array(triangleVerticies), gl.STATIC_DRAW);

	// Unbind the buffer
	gl.bindBuffer(gl.ARRAY_BUFFER, null);

	// Create an empty buffer object to store Index buffer
	let Index_Buffer = gl.createBuffer();

	// Bind appropriate array buffer to it
	gl.bindBuffer(gl.ELEMENT_ARRAY_BUFFER, Index_Buffer);

	// Pass the vertex data to the buffer
	gl.bufferData(gl.ELEMENT_ARRAY_BUFFER, new Uint16Array(indices), gl.STATIC_DRAW);

	// Unbind the buffer
	gl.bindBuffer(gl.ELEMENT_ARRAY_BUFFER, null);

	/*================ Shaders ====================*/

	// Vertex shader source code
	let vertCode =
	'attribute vec3 coordinates;' +

	'void main(void) {' +
	' gl_Position = vec4(coordinates, 1.0);' +
	'}';

	// Create a vertex shader object
	let vertShader = gl.createShader(gl.VERTEX_SHADER);

	// Attach vertex shader source code
	gl.shaderSource(vertShader, vertCode);

	// Compile the vertex shader
	gl.compileShader(vertShader);

	//fragment shader source code
	let fragCode =
	'void main(void) {' +
	' gl_FragColor = vec4(0.0, 0.0, 0.0, 1.0);' +
	'}';

	// Create fragment shader object
	let fragShader = gl.createShader(gl.FRAGMENT_SHADER);

	// Attach fragment shader source code
	gl.shaderSource(fragShader, fragCode); 

	// Compile the fragmentt shader
	gl.compileShader(fragShader);

	// Create a shader program object to store
	// the combined shader program
	let shaderProgram = gl.createProgram();

	// Attach a vertex shader
	gl.attachShader(shaderProgram, vertShader);

	// Attach a fragment shader
	gl.attachShader(shaderProgram, fragShader);

	// Link both the programs
	gl.linkProgram(shaderProgram);

	// Use the combined shader program object
	gl.useProgram(shaderProgram);

	/*======= Associating shaders to buffer objects =======*/

	// Bind vertex buffer object
	gl.bindBuffer(gl.ARRAY_BUFFER, vertex_buffer);

	// Bind index buffer object
	gl.bindBuffer(gl.ELEMENT_ARRAY_BUFFER, Index_Buffer);

	// Get the attribute location
	let coord = gl.getAttribLocation(shaderProgram, "coordinates");

	// Point an attribute to the currently bound VBO
	gl.vertexAttribPointer(coord, 3, gl.FLOAT, false, 0, 0); 

	// Enable the attribute
	gl.enableVertexAttribArray(coord);

	/*=========Drawing the triangle===========*/

	// Clear the canvas
	gl.clearColor(0.0, 0.0, 0.0, 0.0);

	// Enable the depth test
	gl.enable(gl.DEPTH_TEST);

	// Clear the color buffer bit
	gl.clear(gl.COLOR_BUFFER_BIT);

	// Set the view port
	gl.viewport(0,0,canvas.width,canvas.height);

	// Draw the triangle
	gl.drawElements(gl.TRIANGLES, indices.length, gl.UNSIGNED_SHORT,0);

	/*================Creating a canvas=================*/
	canvas = document.getElementById('points');
	gl = canvas.getContext('experimental-webgl'); 

	/*==========Defining and storing the geometry=======*/
	
	let sierpinskiVerticies = generateSierpinskiVerticies(triangleVerticies, iterations);

	// Create an empty buffer object to store the vertex buffer
	vertex_buffer = gl.createBuffer();

	//Bind appropriate array buffer to it
	gl.bindBuffer(gl.ARRAY_BUFFER, vertex_buffer);

	// Pass the vertex data to the buffer
	gl.bufferData(gl.ARRAY_BUFFER, new Float32Array(sierpinskiVerticies), gl.STATIC_DRAW);

	// Unbind the buffer
	gl.bindBuffer(gl.ARRAY_BUFFER, null);

	/*=========================Shaders========================*/

	// vertex shader source code
	vertCode =
	'attribute vec3 coordinates;' +

	'void main(void) {' +
		'gl_Position = vec4(coordinates, 1.0);' +
		'gl_PointSize = 1.0;'+
	'}';

	// Create a vertex shader object
	vertShader = gl.createShader(gl.VERTEX_SHADER);

	// Attach vertex shader source code
	gl.shaderSource(vertShader, vertCode);

	// Compile the vertex shader
	gl.compileShader(vertShader);

	// fragment shader source code
	fragCode =
	'void main(void) {' +
		' gl_FragColor = vec4(0.0, 1.0, 0.0, 1.0);' +
	'}';

	// Create fragment shader object
	fragShader = gl.createShader(gl.FRAGMENT_SHADER);

	// Attach fragment shader source code
	gl.shaderSource(fragShader, fragCode);

	// Compile the fragmentt shader
	gl.compileShader(fragShader);

	// Create a shader program object to store
	// the combined shader program
	shaderProgram = gl.createProgram();

	// Attach a vertex shader
	gl.attachShader(shaderProgram, vertShader); 

	// Attach a fragment shader
	gl.attachShader(shaderProgram, fragShader);

	// Link both programs
	gl.linkProgram(shaderProgram);

	// Use the combined shader program object
	gl.useProgram(shaderProgram);

	/*======== Associating shaders to buffer objects ========*/

	// Bind vertex buffer object
	gl.bindBuffer(gl.ARRAY_BUFFER, vertex_buffer);

	// Get the attribute location
	coord = gl.getAttribLocation(shaderProgram, "coordinates");

	// Point an attribute to the currently bound VBO
	gl.vertexAttribPointer(coord, 3, gl.FLOAT, false, 0, 0);

	// Enable the attribute
	gl.enableVertexAttribArray(coord);

	/*============= Drawing the primitive ===============*/

	// Clear the canvas
	gl.clearColor(0.0, 0.0, 0.0, 0.0);

	// Enable the depth test
	gl.enable(gl.DEPTH_TEST);

	// Clear the color buffer bit
	gl.clear(gl.COLOR_BUFFER_BIT);

	// Set the view port
	gl.viewport(0, 0, canvas.width,canvas.height);

	// Draw the triangle
	gl.drawArrays(gl.POINTS, 0, (sierpinskiVerticies.length / dimensions));
}
