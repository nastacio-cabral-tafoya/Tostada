import os
import ssl
import json
import time
import atexit
import socket
import secrets
import sqlite3
import datetime
import traceback
import subprocess
from sqlite3 import Error
from threading import Semaphore, Thread
from cryptography.fernet import Fernet

def encrypt(data, key):
    fernet = Fernet(key)
    return (fernet.encrypt(data.encode()))

def decrypt(data, key):
    fernet = Fernet(key)
    return (fernet.decrypt(data).decode())

def logger(logfile, logfunc, loguser, logstr):
    database_config = server_config["log-database"]
    database_type = database_config["type"].lower()

    if database_type == "sqlite":
        log_connection = None
        log_c = None

        try:
            log_connection = sqlite3.connect(
                database_config["sqlite-file"],
                timeout=30
            )
            log_c = log_connection.cursor()

            # Allow concurrent readers and make concurrent writers wait rather
            # than immediately failing with "database is locked".
            log_c.execute("PRAGMA journal_mode=WAL")
            log_c.execute("PRAGMA busy_timeout=30000")

            with open("Server_Config/log.sql", "r") as sql:
                log_c.executescript(sql.read())

            log_c.execute(
                "INSERT INTO log (logdate, logfile, logfunc, loguser, logstr) "
                "VALUES (?, ?, ?, ?, ?)",
                (
                    time.strftime("%m/%d/%Y %H:%M:%S %Z"),
                    logfile,
                    logfunc,
                    loguser,
                    logstr
                )
            )

            log_connection.commit()

        finally:
            if log_c is not None:
                log_c.close()
            if log_connection is not None:
                log_connection.close()

    elif database_type == "mysql":
        import mysql.connector

        mysql_config = database_config["mysql"]

        log_connection = mysql.connector.connect(
            host=mysql_config["host"],
            port=mysql_config["port"],
            database=mysql_config["database"],
            user=mysql_config["user"],
            password=mysql_config["password"]
        )

        log_c = log_connection.cursor()

        log_c.execute(
            "CREATE TABLE IF NOT EXISTS log ("
            "logdate VARCHAR(64), "
            "logfile TEXT, "
            "logfunc TEXT, "
            "loguser TEXT, "
            "logstr LONGTEXT"
            ")"
        )

        log_c.execute(
            "INSERT INTO log "
            "(logdate, logfile, logfunc, loguser, logstr) "
            "VALUES (%s, %s, %s, %s, %s)",
            (
                time.strftime("%m/%d/%Y %H:%M:%S %Z"),
                logfile,
                logfunc,
                loguser,
                logstr
            )
        )

        log_connection.commit()
        log_c.close()
        log_connection.close()

    else:
        raise ValueError(
            "Unsupported log database type: " + database_config["type"]
        )
#END #logger()


def _logger_(logfile, logfunc, loguser, logstr):
    try:
        with open("log.txt", 'a') as log_file:
            log_file.write(time.strftime("%m/%d/%Y %H:%M:%S %Z") + " -> " + logfile + ", " + logfunc + ", " + loguser + ", " + logstr + "\n\n")
    except:
        with open("log.txt", 'w') as log_file:
            log_file.write(time.strftime("%m/%d/%Y %H:%M:%S %Z") + " -> " + logfile + ", " + logfunc + ", " + loguser + ", " + logstr + "\n\n")
#END _logger_()

def is_blank(string):
    for ch in string:
        if ((ord(ch) >= 32) and (ord(ch) <= 126)):
            return (False)
    return (True)
#END is_blank()

def timeout_to_seconds(hms_notation):
    (hours, minutes, seconds) = hms_notation.split(':')
    
    hours   = int(hours)
    minutes = int(minutes)
    seconds = int(seconds)
    
    return ((hours * 3600) + (minutes * 60) + seconds)
#END timeout_to_seconds()


def _recv_http_request(client_connection, buffer_size):
    """Receive one complete HTTP/1.x request from a TCP connection.

    Reads the header section first, then determines the request-body framing
    from Content-Length or Transfer-Encoding. Returns the complete request
    as bytes. This server intentionally handles one request per connection.
    """
    data = bytearray()

    # Read until the HTTP header section is complete.
    while b"\r\n\r\n" not in data:
        chunk = client_connection.recv(buffer_size)
        if not chunk:
            break
        data.extend(chunk)

        # Avoid accepting an unbounded header section.
        if len(data) > 1024 * 1024:
            raise ValueError("HTTP request headers too large")

    header_end = data.find(b"\r\n\r\n")
    if header_end == -1:
        raise ValueError("Incomplete HTTP request headers")

    header_end += 4
    header_bytes = bytes(data[:header_end])

    # Parse the request headers without decoding the body.
    header_lines = header_bytes[:-4].decode("iso-8859-1").split("\r\n")
    if not header_lines or not header_lines[0]:
        raise ValueError("Invalid HTTP request line")

    content_length = None
    transfer_encoding = None

    for line in header_lines[1:]:
        if ":" not in line:
            raise ValueError("Invalid HTTP header")

        name, value = line.split(":", 1)
        name = name.strip().lower()
        value = value.strip()

        if name == "content-length":
            try:
                length = int(value, 10)
            except ValueError:
                raise ValueError("Invalid Content-Length")

            if length < 0:
                raise ValueError("Invalid Content-Length")

            if content_length is not None and content_length != length:
                raise ValueError("Conflicting Content-Length headers")

            content_length = length

        elif name == "transfer-encoding":
            if transfer_encoding is None:
                transfer_encoding = value.lower()
            else:
                transfer_encoding += ", " + value.lower()

    if content_length is not None and transfer_encoding is not None:
        raise ValueError("Both Transfer-Encoding and Content-Length present")

    # No request body framing means the request ends at the header section.
    if transfer_encoding is None and content_length is None:
        return bytes(data)

    # Content-Length framing.
    if transfer_encoding is None:
        body_needed = content_length
        while len(data) - header_end < body_needed:
            chunk = client_connection.recv(buffer_size)
            if not chunk:
                raise ValueError("Incomplete HTTP request body")
            data.extend(chunk)

        return bytes(data[:header_end + body_needed])

    # HTTP/1.1 chunked request body.
    encodings = [item.strip().lower() for item in transfer_encoding.split(",")]
    if not encodings or encodings[-1] != "chunked":
        raise ValueError("Unsupported Transfer-Encoding")

    body_start = header_end
    cursor = body_start

    # Decode chunks into a normal body, preserving the original headers.
    decoded_body = bytearray()

    while True:
        # Get a complete chunk-size line.
        while True:
            line_end = data.find(b"\r\n", cursor)
            if line_end != -1:
                break
            chunk = client_connection.recv(buffer_size)
            if not chunk:
                raise ValueError("Incomplete chunked request")
            data.extend(chunk)

        size_line = bytes(data[cursor:line_end])
        cursor = line_end + 2

        # Ignore chunk extensions after ';'.
        size_text = size_line.split(b";", 1)[0].strip()
        try:
            chunk_size = int(size_text, 16)
        except ValueError:
            raise ValueError("Invalid chunk size")

        if chunk_size == 0:
            # Consume the final CRLF after the zero-size chunk and any trailers.
            while True:
                trailer_end = data.find(b"\r\n\r\n", cursor)
                if trailer_end != -1:
                    cursor = trailer_end + 4
                    break

                # The empty trailer section is simply CRLF.
                if data[cursor:cursor + 2] == b"\r\n":
                    cursor += 2
                    break

                chunk = client_connection.recv(buffer_size)
                if not chunk:
                    raise ValueError("Incomplete chunked trailers")
                data.extend(chunk)
            break

        required = cursor + chunk_size + 2
        while len(data) < required:
            chunk = client_connection.recv(buffer_size)
            if not chunk:
                raise ValueError("Incomplete chunk data")
            data.extend(chunk)

        decoded_body.extend(data[cursor:cursor + chunk_size])

        if data[cursor + chunk_size:cursor + chunk_size + 2] != b"\r\n":
            raise ValueError("Invalid chunk delimiter")

        cursor += chunk_size + 2

    # Reconstruct a request suitable for HTTPHandler.parse_request(), with
    # Transfer-Encoding removed and Content-Length set to the decoded body.
    request_head = bytearray(header_bytes[:-4])
    request_head_lines = request_head.decode("iso-8859-1").split("\r\n")

    rebuilt_headers = []
    for line in request_head_lines:
        if line.lower().startswith("transfer-encoding:"):
            continue
        if line.lower().startswith("content-length:"):
            continue
        rebuilt_headers.append(line)

    rebuilt_headers.append("Content-Length: " + str(len(decoded_body)))

    return (
        "\r\n".join(rebuilt_headers).encode("iso-8859-1")
        + b"\r\n\r\n"
        + bytes(decoded_body)
    )

def _handle_client(client_connection, client_address, redirect_to_ssl, true_path, thread_slots):
    try:
        client_request = _recv_http_request(
            client_connection,
            server_config["socket-buffer-size"]
        )

        # HTTPHandler contains mutable request/response state, so each worker
        # must have its own handler instance.
        request_handler = HTTPHandler()

        server_response = request_handler.respond_to_request(
            client_request,
            client_address,
            redirect_to_ssl,
            true_path
        )

        _logger_("MAIN", "listener", "SERVER RESPONSE", str(server_response))

        client_connection.sendall(server_response)

    except:
        logger(
            "MAIN",
            "listener",
            "SERVER",
            "EXCEPTION: " +
            traceback.format_exc()
                .replace('"', '&#34;')
                .replace('<', "&#60;")
                .replace('>', "&#62;")
                .replace('\n', "<br>")
                .replace(' ', "&#160;")
        )

    finally:
        try:
            client_connection.close()
        except:
            pass

        thread_slots.release()
#END _handle_client()

def listener(_socket_, redirect_to_ssl = False, true_path = False):
    logger("MAIN", "listener", "SERVER", "")

    thread_slots = Semaphore(server_config["max-threads"])

    while True:
        thread_slots.acquire()
        client_connection = None

        try:
            (client_connection, client_address) = _socket_.accept()
            client_connection.settimeout(10)

            Thread(
                target=_handle_client,
                args=(
                    client_connection,
                    client_address,
                    redirect_to_ssl,
                    true_path,
                    thread_slots
                ),
                daemon=True
            ).start()

        except:
            if client_connection is not None:
                try:
                    client_connection.close()
                except:
                    pass

            thread_slots.release()

            logger(
                "MAIN",
                "listener",
                "SERVER",
                "EXCEPTION: " +
                traceback.format_exc()
                    .replace('"', '&#34;')
                    .replace('<', "&#60;")
                    .replace('>', "&#62;")
                    .replace('\n', "<br>")
                    .replace(' ', "&#160;")
            )
            pass
#END listener()



def ssl_server():
    #logger("MAIN", "ssl_server", "SERVER", "")
    
    SERVER_HOST = server_config["server-host"]
    tcp_socket  = socket.socket(socket.AF_INET, socket.SOCK_STREAM, 0)
    
    if not(server_config["enable-https"]["enabled"]):
        raise Exception("HTTPS Disabled")
    
    SERVER_PORT = server_config["ssl-port"]
    context     = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
    context.load_cert_chain(server_config["cert-location"], server_config["key-location"])
    tcp_socket.bind((SERVER_HOST, SERVER_PORT))
    tcp_socket.listen(server_config["queue-limit"])
    ssl_tcp_socket = context.wrap_socket(tcp_socket, server_side=True, do_handshake_on_connect=False)
    listener(ssl_tcp_socket)
#END ssl_server()

absolute_path = ""

for location in os.path.realpath(__file__).split('\\')[:-1]:
    absolute_path += (location + '/')

try:
    os.chdir(absolute_path)
except:
    for location in os.path.realpath(__file__).split('/')[:-1]:
        absolute_path += (location + '/')

        os.chdir(absolute_path)
    
    #logger("MAIN", "INITIALIZATION OF ROOT PATH", "SERVER", "Exception 19 occurred. SERVER Likely Running in Linux Based OS.")

server_config = None

with open("Server_Config/server_config.json", 'r') as f_in:
    server_config = json.loads(f_in.read())

with open((absolute_path + "my_http_handler.py"), 'r') as f_in:
    exec(f_in.read())

initialized_handler = HTTPHandler()

ssl_server()






































