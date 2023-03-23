from .libTOSUN import *
import atexit
_curr_path = os.path.dirname(__file__)
_arch, _os = platform.architecture()
_os = platform.system()
_is_windows, _is_linux = False, False
if 'windows' in _os.lower():
    _is_windows = True
    if _arch == '32bit':
        from .windows.x86.parse_xml import *
    else:
        from .windows.x64.parse_xml import *

elif 'linux' in _os.lower():
    _is_linux = True
    if _arch == '64bit':
        from .linux.parse_xml import *

initialize_lib_tsmaster(True,False)




def close():
    tsapp_disconnect_all()
    finalize_lib_tscan()


atexit.register(close)