import json
from rest_framework.renderers import JSONRenderer

class JSONRenderer(JSONRenderer):
  # charset = 'utf-8'

  # def render(self, data, status, accepted_media_type=None, renderer_context=None):
  #   return json.dumps({
  #     'result': data,
  #     'resultCode': status,
  #   })

  def render(self, data, status, accepted_media_type=None, renderer_context=None):
    return {
      'result': data,
      'resultCode': status,
    }