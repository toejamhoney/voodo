{
    "strace": [
        "$SCRIPT scripts/strace_pre.do", 
        "$SCRIPT scripts/strace_post.do", 
        null
    ], 
    "logcat": [
        "$SCRIPT scripts/logcat_pre.do", 
        "$SCRIPT scripts/logcat_post.do", 
        "$SCRIPT scripts/logcat_cleanup.do"
    ], 
    "\n    Format:\n    id : (before,\n          after,\n          cleanup)\n    \n    Commands:\n    Before, after, and cleanup are all strings that should be syntactically correct commands to run processes on the emulator, or on the host.\n    Specifying None in a command (without quotes) means NOP.\n\n    Variable arguments:\n    $ADB - tells voodo to execute this on the device via adb -s <vm id>\n    $APK - expands this into the namespace id of the app (eg, com.android.browser)\n    $SCRIPT - indicates that this is a script file that contains lines with commands\n    $KILL - terminate the process that began this analyzer\n\n    tcpdump": [
        "tcpdump -ennSvXXs 1514 -i en0 -w $LOG_FILE.pcap", 
        "$KILL", 
        null
    ]
}