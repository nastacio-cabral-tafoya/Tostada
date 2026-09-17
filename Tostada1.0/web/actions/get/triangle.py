try:
    #Prevents search engines from indexing.
    self.set_response_header("X-Robots-Tag", "noindex, nofollow, none, noarchive, nositelinkssearchbox, nosnippet, noimageindex")

    self.execute_template("/triangle.html", parameters)
except:
    self.redirect("/initialize")
