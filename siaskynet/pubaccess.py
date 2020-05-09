import json
import os
import string

import requests


class Pubaccess:

    @staticmethod
    def uri_pubaccess_prefix():
        return "scp://"

    @staticmethod
    def default_upload_options():
        return type('obj', (object,), {
            'portal_url': 'https://scp.techandsupply.ca',
            'portal_upload_path': 'pubaccess/pubfile',
            'portal_file_fieldname': 'file',
            'portal_directory_file_fieldname': 'files[]',
            'custom_filename': ''
        })

    @staticmethod
    def default_download_options():
        return type('obj', (object,), {
            'portal_url': 'https://scprime.hashpool.eu',
        })

    @staticmethod
    def strip_prefix(str):
        if str.startswith(Pubaccess.uri_pubaccess_prefix()):
            return str[len(Pubaceess.uri_pubaccess_prefix()):]
        return str

    @staticmethod
    def upload_file(path, opts=None):
        return Pubaccess.uri_pubaccess_prefix() + Pubaccess.upload_file_request(path, opts).json()["publink"]

    @staticmethod
    def upload_file_request(path, opts=None):
        if opts is None:
            opts = Pubaccess.default_upload_options()

        with open(path, 'rb') as f:
            host = opts.portal_url
            path = opts.portal_upload_path
            url = f'{host}/{path}'
            r = requests.post(url, files={opts.portal_file_fieldname: f})
        return r

    @staticmethod
    def upload_file_request_with_chunks(path, opts=None):
        if opts is None:
            opts = Pubaccess.default_upload_options()

        filename = opts.custom_filename if opts.custom_filename else path

        r = requests.post("%s/%s?filename=%s" % (opts.portal_url, opts.portal_upload_path,
                                                 filename), data=path, headers={'Content-Type': 'application/octet-stream'})
        return r

    @staticmethod
    def upload_directory(path, opts=None):
        r = Pubaccess.upload_directory_request(path, opts)
        sia_url = Pubaccess.uri_pubaccess_prefix() + r.json()["publink"]
        r.close()
        return sia_url

    @staticmethod
    def upload_directory_request(path, opts=None):
        if os.path.isdir(path) == False:
            print("Given path is not a directory")
            return

        if opts is None:
            opts = Pubaccess.default_upload_options()

        ftuples = []
        files = list(Pubaccess.walk_directory(path).keys())
        for file in files:
            ftuples.append((opts.portal_directory_file_fieldname,
                            (file, open(file, 'rb'))))

        filename = opts.custom_filename if opts.custom_filename else path

        host = opts.portal_url
        path = opts.portal_upload_path
        url = f'{host}/{path}?filename={filename}'
        r = requests.post(url, files=ftuples)
        return r

    @staticmethod
    def download_file(path, publink, opts=None):
        r = pubaccess.download_file_request(publink, opts)
        open(path, 'wb').write(r.content)
        r.close()

    @staticmethod
    def download_file_request(publink, opts=None, stream=False):
        if opts is None:
            opts = Pubaccess.default_download_options()

        portal = opts.portal_url
        publink = Pubaccess.strip_prefix(publink)
        url = f'{portal}/{publink}'
        r = requests.get(url, allow_redirects=True, stream=stream)
        return r

    @staticmethod
    def metadata(publink, opts=None):
        r = Pubaccess.metadata_request(publink, opts)
        return json.loads(r.headers["skynet-file-metadata"])

    @staticmethod
    def metadata_request(publink, opts=None, stream=False):
        if opts is None:
            opts = Pubaccess.default_download_options()

        portal = opts.portal_url
        publink = Pubaccess.strip_prefix(publink)
        url = f'{portal}/{publink}'
        r = requests.head(url, allow_redirects=True, stream=stream)
        return r

    @staticmethod
    def walk_directory(path):
        files = {}
        for root, subdirs, subfiles in os.walk(path):
            for subdir in subdirs:
                files.update(Pubaccess.walk_directory(os.path.join(root, subdir)))
            for subfile in subfiles:
                fullpath = os.path.join(root, subfile)
                files[fullpath] = True
        return files
    
