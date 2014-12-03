'''
An interface to cleanly communicate with a systemd-nspawn container
'''
# Import python libs
import time
# Import salt libs
import salt.utils.vt


class Spawn(object):
    '''
    Spawn and control a container
    '''
    def __init__(self, loc, user, passwd):
        self.loc = loc
        self.user = user
        self.passwd = passwd
        self.term = self.__login()
        self.prompt = self.__get_prompt()

    def __login(self):
        '''
        Return the vt terminal object that controls the container
        '''
        cmd = 'systemd-nspawn -bD {0}'.format(self.loc)
        term = salt.utils.vt.Terminal(
                cmd,
                shell=True,
                log_stdout=True,
                log_stderr=True,
                stream_stdout=False,
                stream_stderr=False)
        boot_stdout = ''
        boot_stderr = ''
        while True:
            time.sleep(0.5)
            stdout, stderr = term.recv()
            if stderr:
                boot_stderr += stderr
            if stdout:
                boot_stdout += stdout
            if boot_stdout.strip().endswith('login:') and not stdout:
                term.sendline(self.user)
                time.sleep(0.5)
                term.sendline(self.passwd)
                term.recv()
                break
        return term

    def __get_prompt(self):
        '''
        Discover what the shell prompt looks like
        '''
        self.term.sendline('')
        time.sleep(0.5)
        stdout, stderr = self.term.recv(10000)
        return stdout.split()[-1]

    def send(self, cmd):
        '''
        Send in a command
        '''
        self.term.sendline(cmd)
        ret_stdout = ''
        ret_stderr = ''
        while True:
            stdout, stderr = self.term.recv()
            ret_stdout += stdout
            ret_stderr += stderr
            if not stdout:
                # check for the prompt
                comps = ret_stdout.split()
                if comps:
                    if comps[-1] == self.prompt:
                        break
            else:
                yield stdout, stderr

    def close(self):
        self.term.close()


if __name__ == '__main__':
    sp = Spawn('/root/arch', 'root', 'foo')
    for stdout, stderr in sp.send('pacman -Syu --noconfirm git'):
        print(stdout)
