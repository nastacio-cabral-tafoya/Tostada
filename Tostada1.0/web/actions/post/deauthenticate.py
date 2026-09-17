session_id = self.set_session()
data = json.loads(parameters["data"])

try:
    if(self.validate_session(session_id)):
        try:
            logger("MAIN", "post/deauthenticate.py", self.get_session_parameter(session_id, "username"), self.get_session_parameter(session_id, "username") + " signed out.")
            self.deauthenticate_session(session_id)
        except:
            pass
    else:
        logger("MAIN", "post/deauthenticate.py", "SERVER", "session destroyed.")
        self.destroy_session(session_id)
except:
    pass

self.print("{\"stat\": 0, \"msg\":\"User de-authenticated!\"}")
