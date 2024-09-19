import json

from mongoengine import QuerySet

from app.utils.permission_utils import filter_allowed_data


class BaseQuerySet(QuerySet):

    def to_clean_json_dict(self, follow_reference=False, permissions=None, method=0):
        return [Obj.to_clean_json_dict(follow_reference, permissions, method) for Obj in self]

    def to_clean_json(self, follow_reference=False, permissions=None, method=0):
        return json.dumps(self.to_clean_json_dict(follow_reference, permissions, method), default=str)


class CustomDocument:
    def _follow_reference(self, follow_reference, permissions, method):
        ret = {}
        for field_name in self:
            fld = self._fields.get(field_name)
            value = None
            doc = getattr(self, field_name, None)
            if doc and isinstance(doc, CustomDocument):
                value = json.loads(
                    fld.document_type.objects(id=doc.id).get().to_clean_json(follow_reference, permissions, method))
            if value is not None:
                ret.update({field_name: value})
        return ret

    def to_clean_json_dict(self, follow_reference=False, permissions=None, method=0):
        data = self.to_mongo().to_dict()
        if permissions:
            data = filter_allowed_data(data, permissions.get(type(self).__name__), method)
        if follow_reference:
            data.update(self._follow_reference(follow_reference, permissions, method))
        return data

    def to_clean_json(self, follow_reference=False, permissions=None, method=0):
        return json.dumps(self.to_clean_json_dict(follow_reference, permissions, method), default=str)
