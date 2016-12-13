#!/usr/bin/python
# ! -*- coding: utf-8 -*-
import subprocess, datetime, os, argparse
from PDU_Control import PduOutlet



def main():
    m = argparse.ArgumentParser(description=" %(prog)s",
                                epilog="epilog programy %(prog)s", prog="power managment of DUT")

    m.add_argument("--unitest", "-[u]", "--all_list", "-a", type=int, #default=" 0",
                   help="help_menu")

    m.add_argument("--dir", "-p", type=str, default='.', help="path to to will be deleted")
    m.add_argument("--verbose", "-v", action="store_true",
                   help="pokazat deystvia", default=False)
    m.add_argument("--exception", "-e", type=str, default="", action="store", nargs='+',
                   help="exeption of")
    options = m.parse_args()
    p = subprocess.Popen('ls', shell=True, stdout=subprocess.PIPE)
    out = p.stdout.read()
    mas_p = out.split('\n')
    options = vars(options)
    options['dir'] += '/'
    ex = options['exception']
    print options['exception']

    for t in mas_p:
        if t not in ex and (PduOutlet.PduOutlet(t, options['day'])[0] == 'True'):
            print ('JOPA') #  dell = 'rm -rf ' + options['dir'] + proverka.proverka(t, options['day'])[1]
            if options['verbose']:
                print "Folder '" + PDU_Control.TA_OUTLET_2(1)
            subprocess.call(dell, shell=True)


if __name__ == '__main__':
    main()