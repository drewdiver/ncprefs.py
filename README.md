![](https://img.shields.io/badge/python-3.8-green.svg)
![](https://img.shields.io/badge/os-macOS_10.14+-2d74da.svg)

# ncprefs.py

Control Notification Center via the command line!

I needed a project to learn a little Python with and decided to re-write Jacob Salmela's
[NCUtil](https://github.com/jacobsalmela/NCutil) to work with current versions of macOS.

Pull requests, code corrections and ideas are welcome!

## Requirements
- The PyObjC bridge is required: `pip3 install pyobjc`
  (A nice option might be to use Greg Neagle's [relocatable Python](https://github.com/gregneagle/relocatable-python) to push your own and the change the `#!/usr/local/bin/python3` in this script to match the installation path.)

## Caveats
- For Catalina users, this will require the notifications to have been user approved.

## Usage
Print the help dialogue:
```
./ncprefs.py -h
```

List all available Apps along with their Bundle ID's
```
./ncprefs.py -l
```

Show the current alert style for Calendar:
```
./ncprefs.py --get-alert-style com.apple.iCal
```

Set the alert style to Banner for Calendar:
```
./ncprefs.py --set-alert-style banners com.apple.iCal
```

Enable badge icon:
```
./ncprefs.py --set-badge-icon enable com.apple.iCal
```

## Todo
- Re-work Show notifications function to allow for "Always" or "When unlocked" based on setting of "Show notifications on lock screen"
- Adjust setting for multiple bundle-ids?
- Argparse maybe could be cleaner?
- Script the Do Not Disturb settings.


