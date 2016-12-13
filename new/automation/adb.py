import logging
import re
import subprocess


class LogCaptureContext(object):
    class FileCapture(object):
        def __init__(self, fh, proc):
            self.fh = fh
            self.proc = proc
            assert self.proc.poll() is None, 'file capture failed - process not running'

        def close(self):
            self.proc.kill()
            self.proc.wait()
            self.fh.flush()
            self.fh.close()

        def __del__(self):
            assert self.proc.poll() is not None, 'file capture process not terminated'
            assert self.fh.closed, 'file capture is not closed'

    def __init__(
            self,
            adb,
            logcat_file_name,
            logcat_params,
            tz_log_file_name,
            device_tz_log_file
    ):
        self.logger = logging.getLogger('Log-Capture')

        self.adb = adb

        self.logcat_file_name = logcat_file_name
        self.logcat_params = logcat_params

        self.tz_log_file_name = tz_log_file_name
        self.device_tz_log_file = device_tz_log_file

        self.logcat_capture = None
        self.tzlog_capture = None

    def __enter__(self):
        assert not self.tzlog_capture, 'Already Collecting Logcat'
        assert not self.logcat_capture, 'Already Collecting TZ Log'

        cmd = [self.adb.raw_cmd(timeout_in_sec=0), 'logcat' ]
        if self.logcat_params:
            cmd.append(self.logcat_params)

        self.logger.debug('bg>> ' + ' '.join(cmd))
        fh = open(self.logcat_file_name, 'wb')
        self.logcat_capture = self.FileCapture(
            fh,
            subprocess.Popen(cmd, stderr=subprocess.STDOUT, stdout=fh)
        )

        if self.device_tz_log_file:
            cmd = [self.adb.raw_cmd(timeout_in_sec=0), 'shell', 'cat ' + self.device_tz_log_file ]
            self.logger.debug('bg>>' + ' '.join(cmd))
            fh = open(self.tz_log_file_name, 'wb')
            self.tzlog_capture = self.FileCapture(
                fh,
                subprocess.Popen(cmd, stderr=subprocess.STDOUT, stdout=fh)
            )
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        assert self.tzlog_capture, 'Not Collecting Logcat'
        assert self.logcat_capture, 'Not Collecting TZ Log'

        self.tzlog_capture.close()
        self.tzlog_capture = None
        self.logcat_capture.close()
        self.logcat_capture = None


class Adb(object):
    DEFAULT_TIMEOUT_IN_SEC = 300

    def __init__(self, platform_tools_path):
        self.logger = logging.getLogger('ADB')
        self.platform_tools_path = platform_tools_path if platform_tools_path else ''

    def raw_cmd(self, timeout_in_sec=DEFAULT_TIMEOUT_IN_SEC, cmd='adb'):
        # type: (int, str) -> str
        full_cmd = cmd if not self.platform_tools_path else self.platform_tools_path.rstrip('/') + '/' + cmd
        if timeout_in_sec:
            return 'timeout {timeout_in_sec}s {cmd}'.format(
                timeout_in_sec=str(timeout_in_sec),
                cmd=full_cmd)

        return full_cmd

    def push(self, src, dst, timeout_in_sec=DEFAULT_TIMEOUT_IN_SEC):
        cmd = self.raw_cmd(timeout_in_sec) + ' push {0} {1}'.format(src, dst)
        self.logger.debug('>> ' + cmd)
        subprocess.check_call(cmd, shell=True)

    def pull(self, src, dst, timeout_in_sec=DEFAULT_TIMEOUT_IN_SEC):
        cmd = self.raw_cmd(timeout_in_sec) + ' pull {0} {1}'.format(src, dst)
        self.logger.debug('>> ' + cmd)
        subprocess.check_call(cmd, shell=True)

    def shell_check_call(self, shell_cmd, timeout_in_sec=DEFAULT_TIMEOUT_IN_SEC):
        cmd = self.raw_cmd(timeout_in_sec) + r' shell "{} ; echo \$? > /data/local/tmp/ta-res.txt"'.format(shell_cmd)
        self.logger.debug('>> ' + cmd)
        subprocess.check_call(cmd, shell=True)
        try:
            result = int(self.shell_check_output('cat /data/local/tmp/ta-res.txt', timeout_in_sec=5))
            if result != 0:
                raise subprocess.CalledProcessError(result, cmd)
        except ValueError:
            raise subprocess.CalledProcessError(666, cmd)

    def shell_check_output(self, shell_cmd, timeout_in_sec=DEFAULT_TIMEOUT_IN_SEC):
        cmd = self.raw_cmd(timeout_in_sec) + ' shell "{}"'.format(shell_cmd)
        self.logger.debug('>> ' + cmd)
        return subprocess.check_output(cmd, shell=True, stderr=subprocess.STDOUT)

    def reset(self):
        cmd = self.raw_cmd() + ' reset'
        self.logger.debug('>> ' + cmd)
        subprocess.check_call(cmd, shell=True)

    def root(self):
        cmd = self.raw_cmd() + ' root'
        self.logger.debug('>> ' + cmd)
        subprocess.check_call(cmd, shell=True)

    def remount(self):
        cmd = self.raw_cmd() + ' remount'
        self.logger.debug('>> ' + cmd)
        subprocess.check_call(cmd, shell=True)

    def wait_for_device(self, timeout_in_sec=DEFAULT_TIMEOUT_IN_SEC):
        cmd = self.raw_cmd(timeout_in_sec) + ' wait-for-device'
        self.logger.debug('>> ' + cmd)
        subprocess.check_call(cmd, shell=True)

    def start_log_capture(self, logcat_file_name, logcat_params, tz_log_file_name, device_tz_log_file):
        return LogCaptureContext(
            adb=self,
            logcat_file_name=logcat_file_name,
            logcat_params=logcat_params,
            tz_log_file_name=tz_log_file_name,
            device_tz_log_file=device_tz_log_file

        )


class NetworkAdb(Adb):
    def __init__(self, ip, platform_tools_path=None):
        super(NetworkAdb, self).__init__(platform_tools_path)
        assert ip
        self.ip = ip
        cmd = self.raw_cmd(timeout_in_sec=10) + ' connect {0}'.format(self.ip)
        self.logger.debug('>> ' + cmd)
        subprocess.check_call(cmd, shell=True)

    def __del__(self):
        cmd = self.raw_cmd(timeout_in_sec=10) + ' disconnect {0}'.format(self.ip)
        self.logger.debug('>> ' + cmd)
        subprocess.check_call(cmd, shell=True)


class UsbAdb(Adb):
    def __init__(self, device_serial_number=None, platform_tools_path=None):
        super(UsbAdb, self).__init__(platform_tools_path)
        self.device_serial_number = device_serial_number
        if device_serial_number:
            assert self.device_serial_number in self.list_devices()

    def raw_cmd(self, timeout_in_sec=Adb.DEFAULT_TIMEOUT_IN_SEC, cmd='adb'):
        if self.device_serial_number:
            return super(UsbAdb, self).raw_cmd(timeout_in_sec, cmd) + ' -s {0}'.format(self.device_serial_number)
        return super(UsbAdb, self).raw_cmd(timeout_in_sec, cmd)

    def list_devices(self):
        cmd = self.raw_cmd(5) + ' devices'
        self.logger.debug('>> ' + cmd)
        out = subprocess.check_output(cmd, shell=True)
        pattern = re.compile(r'^([0-9a-fA-F]+)\s+device', re.MULTILINE)
        return pattern.findall(out)

if __name__ == '__main__':
    pass

    # logging.basicConfig(
    #     level=logging.DEBUG,
    #     format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    # )
    # __adb = UsbAdb()
    # __adb.shell_check_call('ls /data/local/tmp')
    # __adb.shell_check_output('ls -la /data/local/tmp')
    # logging.info('done')
