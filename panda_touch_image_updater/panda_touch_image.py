"""This AppDaemon script will update the image on a Panda Touch
with the printer's current image.

AppDaemon apps.yaml Arguments:
    image_entity: The entity id of the image provided by ha-bambulab.
    ha_url: The Home Assistant root URL.
    translation_file: The path to the translation file.
    panda_ip: The IP address of the Panda Touch.
"""

import appdaemon.plugins.hass.hassapi as hass

import requests
from base64 import b64encode
from io import BytesIO
from PIL import Image


class PandaImage(hass.Hass):
    MAX_SIZE = (280, 280)
    PTIMGTOOL_URL = 'https://ptimgtool.bttwiki.com/generate'

    def initialize(self):
        self.image_entity     = self.args['image_entity']
        self.ha_url           = self.args['ha_url']
        self.panda_ip         = self.args['panda_ip']
        self.translation_file = self.args['translation_file']

        self.run_in(self.update_image, 30)
        self.listen_state(self.image_changed, self.args['image_entity'])

    def image_changed(self, entity, attribute, old, new, kwargs):
        self.run_in(self.update_image, 10)

    def update_image(self, cb_args):
        image_url = self.get_entity(self.image_entity).get_state(attribute='entity_picture')

        if not image_url:
            self.log('Error: Unable to get image url', level='ERROR')
            return

        # Fetch image data
        response = requests.get(f'{self.ha_url}{image_url}')
        if response.status_code != 200:
            self.log(f'Image retrieve failed {response.status_code}: {image_url}',
                     level='ERROR')
            return

        # Encode image data into base64
        encoded_png = ''
        image_data = BytesIO(response.content)
        with Image.open(image_data) as img:
            buffered = BytesIO()

            img.thumbnail(self.MAX_SIZE)
            img = img.convert('RGBA')
            img.save(buffered, format='PNG')

            encoded_png = b64encode(buffered.getvalue()).decode('utf-8')

        # Encode translation file into base64
        encoded_yml = ''
        with open(self.translation_file, 'rb') as yml:
            encoded_yml = b64encode(yml.read()).decode('utf-8')

        request_data = {}
        request_data['ymlData'] = f'data:application/x-yaml;base64,{encoded_yml}'
        request_data['pngData'] = f'data:image/png;base64,{encoded_png}'

        # Generate Panda Touch IMG
        headers = {'Content-Type': 'application/json;charset=UTF-8'}
        response = requests.post(self.PTIMGTOOL_URL,
                                 headers=headers,
                                 json=request_data)
        if response.status_code != 200:
            self.log(f'Error generating Panda Touch IMG {response.status_code}:\n{response.content}',
                     level='ERROR')
            return
        binary_img = response.content

        # Upload IMG to Panda Touch
        headers = {'Content-Type': 'application/octet-stream'}
        response = requests.post(f'http://{self.panda_ip}:8080/update_add_file',
                                 headers=headers,
                                 data=binary_img)
        if response.status_code != 200:
            self.log(f'Error updating Panda Touch IMG {response.status_code}:\n{response.content}',
                     level='ERROR')
            return

        self.log('===== Panda Touch Image Updated =====')
