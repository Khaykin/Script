#!/bin/bash

if [[ $EUID != 0 ]] ; then
  echo This must be run as root!
  exit 1
fi

for xhci in /sys/bus/pci/drivers/[xe]hci_hcd ; do

  if ! cd $xhci ; then
    echo Weird error. Failed to change directory to $xhci
    exit 1
  fi

  for i in ????:??:??.? ; do
    echo "unbinding $xhci/$i"
    echo -n "$i" > unbind
    sleep ${1-5}
    echo "binding $xhci/$i"
    echo -n "$i" > bind
    echo "done resetting $xhci/$i"
  done
done
echo "done resetting all USB Controllers"