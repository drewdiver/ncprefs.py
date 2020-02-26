#!/usr/local/bin/python3

import os
import argparse
import subprocess
import sys
from platform import mac_ver
from AppKit import NSWorkspace

# pylint: disable=E0611
from Foundation import (
    CFPreferencesCopyAppValue,
    CFPreferencesSetAppValue,
    NSFileManager,
    NSMutableArray,
    NSMutableDictionary,
)
# pylint: enable=E0611

# target com.apple.ncprefs.plist
NCPREFS_PLIST = os.path.expanduser('~/Library/Preferences/com.apple.ncprefs')
CATALINA = None

# bit-shifting
BANNERS = 1 << 3
ALERTS = 1 << 4
SHOW_ON_LOCK_SCREEN = 1 << 12
SHOW_PREVIEW = 1 << 14
SHOW_PREVIEW_ALWAYS = 1 << 13
SHOW_IN_NOTIFICATION_CENTER = 1 << 0
BADGE_APP_ICON = 1 << 1
PLAY_SOUND_FOR_NOTIFICATIONS = 1 << 2
ALLOW_NOTIFICATIONS = 1 << 25

pl = CFPreferencesCopyAppValue('apps', NCPREFS_PLIST)

def verbose(output):
    if args.verbose:
        try:
            print(f"verbose: {output}")
        except:
            pass

def error(output):
    print(f"error: {output}")

def kill_usernoted():
    """Apply settings by killing the usernoted daemon"""
    subprocess.run(['killall', 'cfprefsd', 'usernoted'])

def get_app_name(bundle_id):
    """Return the App name from the bundle-id"""
    app_path = NSWorkspace.sharedWorkspace().absolutePathForAppBundleWithIdentifier_(bundle_id)
    if not app_path:
        app_name = "SYSTEM"
    else:
        app_name = NSFileManager.defaultManager().displayNameAtPath_(app_path)
    return app_name

def list_bundle_id(pl):
    """List all bundle_id's in ncprefs plist"""
    # add bold title above list
    print('\033[1m{:30s} {:20s}\033[0m'.format("App Name", "Bundle ID"))

    for index, app in enumerate(pl):
        try:
            # probably best to avoid messing with _SYSTEM_CENTER_ stuff?
            if '_CENTER_' not in app['bundle-id']:
                app_name = get_app_name(app['bundle-id'])
                print('{:30s} {:20s}'.format(app_name, app['bundle-id']))
        except:
            pass
        index += 1
    verbose(f"{NCPREFS_PLIST}")

def bundle_id_exists(bundle_id):
    """Check that the specified bundle_id exists, get item index and copy the flags value"""
    item_found = False
    for index, app in enumerate(pl):
        try:
            if app['bundle-id'] == bundle_id:
                item_found = True
                item_index = index
                flags = int(app['flags'])
                verbose(f"Found {bundle_id} at index {index} with flags {flags} in {NCPREFS_PLIST}")
                break
        except:
            pass
        index += 1

    if not item_found:
        print(f"Unable to find {bundle_id} in {NCPREFS_PLIST}")
        sys.exit(1)
    elif CATALINA and not flags & ALLOW_NOTIFICATIONS:
        error(f"{get_app_name(bundle_id)} notifications were not user approved!")
        sys.exit(1)

    return item_found, item_index, flags

def get_alert_style(current_flags):
    if current_flags & BANNERS:
        style = "Banners"
    elif current_flags & ALERTS:
        style = "Alerts"
    else:
        style = "None"
    return style

def get_show_on_lock_screen_status(current_flags):
    """Get notifications on lock screen setting"""
    if not current_flags & SHOW_ON_LOCK_SCREEN:
        status = True
    else:
        status = False
    return status

def get_show_preview_status(current_flags):
    """Get show notification preview setting"""
    # a 0 bit indicates enabled, so we need to inverse
    if not current_flags & SHOW_PREVIEW and not get_show_on_lock_screen_status(current_flags):
        status = True
    else:
        status = False
    return status

def get_show_preview_always_status(current_flags):
    """Get show notification preview setting - always"""
    if current_flags & SHOW_PREVIEW_ALWAYS and get_show_on_lock_screen_status(current_flags) and not current_flags & SHOW_PREVIEW:
        status = True
    else:
        status = False
    return status

def get_show_preview_unlocked_status(current_flags):
    """Get show notification preview settings - unlocked"""
    if not current_flags & SHOW_PREVIEW_ALWAYS and get_show_on_lock_screen_status(current_flags) and not current_flags & SHOW_PREVIEW:
        status = True
    else:
        status = False
    return status

def get_show_in_nc_status(current_flags):
    if current_flags & SHOW_IN_NOTIFICATION_CENTER:
        status = True
    else:
        status = False
    return status

def get_badge_app_icon_status(current_flags):
    if current_flags & BADGE_APP_ICON:
        status = True
    else:
        status = False
    return status

def get_play_sound_status(current_flags):
    if current_flags & PLAY_SOUND_FOR_NOTIFICATIONS:
        status = True
    else:
        status = False
    return status

def get_info(bundle_id):
    """Return current settings for specified bundle_id"""
    item_found, _, current_flags = bundle_id_exists(bundle_id)
    if item_found:
        app_name = get_app_name(bundle_id)
        if app_name == "N/A":
            app_name = bundle_id

        print(f"Settings for {app_name} in {NCPREFS_PLIST}\n")

        print(f"Alert Style: {get_alert_style(current_flags)}")

        if get_show_on_lock_screen_status(current_flags):
            print("[✓] Show notifications on lock screen")
        else:
            print("[ ] Show notifications on lock screen")

        if get_show_preview_status(current_flags):
            print("[✓] Show notification preview")
        elif get_show_preview_always_status(current_flags):
            print("[✓] Show notification preview (always)")
        elif get_show_preview_unlocked_status(current_flags):
            print("[✓] Show notification preview (when unlocked)")
        else:
            print("[ ] Show notification preview")

        if get_show_in_nc_status(current_flags):
            print("[ ] Show in Notification Center")
        else:
            print("[✓] Show in Notification Center")

        if get_badge_app_icon_status(current_flags):
            print("[✓] Badge app icon")
        else:
            print("[ ] Badge app icon")

        if get_play_sound_status(current_flags):
            print("[✓] Play sound for notifications")
        else:
            print("[ ] Play sound for notifications")

def set_flags(new_flags, item_index):
    """Set the new flags in the ncprefs plist"""
    # make an immutuble copy of the 'apps' array in ncprefs
    new_apps_array = NSMutableArray.alloc().initWithArray_(pl)
    # make a mutable copy of the target dict within the array
    new_dict = NSMutableDictionary.alloc().initWithDictionary_copyItems_(new_apps_array[item_index], True)
    # set the value
    new_dict['flags'] = new_flags
    # replace the mutible dict within the mutable array
    new_apps_array.replaceObjectAtIndex_withObject_(item_index, new_dict)
    # replace the array in the ncprefs plist
    CFPreferencesSetAppValue("apps", new_apps_array, NCPREFS_PLIST)

def set_alert_style(option, bundle_id):
    item_found, item_index, current_flags = bundle_id_exists(bundle_id)
    if item_found:
    	if option == 'alerts':
    		new_flags = new_flags | ALERTS
    	elif option == 'banners':
    		new_flags = new_flags | BANNERS
    	elif option == 'none':
    	    new_flags = current_flags & ~(BANNERS | ALERTS)
    	else:
    		error(f"{bundle_id} not found")
    		sys.exit(1)

    set_flags(new_flags, item_index)
    kill_usernoted() 	

def set_show_on_lock_screen(option, bundle_id):
    """Enable or disable Show notifications on lock screen setting"""
    item_found, item_index, current_flags = bundle_id_exists(bundle_id)
    if item_found:
        if option == "enable":
            new_flags = current_flags & ~SHOW_ON_LOCK_SCREEN
        elif option == "disable":
            new_flags = current_flags | SHOW_ON_LOCK_SCREEN
        else:
            error(f"{option} should be either 'enable' or 'disable'")
            sys.exit(1)
    else:
        error(f"{bundle_id} not found")
        sys.exit(1)

    set_flags(new_flags, item_index)
    kill_usernoted()

def set_show_preview(option, bundle_id):
    """Enable or disable show notification preview"""
    item_found, item_index, current_flags = bundle_id_exists(bundle_id)
    if item_found and current_flags & SHOW_ON_LOCK_SCREEN:
        if option == "enable":
            new_flags = current_flags & ~SHOW_PREVIEW
        elif option == "disable":
            new_flags = current_flags | SHOW_PREVIEW
        else:
            error(f"{option} should be either 'enable' or 'disable'")
            sys.exit(1)
    else:
        error(f"{bundle_id} not found")
        sys.exit(1)

    set_flags(new_flags, item_index)
    kill_usernoted()

def set_show_in_nc(option, bundle_id):
    """Enable or disable Show in Notification Center"""
    item_found, item_index, current_flags = bundle_id_exists(bundle_id)
    if item_found:
        if option == "enable":
            new_flags = current_flags & ~SHOW_IN_NOTIFICATION_CENTER
        elif option == "disable":
            new_flags = current_flags | SHOW_IN_NOTIFICATION_CENTER
        else:
            error(f"{option} should be either 'enable' or 'disable'")
            sys.exit(1)
    else:
        error(f"{bundle_id} not found")
        sys.exit(1)

    set_flags(new_flags, item_index)
    kill_usernoted()

def set_show_badge_app_icon(option, bundle_id):
    """Enable or disable Show badge app icon in Notification Center"""
    item_found, item_index, current_flags = bundle_id_exists(bundle_id)
    if item_found:
        if option == "enable":
            new_flags = current_flags | BADGE_APP_ICON
        elif option == "disable":
            new_flags = current_flags & ~BADGE_APP_ICON
        else:
            error(f"{option} should be either 'enable' or 'disable'")
            sys.exit(1)
    else:
        error(f"{bundle_id} not found")
        sys.exit(1)

    set_flags(new_flags, item_index)
    kill_usernoted()

def set_play_sound(option, bundle_id):
    """Enable or disable Play sound in Notification Center"""
    for bundle_id in bundle_id:
        item_found, item_index, current_flags = bundle_id_exists(bundle_id)
        if item_found:
            if option == "enable":
                new_flags = current_flags | PLAY_SOUND_FOR_NOTIFICATIONS
            elif option == "disable":
                new_flags = current_flags & ~PLAY_SOUND_FOR_NOTIFICATIONS
            else:
                error(f"{option} should be either 'enable' or 'disable'")
                sys.exit(1)
            set_flags(new_flags, item_index)
        else:
            error(f"{bundle_id} not found")
            sys.exit(1)

    kill_usernoted()

if __name__ == "__main__":

    parser = argparse.ArgumentParser(description="ncprefs.py: control Notification Center via the command line")
    info_options = parser.add_argument_group('info')
    info_options.add_argument("-l", "--list", action="store_true",
                              help="print all available bundle_id's in Notification Center")
    info_options.add_argument("-i", "--get-info", metavar="<bundle_id>",
                              help="display all current notification settings for specified bundle_id")

    get_options = parser.add_argument_group('get specific notification settings')
    get_options.add_argument("--get-alert-style",
                             metavar="<bundle_id>",
                             help="get the current notification alert style for specified bundle_id")
    get_options.add_argument("--get-lock-screen",
                             metavar="<bundle_id>",
                             help="get the current show on lock screen setting for specified bundle_id")
    get_options.add_argument("--get-show-preview",
                             metavar="<bundle_id>",
                             help="get the current show preview setting for specified bundle_id")
    get_options.add_argument("--get-notification-center",
                             metavar="<bundle_id>",
                             help="get the current show notification preview setting for specified bundle_id")
    get_options.add_argument("--get-badge-icon",
                             metavar="<bundle_id>",
                             help="get the current show badge app icon setting for specified bundle_id")
    get_options.add_argument("--get-play-sound",
                             metavar="<bundle_id>",
                             help="get the current play sound setting for specified bundle_id")

    settings_options = parser.add_argument_group('set notification settings')
    settings_options.add_argument("--set-alert-style",
                                  metavar=("alerts|banners|none", "<bundle_id>"),
                                  nargs="*",
                                  help="set notification alert style for specified bundle_id")
    settings_options.add_argument("--set-lock-screen",
                                  metavar=("enable|disable", "<bundle_id>"),
                                  nargs="*",
                                  help="set show on lock screen setting for specified bundle_id")
    settings_options.add_argument("--set-show-preview",
                                  metavar=("enable|disable", "<bundle_id>"),
                                  nargs="*",
                                  help="set show notification preview option for specified bundle_id")
    settings_options.add_argument("--set-notification-center",
                                  metavar=("enable|disable", "<bundle_id>"),
                                  nargs="*",
                                  help="set show in notification center setting for specified bundle_id")
    settings_options.add_argument("--set-badge-icon",
                                  metavar=("enable|disable", "<bundle_id>"),
                                  nargs="*",
                                  help="set show badge app icon setting for specified bundle_id")
    settings_options.add_argument("--set-play-sound",
                                  metavar=("enable|disable", "<bundle_id>"),
                                  nargs="*",
                                  help="set play sound for notifications setting for specified bundle_id")

    debug_options = parser.add_argument_group('debug')
    debug_options.add_argument("-v", "--verbose", action="store_true",
                               help="enable verbosity")
    args = parser.parse_args()

    # get the macOS major number
    v, _, _ = mac_ver()
    mac_major = int(v.split('.')[1])

	# make sure we are on a supported macOS version before continuing.
    if mac_major == 15:
        verbose(f"Running Catalina")
        CATALINA = True
    elif mac_major == 14:
        verbose("Running Mojave")
        CATALINA = False
    else:
        verbose(f"Running unsupported version 10.{mac_major}")
        print("Error: ncprefs only supports macOS 10.14 (Mojave) and later.")
        sys.exit(1)

    # print the help menu if no arguments are specified
    if len(sys.argv) <= 1:
        parser.print_help()
        parser.exit()
    if args.list:
        list_bundle_id(pl)
    if args.get_info:
        get_info(args.get_info)
    if args.get_alert_style:
        item_found, _, current_flags = bundle_id_exists(args.get_alert_style)
        if item_found:
            print(get_alert_style(current_flags))
    if args.get_lock_screen:
        item_found, _, current_flags = bundle_id_exists(args.get_lock_screen)
        if item_found:
            print(get_show_on_lock_screen_status(current_flags))
    if args.get_show_preview:
        item_found, _, current_flags = bundle_id_exists(args.get_show_preview)
        if item_found:
            print(get_show_preview_status(current_flags))
    if args.set_alert_style:
    	set_alert_style(args.set_alert_style[0], args.set_alert_style[1])
    if args.set_lock_screen:
        set_show_on_lock_screen(args.set_lock_screen[0], args.set_lock_screen[1])
    if args.set_show_preview:
        set_show_preview(args.set_show_preview[0], args.set_show_preview[1])
    if args.set_notification_center:
        set_show_in_nc(args.set_notification_center[0], args.set_notification_center[1])
    if args.set_badge_icon:
        set_show_badge_app_icon(args.set_badge_icon[0], args.set_badge_icon[1])
    if args.set_play_sound:
        set_play_sound(args.set_play_sound[0], args.set_play_sound[1:])
