
import os
import time

from skin_engine.versioning import departurebox_version


def _app_root():
    try:
        path = str(__file__).replace('\\', '/')
        marker = '/skin_engine/faults.py'

        
        if path.endswith(marker):
            root = path[:-len(marker)]
            return root if root else '.'

        
        marker = 'skin_engine/faults.py'
        if path.endswith(marker):
            root = path[:-len(marker)].rstrip('/')
            return root if root else '.'
    except Exception:
        pass

    
    return '.'


def _log_dir():
    root = _app_root()
    if root == '.':
        return 'logs'
    return root.rstrip('/') + '/logs'


def _log_file():
    return _log_dir().rstrip('/') + '/skin_fault.log'


def _timestamp():
    try:
        t = time.localtime()
        return '%04d-%02d-%02d %02d:%02d:%02d' % (
            t.tm_year, t.tm_mon, t.tm_mday, t.tm_hour, t.tm_min, t.tm_sec
        )
    except Exception:
        try:
            return 'monotonic=' + str(time.monotonic())
        except Exception:
            return 'time=unknown'


def log_skin_fault(phase, skin_id, exc):
    skin_id = str(skin_id or '<unknown>')
    phase = str(phase or '<unknown>')
    message = str(exc)
    print('SKIN FAULT:', skin_id, phase, message)

    folder = _log_dir()
    path = _log_file()

    try:
        try:
            os.mkdir(folder)
            print('SKIN log folder created:', folder)
        except OSError:
            
            pass

        with open(path, 'a') as handle:
            handle.write('--- SKIN FAULT ---\n')
            handle.write('time: ' + _timestamp() + '\n')
            handle.write('departurebox: ' + str(departurebox_version()) + '\n')
            handle.write('skin: ' + skin_id + '\n')
            handle.write('phase: ' + phase + '\n')
            handle.write('exception: ' + repr(exc) + '\n\n')

        print('SKIN fault log:', path)
        return path

    except Exception as log_exc:
        print('SKIN FAULT LOG WRITE FAILED')
        print('SKIN log folder:', folder)
        print('SKIN log file:', path)
        print('SKIN log exception:', repr(log_exc))
        return None
