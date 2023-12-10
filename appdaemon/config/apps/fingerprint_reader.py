import appdaemon.plugins.hass.hassapi as hass
import datetime
import yaml

CONFIG_PATH = 'appdaemon/config/app_config/fingerprint_reader.yaml'

class FingerprintReader(hass.Hass):

  def initialize(self):
    self.listen_event(self._enrollment_started_callback, "esphome.enrollment_started")
    self.listen_event(self._enrollment_done_callback, 'esphome.enrollment_done')
    self.listen_event(self._enrollment_failed_callback, 'esphome.enrollment_failed')
    self.listen_event(self._finger_deleted_callback, 'esphome.finger_deleted')
    with open(CONFIG_PATH, 'r') as config_file:
      self.config = yaml.safe_load(config_file)

  def _enrollment_started_callback(self, _, data, __):
    self.log('enrollment_started_callback')
    finger_id = int(data['finger_id'])

    existing_index = self._find_index(finger_id)

    new_finger = self._new_finger(
      finger_id=finger_id, 
      user_name=data['user_name'], 
      finger=data['finger'], 
      lock=data['lock'])

    if len(existing_index) == 0:
      self.config['fingers'].append(new_finger)
    else:
      self.config['fingers'][existing_index[0]] = new_finger

    self._save_config()

  def _enrollment_done_callback(self, _, data, __):
    self.log('enrollment_done_callback')
    self._set_status(data['finger_id'], 'done')

  def _enrollment_failed_callback(self, _, data, __):
    self.log('enrollment_done_callback')
    self._set_status(data['finger_id'], 'failed')

  def _finger_deleted_callback(self, _, data, __):
    self.log('finger_deleted_callback')

    index = self._find_index(data['finger_id'])

    if len(index) == 1:
      del self.config['fingers'][index[0]]
    else:
      self.error('There was an error finding an index')

    self._save_config()


  def _find_index(self, finger_id: int) -> list:
        return [index for index,x in enumerate(self.config['fingers']) if x['finger_id'] == int(finger_id)]
  
  def _set_status(self, finger_id: int, status: str):
    index = self._find_index(finger_id)

    if len(index) == 1:
      self.config['fingers'][index[0]]['status'] = 'done'
    else:
      self.error('There was an error finding an index')

    self._save_config()

  def _new_finger(self, finger_id: int, user_name: str, finger:str, lock: str) -> dict:
    return {
        'finger_id': finger_id,
        'user_name': user_name,
        'finger': finger,
        'lock': lock,
        'status': 'pending',
        'datetime': datetime.datetime.now().strftime('%Y-%m-%d_%H:%M:%S')
    }

  def _save_config(self):
    with open(CONFIG_PATH, 'w') as config_file:
      yaml.dump(self.config, config_file)

