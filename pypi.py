#!/usr/bin/python3
# -*- coding: utf-8 -*-

import os
import sys
import json
import requests
import stat
import configparser
import hashlib
from configparser import ConfigParser
from urllib.request import urlretrieve


def get_config(conf, sec, opt):
    cnf = ConfigParser()
    cnf.read(conf)
    return cnf[sec][opt]

def local_check(name, version):
    path = get_config('config.ini', 'downloads', 'basedir')
    path = os.path.join(path, name)
    if os.path.exists(path):
        for root, dirs, files in os.walk(path):
            for file in files:
                name = name + '-' + version + '.tar.gz'
                if file == name:
                    return True
                else:
                    return False
    else:
        return 'path not found.'

def pkg_info(package, version):
    download_url = ""
    filename = ""
    digests = {}
    results = {}
    # Loop over each package and get its download URL from PyPI
    url = f"https://pypi.org/pypi/{package}/json"
    response = requests.get(url)
    
    if response.status_code == 404:
        print(f"The package {package} is not available on PyPI")
    else:
        # Get the latest version number and its download URL
        package_info = response.json()
        for i, item in enumerate(package_info["releases"][version]):
            if 'tar.gz' in item['filename']:
                results.setdefault(package, {})
                results[package]['url'] = item['url']
                results[package]['sig'] = item['digests']['sha256']
                results[package]['file'] = item['filename']
                results[package]['latest'] = package_info["info"]["version"]
    return results

def download(url, dst):
    filename = url.split('/')[-1]
    if not os.path.exists(dst):
        os.mkdir(dst)
    local_filename, headers = urlretrieve(url, os.path.join(dst, filename))
    request = open(local_filename)
    request.close()    

def check_hash(filename, filesig):
    sha256_hash = hashlib.sha256()
    local_filesig =''
    with open(filename,"rb") as f:
        # Read and update hash string value in blocks of 4K
        for byte_block in iter(lambda: f.read(4096),b""):
            sha256_hash.update(byte_block)
        local_filesig = sha256_hash.hexdigest()
    if local_filesig == filesig:
        return True
    else:
        return False

def permission():
    user = get_config('config.ini', 'downloads', 'uid')
    group = get_config('config.ini', 'downloads', 'gid')
    path = get_config('config.ini', 'downloads', 'basedir')
    os.system('chown -R '+user+':'+group+' '+path)
    for root, dirs, files in os.walk(path):
        for dir in dirs:
            # os.chmod(os.path.join(root, dir), 0o755)
            dir_perm = os.stat(os.path.join(root, dir))
            print('dir: ', os.path.join(root, dir), dir_perm.st_mode)
        for file in files:
            # os.chmod(os.path.join(root, file), 0o644)
            file_perm = os.stat(os.path.join(root, file))
            print('file: ', os.path.join(root, file), file_perm.st_mode)
            
def run():
    packages = ["requests-2.27.1"]
    # packages = ["requests-2.28.2"]
    version = ''
    package = ''
    url = ''
    filename = ''
    filesig = ''
    basepath = get_config('config.ini', 'downloads', 'basedir')
    dest_path = ''
    for package in packages:
        version = package.split('-')[1]
        package = package.split('-')[0]
        dest_path = os.path.join(basepath, package)
        if local_check(package, version):
            print('local copy exists.')
        else:
            info = pkg_info(package, version)
            url = info[package]['url']
            filename = info[package]['file']
            filesig = info[package]['sig']
            download(url, dest_path)
            if check_hash(os.path.join(dest_path, filename), filesig):
                print('file hash ok.')
            else:
                print('file hash not ok.')

if __name__ == '__main__':
    # run()
    permission()
