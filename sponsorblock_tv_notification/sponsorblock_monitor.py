"""This AppDaemon script will read from a pipe and look for lines containing
the substring "Skipping segment: seeking to" then trigger an automation when found.
The automation can be configured to display a notification on the TV
when a sponsored segment is skipped by iSponsorBlockTV.

This AppDaemon script requires a shell script to be configured to stream
iSponsorBlockTV's logs to a pipe (See: sponsorblock_log_stream.sh)

AppDaemon apps.yaml Arguments:
    pipe_path: The path to the pipe that the shell script is streaming to.
    automation_id: The entity id for the automation to trigger.
                   This can be found in Developer Tools > States.
"""

import appdaemon.plugins.hass.hassapi as hass

import threading
import time

class SponsorBlockMonitor(hass.Hass):

    def initialize(self):
        self.pipe_path     = self.args['pipe_path']
        self.automation_id = self.args['automation_id']
        self.match_phrase  = 'Skipping segment: seeking to'

        thread = threading.Thread(target=self.watch_pipe, daemon=True)
        thread.start()

    def watch_pipe(self):
        # wait 30 seconds for the shell script to start streaming to the pipe
        time.sleep(30)

        self.log('SponsorBlockMonitor starting log monitoring...')

        while True:
            try:
                self.log(f'Opening pipe: {self.pipe_path}')
                with open(self.pipe_path, 'r') as pipe:
                    for line in pipe:
                        if self.match_phrase in line:
                            line_split = line.strip().split(' - ')
                            self.log(f'{line_split[0]} - {line_split[-1]}')
                            self.call_service('automation/trigger',
                                              entity_id=self.automation_id)
                self.log(f'Closed pipe: {self.pipe_path}')
            except FileNotFoundError:
                self.log('Pipe not found, retrying in 5s...', level='ERROR')
                time.sleep(5)
            except Exception as e:
                self.log(f'Pipe error: {e}', level='ERROR')
                time.sleep(5)
