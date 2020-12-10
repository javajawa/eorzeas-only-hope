#!/usr/bin/python3
# vim: ts=4 expandtab

"""Only Hope Bot"""

from __future__ import annotations

from typing import Dict, Optional, Tuple

import base64
import bcrypt
import datetime
import os
import time
import shutil
import urllib.parse

from http.server import BaseHTTPRequestHandler as Handler

from eorzea.storage import DataStore


FILES: Dict[str, Tuple[str, str]] = {
    "/": ("html/welcome.html", "text/html"),
    "/favicon.ico": ("html/favicon.png", "image/png"),
}


class StatusHandler(Handler):
    server_version = "StellarisEmpireSharer"
    protocol_version = "HTTP/1.1"
    storage: DataStore

    def do_GET(self: StatusHandler) -> None:
        """Serve a GET request."""

        username, role = self.auth()

        if not username:
            self.send_auth_challenge()
            return

        # Get the actual request path, excluding the query string.
        path: str = urllib.parse.urlparse(self.path).path

        if path in FILES:
            filename, mime = FILES[path]
            self.page_file(filename, mime)
            return

        if path == "/moderate":
            self.moderate()

        self.send_error(404, f"Path not found {path}")
        return

    def auth(self) -> Tuple[Optional[bytes], Optional[bytes]]:
        """Checks if a user is authorised"""

        auth: bytes = self.headers["authorization"]

        if not auth:
            print("No auth header")
            return None, None

        try:
            auth = base64.b64decode(auth[6:])
            [user, password] = auth.split(b":", 1)
        except Exception as ex:
            print("Invalid auth header " + str(ex))
            return None, None

        if not user or not password:
            return None, None

        # Open up the current user database.
        with open("users.txt", "r+b") as user_file:
            for line in user_file:
                if line.startswith(b"#") or b":" not in line:
                    continue

                [file_user, role, hashed] = line.strip(b"\n").split(b":", 2)

                if file_user == user.lower():
                    return user, role if bcrypt.checkpw(password, hashed) else None

            # If not matched, add a new user to the file.
            hashed = bcrypt.hashpw(password, bcrypt.gensalt())
            user_file.write(user.lower() + b":none:" + hashed + b"\n")

        return user, role

    def send_auth_challenge(self) -> None:
        self.send_response(401)
        self.send_header(
            "WWW-Authenticate",
            'basic realm="Stellaris Empire Exchange -- Pick a username and password"'
            + 'charset="utf-8"',
        )
        self.send_header("Content-Type", "text/plain")
        self.send_header("Content-Length", "5")
        self.end_headers()

        self.wfile.write(b"Hello")

    def page_file(self, filename: str, mime: str) -> None:
        """Sends an on-disk file to the client, with the given mime type"""

        # 404 if the file is not found.
        if not os.path.exists(filename):
            self.send_error(404, f"File not {filename} found on disk")
            return

        mod_date: int = 0

        if "If-Modified-Since" in self.headers:
            mod_date = int(
                datetime.datetime.strptime(
                    str(self.headers["If-Modified-Since"]), "%a, %d %b %Y %H:%M:%S GMT"
                ).timestamp()
            )

        with open(filename, "rb") as contents:
            # stat(2) the file handle to get the file size.
            stat = os.fstat(contents.fileno())

            if int(stat.st_mtime) <= mod_date:
                self.send_304(stat)

                return

            # Send the HTTP headers.
            self.send_response(200)
            self.send_header("Content-Type", mime)
            self.send_header("Content-Length", str(stat.st_size))
            self.send_header("Last-Modified", self.date_time_string(int(stat.st_mtime)))
            self.send_header("Cache-Control", "public; max-age=3600")
            self.send_header("Expires", self.date_time_string(int(time.time() + 3600)))

            self.end_headers()

            # Send the file to the client
            shutil.copyfileobj(contents, self.wfile)

    def send_304(self, stat: os.stat_result) -> None:
        self.send_response(304)
        self.send_header("Last-Modified", self.date_time_string(int(stat.st_mtime)))
        self.send_header("Cache-Control", "public; max-age=3600")
        self.send_header("Expires", self.date_time_string(int(time.time() + 3600)))
        self.end_headers()

    def moderate(self) -> None:
        self.send_response(200)
        self.send_header("Cache-Control", "private")
        self.send_header("Content-Type", "text/plain; charset=utf-8")
        self.end_headers()

        for value in self.storage.moderation_queue():
            self.wfile.write(str(value).encode("utf-8"))
