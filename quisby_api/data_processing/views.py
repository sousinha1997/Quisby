from rest_framework.decorators import api_view
from rest_framework.response import Response

# Sample GET method.

@api_view(['GET'])
def get_request_data(request):
    try:
        return Response({"Project":"Quisby","Status":"Working"})
    except Exception as e:
        print(e)
        return Response({"status": "failed", "Exception": str(e)})


@api_view(['POST'])
def get_metrics_data(request):
    print(request.data)
    try:
        data = request.data
        print(data['resource_id'])
        return Response({"status": "success","resource_id":data["resource_id"]})
    except Exception as e:
        print(e)
        return Response({"status": "failed", "Exception": str(e)})

@api_view(['POST'])
def delete_record(request):
    try:
        data = request.data
        print(data['resource_id'])
        return Response({"status": "success", "resource_id": data["resource_id"]})
    except Exception as e:
        print(e)
        return Response({"status": "failed", "Exception": str(e)})
