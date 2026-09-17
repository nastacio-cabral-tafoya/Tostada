// Contains the aspect ratio.
aspectRatio = (screen.width / (screen.height - (window.outerHeight - window.innerHeight)));

/*=================================== Variables & Hardcoded Data ===================================*/
var canvas;
var gl;

var vertexShader;
var fragmentShader;
var program;

var vertex_buffer;
var color_buffer;
var index_buffer;

var Pmatrix;
var Vmatrix;
var Mmatrix;

var vertexShaderSource = [
	"// Vector matrix variables.",
	"attribute vec3 position;",
	"uniform   mat4 Pmatrix;",
	"uniform   mat4 Vmatrix;",
	"uniform   mat4 Mmatrix;",
	"",
	"// Color variables.",
	"attribute vec3 color;",
	"varying   vec3 vColor;",
	"",
	"void main(void)",
	"{",
	"   gl_Position = (Pmatrix * Vmatrix * Mmatrix * vec4(position, 1.0));",
	"   vColor      = color;",
	"}"
].join('\n');

var fragmentShaderSource = [
	"precision mediump float;",
	"varying   vec3    vColor;",
	"",
	"void main(void)",
	"{",
	"   gl_FragColor = vec4(vColor, 1.0);",
	"}"
].join('\n');

var cubeVertecies = [
	-1,-1,-1,  1,-1,-1,  1, 1,-1, -1, 1,-1, // Purple Side
	-1,-1, 1,  1,-1, 1,  1, 1, 1, -1, 1, 1, // Orange Side
	-1,-1,-1, -1, 1,-1, -1, 1, 1, -1,-1, 1, // Blue   Side
	 1,-1,-1,  1, 1,-1,  1, 1, 1,  1,-1, 1, // Red    Side
	-1,-1,-1, -1,-1, 1,  1,-1, 1,  1,-1,-1, // Yellow Side
	-1, 1,-1, -1, 1, 1,  1, 1, 1,  1, 1,-1  // Green  Side
];

var cubeColors = [
	0.5,0.0,1.0, 0.5,0.0,1.0, 0.5,0.0,1.0, 0.5,0.0,1.0, // Purple Side
	1.0,0.5,0.0, 1.0,0.5,0.0, 1.0,0.5,0.0, 1.0,0.5,0.0, // Orange Side
	0.0,0.0,1.0, 0.0,0.0,1.0, 0.0,0.0,1.0, 0.0,0.0,1.0, // Blue   Side
	1.0,0.0,0.0, 1.0,0.0,0.0, 1.0,0.0,0.0, 1.0,0.0,0.0, // Red    Side
	1.0,1.0,0.0, 1.0,1.0,0.0, 1.0,1.0,0.0, 1.0,1.0,0.0, // Yellow Side
	0.0,1.0,0.0, 0.0,1.0,0.0, 0.0,1.0,0.0, 0.0,1.0,0.0  // Green  Side
];

var indices = [
	 0, 1, 2,  0, 2, 3,  4, 5, 6,  4, 6, 7,
	 8, 9,10,  8,10,11, 12,13,14, 12,14,15,
	16,17,18, 16,18,19, 20,21,22, 20,22,23 
];

/*=================================== WebGL Context Initializeation ===================================*/

var Clear_Set_Background_Color = function (red, green, blue, alpha)
{// Sets Canvas Background colorDepth
	gl.clearColor((red / 255), (green / 255), (blue / 255), alpha);
	gl.clearDepth(1.0);
	gl.clear(gl.COLOR_BUFFER_BIT | gl.DEPTH_BUFFER_BIT);
};

var Initialize_WebGL_Context = function ()
{
	//Initializes canvas object, and gl context for the canvas object.
	canvas = document.getElementById("rotating_cube");
	gl     = canvas.getContext("webgl");
	
	if (!gl)
	{// If "webgl" context doe snot work, it defaults to "experimental-webgl".
		gl = canvas.getContext("experimental-webgl");
	}
	
	if (!gl)
	{// If "experimental-webgl" does not work either, the browser does not support webgl.
		alert("Your browser does not support WebGL.");
	}
	
	// Creates Shaders
	vertexShader   = gl.createShader(gl.VERTEX_SHADER);
	fragmentShader = gl.createShader(gl.FRAGMENT_SHADER);
	
	gl.shaderSource(vertexShader, vertexShaderSource);
	gl.shaderSource(fragmentShader, fragmentShaderSource);
	
	// Compiles Vertex Shader
	gl.compileShader(vertexShader);
	
	if (!gl.getShaderParameter(vertexShader, gl.COMPILE_STATUS))
	{// Checks for errors compiling vertexShader.
		console.error("ERROR compiling vertex shader!", gl.getShaderInfoLog(vertexShader));
		return;
	}
	
	// Compiles Fragment Shader
	gl.compileShader(fragmentShader);
	
	if (!gl.getShaderParameter(fragmentShader, gl.COMPILE_STATUS))
	{// Checks for errors compiling fragment shader.
		console.error("ERROR compiling fragment shader!", gl.getShaderInfoLog(fragmentShader));
		return;
	}
	
	// Attaches the vertex shader and the fragment shader to the gl program.
	program = gl.createProgram();
	gl.attachShader(program, vertexShader);
	gl.attachShader(program, fragmentShader);
	gl.linkProgram(program);
	
	if (!gl.getProgramParameter(program, gl.LINK_STATUS))
	{// Checks for program linking errors.
		console.error("ERROR linking program!", gl.getProgramInfoLog(program));
		return;
	}
	
	gl.validateProgram(program);
	
	if (!gl.getProgramParameter(program, gl.VALIDATE_STATUS))
	{// Checks for program validation errors.
		console.error("ERROR validating program!", gl.getProgramInfoLog(program));
		return;
	}
};

var Create_Vertex_Buffer = function ()
{// Create and store data into vertex buffer.
	vertex_buffer = gl.createBuffer();
	gl.bindBuffer(gl.ARRAY_BUFFER, vertex_buffer);
	gl.bufferData(gl.ARRAY_BUFFER, new Float32Array(cubeVertecies), gl.STATIC_DRAW);
};

var Create_Color_Buffer = function()
{// Create and store data into color buffer.
	color_buffer = gl.createBuffer();
	gl.bindBuffer(gl.ARRAY_BUFFER, color_buffer);
	gl.bufferData(gl.ARRAY_BUFFER, new Float32Array(cubeColors), gl.STATIC_DRAW);
};

var Create_Index_Buffer = function ()
{// Create and store data into index buffer.
	index_buffer = gl.createBuffer();
	gl.bindBuffer(gl.ELEMENT_ARRAY_BUFFER, index_buffer);
	gl.bufferData(gl.ELEMENT_ARRAY_BUFFER, new Uint16Array(indices), gl.STATIC_DRAW);
};

var Associate_Attribs_To_Vertex_Shader = function ()
{// Associates attributes to vertex shader.
	Pmatrix = gl.getUniformLocation(program, "Pmatrix");
	Vmatrix = gl.getUniformLocation(program, "Vmatrix");
	Mmatrix = gl.getUniformLocation(program, "Mmatrix");
}

var AssociateAttributesToVertexShader = function ()
{// Associates attributes to the shaders.
	// Creates the buffers.
	Create_Vertex_Buffer();
	Create_Color_Buffer();
	Create_Index_Buffer();
	Associate_Attribs_To_Vertex_Shader();
	
	// Binds the vertex_buffer.
	gl.bindBuffer(gl.ARRAY_BUFFER, vertex_buffer);
	
	// Specifies the pointer to the position attribute in the vertex shader and binds it to the buffer.
	let position = gl.getAttribLocation(program, "position");
	gl.vertexAttribPointer(position, 3, gl.FLOAT, false, 0, 0);
	gl.enableVertexAttribArray(position);
	gl.bindBuffer(gl.ARRAY_BUFFER, color_buffer);
	
	// Specifies the pointer to the color attribute in the vertex shader and binds it to the buffer.
	let color = gl.getAttribLocation(program, "color");
	gl.vertexAttribPointer (color, 3, gl.FLOAT, false, 0, 0);
	gl.enableVertexAttribArray(color);
	gl.useProgram(program);
};

/*=================================== MATRIX STUFF ===================================*/

function get_projection(angle, a, zMin, zMax)
{// Generates a projection matrix which is used to transform the 3d world space into the 2d coordinates able to be displayed by the screen with a 2d array of pixels.
	let ang = Math.tan(((angle * 0.5) * Math.PI) / 180); // angle * 0.5
	
	return [
		(0.5 / ang), 0 , 0, 0,
		0, (0.5 * (a / ang)), 0, 0,
		0, 0, -(zMax + zMin)/(zMax - zMin), -1,
		0, 0, (-2 * zMax * zMin)/(zMax - zMin), 0 
	];
}

var proj_matrix = get_projection(40, aspectRatio, 1, 100); // Projection Matrix

var mov_matrix  =
[// Positions the 3d object (cube) in the 3d world space.
	1,0,0,0,
	0,1,0,0,
	0,0,1,0,
	0,0,0,1
];

var view_matrix =
[// Positions the camera view in the 3d world space.
	1,0,0,0,
	0,1,0,0,
	0,0,1,0,
	0,0,0,1
 //|l|u|f|
 //|e|p|o|
 //|f| |r|
 //|t|/|w|
 //| | |a|
 //|/|d|r|
 //| |o|d|
 //|r|w| |
 //|i|n|/|
 //|g| | |
 //|h| |b|
 //|t| |a|
 //| | |c|
 //| | |k|
 //| | |w|
 //| | |a|
 //| | |r|
 //| | |d|
];

// translating z
view_matrix[14] = (-1 * (15)); // Foreward / Backward / Zoom
view_matrix[13] = 0;
view_matrix[12] = 0;

// Maximum range for up/down and left/right parameters.
ud_bound = 8;
lr_bound = (ud_bound * (window.innerWidth / window.innerHeight));

function setFBZAmount(fbz, ud, lr)
{// Sets the forward/backward/zoom amount.

	// The UD Amount and the LR amount needs to be re-calculated based on the current zoom to ensure the cube stays in the visible area.
	setUDAmount(fbz, ud);
	setLRAmount(fbz, lr);
	
	view_matrix[14] = (-1 * (25 - ((25 - 5) * (fbz / 100))));
}

function setUDAmount(fbz, ud)
{// Sets the up / down amount.
	let bound = (2 * (ud_bound - (ud_bound * (fbz / 100))));
	view_matrix[13] = (-1 * ((bound - (bound * (ud / 100))) - (bound / 2)));
}

function setLRAmount(fbz, lr)
{// Sets the left / right amount.
	let bound = (2 * (lr_bound - (lr_bound * (fbz / 100))));
	view_matrix[12] = (-1 * ((bound - (bound * (lr / 100))) - (bound / 2)));
}

function resetFBZ()
{// Resets the FBZ slider to 50%.
	let fbz_slider = document.getElementById("fbz-rng");
	fbz_slider.value = 50;
	setFBZAmount(fbz_slider.value, document.getElementById("ud-rng").value, document.getElementById("lr-rng").value);
}

function resetUD()
{// Resets the UD slider to 50%;
	let ud_slider = document.getElementById("ud-rng");
	ud_slider.value = 50;
	setUDAmount(document.getElementById("fbz-rng").value, ud_slider.value);
}

function resetLR()
{// Resets the LR slider to 50%.
	let lr_slider = document.getElementById("lr-rng");
	lr_slider.value = 50;
	setLRAmount(document.getElementById("fbz-rng").value, lr_slider.value);
}

/*=================================== Rotation Algorithms ===================================*/

function rotateZ(m, angle)
{// Rotates the vertices along the z-axis.
	let c   = Math.cos(angle);
	let s   = Math.sin(angle);
	let mv0 = m[0];
	let mv4 = m[4];
	let mv8 = m[8];

	m[0] = (c * m[0] - s * m[1]);
	m[4] = (c * m[4] - s * m[5]);
	m[8] = (c * m[8] - s * m[9]);

	m[1] = (c * m[1] + s * mv0);
	m[5] = (c * m[5] + s * mv4);
	m[9] = (c * m[9] + s * mv8);
}

function rotateX(m, angle)
{// Rotates the verteces along the x-axis.
	let c   = Math.cos(angle);
	let s   = Math.sin(angle);
	let mv1 = m[1];
	let mv5 = m[5];
	let mv9 = m[9];

	m[1] = (m[1] * c - m[2] * s);
	m[5] = (m[5] * c - m[6] * s);
	m[9] = (m[9] * c - m[10] * s);

	m[2]  = (m[2] * c + mv1 * s);
	m[6]  = (m[6] * c + mv5 * s);
	m[10] = (m[10] * c + mv9 * s);
}

function rotateY(m, angle)
{// Rotates the verteces along the y-axis.
	let c   = Math.cos(angle);
	let s   = Math.sin(angle);
	let mv0 = m[0];
	let mv4 = m[4];
	let mv8 = m[8];

	m[0] = (c * m[0] + s * m[2]);
	m[4] = (c * m[4] + s * m[6]);
	m[8] = (c * m[8] + s * m[10]);

	m[2]  = (c * m[2] - s * mv0);
	m[6]  = (c * m[6] - s * mv4);
	m[10] = (c * m[10] -s * mv8);
}

var time_old = 0;

/*=================================== Animation Frame Generation ===================================*/

var Draw_And_Animate_Cube = function (time)
{// Clears the webgl window and re-draws the verteces after applying the transformations to the verteces of the cube.
	var dt = (time - time_old);
	
	rotateZ(mov_matrix, (dt * 0.0005)); // Rotates the cube along the z-axis.
	rotateX(mov_matrix, (dt * 0.0005)); // Rotates the cube along the x-axis.
	rotateY(mov_matrix, (dt * -0.001)); // Rotates the cube along the y-axis.
	
	time_old = time;
	
	// Configures the depth testing to determine if a fragment should be drawn in the view based on their depth.
	gl.enable(gl.DEPTH_TEST);
	gl.depthFunc(gl.LEQUAL);
	
	// Updates the matrice data in the shader program.
	gl.uniformMatrix4fv(Pmatrix, false, proj_matrix);
	gl.uniformMatrix4fv(Vmatrix, false, view_matrix);
	gl.uniformMatrix4fv(Mmatrix, false, mov_matrix);
	
	// Clears the canvas and sets the background.
	Clear_Set_Background_Color(213, 232, 231, 1.0);
	
	// Specifies the transformation of x and y from normalized coordinates to window coordinates.
	gl.viewport(0.0, 0.0, canvas.width, canvas.height);
	
	// Binds the index buffer and draws the vertices.
	gl.bindBuffer(gl.ELEMENT_ARRAY_BUFFER, index_buffer);
	gl.drawElements(gl.TRIANGLES, indices.length, gl.UNSIGNED_SHORT, 0);
	
	// Instructs the browser to execute the draw function again after it's execution has completely finished.
	// Function cannot be called through direct recursion because the browser will not update the visible buffer until the function instances have completely finished execution.
	window.requestAnimationFrame(Draw_And_Animate_Cube);
};

/*=================================== Automatic Canvas Sizing ===================================*/

// My attempt at keeping as much of the canvas visible while adjusting the canvas to fill as much of the screen as possible.
function makeCanvasWindowSize()
{// On window resize, maintains aspect ratio while keeping canvas height equal to the window inner height. This should keep the cube in the center of the page within the browser window.
	canvas = document.getElementById("rotating_cube");
	
	// Determines canvas height and width based on the outer width of the browser window and the established aspect ratio of the display window of the browser.
	canvas.height = window.outerHeight;
	canvas.width  = (canvas.height * aspectRatio);
	
	if (canvas.width < window.innerWidth)
	{// If the canvas width becomes less than the window inner width, the window height it set to be equal to the inner height instead of the outer height of the browser.
	 // The canvas is positioned exactly in the center while it's top and bottom overlap the visible area of the browser window.
		canvas.height     = window.innerHeight;
		canvas.width      = (canvas.height * aspectRatio);
		canvas.style.top  = ((-1 * ((canvas.height - window.innerHeight) / 2)) + "px");
		canvas.style.left = ((-1 * ((canvas.width - window.innerWidth) / 2)) + "px");
	}
	else
	{// If the canvas width is greater than or equal to the inner width of the browser, the height of the canvas is set equal to the outer height of the browser window, and it is centered allowing a portion of the top and bottom to overlap the visible area.
		canvas.style.top  = ((-1 * ((canvas.height - window.innerHeight) / 2)) + "px");
		canvas.style.left = ((-1 * ((canvas.width - window.innerWidth) / 2)) + "px");
	}
	
	//Adjusts the left/right bound area based on the width of the canvas so the cube always stays in the visible area even if the window resizes.
	// I couldn't really get it to work the way I wanted it to by the time the assignment was due.
	// The canvas width can at times be greater than the inner width of the browser viewing area. The cube can go off-screen if the window's width is small enough relative to it's height.
	lr_bound = (ud_bound * (canvas.width / canvas.height));
	setLRAmount(document.getElementById("fbz-rng").value, document.getElementById("lr-rng").value);
}

window.addEventListener("resize", function(event){
	makeCanvasWindowSize();
});
