self.set_response_header("X-Robots-Tag", "noindex")#Prevents search engines from indexing the webpage.

self.execute_template("/internalerror.html", parameters)
