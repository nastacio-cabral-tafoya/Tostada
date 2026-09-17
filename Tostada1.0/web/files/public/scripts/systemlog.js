async function getSysLog(idFrom, idTo, logFileFilter, logFuncFilter, logUserFilter, logStrFilter, sortBy, order)
{
	await post("getsystemlog", {
	    "idfrom":idFrom,
	    "idto":idTo,
	    "logfilefilter":logFileFilter,
	    "logfuncfilter":logFuncFilter,
	    "loguserfilter":logUserFilter,
	    "logstrfilter":logStrFilter,
	    "sortby":sortBy,
	    "order":order
	}, false);
}

function outPutLog(log)
{
    systemLogTable = "";
    
    for (let row = 0; row < log.length; row++)
    {
        if ((row % 2) == 1)
        {
            systemLogTable += "<tr class=\"system-log-row even-log-row\" id=\"log-row-" + row + "\" onmouseup=\"onmouseup_log_row(" + row + ")\">";
        }
        else
        {
            systemLogTable += "<tr class=\"system-log-row\" id=\"log-row-" + row + "\" onmouseup=\"onmouseup_log_row(" + row + ")\">";
        }
        
        for (let col = 0; col < log[row].length; col++)
        {
            systemLogTable += "<td class=\"system-log-col\"><div class=\"system-log-cell\", id=\"log-cell-" + row + ":" + col + "\">" + log[row][col] + "</div></td>";
        }
        
        systemLogTable += "</tr>";
    }
    
    document.getElementById("system-log-table").innerHTML = systemLogTable;
}

async function onmouseup_log_row(index)
{
    let selected_rows = document.getElementsByClassName("selected-log-row");
    
    for (let i = 0; i < selected_rows.length; i++)
    {
        selected_rows[i].classList.remove("selected-log-row");
    }
    
    document.getElementById("log-row-" + index).classList.add("selected-log-row");
    
    await post("systemlogitem", {
	    "id":document.getElementById("log-cell-" + index + ":0").innerHTML
	}, false);
}

function outPutLogEntry(logEntry)
{
    logItemContent = ("Log ID: " + logEntry[0][0] + "<br>Log Date: " + logEntry[0][1] + "<br>Log File: " + logEntry[0][2] + "<br>Log Function: " + logEntry[0][3] + "<br>Log User: " + logEntry[0][4] + "<br>Log Information:<br><p>" + logEntry[0][5] + "</p>");
    
    document.getElementById("dashboard-footer").innerHTML = logItemContent;
}



























