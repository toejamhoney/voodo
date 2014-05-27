vbox restore -v win7_a
vbox start -v win7_a
tool basic_tools.guest_exec -v win7_a -x c:\service\000066e2c2f7a16461859a8744e1fb90 -j 000066e2c2f7a16461859a8744e1fb90svc_samples_04 -l --delay 15
tool basic_tools.guest_exec -v win7_a -m event_logs -l -j 000066e2c2f7a16461859a8744e1fb90svc_samples_04
tool basic_tools.guest_exec -v win7_a -m shadow -j 000066e2c2f7a16461859a8744e1fb90svc_samples_04
tool basic_tools.guest_exec -v win7_a -m registry -l -j 000066e2c2f7a16461859a8744e1fb90svc_samples_04
tool basic_tools.guest_exec -v win7_a -m autorunsc -l -j 000066e2c2f7a16461859a8744e1fb90svc_samples_04 --diff
vbox kill -v win7_a

vbox restore -v win7_a
vbox start -v win7_a
tool basic_tools.guest_exec -v win7_a -x c:\service\00126b403d53ab6c91d21eb9971dbddf.exe -j 00126b403d53ab6c91d21eb9971dbddfsvc_samples_04 -l --delay 15
tool basic_tools.guest_exec -v win7_a -m event_logs -l -j 00126b403d53ab6c91d21eb9971dbddfsvc_samples_04
tool basic_tools.guest_exec -v win7_a -m shadow -j 00126b403d53ab6c91d21eb9971dbddfsvc_samples_04
tool basic_tools.guest_exec -v win7_a -m registry -l -j 00126b403d53ab6c91d21eb9971dbddfsvc_samples_04
tool basic_tools.guest_exec -v win7_a -m autorunsc -l -j 00126b403d53ab6c91d21eb9971dbddfsvc_samples_04 --diff
vbox kill -v win7_a

vbox restore -v win7_a
vbox start -v win7_a
tool basic_tools.guest_exec -v win7_a -x c:\service\00310a03e9638b1a13c8d07ff2a7dfcd.exe -j 00310a03e9638b1a13c8d07ff2a7dfcdsvc_samples_04 -l --delay 15
tool basic_tools.guest_exec -v win7_a -m event_logs -l -j 00310a03e9638b1a13c8d07ff2a7dfcdsvc_samples_04
tool basic_tools.guest_exec -v win7_a -m shadow -j 00310a03e9638b1a13c8d07ff2a7dfcdsvc_samples_04
tool basic_tools.guest_exec -v win7_a -m registry -l -j 00310a03e9638b1a13c8d07ff2a7dfcdsvc_samples_04
tool basic_tools.guest_exec -v win7_a -m autorunsc -l -j 00310a03e9638b1a13c8d07ff2a7dfcdsvc_samples_04 --diff
vbox kill -v win7_a

vbox restore -v win7_a
vbox start -v win7_a
tool basic_tools.guest_exec -v win7_a -x c:\service\0060b033a0b7ceca2200ae78d2c04e9e.exe -j 0060b033a0b7ceca2200ae78d2c04e9esvc_samples_04 -l --delay 15
tool basic_tools.guest_exec -v win7_a -m event_logs -l -j 0060b033a0b7ceca2200ae78d2c04e9esvc_samples_04
tool basic_tools.guest_exec -v win7_a -m shadow -j 0060b033a0b7ceca2200ae78d2c04e9esvc_samples_04
tool basic_tools.guest_exec -v win7_a -m registry -l -j 0060b033a0b7ceca2200ae78d2c04e9esvc_samples_04
tool basic_tools.guest_exec -v win7_a -m autorunsc -l -j 0060b033a0b7ceca2200ae78d2c04e9esvc_samples_04 --diff
vbox kill -v win7_a

vbox restore -v win7_a
vbox start -v win7_a
tool basic_tools.guest_exec -v win7_a -x c:\service\018f882e6ad52edaf3029ca9e043a822.exe -j 018f882e6ad52edaf3029ca9e043a822svc_samples_04 -l --delay 15
tool basic_tools.guest_exec -v win7_a -m event_logs -l -j 018f882e6ad52edaf3029ca9e043a822svc_samples_04
tool basic_tools.guest_exec -v win7_a -m shadow -j 018f882e6ad52edaf3029ca9e043a822svc_samples_04
tool basic_tools.guest_exec -v win7_a -m registry -l -j 018f882e6ad52edaf3029ca9e043a822svc_samples_04
tool basic_tools.guest_exec -v win7_a -m autorunsc -l -j 018f882e6ad52edaf3029ca9e043a822svc_samples_04 --diff
vbox kill -v win7_a

vbox restore -v win7_a
vbox start -v win7_a
tool basic_tools.guest_exec -v win7_a -x c:\service\019fd20fb884bcedd185df13c9e3a34a.exe -j 019fd20fb884bcedd185df13c9e3a34asvc_samples_04 -l --delay 15
tool basic_tools.guest_exec -v win7_a -m event_logs -l -j 019fd20fb884bcedd185df13c9e3a34asvc_samples_04
tool basic_tools.guest_exec -v win7_a -m shadow -j 019fd20fb884bcedd185df13c9e3a34asvc_samples_04
tool basic_tools.guest_exec -v win7_a -m registry -l -j 019fd20fb884bcedd185df13c9e3a34asvc_samples_04
tool basic_tools.guest_exec -v win7_a -m autorunsc -l -j 019fd20fb884bcedd185df13c9e3a34asvc_samples_04 --diff
vbox kill -v win7_a

vbox restore -v win7_a
vbox start -v win7_a
tool basic_tools.guest_exec -v win7_a -x c:\service\020d6dd4378bcd71771950003f6bbd37.exe -j 020d6dd4378bcd71771950003f6bbd37svc_samples_04 -l --delay 15
tool basic_tools.guest_exec -v win7_a -m event_logs -l -j 020d6dd4378bcd71771950003f6bbd37svc_samples_04
tool basic_tools.guest_exec -v win7_a -m shadow -j 020d6dd4378bcd71771950003f6bbd37svc_samples_04
tool basic_tools.guest_exec -v win7_a -m registry -l -j 020d6dd4378bcd71771950003f6bbd37svc_samples_04
tool basic_tools.guest_exec -v win7_a -m autorunsc -l -j 020d6dd4378bcd71771950003f6bbd37svc_samples_04 --diff
vbox kill -v win7_a

vbox restore -v win7_a
vbox start -v win7_a
tool basic_tools.guest_exec -v win7_a -x c:\service\031fa5c40dcdd7f8f0a092460cffad83.exe -j 031fa5c40dcdd7f8f0a092460cffad83svc_samples_04 -l --delay 15
tool basic_tools.guest_exec -v win7_a -m event_logs -l -j 031fa5c40dcdd7f8f0a092460cffad83svc_samples_04
tool basic_tools.guest_exec -v win7_a -m shadow -j 031fa5c40dcdd7f8f0a092460cffad83svc_samples_04
tool basic_tools.guest_exec -v win7_a -m registry -l -j 031fa5c40dcdd7f8f0a092460cffad83svc_samples_04
tool basic_tools.guest_exec -v win7_a -m autorunsc -l -j 031fa5c40dcdd7f8f0a092460cffad83svc_samples_04 --diff
vbox kill -v win7_a

vbox restore -v win7_a
vbox start -v win7_a
tool basic_tools.guest_exec -v win7_a -x c:\service\03bec2b8a715a5fac469cf7f059f1fb1.exe -j 03bec2b8a715a5fac469cf7f059f1fb1svc_samples_04 -l --delay 15
tool basic_tools.guest_exec -v win7_a -m event_logs -l -j 03bec2b8a715a5fac469cf7f059f1fb1svc_samples_04
tool basic_tools.guest_exec -v win7_a -m shadow -j 03bec2b8a715a5fac469cf7f059f1fb1svc_samples_04
tool basic_tools.guest_exec -v win7_a -m registry -l -j 03bec2b8a715a5fac469cf7f059f1fb1svc_samples_04
tool basic_tools.guest_exec -v win7_a -m autorunsc -l -j 03bec2b8a715a5fac469cf7f059f1fb1svc_samples_04 --diff
vbox kill -v win7_a

vbox restore -v win7_a
vbox start -v win7_a
tool basic_tools.guest_exec -v win7_a -x c:\service\042f88feeb577c42f2b4e88e0a49da9a.exe -j 042f88feeb577c42f2b4e88e0a49da9asvc_samples_04 -l --delay 15
tool basic_tools.guest_exec -v win7_a -m event_logs -l -j 042f88feeb577c42f2b4e88e0a49da9asvc_samples_04
tool basic_tools.guest_exec -v win7_a -m shadow -j 042f88feeb577c42f2b4e88e0a49da9asvc_samples_04
tool basic_tools.guest_exec -v win7_a -m registry -l -j 042f88feeb577c42f2b4e88e0a49da9asvc_samples_04
tool basic_tools.guest_exec -v win7_a -m autorunsc -l -j 042f88feeb577c42f2b4e88e0a49da9asvc_samples_04 --diff
vbox kill -v win7_a

vbox restore -v win7_a
vbox start -v win7_a
tool basic_tools.guest_exec -v win7_a -x c:\service\044f9e144fc9d0d0876bb20255a19bae.exe -j 044f9e144fc9d0d0876bb20255a19baesvc_samples_04 -l --delay 15
tool basic_tools.guest_exec -v win7_a -m event_logs -l -j 044f9e144fc9d0d0876bb20255a19baesvc_samples_04
tool basic_tools.guest_exec -v win7_a -m shadow -j 044f9e144fc9d0d0876bb20255a19baesvc_samples_04
tool basic_tools.guest_exec -v win7_a -m registry -l -j 044f9e144fc9d0d0876bb20255a19baesvc_samples_04
tool basic_tools.guest_exec -v win7_a -m autorunsc -l -j 044f9e144fc9d0d0876bb20255a19baesvc_samples_04 --diff
vbox kill -v win7_a

vbox restore -v win7_a
vbox start -v win7_a
tool basic_tools.guest_exec -v win7_a -x c:\service\04ef919e85dbf80d722036054e6c8796.exe -j 04ef919e85dbf80d722036054e6c8796svc_samples_04 -l --delay 15
tool basic_tools.guest_exec -v win7_a -m event_logs -l -j 04ef919e85dbf80d722036054e6c8796svc_samples_04
tool basic_tools.guest_exec -v win7_a -m shadow -j 04ef919e85dbf80d722036054e6c8796svc_samples_04
tool basic_tools.guest_exec -v win7_a -m registry -l -j 04ef919e85dbf80d722036054e6c8796svc_samples_04
tool basic_tools.guest_exec -v win7_a -m autorunsc -l -j 04ef919e85dbf80d722036054e6c8796svc_samples_04 --diff
vbox kill -v win7_a

vbox restore -v win7_a
vbox start -v win7_a
tool basic_tools.guest_exec -v win7_a -x c:\service\065f6b5d659309cc20fa10fcfc46f9c0.exe -j 065f6b5d659309cc20fa10fcfc46f9c0svc_samples_04 -l --delay 15
tool basic_tools.guest_exec -v win7_a -m event_logs -l -j 065f6b5d659309cc20fa10fcfc46f9c0svc_samples_04
tool basic_tools.guest_exec -v win7_a -m shadow -j 065f6b5d659309cc20fa10fcfc46f9c0svc_samples_04
tool basic_tools.guest_exec -v win7_a -m registry -l -j 065f6b5d659309cc20fa10fcfc46f9c0svc_samples_04
tool basic_tools.guest_exec -v win7_a -m autorunsc -l -j 065f6b5d659309cc20fa10fcfc46f9c0svc_samples_04 --diff
vbox kill -v win7_a

vbox restore -v win7_a
vbox start -v win7_a
tool basic_tools.guest_exec -v win7_a -x c:\service\067f8c83ec6ae9082cbd28fd96aa71b8.exe -j 067f8c83ec6ae9082cbd28fd96aa71b8svc_samples_04 -l --delay 15
tool basic_tools.guest_exec -v win7_a -m event_logs -l -j 067f8c83ec6ae9082cbd28fd96aa71b8svc_samples_04
tool basic_tools.guest_exec -v win7_a -m shadow -j 067f8c83ec6ae9082cbd28fd96aa71b8svc_samples_04
tool basic_tools.guest_exec -v win7_a -m registry -l -j 067f8c83ec6ae9082cbd28fd96aa71b8svc_samples_04
tool basic_tools.guest_exec -v win7_a -m autorunsc -l -j 067f8c83ec6ae9082cbd28fd96aa71b8svc_samples_04 --diff
vbox kill -v win7_a

vbox restore -v win7_a
vbox start -v win7_a
tool basic_tools.guest_exec -v win7_a -x c:\service\069fc75d9bfcabeb31be81a2408dbd5c.exe -j 069fc75d9bfcabeb31be81a2408dbd5csvc_samples_04 -l --delay 15
tool basic_tools.guest_exec -v win7_a -m event_logs -l -j 069fc75d9bfcabeb31be81a2408dbd5csvc_samples_04
tool basic_tools.guest_exec -v win7_a -m shadow -j 069fc75d9bfcabeb31be81a2408dbd5csvc_samples_04
tool basic_tools.guest_exec -v win7_a -m registry -l -j 069fc75d9bfcabeb31be81a2408dbd5csvc_samples_04
tool basic_tools.guest_exec -v win7_a -m autorunsc -l -j 069fc75d9bfcabeb31be81a2408dbd5csvc_samples_04 --diff
vbox kill -v win7_a

vbox restore -v win7_a
vbox start -v win7_a
tool basic_tools.guest_exec -v win7_a -x c:\service\071f6beec71647263e27aa5f01d9bde6.exe -j 071f6beec71647263e27aa5f01d9bde6svc_samples_04 -l --delay 15
tool basic_tools.guest_exec -v win7_a -m event_logs -l -j 071f6beec71647263e27aa5f01d9bde6svc_samples_04
tool basic_tools.guest_exec -v win7_a -m shadow -j 071f6beec71647263e27aa5f01d9bde6svc_samples_04
tool basic_tools.guest_exec -v win7_a -m registry -l -j 071f6beec71647263e27aa5f01d9bde6svc_samples_04
tool basic_tools.guest_exec -v win7_a -m autorunsc -l -j 071f6beec71647263e27aa5f01d9bde6svc_samples_04 --diff
vbox kill -v win7_a

vbox restore -v win7_a
vbox start -v win7_a
tool basic_tools.guest_exec -v win7_a -x c:\service\074ffe0097de7de5ef20d5c1d91bfc1f.exe -j 074ffe0097de7de5ef20d5c1d91bfc1fsvc_samples_04 -l --delay 15
tool basic_tools.guest_exec -v win7_a -m event_logs -l -j 074ffe0097de7de5ef20d5c1d91bfc1fsvc_samples_04
tool basic_tools.guest_exec -v win7_a -m shadow -j 074ffe0097de7de5ef20d5c1d91bfc1fsvc_samples_04
tool basic_tools.guest_exec -v win7_a -m registry -l -j 074ffe0097de7de5ef20d5c1d91bfc1fsvc_samples_04
tool basic_tools.guest_exec -v win7_a -m autorunsc -l -j 074ffe0097de7de5ef20d5c1d91bfc1fsvc_samples_04 --diff
vbox kill -v win7_a

vbox restore -v win7_a
vbox start -v win7_a
tool basic_tools.guest_exec -v win7_a -x c:\service\077f967b05b6496227d3da17ba9a6e39.exe -j 077f967b05b6496227d3da17ba9a6e39svc_samples_04 -l --delay 15
tool basic_tools.guest_exec -v win7_a -m event_logs -l -j 077f967b05b6496227d3da17ba9a6e39svc_samples_04
tool basic_tools.guest_exec -v win7_a -m shadow -j 077f967b05b6496227d3da17ba9a6e39svc_samples_04
tool basic_tools.guest_exec -v win7_a -m registry -l -j 077f967b05b6496227d3da17ba9a6e39svc_samples_04
tool basic_tools.guest_exec -v win7_a -m autorunsc -l -j 077f967b05b6496227d3da17ba9a6e39svc_samples_04 --diff
vbox kill -v win7_a
vbox restore -v win7_a
