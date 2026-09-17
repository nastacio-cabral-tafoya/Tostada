#Class that handles http requests and responses.
from threading import RLock

def _synchronized_session_method(method):
    def wrapper(self, *args, **kwargs):
        with HTTPHandler.session_lock:
            return method(self, *args, **kwargs)
    return wrapper

class HTTPHandler:
    active_sessions = {}
    session_lock = RLock()
    
    def __init__(self):
        #logger("HTTPHandler", "__init__", "SERVER", "")
        #_logger_("HTTPHandler", "__init__", "SERVER", "")
        self.config = {}
        self.import_config()

    # Imports settings for the HTTPHandler such as default page, paths, etc.
    def import_config(self, path = "Server_Config/http_config.json"):
        #logger("HTTPHandler", "import_config", "SERVER", "")
        #_logger_("HTTPHandler", "import_config", "SERVER", "")
        with open(path, 'r') as f_in:
                self.config = json.loads(f_in.read())
    
    # Parses the HTTP request into a dictionary.
    def parse_request(self):
        # HTTP/1.x uses CRLF for line termination. Accept LF-only input only as
        # a compatibility fallback, but normalize parsing internally.
        raw = self.http_request
        if isinstance(raw, bytes):
            raw = raw.decode("iso-8859-1")

        header_end = raw.find("\r\n\r\n")
        delimiter_len = 4

        if header_end == -1:
            header_end = raw.find("\n\n")
            delimiter_len = 2

        if header_end == -1:
            header_section = raw
            body = ""
        else:
            header_section = raw[:header_end]
            body = raw[header_end + delimiter_len:]

        lines = header_section.replace("\r\n", "\n").split("\n")
        if not lines or not lines[0]:
            raise ValueError("Invalid HTTP request: missing request line")

        request_line = lines[0]
        parts = request_line.split(" ", 2)
        if len(parts) != 3 or any(part == "" for part in parts):
            raise ValueError("Invalid HTTP request line")

        method, target, protocol = parts

        if not protocol.startswith("HTTP/"):
            raise ValueError("Invalid HTTP protocol version")

        self.request["type"] = method
        self.request["protocol"] = protocol

        # Request-target parsing.
        from urllib.parse import urlsplit, parse_qsl

        parsed_target = urlsplit(target)
        self.request["path"] = parsed_target.path or "/"
        self.request["path-parameters"] = parsed_target.query

        # Parse headers. HTTP field names are case-insensitive.
        # Preserve the original spelling as the dictionary key for compatibility,
        # while also making lookup of important HTTP fields case-insensitive.
        self.request_headers = {}

        for line in lines[1:]:
            if line == "":
                continue

            if ":" not in line:
                # Malformed header field.
                raise ValueError("Invalid HTTP header")

            key, value = line.split(":", 1)
            key = key.strip()
            value = value.strip()

            if not key:
                raise ValueError("Invalid HTTP header name")

            lower_key = key.lower()

            if lower_key == "cookie":
                cookies = self.request.get("Cookie", {})
                for cookie in value.split(";"):
                    cookie = cookie.strip()
                    if not cookie:
                        continue

                    if "=" not in cookie:
                        continue

                    cookie_name, cookie_value = cookie.split("=", 1)
                    cookie_name = cookie_name.strip()
                    if cookie_name:
                        cookies[cookie_name] = cookie_value.strip()

                self.request["Cookie"] = cookies
                self.request_headers["cookie"] = "; ".join(
                    name + "=" + value for name, value in cookies.items()
                )
            else:
                # HTTP allows multiple fields with the same name. Preserve
                # multiple occurrences using a comma-separated representation
                # for ordinary fields.
                if lower_key in self.request_headers:
                    self.request_headers[lower_key] += ", " + value
                else:
                    self.request_headers[lower_key] = value

                self.request[key] = value

        # Body is the bytes/characters following the HTTP header section.
        # The socket layer must already have supplied the complete HTTP message.
        self.request["parameters"] = body

        # Populate common case-sensitive keys expected by the existing code.
        for key, value in self.request_headers.items():
            canonical = {
                "content-length": "Content-Length",
                "content-type": "Content-Type",
                "transfer-encoding": "Transfer-Encoding",
                "host": "Host",
                "connection": "Connection",
                "cookie": "Cookie",
            }.get(key)

            if canonical and canonical not in self.request:
                self.request[canonical] = value
    # Generates header that instructs the client to redirect to the location specified.
    def redirect(self, path):
        #logger("MAIN", "HTTPHandler.redirect", "SERVER", "")
        #_logger_("MAIN", "HTTPHandler.redirect", "SERVER", "")
        self.set_response_header("Location", path) # Setting redirect location.
        self.set_response(body = "", status = "302 Found") # Setting http status.

    # Executes an action that corresponds to the error code specified.
    def set_error(self, code, parameters, method):
        #logger("MAIN", "HTTPHandler.set_error", "SERVER", "")
        #_logger_("MAIN", "HTTPHandler.set_error", "SERVER", "")
        #
        # Error handlers must not recursively invoke themselves if the
        # configured error resource cannot be loaded.
        if getattr(self, "_handling_error", False):
            self.set_response(status = (code + " " + self.config["status-codes"][code]))
            return

        self._handling_error = True
        try:
            self.execute_action(
                self.config["status-locations"][code],
                parameters,
                method,
                status = (code + " " + self.config["status-codes"][code])
            )
        finally:
            self._handling_error = False
    
    # Adds information to the response.
    def set_response(self, body=None, status="200 OK"):
        if self.response is not None:
            return

        if body is None:
            body = self.response_body

        if isinstance(body, str):
            body_bytes = body.encode("utf-8")
        elif isinstance(body, bytes):
            body_bytes = body
        else:
            raise TypeError("HTTP response body must be str or bytes")

        # HTTP/1.x requires CRLF between the status line and each header.
        status_line = self.config["version"] + " " + status + "\r\n"

        header_lines = []

        for key, value in self.response_headers.items():
            header_lines.append(str(key) + ": " + str(value) + "\r\n")

        # Each Set-Cookie field is a separate HTTP header field.
        for cookie in self.response_cookies:
            header_lines.append("Set-Cookie: " + str(cookie) + "\r\n")

        self.response = (
            status_line.encode("iso-8859-1")
            + "".join(header_lines).encode("iso-8859-1")
            + b"\r\n"
            + body_bytes
        )

    def set_response_header(self, key, value):
        #logger("MAIN", "HTTPHandler.set_response_header", "SERVER", "")
        #_logger_("MAIN", "HTTPHandler.set_response_header", "SERVER", "")
        self.response_headers[key] = value
    
    @_synchronized_session_method
    def set_session(self):
        #logger("MAIN", "HTTPHandler.set_session", "SERVER", "")
        #_logger_("MAIN", "HTTPHandler.set_session", "SERVER", "")
        ret_val = None
        
        try:
            if (self.request["Cookie"][self.config["session-cookie-name"]] in HTTPHandler.active_sessions):
                if (self.validate_session(self.request["Cookie"][self.config["session-cookie-name"]])):
                    HTTPHandler.active_sessions[self.request["Cookie"][self.config["session-cookie-name"]]]["set-date"] = datetime.datetime.now()
                    
                    ret_val = self.request["Cookie"][self.config["session-cookie-name"]]
                else:
                    ##print(str(HTTPHandler.active_sessions[self.request["Cookie"][self.config["session-cookie-name"]]]))
                    raise Exception("Session Expired or Invalid")
            else:
                raise Exception("No Session Exists")
        except:
            #logger("MAIN", "HTTPHandler.set_session", "SERVER", "EXCEPTION: " + traceback.format_exc().replace('"', '&#34;').replace('<', "&#60;").replace('>', "&#62;").replace('\n', "<br>").replace(' ', "&#160;"))
            #_logger_("MAIN", "HTTPHandler.set_session", "SERVER", "EXCEPTION: " + traceback.format_exc())
            set_date   = datetime.datetime.now()
            session_id = secrets.token_urlsafe(64)

            while (session_id in HTTPHandler.active_sessions):
                session_id = secrets.token_urlsafe(64)

            HTTPHandler.active_sessions[session_id] = {"set-date":set_date, "timeout":self.config["session-timeout"], "parameters":{"authenticated":False}}
            ret_val                                 = session_id
            self.set_cookie(self.config["session-cookie-name"], session_id, {"Max-Age": timeout_to_seconds(self.config["session-timeout"]), "SameSite": "Strict"})

        return (ret_val)

    @_synchronized_session_method
    def validate_session(self, session_id):
        #logger("MAIN", "HTTPHandler.validate_session", "SERVER", "")
        #_logger_("MAIN", "HTTPHandler.validate_session", "SERVER", "")
        ret_val      = False
        session      = HTTPHandler.active_sessions[session_id]
        timeout      = timeout_to_seconds(session["timeout"])
        timediff     = (datetime.datetime.now() - session["set-date"])
        session_age  = ((timediff.days * 24 * 60 * 60) + timediff.seconds)

        if (session_age < timeout):
            ret_val = True
        else:
            session["parameters"]["authenticated"] = ret_val
        
        return (ret_val)

    @_synchronized_session_method
    def destroy_session(self, session_id):
        #logger("MAIN", "HTTPHandler.destroy_session", "SERVER", "")
        #_logger_("MAIN", "HTTPHandler.destroy_session", "SERVER", "")
        try:
            del HTTPHandler.active_sessions[session_id]
        except:
            #logger("MAIN", "HTTPHandler.destroy_session", "SERVER", "EXCEPTION: " + traceback.format_exc().replace('"', '&#34;').replace('<', "&#60;").replace('>', "&#62;").replace('\n', "<br>").replace(' ', "&#160;"))
            #_logger_("MAIN", "HTTPHandler.destroy_session", "SERVER", "EXCEPTION: " + traceback.format_exc())
            pass

    @_synchronized_session_method
    def get_session_parameter(self, session_id, key):
        #logger("MAIN", "HTTPHandler.get_session_parameter", "SERVER", "")
        #_logger_("MAIN", "HTTPHandler.get_session_parameter", "SERVER", "")
        try:
            return (HTTPHandler.active_sessions[session_id]["parameters"][key])
        except:
            #logger("MAIN", "HTTPHandler.get_session_parameter", "SERVER", "EXCEPTION: " + traceback.format_exc().replace('"', '&#34;').replace('<', "&#60;").replace('>', "&#62;").replace('\n', "<br>").replace(' ', "&#160;"))
            #_logger_("MAIN", "HTTPHandler.get_session_parameter", "SERVER", "EXCEPTION: " + traceback.format_exc())
            return (None)

    @_synchronized_session_method
    def set_session_parameter(self, session_id, key, value):
        #logger("MAIN", "HTTPHandler.set_session_parameter", "SERVER", "")
        #_logger_("MAIN", "HTTPHandler.set_session_parameter", "SERVER", "")
        try:
            HTTPHandler.active_sessions[session_id]["parameters"][key] = value
        except:
            #logger("MAIN", "HTTPHandler.set_session_parameter", "SERVER", "EXCEPTION: " + traceback.format_exc().replace('"', '&#34;').replace('<', "&#60;").replace('>', "&#62;").replace('\n', "<br>").replace(' ', "&#160;"))
            #_logger_("MAIN", "HTTPHandler.set_session_parameter", "SERVER", "EXCEPTION: " + traceback.format_exc())
            pass

    @_synchronized_session_method
    def session_authenticated(self, session_id):
        #logger("MAIN", "HTTPHandler.session_authenticated", "SERVER", "")
        #_logger_("MAIN", "HTTPHandler.session_authenticated", "SERVER", "")
        try:
            return (HTTPHandler.active_sessions[session_id]["parameters"]["authenticated"])
        except:
            #logger("MAIN", "HTTPHandler.session_authenticated", "SERVER", "EXCEPTION: " + traceback.format_exc().replace('"', '&#34;').replace('<', "&#60;").replace('>', "&#62;").replace('\n', "<br>").replace(' ', "&#160;"))
            #_logger_("MAIN", "HTTPHandler.session_authenticated", "SERVER", "EXCEPTION: " + traceback.format_exc())
            return False

    @_synchronized_session_method
    def authenticate_session(self, session_id, username):
        #logger("MAIN", "HTTPHandler.authenticate_session", "SERVER", "")
        #_logger_("MAIN", "HTTPHandler.authenticate_session", "SERVER", "")
        try:
            HTTPHandler.active_sessions[session_id]["parameters"]["authenticated"] = True
            HTTPHandler.active_sessions[session_id]["parameters"]["username"]      = username
        except:
            #logger("MAIN", "HTTPHandler.authenticate_session", "SERVER", "EXCEPTION: " + traceback.format_exc().replace('"', '&#34;').replace('<', "&#60;").replace('>', "&#62;").replace('\n', "<br>").replace(' ', "&#160;"))
            #_logger_("MAIN", "HTTPHandler.authenticate_session", "SERVER", "EXCEPTION: " + traceback.format_exc())
            pass

    @_synchronized_session_method
    def deauthenticate_session(self, session_id):
        #logger("MAIN", "HTTPHandler.deauthenticate_session", "SERVER", "")
        #_logger_("MAIN", "HTTPHandler.deauthenticate_session", "SERVER", "")
        try:
            HTTPHandler.active_sessions[session_id]["parameters"]["authenticated"] = False
        except:
            #logger("MAIN", "HTTPHandler.deauthenticate_session", "SERVER", "EXCEPTION: " + traceback.format_exc().replace('"', '&#34;').replace('<', "&#60;").replace('>', "&#62;").replace('\n', "<br>").replace(' ', "&#160;"))
            #_logger_("MAIN", "HTTPHandler.deauthenticate_session", "SERVER", "EXCEPTION: " + traceback.format_exc())
            pass

    @_synchronized_session_method
    def destroy_session(self, session_id):
        #logger("MAIN", "HTTPHandler.destroy_session", "SERVER", "")
        #_logger_("MAIN", "HTTPHandler.destroy_session", "SERVER", "")
        try:
            del HTTPHandler.active_sessions[session_id]
        except:
            #logger("MAIN", "HTTPHandler.destroy_session", "SERVER", "EXCEPTION: " + traceback.format_exc().replace('"', '&#34;').replace('<', "&#60;").replace('>', "&#62;").replace('\n', "<br>").replace(' ', "&#160;"))
            #_logger_("MAIN", "HTTPHandler.destroy_session", "SERVER", "EXCEPTION: " + traceback.format_exc())
            pass
    
    def set_cookie(self, name, value, cookie_parameters = {}):
        #logger("MAIN", "HTTPHandler.set_cookie", "SERVER", "")
        #_logger_("MAIN", "HTTPHandler.set_cookie", "SERVER", "")
        cookie = (name + '=' + value)

        for parameter in cookie_parameters:
            cookie += ("; " + parameter + '=' + str(cookie_parameters[parameter]))
        
        self.response_cookies.append(cookie)

    def print(self, text, end = '\n'):
        #logger("MAIN", "HTTPHandler.print", "SERVER", "")
        #_logger_("MAIN", "HTTPHandler.print", "SERVER", "")
        self.response_body += (text + end)

    def get_exec_stdout(self):
        #logger("MAIN", "HTTPHandler.get_exec_stdout", "SERVER", "")
        #_logger_("MAIN", "HTTPHandler.get_exec_stdout", "SERVER", "")
        return (self.execution_stdout)
    
    def template_print(self, string, end = '\n'):
        #logger("MAIN", "HTTPHandler.template_print", "SERVER", "")
        #_logger_("MAIN", "HTTPHandler.template_print", "SERVER", "")
        self.execution_stdout += (string + end)

    def reset_exec_stdout(self):
        #logger("MAIN", "HTTPHandler.reset_exec_stdout", "SERVER", "")
        #_logger_("MAIN", "HTTPHandler.reset_exec_stdout", "SERVER", "")
        self.execution_stdout = ""

    def execute_template(self, path, parameters):
        #logger("HTTPHandler", "execute_template", "SERVER", "")
        #_logger_("HTTPHandler", "execute_template", "SERVER", "")
        template   = ""
        holder     = ""
        scripts    = []
        script_indents = []
        found_code = False
        i          = 0
        result     = ""

        with open((self.config["root-path"] + self.config["paths"]["templates"] + path), 'r') as f_in:
            template = f_in.read()

        while (i < len(template)):
            if (template[i] == '<'):
                if not(i == (len(template) - 2)):
                    if (template[i + 1] == '%'):
                        # Capture the indentation of the line containing the
                        # embedded Python block. This is later applied to every
                        # line emitted by that block.
                        line_start = template.rfind('\n', 0, i) + 1
                        line_prefix = template[line_start:i]
                        if line_prefix.strip() == "":
                            script_indents.append(line_prefix)
                        else:
                            # Inline Python (e.g. <div><%...%>) should remain
                            # inline and must not acquire the surrounding text
                            # as indentation.
                            script_indents.append("")

                        j = (i + 2)

                        while (j < (len(template) - 1)):
                            if (template[j] == '%'):
                                if not(j == (len(template) - 1)):
                                    if (template[j + 1] == '>'):
                                        result += ("%>" + str(len(scripts)) + "<%")

                                        scripts.append(holder)

                                        holder  = ""
                                        i       = (j + 1)
                                        break
                                    else:
                                        holder += template[j]
                                else:
                                    holder += template[j]
                            else:
                                holder += template[j]
                            j += 1
                    else:
                        result += template[i]
                else:
                    result += template[i]
            else:
                result += template[i]
            i += 1

        for s, script in enumerate(scripts):
            lines      = script.split('\n')
            code_lines = []

            for line in lines:
                if not(is_blank(line)):
                    code_lines.append(line.replace('\t', '    '))

            indent = 0

            while ((code_lines[0][indent] == '\t') or (code_lines[0][indent] == ' ')):
                indent += 1

            corrected = ""

            for line in code_lines:
                corrected += (line[indent:].replace('\t', "    ") + '\n')

            ##logger("EXECUTING: " + corrected)
            exec(corrected)

            # Indent generated output to the same level as the <% marker,
            # but only when the marker is on an otherwise-whitespace line.
            output = self.get_exec_stdout()
            output_indent = script_indents[s]

            if output_indent:
                output_lines = output.splitlines(True)
                indented_output = ""

                for output_line in output_lines:
                    if output_line.strip("\r\n") == "":
                        indented_output += output_line
                    else:
                        line_ending = ""
                        if output_line.endswith("\r\n"):
                            line_ending = "\r\n"
                            content = output_line[:-2]
                        elif output_line.endswith("\n"):
                            line_ending = "\n"
                            content = output_line[:-1]
                        elif output_line.endswith("\r"):
                            line_ending = "\r"
                            content = output_line[:-1]
                        else:
                            content = output_line

                        indented_output += output_indent + content + line_ending

                output = indented_output

            # Both standalone and inline <% ... %> blocks use the template's
            # own surrounding whitespace for the final line termination.
            # template_print() defaults to adding a newline, so remove only
            # that final generated newline. Internal newlines are preserved.
            if output.endswith("\r\n"):
                output = output[:-2]
            elif output.endswith("\n") or output.endswith("\r"):
                output = output[:-1]

            # For a standalone <% ... %> block, the template already has
            # indentation immediately before the marker. Remove that
            # indentation before inserting the generated output, because the
            # generated lines are explicitly indented above. This prevents
            # the first generated line from receiving the indentation twice.
            marker = "%>" + str(s) + "<%"
            marker_position = result.find(marker)

            if marker_position != -1 and output_indent:
                line_start = result.rfind("\n", 0, marker_position) + 1
                existing_prefix = result[line_start:marker_position]

                if existing_prefix.strip() == "":
                    result = result[:line_start] + result[marker_position:]

            result = result.replace(marker, output, 1)
            self.reset_exec_stdout()

        self.set_response_header("Content-Type", "text/html")
        self.set_response_header("Content-Length", str(len(result.encode("utf-8"))))
        self.print(result)

    # Determines what to do with a request.
    def handle_request(self):
        #logger("MAIN", "HTTPHandler.handle_request", "SERVER", "")
        #_logger_("MAIN", "HTTPHandler.handle_request", "SERVER", "")
        if (self.request["type"] == "GET"):
            self.do_get(self.request["path"], self.request["path-parameters"])
        elif (self.request["type"] == "HEAD"):
            self.do_head(self.request["path"], self.request["path-parameters"])
        elif (self.request["type"] == "POST"):
            self.do_post(self.request["path"], self.request["parameters"])
        elif (self.request["type"] == "PUT"):
            self.do_put(self.request["path"], self.request["parameters"])
        elif (self.request["type"] == "DELETE"):
            self.do_delete(self.request["path"], self.request["path-parameters"])
        elif (self.request["type"] == "CONNECT"):
            self.do_connect(self.request["path"], self.request["path-parameters"])
        elif (self.request["type"] == "OPTIONS"):
            self.do_options(self.request["path"], self.request["path-parameters"])
        elif (self.request["type"] == "TRACE"):
            self.do_trace(self.request["path"], self.request["path-parameters"])
        elif (self.request["type"] == "PATCH"):
            self.do_patch(self.request["path"], self.request["path-parameters"])
        else:
            self.set_response_header("Allow", "GET, HEAD, POST, PUT, DELETE, CONNECT, OPTIONS, TRACE, PATCH")
            self.set_error(
                "405",
                ("path=" + self.request["path"].replace("/", "%2F")),
                "get"
            )

    # Does a get method. It is in a separate function so that additional stuff can be added if required before an action is executed.
    def do_get(self, path, args):
        #logger("MAIN", "HTTPHandler.do_get", "SERVER", "")
        #_logger_("MAIN", "HTTPHandler.do_get", "SERVER", "")
        if (path == "/"):
            self.execute_action(self.config["default-location"], args, method = "get")
        else:
            self.execute_action(path, args, method = "get")

    # Does a HEAD method. The response headers are generated as for GET,
    # but the HTTP response body is omitted.
    def do_head(self, path, args):
        if path == "/":
            self.execute_action(self.config["default-location"], args, method="get")
        else:
            self.execute_action(path, args, method="get")

        if self.response is not None:
            header_end = self.response.find(b"\r\n\r\n")
            if header_end != -1:
                self.response = self.response[:header_end + 4]

    # Does a post method. It is in a separate function so that additional stuff can be added if required before an action is executed.
    def do_post(self, path, args):
        #logger("MAIN", "HTTPHandler.do_post", "SERVER", "")
        #_logger_("MAIN", "HTTPHandler.do_post", "SERVER", "")
        self.execute_action(path, args, method = "post")

    # Does a put method. It is in a separate function so that additional stuff can be added if required before an action is executed.
    def do_put(self, path, args):
        #logger("MAIN", "HTTPHandler.do_put", "SERVER", "")
        #_logger_("MAIN", "HTTPHandler.do_put", "SERVER", "")
        
        self.execute_action(path, args, method = "put")

    # Does a delete method. It is in a separate function so that additional stuff can be added if required before an action is executed.
    def do_delete(self, path, args):
        #logger("MAIN", "HTTPHandler.do_delete", "SERVER", "")
        #_logger_("MAIN", "HTTPHandler.do_delete", "SERVER", "")
        
        self.execute_action(path, args, method = "delete")
        
    # Does a connect method. It is in a separate function so that additional stuff can be added if required before an action is executed.
    def do_connect(self, path, args):
        #logger("MAIN", "HTTPHandler.do_connect", "SERVER", "")
        #_logger_("MAIN", "HTTPHandler.do_connect", "SERVER", "")
        
        self.execute_action(path, args, method = "connect")
    
    # Does a options method. It is in a separate function so that additional stuff can be added if required before an action is executed.
    def do_options(self, path, args):
        #logger("MAIN", "HTTPHandler.do_options", "SERVER", "")
        #_logger_("MAIN", "HTTPHandler.do_options", "SERVER", "")
        
        self.execute_action(path, args, method = "options")
    
    # Does a trace method. It is in a separate function so that additional stuff can be added if required before an action is executed.
    def do_trace(self, path, args):
        #logger("MAIN", "HTTPHandler.do_trace", "SERVER", "")
        #_logger_("MAIN", "HTTPHandler.do_trace", "SERVER", "")
        
        self.execute_action(path, args, method = "trace")

    # Does a patch method. It is in a separate function so that additional stuff can be added if required before an action is executed.
    def do_patch(self, path, args):
        #logger("MAIN", "HTTPHandler.do_patch", "SERVER", "")
        #_logger_("MAIN", "HTTPHandler.do_patch", "SERVER", "")
        
        self.execute_action(path, args, method = "patch")

    # Executes an action. The default method if one is not specified is get.
    def execute_action(self, action, args, method = "get", status = "200 OK"):
        try:
            #logger("MAIN", "HTTPHandler.execute_action", "SERVER", "")
            #_logger_("MAIN", "HTTPHandler.execute_action", "SERVER", "")
            
            # Parses the parameters from the http request that need to be passed as args to the `action`.
            parameters    = {}
            action_script = ""
            
            from urllib.parse import parse_qsl

            # Parse application/x-www-form-urlencoded/query-style parameters
            # using standard URL decoding rather than a partial hand-written map.
            for key, value in parse_qsl(args, keep_blank_values=True):
                parameters[key] = value

            # Preserve malformed bare arguments as None for compatibility.
            for arg in args.split("&"):
                if arg and "=" not in arg:
                    parameters[arg] = None

            # Attempts to execute the action as a python script.
            try:
                ##print("Action: " + absolute_path + (self.config["root-path"] + self.config["paths"]["actions"]["actions-root"] + self.config["paths"]["actions"][method] + action + ".py"))
                with open((self.config["root-path"] + self.config["paths"]["actions"]["actions-root"] + self.config["paths"]["actions"][method] + action + ".py"), 'r') as f_in:
                    action_script = f_in.read()
    
                # Setting http headers.
                self.set_response_header("Content-Type", "text/html;charset=utf-8")
                exec(action_script)
                
                self.set_response_header("Content-Length", str(len(self.response_body.encode())))
                
                self.set_response(status = status)
            except FileNotFoundError as fnfe:
                #logger("MAIN", "HTTPHandler.execute_action", "SERVER", "EXCEPTION: " + traceback.format_exc().replace('"', '&#34;').replace('<', "&#60;").replace('>', "&#62;").replace('\n', "<br>").replace(' ', "&#160;"))
                #_logger_("MAIN", "HTTPHandler.execute_action", "SERVER", "EXCEPTION: " + traceback.format_exc())
                
                self.get_file_bytes(action, method)
            except Exception as general_exception:
                #logger("MAIN", "HTTPHandler.execute_action", "SERVER", "EXCEPTION: " + traceback.format_exc().replace('"', '&#34;').replace('<', "&#60;").replace('>', "&#62;").replace('\n', "<br>").replace(' ', "&#160;"))
                #_logger_("MAIN", "HTTPHandler.execute_action", "SERVER", "EXCEPTION: " + traceback.format_exc())
                
                self.set_error("500", ("path=" + action.replace('/', "%2F")), method)
        except:
            #logger("MAIN", "HTTPHandler.execute_action", "SERVER", "EXCEPTION: " + traceback.format_exc())
            #_logger_("MAIN", "HTTPHandler.execute_action", "SERVER", "EXCEPTION: " + traceback.format_exc())
            pass

    # Gets the bytes of a file that matches the path from the url and puts them in the response.
    def get_file_bytes(self, path, method = "get", status = "200 OK"):
        #logger("MAIN", "HTTPHandler.get_file_bytes", "SERVER", "")
        #_logger_("MAIN", "HTTPHandler.get_file_bytes", "SERVER", "")
        try:
            # Reading file bytes.
            f_in = open((self.config["root-path"] + self.config["paths"]["public-files"] + path), "rb")
            file_bytes = f_in.read()

            # Setting http headers.
            content_type = self.config["content-types"][path.split(".")[-1:][0]]
            if content_type.startswith("text/") or content_type in (
                "application/json",
                "application/javascript",
                "application/xml",
                "application/xhtml+xml",
                "application/x-www-form-urlencoded",
            ):
                content_type += ";charset=utf-8"
            self.set_response_header("Content-Type", content_type)
            self.set_response_header("Content-Length", str(len(file_bytes)))

            # Setting http response.
            self.set_response(body = file_bytes, status = status)
            f_in.close()
        except Exception as e:
            #logger("MAIN", "HTTPHandler.get_file_bytes", "SERVER", "EXCEPTION: " + traceback.format_exc().replace('"', '&#34;').replace('<', "&#60;").replace('>', "&#62;").replace('\n', "<br>").replace(' ', "&#160;"))
            #_logger_("MAIN", "HTTPHandler.get_file_bytes", "SERVER", "EXCEPTION: " + traceback.format_exc())
            # If the bytes cannot be read, a 404 error is returned because the path does not exist.
            self.set_error("404", ("path=" + path.replace('/', "%2F")), method)

    def create_sqlite_connection(self, db_file):
        #logger("MAIN", "HTTPHandler.create_sqlite_connection", "SERVER", "")
        #_logger_("MAIN", "HTTPHandler.create_sqlite_connection", "SERVER", "")
        
        connection = None

        try:
            #logger("MAIN", "HTTPHandler.create_sqlite_connection", "SERVER", ("CONNECTING TO: " + self.config["root-path"] + self.config["paths"]["private-files"] + "/databases/" + db_file))
            connection = sqlite3.connect(self.config["root-path"] + self.config["paths"]["private-files"] + "/databases/" + db_file)
        except Error as e:
            #logger("MAIN", "HTTPHandler.create_sqlite_connection", "SERVER", "EXCEPTION: " + traceback.format_exc().replace('"', '&#34;').replace('<', "&#60;").replace('>', "&#62;").replace('\n', "<br>").replace(' ', "&#160;"))
            pass
        return (connection)
    
    def respond_to_request(self, client_request, request_origin, redirect_to_ssl, true_path):
        self.origin            = request_origin
        self.http_request      = client_request
        self.http_request_data = ""
        self.execution_stdout  = ""
        self.request           = {}
        self.response_headers  = {}
        self.response_cookies  = []
        self.response_body     = ""
        self.response          = None
        
        self.parse_request() # Parses the http request into a dictionary.)
        
        if (redirect_to_ssl):
            if (true_path):
                self.request["path-parameters"] = ("location=" + self.request["path"].replace('/', "%2F"))
            else:
                self.request["path-parameters"] = ("location=" + ("%2F"))
            
            self.request["path"] = "/redirecttossl"
        
        self.handle_request() # Determines what to do with the request, and what to respond to the client with.
        
        return(self.response)
#END HTTPHandler Class
