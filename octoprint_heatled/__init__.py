# coding=utf-8
from __future__ import absolute_import

### (Don't forget to remove me)
# This is a basic skeleton for your plugin's __init__.py. You probably want to adjust the class name of your plugin
# as well as the plugin mixins it's subclassing from. This is really just a basic skeleton to get you started,
# defining your plugin as a template plugin, settings and asset plugin. Feel free to add or remove mixins
# as necessary.
#
# Take a look at the documentation on what other plugin mixins are available.

import octoprint.plugin
import re
import RPi.GPIO as GPIO

class HeatledPlugin(octoprint.plugin.SettingsPlugin,
    octoprint.plugin.AssetPlugin,
    octoprint.plugin.TemplatePlugin,
    octoprint.plugin.StartupPlugin
):

    def reset_gpio(self):
        self._logger.debug("Refreshing GPIO Settings")
        GPIO.setup(int(self._settings.get(["bedgpio"])), GPIO.OUT)
        GPIO.setup(int(self._settings.get(["hotendgpio"])), GPIO.OUT)


    ##~~ SettingsPlugin mixin

    def get_settings_defaults(self):
        return dict(hotendgpio=2, bedgpio=4)
        
    def on_settings_save(self, data):
        octoprint.plugin.SettingsPlugin.on_settings_save(self, data)
        self.reset_gpio()

    def get_template_configs(self):
        return [
            dict(type="settings", custom_bindings=False)
        ]

    ##~~ AssetPlugin mixin

    def get_assets(self):
        # Define your plugin's asset files to automatically include in the
        # core UI here.
        return {
            "js": ["js/heatled.js"],
            "css": ["css/heatled.css"],
            "less": ["less/heatled.less"]
        }

    ##~~ Softwareupdate hook

    def get_update_information(self):
        # Define the configuration for your plugin to use with the Software Update
        # Plugin here. See https://docs.octoprint.org/en/master/bundledplugins/softwareupdate.html
        # for details.
        return {
            "heatled": {
                "displayName": "Heatled Plugin",
                "displayVersion": self._plugin_version,

                # version check: github repository
                "type": "github_release",
                "user": "jchancel",
                "repo": "OctoPrint-Heatled",
                "current": self._plugin_version,

                # update method: pip
                "pip": "https://github.com/jchancel/OctoPrint-Heatled/archive/{target_version}.zip",
            }
        }

    
    def on_after_startup(self):
        if (GPIO.getmode() is None):
            GPIO.setmode(GPIO.BOARD)
        if (GPIO.getmode() == GPIO.BCM):
            self._logger.error("Another plugin has set the GPIO mode to BCM which is incompatible with heatled plugin")
            
        self.reset_gpio()
        

    
    def hook_gcode_sending(self, comm_instance, phase, cmd, cmd_type, gcode, *args, **kwargs):

        self._logger.debug("GCODE Command Found: %s" % cmd)

        #M104 S180 (HotEnd ON)
        #M104 S0 (HotEnd OFF)
        
        #M140 S60 (Bed ON)
        #M140 S0 (Bed OFF)
        
        #Quickly filter out everything we dont care about
        if cmd[:4] != 'M104' and cmd[:4] != 'M140':
            return

        #grab the cmd and arguments
        match = re.search(r'^(M[0-9]+)(?:\sS(.*))?$', cmd)
        if match is None:
            return

        cmd_id = match.group(1)
        cmd_temp = match.group(2)
        temp = int(cmd_temp)
        
        self._logger.debug("GCODE Parse Command: %s" % cmd_id)
        self._logger.debug("GCODE Parse Args: %s" % cmd_temp)
                
        if cmd_id == 'M140':
            if temp > 0:
                self._logger.info(" -- Bed LED ON: %s", self._settings.get(["bedgpio"]))
                GPIO.output(int(self._settings.get(["bedgpio"])), GPIO.HIGH)
            else:
                self._logger.info(" -- Bed LED OFF: %s", self._settings.get(["bedgpio"]))
                GPIO.output(int(self._settings.get(["bedgpio"])), GPIO.LOW)
        elif cmd_id == 'M104':
            if temp > 0:
                self._logger.info(" -- HotEnd LED ON: %s", self._settings.get(["hotendgpio"]))
                GPIO.output(int(self._settings.get(["hotendgpio"])), GPIO.HIGH)
            else:
                self._logger.info(" -- HotEnd LED OFF: %s", self._settings.get(["hotendgpio"]))
                GPIO.output(int(self._settings.get(["hotendgpio"])), GPIO.LOW)
       
        status = 'ok'

        comm_instance._log("Return(HeatledPlugin): %s" % status)

        return

        


# If you want your plugin to be registered within OctoPrint under a different name than what you defined in setup.py
# ("OctoPrint-PluginSkeleton"), you may define that here. Same goes for the other metadata derived from setup.py that
# can be overwritten via __plugin_xyz__ control properties. See the documentation for that.
__plugin_name__ = "Heatled Plugin"


# Set the Python version your plugin is compatible with below. Recommended is Python 3 only for all new plugins.
# OctoPrint 1.4.0 - 1.7.x run under both Python 3 and the end-of-life Python 2.
# OctoPrint 1.8.0 onwards only supports Python 3.
__plugin_pythoncompat__ = ">=3,<4"  # Only Python 3

def __plugin_load__():
    global __plugin_implementation__
    __plugin_implementation__ = HeatledPlugin()

    global __plugin_hooks__
    __plugin_hooks__ = {
        "octoprint.plugin.softwareupdate.check_config": __plugin_implementation__.get_update_information,
        "octoprint.comm.protocol.gcode.sending": __plugin_implementation__.hook_gcode_sending
    }
    

