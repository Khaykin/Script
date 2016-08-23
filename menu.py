#!/usr/bin/env python
# -*- coding: utf-8 -*-
#title           :menu.py

#=======================================================================
import subprocess
import time
import re
from adb_handler import AdbDevice 
import sys
import os 
# Main definition - constants
menu_actions  = {}  
myadb = AdbDevice() 
# =======================
#     MENUS FUNCTIONS
# =======================
 
# Main menu
def main_menu():
    os.system('clear')
    
    print "Welcome,\n"
    print "Please choose the menu you want to start:"
    print "1.to perform RPMB Provisioning Test Key & RPMB partition erasing press 1 "
    #print "2. Menu 2"
    print "\n0. Quit"
    choice = raw_input(" >>  ")
    exec_menu(choice)
 
    return
 
# Execute menu
def exec_menu(choice):
    os.system('clear')
    ch = choice.lower()
    if ch == '':
        menu_actions['main_menu']()
    else:
        try:
            menu_actions[ch]()
        except KeyError:
            print "Invalid selection, please try again.\n"
            menu_actions['main_menu']()
    return
 
# Menu 1
def menu1():
    print 'RPMB Provisioning Test Key'
    myadb.adb_command('shell "echo 1 | qseecom_sample_client -v sampleapp 14 1"')
    time.sleep(5)
    print 'RPMB partition erasing'
    myadb.adb_command('shell "echo y | qseecom_sample_client -v sampleapp 15 1"')
    print 'RPMB provisioning done'
    time.sleep(5)
    choice = raw_input(" >>  ")
    exec_menu(choice)
    return
 
 
# Menu 2
def menu2():
    print "Hello Menu 2 !\n"
    print "9. Back"
    print "0. Quit" 
    choice = raw_input(" >>  ")
    exec_menu(choice)
    return
 
# Back to main menu
def back():
    menu_actions['main_menu']()
 
# Exit program
def exit():
    sys.exit()
 
# =======================
#    MENUS DEFINITIONS
# =======================
 
# Menu definition
menu_actions = {
    'main_menu': main_menu,
    '1': menu1,
    '2': menu2,
    '9': back,
    '0': exit,
}
 
# =======================
#      MAIN PROGRAM
# =======================
 
# Main Program
if __name__ == "__main__":
    # Launch main menu
    main_menu()
