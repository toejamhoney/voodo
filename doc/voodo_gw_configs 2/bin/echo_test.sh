if [ "$#" -ne 1 ]; then
    echo Incorrect input
else
    echo Input: $1
fi
echo $HOME
echo $HOME"/bin"
if [ -d $HOME"/bin" ]; then
    echo It\'s a directory
fi
if [ -d $HOME"/bin/echo_test.sh" ]; then
    echo It\'s a directory
else
    echo Who knows what that is
fi
