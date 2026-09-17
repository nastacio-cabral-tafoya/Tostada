def queryLog(idFrom, idTo, logFileFilter, logFuncFilter, logUserFilter, logStrFilter, sortBy, order, log_connection):
    retVal = {}

    try:
        log_c = log_connection.cursor()
        
        log_c.execute("SELECT * FROM log WHERE id >= " + idFrom + " AND id <= " + idTo + " ORDER BY id DESC")
        
        log = log_c.fetchall()
        log_c.close()
        
        retVal       = "["
        recordHolder = ""
        
        for record in log:
            if not(record == None):
                if (len(recordHolder) > 0):
                    recordHolder += ", "
                
                recordHolder += "["
                fieldHolder   = ""
                
                for field in record:
                    if (len(fieldHolder) > 0):
                        fieldHolder += ", "
                    
                    fieldHolder += "\"" + str(field).replace('\\', "\\\\") + "\""
                
                recordHolder += fieldHolder + "]"
        retVal += recordHolder + "]"
        
        return (str(retVal))
    except:
        return ("EXCEPTION: " + traceback.format_exc().replace('"', '&#34;').replace('<', "&#60;").replace('>', "&#62;").replace('\n', "<br>").replace(' ', "&#160;"))

session_id = self.set_session()

try:
    if (self.session_authenticated(session_id) and self.validate_session(session_id)):
        data = json.loads(parameters["data"])
        
        log_connection = sqlite3.connect("log.db")
        
        self.print("{\"stat\": 8, \"msg\": \"\", \"log\": " + queryLog(data["idfrom"], data["idto"], data["logfilefilter"], data["logfuncfilter"], data["loguserfilter"], data["logstrfilter"], data["sortby"], data["order"], log_connection) + "}")
        
        log_connection.close()
    else:
        logger("MAIN", "post/discover.py", "SYSTEM", "Unauthorized Attempted Access")
        raise("Unauthorized Attempted Access")
except:
    self.print("{\"stat\": 1, \"msg\": \"Some kind of an error happened!\"}")
    logger("systemlog.py", "queryLog", "TEST", "EXCEPTION: " + traceback.format_exc().replace('"', '&#34;').replace('<', "&#60;").replace('>', "&#62;").replace('\n', "<br>").replace(' ', "&#160;"))
    logger("systemlog.py", "queryLog", "TEST", str(parameters).replace('"', '&#34;').replace('<', "&#60;").replace('>', "&#62;").replace('\n', "<br>").replace(' ', "&#160;"))
    raise("Unauthorized Attempted Access")




























