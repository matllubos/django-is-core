from django.conf import settings
from pydjamodb.models import DynamoModel
from pynamodb.attributes import (
    MapAttribute, NumberAttribute, UnicodeAttribute, UTCDateTimeAttribute, BooleanAttribute, NumberAttribute
)


class Comment(DynamoModel):

    issue_id = UnicodeAttribute(hash_key=True)
    user_id = UnicodeAttribute(range_key=True)
    content = UnicodeAttribute()
    is_public = BooleanAttribute()
    priority = NumberAttribute()

    class Meta:
        table_name = 'comment'
