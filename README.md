![](https://img.shields.io/badge/python-3.9-green.svg)
![](https://img.shields.io/badge/os-macOS_11+-2d74da.svg)

# ncprefs.py

Control Notification Center via the command line!

I needed a project to learn a little Python with and decided to re-write Jacob Salmela's
[NCUtil](https://github.com/jacobsalmela/NCutil) to work with current versions of macOS.

Managed Preferences are all or nothing, often you want to be flexible but ensure certain notifications aren't displaying on the lock screen of your clients. This is where `ncprefs.py` can come in handy!

## Updated for Big Sur / Monterey!

I've heavily refactored this script (implemented a little "DRY" this time) and simplified the flags.

The changes since Big Sur have made some bits easier and others harder, the changes are enough that version 0.2 will only support Big Sur and up.

The initial script has been versioned "0.1" and placed in the releases page as-is for Mojave/Catalina users.

## Caveats

### Time Sensitive Notifications

I assume once Monterey is officially released, apps can ask if you'd like to allow this for Focus mode.

### Critical Alerts

As of now it seems only the Home app supports the critical alert type

### False-positives

Check which settings are available on a test machine prior to pushing out settings.

`./ncprefs.py -b at.obdev.littlesnitch.agent` reports `True` even though we don't have an option to enable 'Bage app icon.'

### User-approved Notifications

Since Catalina the user _must_ allow notifications before we can change any settings, `ncprefs.py` will let you know when the specific bundle-id has not been approved.


## Requirements
- The PyObjC bridge is required: `pip3 install pyobjc`
  (A nice option might be to use Greg Neagle's [relocatable Python](https://github.com/gregneagle/relocatable-python) to push your own and the change the `#!/usr/local/bin/python3` in this script to match the installation path.)
- The macadmins org on GitHub has a solution for maintaining your instance of python. [github.com/macadmins/python](https://github.com/macadmins/python) This repo is designed to take and extend Greg Neagle's relocatable python and make managing your python even easier.


## Examples

List all available Apps along with their Bundle ID's:

`./ncprefs.py -l`

Get the alert setting for an app:

`./ncprefs.py -a com.apple.iCal`

Set a new alert type for an app:

`./ncprefs.py -sa banner com.apple.iCal`

## To-do

- Detect if settings are managed via MDM

