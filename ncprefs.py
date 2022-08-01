#!/usr/bin/env python

import os, argparse, subprocess, sys
from platform import mac_ver
from AppKit import NSWorkspace
from Foundation import (
    CFPreferencesCopyAppValue,
    CFPreferencesSetAppValue,
    NSFileManager,
    NSMutableArray,
    NSMutableDictionary,
)

##########################################################################################
# CONSTANTS
##########################################################################################

NCPREFSPY_VERSION = '0.2'

BANNERS = 1 << 3
ALERTS = 1 << 4
SHOW_ON_LOCK_SCREEN = 1 << 12
SHOW_IN_NOTIFICATION_CENTER = 1 << 0
BADGE_APP_ICON = 1 << 1
PLAY_SOUND_FOR_NOTIFICATIONS = 1 << 2
ALLOW_NOTIFICATIONS = 1 << 25
NCPREFS_PLIST = os.path.expanduser('~/Library/Preferences/com.apple.ncprefs')
CRITICAL_ALERTS = 1 << 26
TIME_SENSITIVE_ALERTS = 1 << 29
TIME_SENSITIVE_APPS = [ "com.apple.iBooksX",
                        "com.apple.iCal", 
                        "com.apple.gamecenter",
                        "com.apple.Home",
                        "com.apple.MobileSMS",
                        "com.apple.reminders",
                        "com.apple.ScreenTimeNotifications",
                        "com.apple.Passbook" ]

##########################################################################################
# Utility
##########################################################################################

def error(output):
    print(f"ERROR: {output}")

def verbose(output):
    if args.verbose:
        try:
            print(f"verbose: {output}")
        except:
            pass

def kill_usernoted():
    subprocess.run(['killall', 'cfprefsd', 'usernoted'])

##########################################################################################
# Get Functions
##########################################################################################

# check that the specified bundle_id exists, get item index and copy the flags value
def bundle_id_exists(bundle_id):
    item_found = False
    for index, app in enumerate(pl):
        try:
            if app['bundle-id'] == bundle_id:
                item_found = True
                item_index = index
                flags = int(app['flags'])
                grouping = int(app['grouping'])
                content_visibility = int(app['content_visibility'])
                verbose(f"Found {bundle_id} at index {index} in {NCPREFS_PLIST}")
                verbose(f"flags: {flags}")
                verbose(f"grouping: {grouping}")
                verbose(f"content_visibility: {content_visibility}")
                break
        except:
            pass
        index += 1

    if item_found is False:
        print(f"Unable to find {bundle_id} in {NCPREFS_PLIST}")
        sys.exit(1)
    elif not flags & ALLOW_NOTIFICATIONS:
        print(f"Notifications were not user approved for {get_app_name(bundle_id)}, nothing to do.")
        sys.exit(1)
    else:
        return item_found, item_index, flags, grouping, content_visibility

# return the App name from the bundle-id
def get_app_name(bundle_id):
    app_path = NSWorkspace.sharedWorkspace().absolutePathForAppBundleWithIdentifier_(bundle_id)
    if not app_path:
        app_name = "SYSTEM"
    else:
        app_name = NSFileManager.defaultManager().displayNameAtPath_(app_path)
    return app_name

# list all app names and corresponding bundle-id's alphabetically in ncprefs.plist
def list_bundle_ids(pl):
    app_list = []

    for index, app in enumerate(pl):
        try:
            app_name = get_app_name(app['bundle-id'])
            app_list.append([app_name, app['bundle-id']])
        except:
            pass
        index += 1

    for app, bundle in sorted(app_list, key=lambda x:x[0].lower()):
        #print('{:30s} {:20s}'.format(app, bundle))
        print(f"{app} ({bundle})")

def get_alert_style(current_flags):
    if current_flags & BANNERS:
        return "Banners"
    elif current_flags & ALERTS:
        return "Alerts"
    else:
        return "None"

def get_notification_setting(current_flags, nc_setting):
    """Annoyingly this nc_setting is represented by a 0 when enabled, so we have to negate
    the 'if' block, is there a better way to invert? """
    if nc_setting == SHOW_ON_LOCK_SCREEN:
         if not current_flags & nc_setting:
             return True
         else:
             return False
    elif current_flags & nc_setting:
    	return True
    else:
        return False

def get_show_previews(value):
    if value == 1:
        return "never (default)"
    elif value == 2:
        return "when unlocked"
    elif value == 3:
        return "always"
    else:
        print("Error, unknown value.")
        sys.exit(1)

def get_notification_grouping(value):
    if value == 0:
        return "automatic"
    elif value == 1:
        return "by app"
    elif value == 2:
        return "off"
    else:
        print("Error, unknown value")
        sys.exit(1)

##########################################################################################
# Set Functions
##########################################################################################

# set the new flags in the ncprefs plist
# key is one of 'flags', 'grouping' or 'content_visibility'
def modify_ncprefs_plist(key, value, item_index):
    # make an immutuble copy of the 'apps' array in ncprefs
    new_apps_array = NSMutableArray.alloc().initWithArray_(pl)
    # make a mutable copy of the target dict within the array
    new_dict = NSMutableDictionary.alloc().initWithDictionary_copyItems_(new_apps_array[item_index], True)
    # set the value
    new_dict[key] = value
    # replace the mutible dict within the mutable array
    new_apps_array.replaceObjectAtIndex_withObject_(item_index, new_dict)
    # replace the array in the ncprefs plist
    CFPreferencesSetAppValue("apps", new_apps_array, NCPREFS_PLIST)

def disallow_notifications():
	"""
	if notifications are enabled, you can turn off, this removes the app from the 
	notifications list and will re-prompt the user at next app launch
	"""
	new_flags = current_flags | ~ALLOW_NOTIFICATIONS
		
	modify_ncprefs_plist('flags', new_flags, item_index)
	kill_usernoted()

def set_alert_style(option):
    new_flags = current_flags
    # clear the current alert style (which is also equivalent to an alert style of 'None')
    new_flags &= ~0b111000
    if option == 'alerts':
        new_flags |= ALERTS
    elif option == 'banners':
        new_flags |= BANNERS
    elif option == 'none':
        pass
    else:
        error(f"{option} not found, must be one of alert, banners or none")
        sys.exit(1)

    modify_ncprefs_plist('flags', new_flags, item_index)
    kill_usernoted()

def set_notification_option(option, nc_setting):
    # there's probably a much cleaner way to handle this...
    if nc_setting == SHOW_ON_LOCK_SCREEN or nc_setting == SHOW_IN_NOTIFICATION_CENTER:
        if option == "enable":
            new_flags = current_flags & ~nc_setting
        else:
            new_flags = current_flags | nc_setting
    elif option == "enable":
        new_flags = current_flags | nc_setting
    elif option == "disable":
        new_flags = current_flags & ~nc_setting
    else:
        error(f"{option} should be either 'enable' or 'disable'")
        sys.exit(1)

    modify_ncprefs_plist('flags', new_flags, item_index)
    kill_usernoted()

def set_show_previews(option):
    if option == "always":
        new_option = 3
    elif option == "unlocked":
        new_option = 2
    elif option == "never":
        new_option = 1
    else:
        error(f"{option} unrecognized, must be one of 'always', 'unlocked' or 'never'")
        sys.exit(1)

    modify_ncprefs_plist('content_visibility', new_option, item_index)
    kill_usernoted()

def set_notification_grouping(option):
    if option == "automatic":
        new_option = 0
    elif option == "byapp":
        new_option = 1
    elif option == "off":
        new_option = 2
    else:
        error(f"{option} unrecognized, must be one of 'automatic', 'byapp' or 'off'")
        sys.exit(1)
    
    modify_ncprefs_plist('grouping', new_option, item_index)
    kill_usernoted()

if __name__ == "__main__":
    
    # get the dict of 'apps' from the logged in users plist
    pl = CFPreferencesCopyAppValue('apps', NCPREFS_PLIST)

    parser = argparse.ArgumentParser(description="ncprefs.py: control Notification Center via the command line")
    info_options = parser.add_argument_group('info')
    info_options.add_argument("-l", "--list", action="store_true",
                              help="print all available bundle_id's in Notification Center")

    get_options = parser.add_argument_group('get specific notification settings')
    get_options.add_argument("-a", "--get-alert-style", metavar="<bundle_id>",
                              help="get the notification 'Alert style'")
    get_options.add_argument("-c", "--get-allow-critical-alerts", metavar="<bundle_id>",
                              help="get the 'Allow critical alerts' setting")
    get_options.add_argument("-t", "--get-time-sensitive-alerts", metavar="<bundle_id>",
                              help="get the 'Allow time-sensitive alerts' setting")
    get_options.add_argument("-o", "--get-show-on-lock-screen", metavar="<bundle_id>",
                              help="get the 'Show notifications on lock screen' setting")
    get_options.add_argument("-n", "--get-show-in-notification-center", metavar="<bundle_id>",
                              help="get the 'Show in notification center' setting")
    get_options.add_argument("-b", "--get-badge-app-icon", metavar="<bundle_id>",
                              help="get the 'Badge app icon\' setting")
    get_options.add_argument("-p", "--get-play-sound", metavar="<bundle_id>",
                              help="get the 'Play sound for notifications' setting")
    get_options.add_argument("-r", "--get-show-previews", metavar="<bundle_id>",
    						  help="get the 'Show previews' setting")
    get_options.add_argument("-g", "--get-notification-grouping", metavar="<bundle_id>",
    						  help="get the 'Notification grouping' setting")

    set_options = parser.add_argument_group('set specific notification nc_settings')
    set_options.add_argument("-sd", "--disallow-notifications", metavar="<bundle_id>",
                              help="Turn off 'Allow notifications' for specified bundle_id. The app will re-prompt at next launch.")
    set_options.add_argument("-sa", "--set-alert-style",
                              metavar=("alerts|banners|none", "<bundle_id>"),
                              nargs="*",
                              help="set notification 'Alert style' for specified bundle_id")
    set_options.add_argument("-st", "--set-time-sensitive-alerts",
                              metavar=("enable|disable", "<bundle_id>"),
                              nargs="*",
                              help="set 'Time-sensitivie alerts' for specified bundle_id")
    set_options.add_argument("-so", "--set-show-on-lock-screen",
                              metavar=("enable|disable", "<bundle_id>"),
                              nargs="*",
                              help="set 'Show notifications on lock screen' for specified bundle_id")
    set_options.add_argument("-sn", "--set-show-in-notification-center",
                              metavar=("enable|disable", "<bundle_id>"),
                              nargs="*",
                              help="set 'Show in notification center' for specified bundle_id")
    set_options.add_argument("-sb", "--set-badge-app-icon",
                              metavar=("enable|disable", "<bundle_id>"),
                              nargs="*",
                              help="set 'Badge app icon' for specified bundle_id")
    set_options.add_argument("-sp", "--set-play-sound",
                              metavar=("enable|disable", "<bundle_id>"),
                              nargs="*",
                              help="set 'Play sound for notifications\' for specified bundle_id")
    set_options.add_argument("-sr", "--set-show-previews",
                              metavar=("always|unlocked|never", "<bundle_id>"),
                              nargs="*",
                              help="set 'Show previews' option for specified bundle_id")
    set_options.add_argument("-sg", "--set-notification-grouping",
                              metavar=("automatic|byapp|off", "<bundle_id>"),
                              nargs="*",
                              help="set 'Notification grouping' for specified bundle_id")

    global_options = parser.add_argument_group('global notification settings')
    global_options.add_argument("--get-global-show-previews", action="store_true",
                              help="get the global 'Show previews' setting")
    global_options.add_argument("--set-global-show-previews",
                              metavar=("always|unlocked|never"),
                              nargs="*",
                              help="set the global 'Show previews' option for specified bundle_id")

    debug_options = parser.add_argument_group('debug')
    debug_options.add_argument("-v", "--verbose", action="store_true",
                              help="enable verbosity")
    debug_options.add_argument("--version", action="store_true",
                              help="display ncprefs.py version")

    args = parser.parse_args()
    
    # when no argument specified, auto print the help
    if len(sys.argv) <= 1:
        parser.print_help()

    if args.list:
        list_bundle_ids(pl)

    if args.get_alert_style:
        item_found, _, current_flags, _, _ = bundle_id_exists(args.get_alert_style)
        if item_found:
            print(get_alert_style(current_flags))
    
    if args.get_allow_critical_alerts:
        item_found, _, current_flags, _, _ = bundle_id_exists(args.get_allow_critical_alerts)
        if item_found and args.get_allow_critical_alerts == "com.apple.Home":
            print(get_notification_setting(current_flags, CRITICAL_ALERTS))
        else:
            error("'Allow critical alerts' seems only available to the Home app")

    if args.get_time_sensitive_alerts:
        item_found, _, current_flags, _, _ = bundle_id_exists(args.get_time_sensitive_alerts)
        if item_found:
            if args.get_time_sensitive_alerts in TIME_SENSITIVE_APPS:
                print(get_notification_setting(current_flags, TIME_SENSITIVE_ALERTS))
            else:
        	    error(f"'Allow time-sensitive alerts' not available for {args.get_time_sensitive_alerts}")

    if args.get_show_on_lock_screen:
        item_found, _, current_flags, _, _ = bundle_id_exists(args.get_show_on_lock_screen)
        if item_found:
            print(get_notification_setting(current_flags, SHOW_ON_LOCK_SCREEN))

    if args.get_show_in_notification_center:
        item_found, _, current_flags, _, _ = bundle_id_exists(args.get_show_in_notification_center)
        if item_found:
            print(get_notification_setting(current_flags, SHOW_IN_NOTIFICATION_CENTER))

    if args.get_badge_app_icon:
        item_found, _, current_flags, _, _ = bundle_id_exists(args.get_badge_app_icon)
        if item_found:
            print(get_notification_setting(current_flags, BADGE_APP_ICON))

    if args.get_play_sound:
        item_found, _, current_flags, _, _ = bundle_id_exists(args.get_play_sound)
        if item_found:
            print(get_notification_setting(current_flags, PLAY_SOUND_FOR_NOTIFICATIONS))

    if args.get_show_previews:
        item_found, _, _, _, content_visibility = bundle_id_exists(args.get_show_previews)
        if item_found:
    	    print(get_show_previews(content_visibility))

    if args.get_notification_grouping:
        item_found, _, _, grouping, _ = bundle_id_exists(args.get_notification_grouping)
        if item_found:
    	    print(get_notification_grouping(grouping))

    if args.disallow_notifications:
        item_found, item_index, current_flags, _, _ = bundle_id_exists(args.disallow_notifications)
        if item_found:
            disallow_notifications()

    if args.set_alert_style:
        item_found, item_index, current_flags, _, _ = bundle_id_exists(args.set_alert_style[1])
        if item_found:
            set_alert_style(args.set_alert_style[0])

    if args.set_time_sensitive_alerts:
        item_found, item_index, current_flags, _, _ = bundle_id_exists(args.set_time_sensitive_alerts[1])
        if item_found:
            set_notification_option(args.set_time_sensitive_alerts[0], TIME_SENSITIVE_ALERTS)

    if args.set_show_on_lock_screen:
        item_found, item_index, current_flags, _, _ = bundle_id_exists(args.set_time_sensitive_alerts[1])
        if item_found:
            set_notification_option(args.set_show_on_lock_screen[0], SHOW_ON_LOCK_SCREEN)

    if args.set_show_in_notification_center:
        item_found, item_index, current_flags, _, _ = bundle_id_exists(args.set_show_in_notification_center[1])
        if item_found:
            set_notification_option(args.set_show_in_notification_center[0], SHOW_IN_NOTIFICATION_CENTER)

    if args.set_badge_app_icon:
        item_found, item_index, current_flags, _, _ = bundle_id_exists(args.set_badge_app_icon[1])
        if item_found:
            set_notification_option(args.set_badge_app_icon[0], BADGE_APP_ICON)

    if args.set_play_sound:
        item_found, item_index, current_flags, _, _ = bundle_id_exists(args.set_play_sound[1])
        if item_found:
            set_notification_option(args.set_play_sound[0], PLAY_SOUND_FOR_NOTIFICATIONS)

    if args.set_show_previews:
        item_found, item_index, _, _, _ = bundle_id_exists(args.set_show_previews[1])
        if item_found:
            set_show_previews(args.set_show_previews[0])

    if args.set_notification_grouping:
        item_found, item_index, _, _, _ = bundle_id_exists(args.set_notification_grouping[1])
        if item_found:
            set_notification_grouping(args.set_notification_grouping[0])

    if args.get_global_show_previews:
        value = CFPreferencesCopyAppValue('content_visibility', NCPREFS_PLIST)
        print(get_show_previews(value))

    if args.set_global_show_previews:
        option = args.set_global_show_previews[0]
        if option == "always":
            new_option = 3
        elif option == "unlocked":
            new_option = 2
        elif option == "never":
            new_option = 1
        else:
            error(f"{option} unrecognized, must be one of 'always', 'unlocked' or 'never'")
            sys.exit(1)
        
        CFPreferencesSetAppValue('content_visibility', new_option, NCPREFS_PLIST)
        kill_usernoted()

    if args.version:
        print(f"{NCPREFSPY_VERSION}")
