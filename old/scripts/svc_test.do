vbox restore -v win7_a
vbox start -v win7_a
tool basic_tools.guest_exec -v win7_a -x c:\service\000066e2c2f7a16461859a8744e1fb90 -j svc_samples_02 -l
tool basic_tools.guest_exec -v win7_a -m event_logs -l -j svc_samples_02
tool basic_tools.guest_exec -v win7_a -m shadow -j svc_samples_02
tool basic_tools.guest_exec -v win7_a -m registry -l -j svc_samples_02
tool basic_tools.guest_exec -v win7_a -m autorunsc -l -j svc_samples_02 --diff
vbox kill -v win7_a
vbox restore -v win7_a
