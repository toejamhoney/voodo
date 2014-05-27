#!/system/bin/sh
rm -Rf /sdcard/vtrace
mkdir /sdcard/vtrace
echo Launch strace
echo Running $* with strace launcher > /sdcard/strace.log
exec /system/xbin/strace -f -ff -o /sdcard/vtrace/vtrace $*
