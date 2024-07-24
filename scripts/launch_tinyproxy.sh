#!/bin/bash

BASE_DIR="$1"
SCRIPT_DIR="$(dirname $0)"

PORT_START=9000
PORT_END=9100

if [ "$1" == "-h" ] || [ "$1" == "--help" ]; then
    echo "Launch tinyproxy server with opened port between 9000-9100 and"
    echo "return this port number in format \"port <number>\""
    echo ""
    echo "Usage:"
    echo "./launch_tinyproxy base_dir script_dir"
    echo ""
    echo "base_diry - directory where the pid and conf file should be saved"
    echo "script_dir - directory where this script is placed and confs folder"
    echo "is present"
    echo ""
    exit 0
fi

TINYPROXY=$(which tinyproxy 2>/dev/null)

if [ "$?" -ne 0 ]; then
    echo "Program tinyproxy must be installed for this kickstart test!" >&2
    exit 1
fi

if [ ! -d "$BASE_DIR" ]; then
    echo "You must specify base directory for the test!" >&2
    exit 1
fi

mkdir -p $BASE_DIR/tinyproxy/

for i in $(shuf -i "${PORT_START}-${PORT_END}" -n 20); do
    sed -e "s;@PROXY_PORT@;$i;" -e "s;@TMP_DIR@;$BASE_DIR;" $SCRIPT_DIR/confs/tinyproxy.conf > \
        $BASE_DIR/tinyproxy/tinyproxy.conf

    #TODO FIX PORT RANGE

    $TINYPROXY -c $BASE_DIR/tinyproxy/tinyproxy.conf
    sleep 1

    if [ -f $BASE_DIR/tinyproxy/tinyproxy.pid ]; then
        echo "port $i"
        exit 0
    fi
done

echo "Can't find usable port!" >&2
exit 2
