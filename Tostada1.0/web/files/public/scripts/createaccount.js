function show_errors(data)
{
	for (name in data)
	{
		set_textbox_errorlevel(document.getElementById(name + "-textbox"), 3)
	}
}

document.getElementById("dob-textbox").addEventListener("keypress", function(e){
    e = e || window.event;
    
    console.log(e.keyCode);
    
    if ((e.keyCode < 48) || (e.keyCode > 57))
    {
        e.preventDefault();
    }
    else
    {
        switch(document.getElementById("dob-textbox").value.length)
        {
            case 2:
            case 5:
                document.getElementById("dob-textbox").value += '/';
                break;
        }
    }
}, false);