'''
Author: seven 865762826@qq.com
Date: 2023-03-23 18:23:08
LastEditors: seven 865762826@qq.com
LastEditTime: 2023-05-08 10:31:32
'''
from .libTOSUN import *

import atexit
# _curr_path = os.path.dirname(__file__)
# _arch, _os = platform.architecture()
# _os = platform.system()
# _is_windows, _is_linux = False, False
# if 'windows' in _os.lower():
#     _is_windows = True
#     if _arch == '32bit':
#         from .windows.x86.parse_xml import *
#     else:
#         from .windows.x64.parse_xml import *

# elif 'linux' in _os.lower():
#     _is_linux = True
#     if _arch == '64bit':
#         from .linux.parse_xml import *

initialize_lib_tsmaster(True,True,False)




def close():
    tsapp_disconnect_all()
    finalize_lib_tscan()


atexit.register(close)