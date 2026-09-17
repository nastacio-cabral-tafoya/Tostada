session_id = self.set_session()

try:
    if (self.session_authenticated(session_id) and self.validate_session(session_id)):
        data = json.loads(parameters["data"])
        logger("MAIN", "post/renewsession.py", "SERVER", "NOTICE: Renewed session " + session_id + ".")
        self.print("{\"stat\": 4, \"msg\": \"\", \"session_timeout\": " + str(timeout_to_seconds(HTTPHandler.active_sessions[session_id]["timeout"])) + "}")
    else:
        logger("MAIN", "post/renewsession.py", "SYSTEM", "Unauthorized Attempted Access")
        raise("Unauthorized Attempted Access")
except:
    logger("MAIN", "post/renewsession.py", "SYSTEM", "Unauthorized Attempted Access")
    raise("Unauthorized Attempted Access")
