$ADB logcat -b main -v long -d -f /sdcard/main_logcat.txt &
$ADB logcat -b radio -v long -d -f /sdcard/radio_logcat.txt &
$ADB logcat -b events -v long -d -f /sdcard/events_logcat.txt &
