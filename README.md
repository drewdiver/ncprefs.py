![](https://img.shields.io/badge/python-3.8-green.svg)
![](https://img.shields.io/badge/os-macOS_10.14+-2d74da.svg)

# ncprefs.py

Control Notification Center via the command line!

This is definitely not a 1.0 release, I needed a project to learn learn some Python with and decided to bring Jacob Salmela's
[NCUtil](https://github.com/jacobsalmela/NCutil) up to date as the behind-the-scenese of Notificaton Center has changed drastically since El Capitan.

Since this has been basically re-written, I am releasing under the MIT license.

Pull requests, code corrections and ideas welcome!

## Requirements
- PyObjC bridge: `pip3 install pyobjc`
  (This _could_ be packaged with but a better option might be to use Greg Neagle's [relocatable Python](https://github.com/gregneagle/relocatable-python) to push your own and the change the `#!/usr/local/bin/python3` in this script to match the path.)

## Caveats
- For Catalina users, this will require the notifications to have been user approved.

## Todo
- Adjust setting for multiple bundle-ids?
- Argparse maybe could be cleaner?
- Script the Do Not Disturb settings.


