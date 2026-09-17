def setSecureQuestions(username, data, user_connection, userdb_script_path):
    status         = -1
    message        = ""
    retVal         = {}
    lastaccessdate = time.strftime("%m/%d/%Y %H:%M:%S")

    try:
        status = 5
        
        user_c = user_connection.cursor()

        user_c.execute("UPDATE users SET lastaccess=\"" + lastaccessdate + "\" WHERE username=\"" + username + "\"")
        user_connection.commit()

        user_c.execute("UPDATE secureanswers SET lastaccess=\"" + lastaccessdate + "\" WHERE username=\"" + username + "\"")
        user_connection.commit()
        
        user_c.execute("UPDATE secureanswers SET securequestion1=\"" + data["securequestion1"][0] + "\", secureanswer1=\"" + data["secureanswer1"][0] + "\", securequestion2=\"" + data["securequestion2"][0] + "\", secureanswer2=\"" + data["secureanswer2"][0] + "\", securequestion3=\"" + data["securequestion3"][0] + "\", secureanswer3=\"" + data["secureanswer3"][0] + "\" WHERE username=\"" + username + "\"")
        user_connection.commit()

        message = "Security Questions successfully updated!"
    except:
        logger("MAIN", "put/setsecurequestions.py > setSecureQuestions", "SERVER", "EXCEPTION: " + traceback.format_exc().replace('"', '&#34;').replace('<', "&#60;").replace('>', "&#62;").replace('\n', "<br>").replace(' ', "&#160;"))
        status = 1
        message = "Some kind of Error Happened."

    return (status, message, retVal)
        
session_id = self.set_session()
logger("MAIN", "put/setsecurequestions.py", "SERVER", "ACCESSED /setsecurequestions")

try:
    if (self.session_authenticated(session_id) and self.validate_session(session_id)):
        userdb_script_path               = (self.config["root-path"] + self.config["paths"]["private-files"] + "/sqlite_scripts/usersdb.sql")
        user_connection                  = self.create_sqlite_connection("users.db")
        parameters["username"]           = self.get_session_parameter(session_id, "username")

        (status, message, response_data) = setSecureQuestions(parameters["username"], json.loads(parameters["data"]), user_connection, userdb_script_path)

        if (status == 5):
            self.set_session_parameter(session_id, "questionsset", True)
        
        self.print("{\"stat\": " + str(status) + ", \"msg\": \"" + str(message) + "\", \"newaccresponse\": " + str(response_data).replace("'", "\"") + "}")
    else:
        self.print("{\"stat\": 1, \"msg\": \"Some kind of Error Happened 1.\", \"data\": {}}")
except:
    logger("MAIN", "put/dashboard.py", "SERVER", "EXCEPTION: " + traceback.format_exc().replace('"', '&#34;').replace('<', "&#60;").replace('>', "&#62;").replace('\n', "<br>").replace(' ', "&#160;"))
    self.print("{\"stat\": 1, \"msg\": \"Some kind of Error Happened 2.\", \"data\": {}}")
