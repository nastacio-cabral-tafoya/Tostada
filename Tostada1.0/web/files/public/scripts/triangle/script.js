var vertexShaderText = [
	"precision mediump float;",
	"",
	"attribute vec2 vertPosition;",
	"attribute vec3 vertColor;",
	"varying   vec3 fragColor;",
	"",
	"void main()",
	"{",
	"   fragColor   = vertColor;",
	"   gl_Position = vec4(vertPosition, 0.0, 1.0);",
	"}"
].join('\n');

var fragmentShaderText = [
	"precision mediump float;",
	"",
	"varying vec3 fragColor;",
	"",
	"void main()",
	"{ ",
	"   //gl_FragColor = vec4(1.0, 0.0, 0.0 , 1.0);", // Draws a solid triangle color.
	"   gl_FragColor = vec4(fragColor , 1.0);",       // Draws varying colors wich each vertex being a specified color from the triangle vertecies.
	"}"
].join('\n');

var InitDemo = function(){
	// Initializes canvas object, and gl context for the canvas object.
	var canvas = document.getElementById("triangle-scene");
	var gl     = canvas.getContext("webgl");
	
	// If 'webgl' context does not work, it defaults to 'experimental-webgl'.
	if (!gl)
	{
		gl = canvas.getContext("experimental-webgl");
	}
	
	//If 'experimental-webgl' does not work either, the browser is old and not worth using.
	if (!gl)
	{
		alert("Your browser sucks.");
	}
	
	// Sets Canvas Background Color
	gl.clearColor(0.72, 0.85, 0.82, 1.0);
	gl.clear(gl.COLOR_BUFFER_BIT | gl.DEPTH_BUFFER_BIT);
	
	// Creating shaders.
	var vertexShader   = gl.createShader(gl.VERTEX_SHADER);
	var fragmentShader = gl.createShader(gl.FRAGMENT_SHADER);
	
	gl.shaderSource(vertexShader, vertexShaderText);
	gl.shaderSource(fragmentShader, fragmentShaderText);
	
	// Compiles vertex shader.
	gl.compileShader(vertexShader);
	
	if (!gl.getShaderParameter(vertexShader, gl.COMPILE_STATUS))
	{// Checks for errors compiling vertex shader.
		console.error("ERROR compiling vertex shader!", gl.getShaderInfoLog(vertexShader));
		return;
	}
	
	//Compiles fragment shader.
	gl.compileShader(fragmentShader);
	
	if (!gl.getShaderParameter(fragmentShader, gl.COMPILE_STATUS))
	{// Checks for errors compiling fragment shader.
		console.error("ERROR compiling fragment shader!", gl.getShaderInfoLog(fragmentShader));
		return;
	}
	
	// Attaches the vertex shader and the fragment shader to the gl program.
	var program = gl.createProgram();
	gl.attachShader(program, vertexShader);
	gl.attachShader(program, fragmentShader);
	gl.linkProgram(program);
	
	if (!gl.getProgramParameter(program, gl.LINK_STATUS))
	{// Checks for program linking errors.
		console.error("ERROR linking program.", gl.getProgramInfoLog(program));
		return;
	}
	
	gl.validateProgram(program);
	
	if (!gl.getProgramParameter(program, gl.VALIDATE_STATUS))
	{
		console.error("ERROR validating program!", gl.getProgramInfoLog(program));
		return;
	}
	
	// This is sitting on CPU memory, the graphics card has no idea what is here.
	// Create Buffer
	// We are setting all the inforamtion the graphics card is going to be using.
	// new Float32Array() needs to be used to conver the float numbers in the triangle verticies to 32 bit numbers.
	var triangleVerticies =
	[// x, y         R, G, B
		0.0, 0.75,    0.0, 1.0, 0.0,
		-0.75, -0.75,  1.0, 0.0, 0.0,
		0.75, -0.75,   0.0, 0.0, 1.0
	];
	
	// Passing the triangle vertecies from the RAM to the graphics card.
	var triangleVertexBufferObject = gl.createBuffer();
	gl.bindBuffer(gl.ARRAY_BUFFER, triangleVertexBufferObject);
	gl.bufferData(gl.ARRAY_BUFFER, new Float32Array(triangleVerticies), gl.STATIC_DRAW);
	
	var positionAttributeLocation = gl.getAttribLocation(program, "vertPosition");
	var colorAttributeLocation    = gl.getAttribLocation(program, "vertColor");
	
	let vertexSize        = 5;
	let colorElementCount = 3;
	
	gl.vertexAttribPointer(
		positionAttributeLocation,                     // Attribute Location
		2,                                             // Number of elements per attribute.
		gl.FLOAT,                                      // Type of elements.
		gl.FALSE,
		(vertexSize * Float32Array.BYTES_PER_ELEMENT), // Size of an individual vertex.
		0                                              // Offset from the beginning of a single vertex to this attribute.
	);
	
	gl.vertexAttribPointer(
		colorAttributeLocation,                     // Attribute Location
		colorElementCount,                             // Number of elements per attribute.
		gl.FLOAT,                                      // Type of elements.
		gl.FALSE,
		(vertexSize * Float32Array.BYTES_PER_ELEMENT), // Size of an individual vertex.
		2 * Float32Array.BYTES_PER_ELEMENT             // Offset from the beginning of a single vertex to this attribute.
	); 
	
	gl.enableVertexAttribArray(positionAttributeLocation);
	gl.enableVertexAttribArray(colorAttributeLocation);
	
	//
	// Main Render Loop
	// gl.TRIANGLES says we are going to be drawing triangles.
	gl.useProgram(program);
	// gl.drawArrays(Drawing in Triangles, Number of Vertecies to Skip, Number of Vertecies);
	gl.drawArrays(gl.TRIANGLES, 0, 3);
};
