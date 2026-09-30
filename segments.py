import os

import django

# Set the default Django settings module for the 'one-signal' program.
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'column.settings')

django.setup()

from django.db.models.functions import Lower

from api.one_signal.api import SegmentAPI
from api.models import Categories


segment_api = SegmentAPI()
sport = Categories.objects.get(name='Sports')

def create_segments(categories, recursion=False):
    for category in categories:
        if category.subcategories.exists():
            create_segments(category.subcategories.all(), True)

            filters = list()
            for cat_name in category.subcategories.annotate(lname=Lower('name')).values_list('lname', flat=True):
                if filters:
                    filters.append({"operator": "OR"})
                filters.append({
                    "field": "tag",
                    "key": cat_name,
                    "relation": "=",
                    "value": 1
                })

            status_code, data = segment_api.create_segment(category.name, filters)
        else:
            filters = [
                {
                    "field": "tag",
                    "key": category.name.lower(),
                    "relation": "=",
                    "value": 1
                }
            ]

            if recursion:
                filters.append({"operator": "OR"})
                filters.append({
                    "field": "tag",
                    "key": category.parent.name.lower(),
                    "relation": "=",
                    "value": 1
                })
            status_code, data = segment_api.create_segment(category.name, filters)
        print(status_code, data)

create_segments(sport.subcategories.all())

status_code, data = segment_api.get_segments()

for segment in data['segments']:
    print(segment)

# 1. Get all subcategories of Sports
# 2. if category has subcategories, create segment for each subcategory
# 3. if category hasn't subcategories, create segment
# 4. Create a segment for category with subcategories