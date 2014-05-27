#!/bin/bash
echo "Beginning hourly git push of voodo. Getting keychain ssh-agent info..."
source $HOME/.keychain/${HOSTNAME}-sh
echo "Changing to /src/voodo.git/"
cd /src/voodo.git
echo "Running git push --all"
git push --all
echo "Push complete. Exiting"
