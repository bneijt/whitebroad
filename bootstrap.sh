#!/bin/bash
set -e
if [ ! -d "virtualenv" ]; then
    virtualenv -p `which python3` virtualenv
fi

. virtualenv/bin/activate
pip install tornado==3.2
pip install pillow==2.4.0
echo 'You need virtualenv to work with this'
echo '. virtualenv/bin/activate'

