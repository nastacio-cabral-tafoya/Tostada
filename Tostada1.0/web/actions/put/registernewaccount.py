def registerNewAccount(data, user_connection, userdb_script_path, salt_connection, saltdb_script_path, securequestiondb_script_path):
    status         = -1
    message        = ""
    retVal         = {}
    lastaccessdate = time.strftime("%m/%d/%Y %H:%M:%S")
    
    try:
        status = 6

        # Attempts to validate each field submitted by the user.
        for item in data:
            if is_blank(data[item][0]):
                retVal[item] = data[item]

                if not(status == 7):
                    status == 7

        if not(status == 7):
            # No issues with user input have been detected.
            salt_c = salt_connection.cursor()
            user_c = user_connection.cursor()

            # If the table does not exist, SQL scripts are executed to create the able in the proper database file.
            with open(saltdb_script_path, "r") as sql:
                salt_c.executescript(sql.read())
            with open(userdb_script_path, "r") as sql:
                user_c.executescript(sql.read())

            user_c.execute("SELECT * FROM securequestions;")
            security_questions = user_c.fetchall()

            if (len(security_questions) == 0):
                user_c.executescript("""INSERT INTO securequestions (securequestion) VALUES ("In what city were you born?");
                    INSERT INTO securequestions (securequestion) VALUES ("What is the name of your favorite pet?");
                    INSERT INTO securequestions (securequestion) VALUES ("What is your mother's maiden name?");
                    INSERT INTO securequestions (securequestion) VALUES ("What high school did you attend?");
                    INSERT INTO securequestions (securequestion) VALUES ("What was the name of your elementary school?");
                    INSERT INTO securequestions (securequestion) VALUES ("What was the make of your first car?");
                    INSERT INTO securequestions (securequestion) VALUES ("What was your favorite food as a child?");
                    INSERT INTO securequestions (securequestion) VALUES ("Where did you meet your spouse?");
                    INSERT INTO securequestions (securequestion) VALUES ("What year was your father (or mother) born?");""")
                

            # Attempts to query the username entered by the user.
            # If the query returns something, the username has already been taken.
            # User will be notified username is not available.
            user_c.execute("SELECT username FROM users WHERE username=\"" + data["username"][0] + "\"")
            users_list = user_c.fetchall()
            
            if (len(users_list) > 0):
                # The selected username already exists.
                status             = 7
                message            = ("Username '" + data["username"][0] + "' is not available.")
                retVal["username"] = data["username"]

                # Closes each database connection.
                salt_c.close()
                user_c.close()
            else:
                # The selected username is already available.
                salt = (secrets.token_urlsafe(64) + time.strftime("%Y%m%d%H%M%S")) # Generates SALT string.

                # Code in try block attempts to create accounts records in the salts database and the users database.
                try:
                    # INSERTS salt into salt database.
                    salt_c.execute("INSERT INTO salts (saltstr, createdate, lastaccess) VALUES (\"" + salt + "\", \"" + time.strftime("%m/%d/%Y %H:%M:%S") + "\", \"" + lastaccessdate + "\");")
                    salt_connection.commit()

                    # SELECTS the recently created salt from the salts database but only selects the id field.
                    salt_c.execute("SELECT id FROM salts WHERE saltstr=\"" + salt + "\"")
                    record = salt_c.fetchall()

                    # CREATES a 'link' item in the data dictionary to be inserted into the users database.
                    data["link"] = [str(record[0][0])]

                    # INSERTS user record into the users table of the users database.
                    data["password"][0] = (server_config["pepper"] + salt + data["password"][0])
                    user_c.execute("INSERT INTO users (username, password, link, createdate, firstname, lastname, dob, email, verified, twofactor, lastaccess) VALUES (\"" + data["username"][0] + "\", \"" + data["password"][0] + "\", \"" + data["link"][0] + "\", \"" + time.strftime("%m/%d/%Y %H:%M:%S") + "\", \"" + data["firstname"][0] + "\", \"" + data["lastname"][0] + "\", \"" + data["dob"][0] + "\", \"" + data["email"][0] + "\", \"FALSE\", \"DISABLED\", \"" + lastaccessdate + "\");")
                    user_connection.commit()

                    # SELECTS the user record that was just created, but only selects the id field.
                    user_c.execute("SELECT id FROM users WHERE username=\"" + data["username"][0] + "\"")
                    record = user_c.fetchall()

                    # Updates the salt record that was previously created so that it has the ID for the user record in the link field.
                    salt_c.execute("UPDATE salts SET link=\"" + str(record[0][0]) + "\" WHERE id=\"" + data["link"][0] + "\"")
                    salt_connection.commit()

                    # INSERTS a record for security questions for the new user account into the secureanswers table.
                    # The security questions will be blank because the user account has not been verified yet.
                    user_c.execute("INSERT INTO secureanswers (username, lastaccess) VALUES(\"" + data["username"][0] + "\", \"" + lastaccessdate + "\");")
                    user_connection.commit()

                    # Closes each database connection.
                    salt_c.close()
                    user_c.close()
                    
                    message = "Successfully Created Account"
                except Error as e:
                    # Some kind of error happend. User account will not be able to be created.
                    # Creats log entry with a stack trace for the developer.
                    logger("MAIN", "put/registernewaccount.py > registerNewAccount", "SERVER", "EXCEPTION: " + traceback.format_exc().replace('"', '&#34;').replace('<', "&#60;").replace('>', "&#62;").replace('\n', "<br>").replace(' ', "&#160;"))
                    status  = 1
                    message = "Some kind of Error Happened. 2"
                    salt_c.close()
                    user_c.close()
        elif (status == 7):
            # Issues with user input have been detected.
            message = "Required fields cannot be left blank!"
            salt_c.close()
            user_c.close()
    except:
        # Some kind of exception occurred. The errors are not granular enough to narrow down the issue from the user's END.
        # A log entry with a stack trace for the developer is created.
        logger("MAIN", "put/registernewaccount.py", "SERVER", "EXCEPTION: " + traceback.format_exc().replace('"', '&#34;').replace('<', "&#60;").replace('>', "&#62;").replace('\n', "<br>").replace(' ', "&#160;"))
        status  = 1
        message = "Some kind of Error Happened. 3"
        salt_c.close()
        user_c.close()
    
    return (status, message, retVal)
#END OF REGISTER NEW ACCOUNT
session_id = self.set_session()

try:
    userdb_script_path               = (self.config["root-path"] + self.config["paths"]["private-files"] + "/sqlite_scripts/usersdb.sql")
    saltdb_script_path               = (self.config["root-path"] + self.config["paths"]["private-files"] + "/sqlite_scripts/saltsdb.sql")
    securequestiondb_script_path     = (self.config["root-path"] + self.config["paths"]["private-files"] + "/sqlite_scripts/secureanswerstb.sql")
    user_connection                  = self.create_sqlite_connection("users.db")
    salt_connection                  = self.create_sqlite_connection("salts.db")
    
    (status, message, response_data) = registerNewAccount(json.loads(parameters["data"]), user_connection, userdb_script_path, salt_connection, saltdb_script_path, securequestiondb_script_path)
    user_connection.close()
    salt_connection.close()

    if (status == 6):
        self.set_session_parameter(session_id, "newuserlogin", True)

    # Variable response_data needed to have single quotes replaced with
    # double quotes because python dictionaries use single quotes when
    # converted to string representations. JSON cannot be parsed if single
    # quotes are used instead of double quotes. In order for the JSON to be
    # parsed, single quotes needed to be replaced with double quotes.
    self.print("{\"stat\": " + str(status) + ", \"msg\": \"" + str(message) + "\", \"newaccresponse\": " + str(response_data).replace("'", "\"") + "}")
except:
    self.print("{\"stat\": 1, \"msg\": \"Some kind of Error Happened.\", \"data\": {}}")























