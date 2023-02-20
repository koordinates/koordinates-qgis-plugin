#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import fnmatch
import os
import subprocess
import re
import shutil
import sys
import urllib.parse
import xmlrpc.client
import zipfile
from configparser import ConfigParser
from io import StringIO


def package(version=None):
    if not version or version.startswith("dev-"):
        # CI uses dev-{SHA}
        archive = "koordinates.zip"
    else:
        archive = f"koordinates-{version}.zip"
    print(f"Creating {archive} ...")

    with zipfile.ZipFile(archive, "w", zipfile.ZIP_DEFLATED) as zipFile:
        excludes = {"test", "test", "*.pyc", ".git", "metadata.txt"}
        src_dir = os.path.join(os.path.dirname(__file__), "koordinates")
        exclude = lambda p: any([fnmatch.fnmatch(p, e) for e in excludes])

        cfg = ConfigParser()
        cfg.optionxform = str
        cfg.read(os.path.join(src_dir, "metadata.txt"))

        if version:
            cfg.set("general", "version", re.sub(r"^v", "", version))

        buf = StringIO()
        cfg.write(buf)
        zipFile.writestr("koordinates/metadata.txt", buf.getvalue())

        def filter_excludes(files):
            if not files:
                return []
            for i in range(len(files) - 1, -1, -1):
                f = files[i]
                if exclude(f):
                    files.remove(f)
            return files

        for root, dirs, files in os.walk(src_dir):
            for f in filter_excludes(files):
                relpath = os.path.relpath(root, ".")
                zipFile.write(os.path.join(root, f), os.path.join(relpath, f))
            filter_excludes(dirs)


def install(profile: str = None):
    if not profile:
        profile = 'default'

    src = os.path.join(os.path.dirname(__file__), "koordinates")
    if os.name == "nt":
        default_profile_plugins = (
            f"~/AppData/Roaming/QGIS/QGIS3/profiles/{profile}/python/plugins"
        )
    elif sys.platform == "darwin":
        default_profile_plugins = (
            f"~/Library/Application Support/QGIS/QGIS3/profiles/{profile}/python/plugins"
        )
    else:
        default_profile_plugins = (
            f"~/.local/share/QGIS/QGIS3/profiles/{profile}/python/plugins"
        )

    dst_plugins = os.path.expanduser(default_profile_plugins)
    os.makedirs(dst_plugins, exist_ok=True)
    dst = os.path.abspath(os.path.join(dst_plugins, "koordinates"))
    print(f"Installing to {dst} ...")
    src = os.path.abspath(src)
    if os.path.exists(dst):
        try:
            os.remove(dst)
        except IsADirectoryError:
            shutil.rmtree(dst)
    if not hasattr(os, "symlink"):
        shutil.copytree(src, dst)
    elif not os.path.exists(dst):
        os.symlink(src, dst, True)


def setup():
    extlibs = os.path.join(os.path.dirname(__file__), "koordinates", "extlibs")
    os.makedirs(extlibs, exist_ok=True)
    reqs = open("requirements.txt").readlines()
    os.environ["PYTHONPATH"] = extlibs
    for req in reqs:
        try:
            subprocess.check_call(
                [
                    sys.executable,
                    "-m",
                    "pip",
                    "install",
                    "--upgrade",
                    "-t",
                    extlibs,
                    req,
                ]
            )
        except subprocess.CalledProcessError:
            print(f"Error installing {req} with pip.")
            sys.exit(1)


def publish(archive):
    try:
        creds = os.environ["QGIS_CREDENTIALS"]
    except KeyError:
        print("QGIS_CREDENTIALS not set")
        sys.exit(2)

    url = f"https://{creds}@plugins.qgis.org/plugins/RPC2/"
    conn = xmlrpc.client.ServerProxy(url)
    print(f"Uploading {archive} to https://plugins.qgis.org ...")
    with open(archive, "rb") as fd:
        blob = xmlrpc.client.Binary(fd.read())
    conn.plugin.upload(blob)
    print(f"Upload complete")


def usage():
    print(
        (
            "Usage:\n"
            f"  {sys.argv[0]} package [VERSION]      Build a QGIS plugin zip file\n"
            f"  {sys.argv[0]} install [profile name] Install in your local QGIS (for development)\n"
        ),
        file=sys.stderr,
    )
    sys.exit(2)


if len(sys.argv) >= 2 and sys.argv[1] == "install":
    install(profile=(None if len(sys.argv) < 3 else sys.argv[2]))
elif len(sys.argv) == 2 and sys.argv[1] == "setup":
    setup()
elif len(sys.argv) in [2, 3] and sys.argv[1] == "package":
    package(*sys.argv[2:])
elif len(sys.argv) == 3 and sys.argv[1] == "publish":
    publish(sys.argv[2])
else:
    usage()
