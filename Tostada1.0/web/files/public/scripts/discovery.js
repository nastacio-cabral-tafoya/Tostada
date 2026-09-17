var row           = 0;
var max_col_width = new Array(0);

function output_title(data)
{
	let generated_row = "<tr class='title-row'>";
	let col           = 0;
	
	for (let key in data)
	{
		generated_row += ("<td class='table-cell' id='col-" + intToString(col, 0) + "'><div class='col-" + intToString(col, 0) + "'>" + key + "</div></td>");
		col++;
		max_col_width.push(0);
	}
	
	generated_row += "</tr>";
	
	document.getElementById("title-table").innerHTML = generated_row;
}

function output_data(data)
{
	let className = "table-row-odd";
	let col    = 0;
	
	if ((row % 2) === 0)
	{
		if (row === 0)
		{
			output_title(data);
		}
		
		className = "table-row-even"
	}
	
	let generated_row = ("<tr class='table-row " + className + "'>");
	
	for (let key in data)
	{
		if (key === "IP Address")
		{
			generated_row += ("<td class='table-cell'><div class='col-" + intToString(col, 0) + "'>" + data[key] + "</div></td>");
		}
		else if (key === "MAC Address")
		{
			generated_row += ("<td class='table-cell'><div class='col-" + intToString(col, 0) + "'>" + format_mac_address(data[key]) + "</div></td>");
		}
		else
		{
			generated_row += ("<td class='table-cell'><div class='col-" + intToString(col, 0) + "'>" + hexToASCII(data[key]) + "</div></td>");
		}
		
		col++;
	}
	
	generated_row += "</tr>";
	
	document.getElementById("data-table").innerHTML += generated_row;
	
	row++;
}

function standard_discover()
{
	let input_data = [document.getElementById("discovery-network-textbox").value, document.getElementById("discovery-subnet-textbox").value];
	let errors     = false;
	
	for (let i = 0; i < input_data.length; i++)
	{
		if (isblank(input_data[i]))
		{
			set_textbox_errorlevel(textboxes[i], 2);
			errors = true;
		}
	}
	
	if (!errors)
	{
		document.getElementById("discovered").innerHTML = "";
		discover(ip_range(ip_dec_to_binary(input_data[0]), ip_dec_to_binary(input_data[1])));
	}
}

function cdir_discover()
{
	let input_data = document.getElementById("discovery-addressrange-textbox").value;
	
	if (isblank(input_data))
	{
		set_textbox_errorlevel(textboxes[i], 2);
	}
	else
	{
		let ip_data = split(input_data, '/');
		document.getElementById("discovery-network-textbox").value = ip_data[0];
		document.getElementById("discovery-subnet-textbox").value  = cdir_to_subnetmask(strToInt(ip_data[1]));
		
		document.getElementById("data-table").innerHTML = "";
		discover(ip_range(ip_dec_to_binary(ip_data[0]), ip_dec_to_binary(cdir_to_subnetmask(strToInt(ip_data[1])))));
	}
}

async function discover(ip_list)
{
	for (let i = 0; i < ip_list.length; i++)
	{
		await post("discover", {"ip":ip_list[i], "username":document.getElementById("gpen-username-textbox").value, "password":document.getElementById("gpen-password-textbox").value}, false);
		
		for (let k = 0; k < max_col_width.length; k++)
		{
			let col   = document.getElementsByClassName("col-" + intToString(k, 0));
			let width = "auto";
			
			for (let j = 0; j < col.length; j++)
			{
				if (col[j].offsetWidth > max_col_width[k])
				{
					max_col_width[k] = col[j].offsetWidth;
				}
			}
			
			for (let j = 0; j < col.length; j++)
			{
				col[j].style.width = (intToString(max_col_width[k], 0) + "px");
			}
		}
		
		await sleep(250);
	}
}

function cdir_to_subnetmask(cdir)
{
	let subnetmask = "";
	
	for (let i = 0; i < cdir; i++)
	{
		subnetmask += '1';
	}
	
	while (subnetmask.length < 32)
	{
		subnetmask += '0';
	}
	
	return (ip_binary_to_dec(insert_ip_dots(subnetmask)));
}

function ip_range(network, subnet)
{
	let net  = "";
	let low  = "";
	let high = "";
	
	for (let i = 0; i < subnet.length; i++)
	{
		if (subnet[i] === '0')
		{
			low  += network[i];
			high += '1';
		}
		else
		{
			net += network[i];
		}
	}
	
	low  = parseInt(low, 2);
	high = parseInt(high, 2);
	
	let retVal = new Array(0);
	
	for (let i = (low + 1); i < high; i++)
	{
		retVal.push(ip_binary_to_dec(insert_ip_dots(net + makeLength_preceding(i.toString(2), '0', (32 - net.length)))));
	}
	
	return (retVal);
}

function insert_ip_dots(ip)
{
	let retVal = "";
	
	for (let i = 0; i < ip.length; i++)
	{
		if (((i % 8) === 0) && (retVal.length > 0))
		{
			retVal += ('.' + ip[i]);
		}
		else
		{
			retVal += ip[i];
		}
	}
	
	return (retVal);
}

function ip_binary_to_dec(ip)
{
	let retVal = "";
	let octets = split(ip, '.');
	
	for (let i = 0; i < octets.length; i++)
	{
		if (retVal.length > 0)
		{
			retVal += '.';
		}
		
		retVal += parseInt(octets[i], 2);
	}
	
	return (retVal);
}

function ip_dec_to_binary(ip)
{
	let retVal = "";
	let octets = split(ip, '.');
	
	for (let i = 0; i < octets.length; i++)
	{
		retVal += makeLength_preceding(strToInt(octets[i]).toString(2), '0', 8);
	}
	
	return (retVal);
}

function change_discovery_form()
{
	let selected_form = document.getElementById("methodselect-selectbox");
	
	for (let i = 0; i < selected_form.length; i++)
	{
		if (selected_form[i].value === selected_form.value)
		{
			document.getElementById(selected_form[i].value + "-fields").classList.remove("hidden");
			document.getElementById(selected_form[i].value + "-fields").classList.add("visible");
		}
		else
		{
			document.getElementById(selected_form[i].value + "-fields").classList.remove("visible");
			document.getElementById(selected_form[i].value + "-fields").classList.add("hidden");
		}
	}
}

var textboxes = document.getElementsByClassName("textbox");

for (let i = 0; i < textboxes.length; i++)
{
	textboxes[i].addEventListener("focusout", function(){
		if (!isblank(textboxes[i].value))
		{
			set_textbox_errorlevel(textboxes[i], 0);
		}
		else
		{
			set_textbox_errorlevel(textboxes[i], 2);
		}
	}, false);
}