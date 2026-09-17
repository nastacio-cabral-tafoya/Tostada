function set_textbox_error_levels(textbox)
{
    if (!isblank(textbox.value))
	{
	    if (textbox.id === "dob-textbox")
	    {
	        if (/[0-9]{2}\/[0-9]{2}\/[0-9]{4}/.test(textbox.value))
		    {
		        set_textbox_errorlevel(textbox, 0);
		        return (false);
		    }
		    else
		    {
		        set_textbox_errorlevel(textbox, 2);
		        return (true);
		    }
	    }
	    else if (textbox.id === "confirmpassword-textbox")
	    {
	        if (textbox.value === document.getElementById("password-textbox").value)
	        {
	            set_textbox_errorlevel(document.getElementById("password-textbox"), 0);
		        set_textbox_errorlevel(textbox, 0);
		        return (false);
	        }
	        else
	        {
	            set_textbox_errorlevel(document.getElementById("password-textbox"), 2);
	            set_textbox_errorlevel(textbox, 2);
		        return (true);
	        }
	    }
	    else
	    {
	        set_textbox_errorlevel(textbox, 0);
		    return (false);
	    }
	}
	else
	{
		set_textbox_errorlevel(textbox, 2);
		return (true);
	}
}

function set_selectbox_error_levels(selectbox)
{
    if (!isblank(selectbox.value))
	{
		set_selectbox_errorlevel(selectbox, 0);
		return (false);
	}
	else
	{
		set_selectbox_errorlevel(selectbox, 2);
		return (true);
	}
}

//==========================================================//
var textboxes = document.getElementsByClassName("textbox"); //
                                                            //
for (let i = 0; i < textboxes.length; i++)                  //
{                                                           //
	textboxes[i].addEventListener("focusout", function(){   //
		set_textbox_error_levels(textboxes[i]);              //
	}, false);                                              //
}                                                           //
//==========================================================//

//==========================================================//
var selectboxes = document.getElementsByClassName("selectbox"); //
                                                            //
for (let i = 0; i < textboxes.length; i++)                  //
{                                                           //
	selectboxes[i].addEventListener("focusout", function(){   //
		set_selectbox_error_levels(selectboxes[i]);              //
	}, false);                                              //
}                                                           //
//==========================================================//

function submit_data(method, path)
{
	let textboxes       = document.getElementsByClassName("textbox");
	let selectboxes     = document.getElementsByClassName("selectbox");
	let data            = {};
	let errors          = false;
	
	show_loader();
	
	for (let i = 0; i < textboxes.length; i++)
	{
		console.log(window.getComputedStyle(textboxes[i]).visibility);
		if (window.getComputedStyle(textboxes[i]).visibility !== "hidden")
		{
			data[textboxes[i].name] = [textboxes[i].value, textboxes[i].id]
			
			if (set_textbox_error_levels(textboxes[i]))
			{
			    errors = true;
			}
		}
	}
	
	for (let i = 0; i < selectboxes.length; i++)
	{
		console.log(window.getComputedStyle(selectboxes[i]).visibility);
		if (window.getComputedStyle(selectboxes[i]).visibility !== "hidden")
		{
		    data[selectboxes[i].name] = [selectboxes[i].value, selectboxes[i].id]
			
			if (set_selectbox_error_levels(selectboxes[i]))
			{
			    errors = true;
			}
		}
	}
	
	if (errors)
	{
		page_alert(("One or more of the required fields were filled out incorrectly.\n\nPlease check your entries and try again."), "Okay", function(){
			confirm_alert();
		})
		return;
	}
	
	if (method === "post")
	{
        post(path, data, true);
	}
	else if (method === "put")
	{
	    put(path, data, true);
	}
}

function post(path, data, showLoader)
{
	if (showLoader)
	{
		show_loader();
	}
	
	var xhr = new XMLHttpRequest();
	
	xhr.onreadystatechange = function()
	{
		if (xhr.readyState === 4)
		{
		    console.log(xhr.response)
			let response = JSON.parse(xhr.response);
			
			switch(response.stat)
			{
				case 0:
					location.reload();
					break;
				case 1:
					hide_loader();
					
					page_alert(("Error: " + response.msg), "Okay", function(){
						confirm_alert()
					})
					break;
				case 2:
					hide_loader();
					
					for (let i = 0; i < response.incorrect_fields.length; i++)
					{
						set_textbox_errorlevel(document.getElementById(response.incorrect_fields[i]), response.stat);
					}
					
					page_alert(response.msg, "Okay", function(){
						confirm_alert()
					});
					break;
				case 4:
					hide_loader();
					
					if (response.gpenresponse != null)
					{
						output_data(response.gpenresponse);
					}
					break;
				case 5:
					hide_loader();
					
					page_alert(response.msg, "Okay", function(){
						confirm_alert();
						location.reload();
					});
					break;
				case 6:
					hide_loader();
					
					page_alert(response.msg, "Okay", function(){
						confirm_alert();
						window.location.href = "/login";
					});
					break;
				case 7:
					hide_loader();
					
					if (response.newaccresponse != null)
					{
						show_errors(response.newaccresponse);
					}
					
					page_alert(("Error: " + response.msg), "Okay", function(){
						confirm_alert()
					})
					break;
				case 8:
					hide_loader();
				    
				    outPutLog(response.log);
				    break;
				case 9:
					hide_loader();
					
					outPutLogEntry(response.logentry);
				    break;
			}
		}
		
		waiting = false;
	};
	
	xhr.open("POST", path, true);
	xhr.setRequestHeader("Content-Type", "application/json");
	xhr.send("data=" + JSON.stringify(data));
}

function put(path, data, showLoader)
{
	if (showLoader)
	{
		show_loader();
	}
	
	var xhr = new XMLHttpRequest();
	
	xhr.onreadystatechange = function()
	{
		if (xhr.readyState === 4)
		{
		    console.log(xhr.response)
			let response = JSON.parse(xhr.response);
			
			handle_response(response);
		}
		
		waiting = false;
	};
	
	xhr.open("PUT", path, true);
	xhr.setRequestHeader("Content-Type", "application/json");
	xhr.send("data=" + JSON.stringify(data));
}

function handle_response(response)
{
    switch(response.stat)
	{
    	case 0:
    		location.reload();
    		break;
    	case 1:
    		hide_loader();
    		
    		page_alert(("Error: " + response.msg), "Okay", function(){
    			confirm_alert()
    		})
    		break;
    	case 2:
    		hide_loader();
    		
    		for (let i = 0; i < response.incorrect_fields.length; i++)
    		{
    			set_textbox_errorlevel(document.getElementById(response.incorrect_fields[i]), response.stat);
    		}
    		
    		page_alert(response.msg, "Okay", function(){
    			confirm_alert()
    		});
    		break;
    	case 4:
    		hide_loader();
    		
    		if (response.gpenresponse != null)
    		{
    			output_data(response.gpenresponse);
    		}
    		break;
    	case 5:
    		hide_loader();
    		
    		page_alert(response.msg, "Okay", function(){
    			confirm_alert();
    			location.reload();
    		});
    		break;
    	case 6:
    		hide_loader();
    		
    		page_alert(response.msg, "Okay", function(){
    			confirm_alert();
    			window.location.href = "/login";
    		});
    		break;
    	case 7:
    		hide_loader();
    		
    		if (response.newaccresponse != null)
    		{
    			show_errors(response.newaccresponse);
    		}
    		
    		page_alert(("Error: " + response.msg), "Okay", function(){
    			confirm_alert()
    		})
    		break;
    	case 8:
    		hide_loader();
    	    
    	    outPutLog(response.log);
    	    break;
    	case 9:
    		hide_loader();
    		
    		outPutLogEntry(response.logentry);
    	    break;
	}
}

function show_loader()
{
	let hidden_elements = document.getElementsByClassName("hidden");
	let incrementation  = 0;
	
	while ((hidden_elements.length > 0) && (incrementation < hidden_elements.length))
	{
		let hidden_element = document.getElementById(hidden_elements[incrementation].id);
		
		if (!hidden_element.classList.contains("interchangable-fields") && !hidden_element.classList.contains("phantom-spacer") && !hidden_element.classList.contains("alert-container"))
		{
			hidden_element.classList.remove("hidden");
			hidden_element.classList.add("visible");
		}
		else
		{
			incrementation++;
		}
	}
}

function hide_loader()
{
	let visible_elements = document.getElementsByClassName("visible");
	let incrementation   = 0;
	
	while ((visible_elements.length > 0) && (incrementation < visible_elements.length))
	{
		let visible_element = document.getElementById(visible_elements[incrementation].id);
		
		if (!visible_element.classList.contains("interchangable-fields") && !visible_element.classList.contains("phantom-spacer") && !visible_element.classList.contains("alert-container"))
		{
			visible_element.classList.remove("visible");
			visible_element.classList.add("hidden");
		}
		else
		{
			incrementation++;
		}
	}
}

function show(id)
{
	document.getElementById(id).classList.remove("hidden");
	document.getElementById(id).classList.add("visible");
}

function hide(id)
{
	document.getElementById(id).classList.remove("visible");
	document.getElementById(id).classList.add("hidden");
}

function set_textbox_errorlevel(textbox, number)
{
	switch(number)
	{
		case 0:
			textbox.classList.remove("textbox-no-status");
			textbox.classList.remove("textbox-error");
			textbox.classList.add("textbox-no-error");
			break;
		case 1:
			textbox.classList.remove("textbox-error");
			textbox.classList.remove("textbox-no-error");
			textbox.classList.add("textbox-no-status");
			break;
		case 2:
			textbox.classList.remove("textbox-no-status");
			textbox.classList.remove("textbox-no-error");
			textbox.classList.add("textbox-error");
			break;
	}
}

function set_selectbox_errorlevel(selectbox, number)
{
    switch(number)
	{
		case 0:
			selectbox.classList.remove("selectbox-no-status");
			selectbox.classList.remove("selectbox-error");
			selectbox.classList.add("selectbox-no-error");
			break;
		case 1:
			selectbox.classList.remove("selectbox-error");
			selectbox.classList.remove("selectbox-no-error");
			selectbox.classList.add("selectbox-no-status");
			break;
		case 2:
			selectbox.classList.remove("selectbox-no-status");
			selectbox.classList.remove("selectbox-no-error");
			selectbox.classList.add("selectbox-error");
			break;
	}
}

function textbox_onfocusout_event(e)
{
	alert(JSON.stringify(e));
}

function extend_session()
{
	post("renewsession", {}, false);
	timein = 0;
}

function page_alert(message, button_label, button_action)
{
	show("disabling-overlay");
	show("alert-box");
	
	document.getElementById("alert-message").innerHTML = message;
	document.getElementById("alert-okay-button").value = button_label;
	document.getElementById("alert-okay-button").onclick = button_action;
}

function confirm_alert()
{
	hide("alert-box");
	hide("disabling-overlay");
	
	document.getElementById("alert-message").innerHTML = "";
	document.getElementById("alert-okay-button").value = "";
	document.getElementById("alert-okay-button").onclick = null;
	hide_loader();
	
}

function session_timeout(timeout)
{
	let alert_box = document.getElementById("alert-box");
	
	if ((timeout <= 30) && (timeout > 0))
	{
		page_alert("Session is about to expire in <span style=\"font-size: 150%; color: red;\">" + intToString(timeout) + "</span> seconds.", "Renew Session", function(){
			extend_session();
		});
	}
	else if (timeout === 0)
	{
		window.location.reload();
	}
}


/*
========================================================================
							GENERAL FUNCTIONS
========================================================================
*/
baseChars = {"0":0, "1":1, "2":2, "3":3, "4":4, "5":5, "6":6, "7":7, "8":8, "9":9, "A":10, "B":11, "C":12, "D":13, "E":14, "F":15};

function clip_string(string, from, to)
{
	retVal = "";
	
	for (let i = from; (i < string.length) && (i <= to); i++)
	{
		retVal += string[i];
	}
	
	return (retVal);
}

function clip_string(string, from)
{
	retVal = "";
	
	for (let i = from; (i < string.length); i++)
	{
		retVal += string[i];
	}
	
	return (retVal);
}

function baseToDec(string, base)
{
	if (string.length == 0)
	{
		return (0);
	}
    else
	{
        return(baseChars[string[0]] * (base ** (string.length - 1)) + baseToDec(clip_string(string, 1), base));
	}
}

function hexToASCII(hex_string)
{
    retVal = ""
    holder = ""
    
	for (let i = 0; i < hex_string.length; i++)
	{
		holder += hex_string[i];
		
		if (holder.length == 2)
		{
			retVal += String.fromCharCode(baseToDec(holder.toUpperCase(), 16));
			holder  = "";
		}
	}
	
    return (retVal);
}

function format_mac_address(mac_string)
{
	let retVal = "";
	
	for (let i = 0; i < mac_string.length; i++)
	{
		if (((i % 2) === 0) && (i > 0))
		{
			retVal += ":";
		}
		
		retVal += mac_string[i];
	}
	
	return (retVal.toUpperCase());
}

function sleep(ms)
{
	return new Promise(resolve => setTimeout(resolve, ms));
}

function makeLength_preceding(string, filler_char, length)
{
	let retVal = string;
	
	while (retVal.length < length)
	{
		retVal = (filler_char + retVal);
	}
	
	return (retVal);
}

function makeLength_proceeding(string, filler_char)
{
	let retVal = string;
	
	while (retVal.length < length)
	{
		retVal += filler_char;
	}
	
	return (retVal);
}

function split(string, delimiter)
{
	let retVal = new Array(0);
	let holder = "";
	
	for (let i = 0; i < string.length; i++)
	{
		if (string[i] === delimiter)
		{
			retVal.push(holder);
			holder = "";
		}
		else
		{
			holder += string[i];
		}
	}
	
	retVal.push(holder);
	
	return (retVal);
}

function isblank(string)
{
	for (let i = 0; i < string.length; i++)
	{
		if ((string.charCodeAt(i) > 32) && (string.charCodeAt(i) < 127))
		{
			return (false);
		}
	}
	
	return (true);
}

function search(toSearch, from)
{
	for(let i = 0; (i < from.length) && (from.length >= toSearch.length); i++)
	{
		var tempString = "";

		for(let j = i; ((j - i) < toSearch.length) && (j < from.length); j++)
		{
			tempString += from[j];
		}

		if(tempString.toUpperCase() === toSearch.toUpperCase())
		{
			return true;
		}
	}

	return (false);
}

function power(base, exp)
{
	var retVal = 1;

	for(let i = 0; (i < exp); i++)
	{
		retVal *= base;
	}

	return (retVal);
}

function logarithm(base, number)
{
	var retVal = 0;

	while((number|0) > (base - 1))
	{
		number = ((number|0) / base);
		retVal++;
	}
	
	return (retVal);
}

function intToString(number, decimalPlaces)
{
	var retVal = "";

	if(number !== undefined)
	{
		if(number.length === undefined)
		{
			if(number < 0)
			{
				number *= -1;
				retVal += "-";
			}

			let integerComponent    = (number|0);
			let fractionalComponent = (number - integerComponent);
			let numLength           = (logarithm(10, integerComponent) + 1);
			let quotent             = (integerComponent / power(10, (numLength)));

			for(let i = 0; (i < numLength); i++)
			{
				let product = (quotent.toPrecision(numLength) * 10);
				retVal      += intToChar((product|0) + 48);
				quotent     = (product.toPrecision(numLength) - (product|0));
			}

			if(decimalPlaces > 0)
			{
				retVal += '.';

				for(let i = 0; (i < decimalPlaces); i++)
				{
					let product         = (fractionalComponent.toPrecision(decimalPlaces) * 10);
					retVal              += intToChar((product|0) + 48);
					fractionalComponent = (product.toPrecision(decimalPlaces) - (product|0));
				}
			}
		}
		else
		{
			retVal = number;
		}
	}
	else
	{
		retVal = "";
	}

	return (retVal);
}

function strToInt(str)
{
	var retVal = 0;

	if(str.length > 0)
	{
		let decimalLocation = 0;
		let filteredString  = "";

		for(let i = 0; (i < str.length); i++)
		{
			if(((str[i].charCodeAt() >= 48) && (str[i].charCodeAt() <= 57)) || (str[i] === '.'))
			{
				filteredString += str[i];
			}
		}

		let noDecimalString = "";

		for(let i = 0; (i < filteredString.length); i++)
		{
			if(filteredString[i] === '.')
			{
				decimalLocation = ((filteredString.length - 1) - i);
			}
			else if((filteredString[i].charCodeAt() >= 48) && (filteredString[i].charCodeAt() <= 57))
			{
				noDecimalString += filteredString[i];
			}
		}

		let place = (noDecimalString.length - 1);

		for(let i = 0; (i < noDecimalString.length); i++)
		{
			retVal += ((noDecimalString[i].charCodeAt() - 48) * power(10, place));
			place--;
		}

		retVal = (retVal / power(10, decimalLocation));

		if(str[0] === '-')
		{
			retVal *= -1;
		}
	}
	else
	{
		retVal = str; 
	}

	return (retVal);
}

function intToChar(ch)
{
	switch(ch)
	{
		case 48:
			return '0';
		case 49:
			return '1';
		case 50:
			return '2';
		case 51:
			return '3';
		case 52:
			return '4';
		case 53:
			return '5';
		case 54:
			return '6';
		case 55:
			return '7';
		case 56:
			return '8';
		case 57:
			return '9';
		case 65:
			return 'A';
		case 66:
			return 'B';
		case 67:
			return 'C';
		case 68:
			return 'D';
		case 69:
			return 'E';
		case 70:
			return 'F';
		case 71:
			return 'G';
		case 72:
			return 'H';
		case 73:
			return 'I';
		case 74:
			return 'J';
		case 75:
			return 'K';
		case 76:
			return 'L';
		case 77:
			return 'M';
		case 78:
			return 'N';
		case 79:
			return 'O';
		case 80:
			return 'P';
		case 81:
			return 'Q';
		case 82:
			return 'R';
		case 83:
			return 'S';
		case 84:
			return 'T';
		case 85:
			return 'U';
		case 86:
			return 'V';
		case 87:
			return 'W';
		case 88:
			return 'X';
		case 89:
			return 'Y';
		case 90:
			return 'Z';
	}

	return (null);
}

function a1ToInt(a1Notation)
{
	var row                = "";
	var col                = "";
	var filteredA1Notation = "";

	a1Notation = a1Notation.toUpperCase();

	for(var i = 0; i < a1Notation.length; i++)
	{
		if((a1Notation[i].charCodeAt() >= 65) && (a1Notation[i].charCodeAt() <= 90))
		{
			col += a1Notation[i];
		}
		else if((a1Notation[i].charCodeAt() >= 48) && (a1Notation[i].charCodeAt() <= 57))
		{
			row += a1Notation[i];
		}
	}

	if(row.length === 0)
	{
		row = "1";
	}

	var retVal = {};
	retVal.row = strToInt(row);
	retVal.col = 0;

	var length = (col.length - 1);

	for(var i = 0; i < col.length; i++)
	{
		retVal.col += ((col.charCodeAt(i) - 64) * power(26, length));
		length--;
	}

	return (retVal);
}

function intToA1(row, col)
{
	var retVal = "";

	while(col > 0)
	{
		var remainder = ((col - 1) % 26);
		retVal        = (intToChar(remainder + 65) + retVal);
		col           = (((col - remainder) - 1) / 26);
	}

	retVal += intToString(row, 0);

	return (retVal);
}

function daysInMonth(month, year)
{
	switch(month)
	{
		case 1://February
			if(isLeapYear(year))
			{
				return 29;
			}
			
			return 28;
		case 0://January
		case 2://March
		case 4://May
		case 6://July
		case 7://August
		case 9://October
		case 11://December
			return 31;
		case 3://April
		case 5://June
		case 8://September
		case 10://November
			return 30;
	}
}

function isLeapYear(year)
{
	if((year % 4) === 0)
	{
		if((year % 100) !== 0)
		{
			return (true);
		}
		else
		{
			if((year % 400) === 0)
			{
				return (true);
			}
		}
	}

	return false;
}

function getWeekDayName(day)
{
	switch(day)
	{
		case 0:
			return "Sunday";
		case 1:
			return "Monday";
		case 2:
			return "Tuesday";
		case 3:
			return "Wednesday";
		case 4:
			return "Thursday";
		case 5:
			return "Friday";
		case 6:
			return "Saturday";
	}
}

function getMonthName(month)
{
	switch(month)
	{
		case 0:
			return "January";
		case 1:
			return "February";
		case 2:
			return "March";
		case 3:
			return "April";
		case 4:
			return "May";
		case 5:
			return "June";
		case 6:
			return "July";
		case 7:
			return "August";
		case 8:
			return "September";
		case 9:
			return "October";
		case 10:
			return "November";
		case 11:
			return "December";
	}
}

function getPostFix(number)
{
	var str_num = makeDoubleDigit(intToString(number, 0));

	if(strToInt(str_num[str_num.length - 2]) !== 1)
	{
		switch(strToInt(str_num[str_num.length - 1]))
		{
			case 1:
				return "st";
			case 2:
				return "nd";
			case 3:
				return "rd";
		}
	}

	return "th";
}

function twentyfour_to_twelve(hour)
{
	if(hour > 11)
	{
		return (hour - 12);
	}
	else if(hour === 0)
	{
		return (12);
	}

	return (hour);
}

function twelve_to_twentyfour(hour, ampm)
{
	if(ampm === "AM")
	{
		if(hour > 11)
		{
			return (hour - 12);
		}
		else
		{
			return hour; 
		}
	}
	else if(ampm === "PM")
	{
		if(hour > 11)
		{
			return hour;
		}
		else
		{
			return (hour + 12); 
		}
	}
}

function getDate_month_dd_yyyy(date)
{
	return (getMonthName(date.getMonth()) + " " + intToString(date.getDate(), 0) + getPostFix(date.getDate()) + ", " + intToString(date.getFullYear(), 0));
}

function getDate_mm_dd_yyyy(date)
{
	return (intToString(date.getMonth(), 0) + "/" + intToString(date.getDate(), 0) + "/" + intToString(date.getFullYear(), 0));
}

function makeDoubleDigit(str_num)
{
	if(str_num.length < 2)
	{
		return ("0" + str_num);
	}

	return str_num;
}

function getTime_hh_mm(time)
{
	var hour = "";

	if(time.getHours() > 12)
	{
		hour = (time.getHours() - 12);
	}
	else if(time.getHours() < 1)
	{
		hour = (time.getHours() + 12);
	}
	else
	{
		hour = time.getHours();
	}

	if(time.getHours() > 11)
	{
		return (intToString(hour, 0) + ":" + makeDoubleDigit(intToString(time.getMinutes(), 0)) + " PM");
	}
	else
	{
		return (intToString(hour, 0) + ":" + makeDoubleDigit(intToString(time.getMinutes(), 0)) + " AM");
	}
}