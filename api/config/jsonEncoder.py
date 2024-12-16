from datetime import datetime
from django.db import models as django_models
from django.db.models.query import QuerySet
import json

""" [JsonEncode処理]
    Json形式に変換する
Returns:
    [string]: [Json文字列]
"""
class JsonEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, django_models.Model) and hasattr(obj, 'to_dict'):
            return obj.to_dict()
        if isinstance(obj, QuerySet):
            return list(obj)
        if isinstance(obj, datetime):
            return obj.isoformat()
        # return super(DateTimeSupportJSONEncoder, self).default(obj)
        json.JSONEncoder.default(self, obj)

    def getJson(obj):
        return json.dumps(obj, ensure_ascii = False, cls = JsonEncoder);