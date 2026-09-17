def authenticateUser(data, user_connection, userdb_script_path, salt_connection, saltdb_script_path):
    status         = -1
    message        = ""
    retVal         = {}
    lastaccessdate = time.strftime("%m/%d/%Y %H:%M:%S")

    # SELECTS user record from users database from users table.
    # UPDATES user record from users database in users table to record last access date.
    user_c = user_connection.cursor()
    user_c.execute("UPDATE users SET lastaccess=\"" + lastaccessdate + "\" WHERE username=\"" + data["username"][0] + "\"")
    user_connection.commit()
    
    user_c.execute("SELECT * FROM users WHERE username=\"" + data["username"][0] + "\"")
    user_record = user_c.fetchall()

    # SELECTS salt record from salts database from salts table.
    # UPDATES salt record from salts database in salts table to record last access date.
    salt_c = salt_connection.cursor()
    salt_c.execute("UPDATE salts SET lastaccess=\"" + lastaccessdate + "\" WHERE id=\"" + user_record[0][3] + "\"")
    salt_connection.commit()
    
    salt_c.execute("SELECT * FROM salts WHERE id=\"" + user_record[0][3] + "\"")
    salt_record = salt_c.fetchall()

    if ((server_config["pepper"] + salt_record[0][1] + data["password"][0]) == user_record[0][2]):
        # The following block executes if user successfully authenticated.
        user_c.execute("UPDATE users SET lastsuccessfulllogin=\"" + lastaccessdate + "\" WHERE username=\"" + data["username"][0] + "\"")
        user_connection.commit()

        user_c.execute("SELECT securequestion1, secureanswer1, securequestion2, secureanswer2, securequestion3, secureanswer3 FROM secureanswers WHERE username=\"" + data["username"][0] + "\"")
        secure_questions = user_c.fetchall()
        
        retVal["questionsset"] = True
        
        for field in secure_questions[0]:
            if (field == None):
                retVal["questionsset"] = False
        
        status  = 0
        message = "User Successfully Authenticated"
    else:
        # The following block executes if user was not able to successfully authenticate.
        status  = 1
        message = "Unable to Authenticate User"
        
    return (status, message, retVal)
# END OF authenticateUser()

# Gets session data.
# Parses JSON into python dictionary.
session_id = self.set_session()
data = json.loads(parameters["data"])

try:
    # Initializes SQL script paths, and database connections.
    userdb_script_path               = (self.config["root-path"] + self.config["paths"]["private-files"] + "/sqlite_scripts/usersdb.sql")
    saltdb_script_path               = (self.config["root-path"] + self.config["paths"]["private-files"] + "/sqlite_scripts/saltsdb.sql")
    user_connection                  = self.create_sqlite_connection("users.db")
    salt_connection                  = self.create_sqlite_connection("salts.db")

    # Authenticates user. Captures output in python tuple.
    (status, message, response_data) = authenticateUser(json.loads(parameters["data"]), user_connection, userdb_script_path, salt_connection, saltdb_script_path)

    if (status == 0):
        # TP was able to successfully authenticate.
        if (self.validate_session(session_id)):
            # Session is still valid.
            self.authenticate_session(session_id, data["username"][0])
            self.set_session_parameter(session_id, "questionsset", response_data["questionsset"])
            
            #logger("MAIN", "post/authenticate.py", "SERVER", "signed in.")
            #_logger_("MAIN", "post/authenticate.py", "SERVER", "signed in.")
            
            self.print("{\"stat\": " + str(status) + ", \"msg\": \"" + str(message) + "\", \"loginresponse\": {}}")
        else:
            # Session was no longer valid.
            #logger("MAIN", "post/authenticate.py", "SERVER", "ERROR: Failed to authenticate.")
            #_logger_("MAIN", "post/authenticate.py", "SERVER", "ERROR: Failed to authenticate.")
            self.destroy_session(session_id)
            self.print("{\"stat\": 3, \"msg\": \"One or more of the required fields were filled out incorrectly.\\n\\nPlease check your entries and try again.\"}")
    else:
        # User was not able to successfully authenticate.
        #logger("MAIN", "post/authenticate.py", "SERVER", "ERROR: Failed to authenticate.")
        #self.print("{\"stat\": " + str(status) + ", \"msg\": \"" + str(message) + "\", \"loginresponse\": " + str(response_data) + "}")
        
        #logger("MAIN", "post/authenticate.py", "SERVER", "ERROR: Failed to authenticate.")
        self.print("{\"stat\": " + str(status) + ", \"msg\": \"" + str(message) + "\", \"loginresponse\": " + str(response_data) + "}")
except:
    # User was not able to successfully Authenticate.
    #logger("MAIN", "post/authenticate.py", "SERVER", "ERROR: Failed to authenticate.")
    #logger("MAIN", "post/authenticate.py", "SERVER", "EXCEPTION: " + traceback.format_exc().replace('"', '&#34;').replace('<', "&#60;").replace('>', "&#62;").replace('\n', "<br>").replace(' ', "&#160;"))
    self.print("{\"stat\": 1, \"msg\": \"Unable to Authenticate User\"}")
    
    #_logger_("MAIN", "post/authenticate.py", "SERVER", "ERROR: Failed to authenticate.")
    #_logger_("MAIN", "post/authenticate.py", "SERVER", "EXCEPTION: " + traceback.format_exc().replace('"', '&#34;').replace('<', "&#60;").replace('>', "&#62;").replace('\n', "<br>").replace(' ', "&#160;"))
    #self.print("{\"stat\": 1, \"msg\": \"Unable to Authenticate User\"}")
