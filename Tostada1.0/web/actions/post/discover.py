def discoverGPEN(ip, username, password):
    retVal = {}

    try:
        data_list = subprocess.check_output(["curl", "--digest", "-s", "-u", (username + ":" + password), ("http://" + ip + "/sys.b")]).decode()[1:-1].split(',')
    
        for item in data_list:
            data_item            = item.split(':')
            retVal[data_item[0]] = data_item[1]

        return ("{\"Board Name\": \"" + retVal["i07"].replace("'", '') + "\", \"MAC Address\": \"" + retVal["i03"].replace("'", '') + "\", \"IP Address\": \"" + ip + "\", \"Serial Number\": \"" + retVal["i04"].replace("'", '') + "\", \"Identity\": \"" + retVal["i05"].replace("'", '') + "\"}")
    except:
        return ("null")

session_id = self.set_session()

try:
    if (self.session_authenticated(session_id) and self.validate_session(session_id)):
        data = json.loads(parameters["data"])
        self.print("{\"stat\": 4, \"msg\": \"\", \"gpenresponse\": " + discoverGPEN(data["ip"], data["username"], data["password"]) + "}")
    else:
        logger("MAIN", "post/discover.py", "Unauthorized Attempted Access")
        raise("Unauthorized Attempted Access")
except:
    logger("MAIN", "post/discover.py", "Unauthorized Attempted Access")
    raise("Unauthorized Attempted Access")
