session_id = self.set_session()

try:
    self.set_response_header("X-Robots-Tag", "noindex")#Prevents search engines from indexing the webpage.
    
    #logger("MAIN", "get/dashboard.py", "SERVER", "NOTICE: Redirect to ssl.")
    
    self.execute_template("/redirecttossl.html", parameters)
except:
    #logger("MAIN", "get/redirecttossl.py", "SERVER", "EXCEPTION: " + traceback.format_exc().replace('"', '&#34;').replace('<', "&#60;").replace('>', "&#62;").replace('\n', "<br>").replace(' ', "&#160;"))
    self.redirect("/initialize")
