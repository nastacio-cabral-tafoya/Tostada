session_id = self.set_session()

try:
    #Prevents search engines from indexing.
    self.set_response_header("X-Robots-Tag", "noindex, nofollow, none, noarchive, nositelinkssearchbox, nosnippet, noimageindex")

    if (self.session_authenticated(session_id)):
        self.redirect("/dashboard")
    else:
        self.redirect("/login")
    
except:
    self.redirect("/initialize")
