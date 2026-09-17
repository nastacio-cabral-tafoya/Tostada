starting_mouse_position        = null;
new_position                   = 0;
mouse_down_left_center_spacer  = false;
mouse_down_center_right_spacer = false;
mouse_down_body_bottom_spacer  = false;

document.getElementById("left-center-spacer").addEventListener("mousedown", function(e) {
	e.preventDefault();
	
	starting_mouse_position       = e.pageX;
	mouse_down_left_center_spacer = true;
}, false);

document.getElementById("center-right-spacer").addEventListener("mousedown", function(e) {
	e.preventDefault();
	
	starting_mouse_position        = e.pageX;
	mouse_down_center_right_spacer = true;
}, false);

document.getElementById("bottom-body-spacer").addEventListener("mousedown", function(e) {
	e.preventDefault();
	
	new_position = 1;
	starting_mouse_position        = e.pageY;
	mouse_down_body_bottom_spacer  = true;
}, false);

window.addEventListener("mouseup", function(e) {
	e.preventDefault();
	
	if (mouse_down_left_center_spacer)
	{
		document.querySelector(":root").style.setProperty("--left-pane-width", ((strToInt(getComputedStyle(document.querySelector(":root")).getPropertyValue("--left-pane-width")) + new_position) + "px"));
	}
	else if (mouse_down_center_right_spacer)
	{
		document.querySelector(":root").style.setProperty("--right-pane-width", ((strToInt(getComputedStyle(document.querySelector(":root")).getPropertyValue("--right-pane-width")) + new_position) + "px"));
	}
	else if (mouse_down_body_bottom_spacer)
	{
		document.querySelector(":root").style.setProperty("--footer-height", ((strToInt(getComputedStyle(document.querySelector(":root")).getPropertyValue("--footer-height")) + new_position) + "px"));
	}
	
	mouse_down_left_center_spacer  = false;
	mouse_down_center_right_spacer = false;
	mouse_down_body_bottom_spacer  = false;
	starting_mouse_position        = null;
	new_position                   = 0;
	
	hide("phantom-vertical-spacer");
	hide("phantom-horizontal-spacer");
}, false);

window.addEventListener("mousemove", function(e) {
	e.preventDefault();
	
	if (mouse_down_left_center_spacer && ((document.getElementById("dashboard-center-pane").clientWidth - (e.pageX - starting_mouse_position)) > 0))
	{
		show("phantom-vertical-spacer");
		document.getElementById("phantom-vertical-spacer").style.left = (e.pageX + "px");
		new_position = (e.pageX - starting_mouse_position);
	}
	else if (mouse_down_center_right_spacer && ((document.getElementById("dashboard-center-pane").clientWidth - (starting_mouse_position - e.pageX)) > 0))
	{
		show("phantom-vertical-spacer");
		document.getElementById("phantom-vertical-spacer").style.left = (e.pageX + "px");
		new_position = (starting_mouse_position - e.pageX);
	}
	else if (mouse_down_body_bottom_spacer && ((document.getElementById("dashboard-footer").clientHeight + new_position) > 0) && ((document.getElementById("dashboard-body").clientHeight - (starting_mouse_position - e.pageY)) > 0))
	{
		show("phantom-horizontal-spacer");
		document.getElementById("phantom-horizontal-spacer").style.top = (e.pageY + "px");
		new_position = (starting_mouse_position - e.pageY);
	}
}, false);