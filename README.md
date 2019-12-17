# DRF-dynamodb-pagination
Dynamodb pagination for django rest framework.

# Usage:
```
class SomeViewSet(viewsets.ViewSet, generics.GenericAPIView):
    pagination_class = DynamoDBPagination

    def list(self, request):
        serializer = SomeSerializer(data=request.GET)
        if serializer.is_valid():                                                                                                                                                                                                           
            try:
                ddb_resp = self.get_raw_ddb_response()

                resp_args = {'ddb_resp': ddb_resp, 'request': request}
                resp = self.get_paginated_response(resp_args)

                resp['Access-Control-Allow-Origin'] = '*' 
                resp["Access-Control-Allow-Headers"] = "X-Requested-With, Content-Type"
                return resp

            except Exception as e:
                log.error('Cannot perform search: {}'.format(e))

                return Response(
                    {'error': str(e)}, status=status.HTTP_400_BAD_REQUEST
                )   

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

```
