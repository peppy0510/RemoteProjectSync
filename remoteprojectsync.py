# encoding: utf-8


'''
author: Taehong Kim
email: peppy0510@hotmail.com

requirements:

description:

reference:

'''


import json
import os
import sublime
import sublime_plugin
import sys
import threading
import time

# try:
#     from scp import SCPClient
#     from paramiko import SSHClient
# except ImportError as error:
#     print(error)


try:
    from paramiko import SSHClient
except ImportError as error:
    print(error)


DIRECTORY_BLACKLIST = [
    '__pycache__', '__deprecated__',
    '.git', '.log', 'log', 'media',
    'node_modules', 'venv', 'static/fonts', 'static/images'
]


class UpdateThread(threading.Thread):

    def __init__(self, parent):
        self.parent = parent
        threading.Thread.__init__(self)
        self.__stop = threading.Event()
        self.start()

    def stop(self):
        self.__stop.set()

    def stopped(self):
        return self.__stop.is_set()

    def run(self):
        timeout_count = self.check_timeout / self.check_interval

        while (not self.stopped() and self.parent.activated and timeout_count > 0):
            time.sleep(self.check_interval)

            if not self.parent.pending_arrow_position:
                self.parent.view.run_command(
                    'korean_input_renderer', {'commands': self.commands})
                break

            timeout_count -= 1

        self.stop()


class KoreanInputRendererCommand(sublime_plugin.TextCommand):

    def __init__(self, view):
        sublime_plugin.TextCommand.__init__(self, view)

    def run(self, edit, commands):

        for command in commands:

            method = command['method']
            kwargs = command['kwargs']

            if method == 'cursor':
                self.view.sel().clear()
                self.view.sel().add(sublime.Region(**kwargs['region']))

            elif method == 'insert':
                self.view.insert(
                    edit, kwargs['offset'], kwargs['string'])

            elif method == 'replace':
                self.view.replace(
                    edit, sublime.Region(**kwargs['region']), kwargs['string'])

            elif method == 'erase':
                self.view.insert(
                    edit, sublime.Region(**kwargs['region']), kwargs['string'])


# class RemoteProjectSync:

class RemoteProjectSyncEventListener(sublime_plugin.ViewEventListener):

    def __init__(self, view):
        sublime_plugin.ViewEventListener.__init__(self, view)

    def on_activated(self):
        pass

    def __listdir_parents(self, path):
        return [os.path.join(path, v) for v in os.listdir(path)]

    def listdir_parents(self, path, depth=10):
        paths = []
        for i in range(depth):
            parts = os.path.split(path)
            path = parts[0]
            if not parts[1]:
                break
            paths += self.__listdir_parents(path)
        return paths

    def get_remotesync_preset(self):
        path = self.view.file_name()
        paths = self.listdir_parents(path)
        paths = [v for v in paths if v.endswith('.remotesync')]
        if not paths:
            return
        with open(paths[0], 'rb') as file:
            preset = json.loads(file.read().decode('utf-8'))
        return preset

    def on_post_save(self):
        path = self.view.file_name()

        preset = self.get_remotesync_preset()
        if not preset:
            return

        remotes = preset.get('REMOTES')
        ssh = SSHClient()
        ssh.load_system_host_keys()
        print(ssh)
        for remote in remotes:
            print(remote)
            port = remote.get('port', 22)
            hostname = remote.get('hostname')
            username = remote.get('username')

            ssh.connect(hostname, port=port, username=username)

        # print(self.listdir_parents(path))
        # for v in os.listdir(os.path.dirname(path)):
        #     print(v)
        # print(self.view.file_name())
        # print(self.view.file_name())
        # print(self.view.name())
        # print(self.view.scope_name())
        # print(self.view.view_id)
        # get_status
