"""This AppDaemon script will automatically download timelapses
when a Bambu Lab printer finishes printing.
The printer should be set up with the Bambu Lab integration.

AppDaemon apps.yaml Arguments:
    print_type_entity: The printer's print type sensor entity.
    downloader_path: The path to the bambu_timelapse_downloader executable.
    printer_ip_entity: The printer's ip address sensor entity.
    access_code: The printer's access code.
    download_dir: The directory to download timelapses to.
"""

import appdaemon.plugins.hass.hassapi as hass

import os
import threading

class BambuTimelapse(hass.Hass):

    def initialize(self):
        self.print_type_entity = self.args['print_type_entity']
        self.downloader_path = self.args['downloader_path']
        self.ip_address = self.get_state(self.args['printer_ip_entity'])
        self.access_code = self.args['access_code']
        self.download_dir = self.args['download_dir']

        self.run_in(self.check_print_type_state, 1)
        self.listen_state(self.status_changed, self.print_type_entity)

    def status_changed(self, entity, attribute, old, new, kwargs):
        self.run_in(self.check_print_type_state, 1)

    def check_print_type_state(self, cb_args):
        if self.get_state(self.print_type_entity) == 'idle':
            thread = threading.Thread(target=self.download_timelapse, daemon=True)
            thread.start()

    def download_timelapse(self):
        os.system(f'{self.downloader_path} {self.ip_address} --access-code={self.access_code} --download-dir="{self.download_dir}" --convert --console-only-logging')
        self.log('--- DONE ---')
        return