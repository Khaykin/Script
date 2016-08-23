#!/usr/bin/python

f = open('1.txt')
ints = []
try:
    for line in f:
        ints.append(int(line))
except ValueError:
    print('eto ne hislo. vyxodim')
except Exception:
    print('eto hto?')
else:
    print('GOOD')
finally:
    f.close()
    print('zakryl fail')
    # v akom poradke: try, gruppa except, potom else, ? i poslednee finally.
#eto ne hislo.

