import os
from subprocess import Popen

PINTOOL = 'c:\\pin-2.11-49306-msvc10-ia32_intel64-windows\\source\\tools\\SimpleExamples\\obj-ia32\\v5.dll'
PINBAT = 'c:\\pin-2.11-49306-msvc10-ia32_intel64-windows\\pin.bat'
CWD = "c:\malware"
CMD = "{pin} -t {tool} {toolflags} -- {prefix} {sample} {sampleflags}"

os.chdir(CWD)

CMD = CMD.format(pin=PINBAT, tool=PINTOOL, )


