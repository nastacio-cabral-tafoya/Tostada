session_id = self.set_session()

try:
    #Prevents search engines from indexing.
    self.set_response_header("X-Robots-Tag", "noindex, nofollow, none, noarchive, nositelinkssearchbox, nosnippet, noimageindex")

    if (self.session_authenticated(session_id)):
        self.redirect("/dashboard")
    else:
        parameters["newuserlogin"] = self.get_session_parameter(session_id, "newuserlogin")
        self.set_session_parameter(session_id, "newuserlogin", False)

        self.execute_template("/login.html", parameters)
except:
    self.redirect("/initialize")
