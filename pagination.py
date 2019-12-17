import json                                                                                                                                                                                                                                 
import logging
from base64 import b64encode
from urllib.parse import urlparse, parse_qsl, urlunparse, urlencode

from rest_framework import pagination
from rest_framework.response import Response


log = logging.getLogger('applog')


class DecimalEncoder(json.JSONEncoder):                                                                                                                                                                                                     
    def default(self, obj):
        if isinstance(obj, Decimal):
            return float(obj)
        return super(DecimalEncoder, self).default(obj)


class DynamoDBPagination(pagination.PageNumberPagination):
    def __init__(self, *pargs, **kwargs):
        super(DynamoDBPagination, self).__init__(*pargs, **kwargs)
        self.pagination_keys = 'page_keys'

    def get_paginated_response(self, resp_args):
        ddb_resp = resp_args['ddb_resp']
        request = resp_args['request']

        start_key = request.GET.get('start_key')

        if not start_key:
            self._store_key(request, 'init')
        else:
            self._store_key(request, start_key)

        prev_url = self._create_previous_page_url(request, ddb_resp, start_key)
        next_url = self._create_next_page_url(request, ddb_resp)

        return Response({
            'count': ddb_resp.get('Count'),
            'results': ddb_resp.get('Items', []),
            'previous': prev_url,
            'next': next_url
        })  

    def _create_previous_page_url(self, request, ddb_resp, start_key):
        if not start_key:
            return None

        try:
            key = self._get_previous_key(request, start_key)
            if key:
                if key == 'init':
                    return self._create_url_with_start_key(request, None)

                url = self._create_url_with_start_key(request, key)
                return url 

        except Exception as e:
            log.error(f'Cannot create previous page url: {e}')

        return None

    def _create_next_page_url(self, request, ddb_resp):
        try:
            key = ddb_resp.get('LastEvaluatedKey')
            if key:
                key = self._serialize_key(key)
                url = self._create_url_with_start_key(request, key)
                return url

        except Exception as e:
            log.error(f'Cannot create next page url: {e}')

        return None

    def _create_url_with_start_key(self, request, start_key):
        full_path = request.get_full_path()
        # full_path = request.build_absolute_uri()

        parsed_url = urlparse(full_path)
        parsed_query = [val for val in parse_qsl(parsed_url.query) if val[0] != 'start_key']

        if start_key:
            parsed_query.append(('start_key', start_key))

        new_url = parsed_url._replace(query=urlencode(parsed_query))

        return urlunparse(new_url)

    def _serialize_key(self, key):
        key = json.dumps(key, cls=DecimalEncoder).encode('utf-8')
        key = b64encode(key).decode('utf-8')

        return key

    def _store_key(self, request, key):
        keys = request.session.get(self.pagination_keys, '[]')
        keys = json.loads(keys)

        if key == 'init':
            keys = [key]
        else:
            keys.append(key)

        keys = json.dumps(keys)
        request.session[self.pagination_keys] = keys

    def _show_keys(self, request):
        keys = request.session.get(self.pagination_keys, '[]')
        keys = json.loads(keys)
        log.info(keys)
        
    def _get_previous_key(self, request, current_key):                                                                                                                                                                                      
        keys = request.session.get(self.pagination_keys)
        keys = json.loads(keys)

        previous_key = keys[keys.index(current_key) - 1]

        return previous_key

