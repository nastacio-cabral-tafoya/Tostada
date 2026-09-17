session_id = self.set_session()

try:
    self.set_response_header("X-Robots-Tag", "noindex")#Prevents search engines from indexing the webpage.

    if (self.session_authenticated(session_id) and self.validate_session(session_id)):
        parameters["username"]                = self.get_session_parameter(session_id, "username")
        parameters["session-timeout-seconds"] = str(timeout_to_seconds(HTTPHandler.active_sessions[session_id]["timeout"]))

        if (self.get_session_parameter(session_id, "questionsset")):
            logger("MAIN", "get/fsequence.py", self.get_session_parameter(session_id, "username"), "NOTICE: Access Granted.")
            
            self.execute_template("/fsequence.html", parameters)
        else:
            user_connection = self.create_sqlite_connection("users.db")
            user_c          = user_connection.cursor()
            
            user_c.execute("SELECT * FROM securequestions;")

            parameters["securequestions"] = user_c.fetchall();
            
            logger("MAIN", "get/fsequence.py", self.get_session_parameter(session_id, "username"), "NOTICE: User '" + self.get_session_parameter(session_id, "username") + "' security questions not set!")
            
            self.execute_template("/setsecurequestions.html", parameters)
    else:
        parameters["newuserlogin"] = self.get_session_parameter(session_id, "newuserlogin")
        self.set_session_parameter(session_id, "newuserlogin", False)
        
        logger("MAIN", "get/fsequence.py", self.get_session_parameter(session_id, "username"), "ERROR: Access Denied.")
        
        self.execute_template("/login.html", parameters)
except:
    logger("MAIN", "get/fsequence.py", "SERVER", "EXCEPTION: " + traceback.format_exc().replace('"', '&#34;').replace('<', "&#60;").replace('>', "&#62;").replace('\n', "<br>").replace(' ', "&#160;"))
    self.redirect("/initialize")
