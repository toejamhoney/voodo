$ADB push scripts/launch_strace.sh $AWD
$ADB shell chmod 777 $AWD/launch_strace.sh
$ADB shell setprop wrap.$APK "logwrapper $AWD/launch_strace.sh" 
