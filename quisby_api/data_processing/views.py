from rest_framework.decorators import api_view
from rest_framework.response import Response

# Sample GET method.
from pquisby import get_data

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
        tests = data['resource_id']
        if len(tests) == 1:
            # Process single result
            test_name = tests[0]["name"]
            resource_id = tests[0]["rid"]
            spreadsheetId = get_data.fetch_test_data(resource_id,test_name)
        for test in tests:
            # Compare multiple results
            # test_name = test["name"]
            # resource_id = test["rid"]
            # Get required files
            pass

        return Response({"status": "success","spreadsheetId":spreadsheetId})
    except Exception as e:
        print(e)
        return Response({"status": "failed", "Exception": str(e)})

@api_view(['POST'])
def delete_record(request):
    try:
        data = request.data
        tests = data['resource_id']
        if len(tests) == 1:
            # Process single result
            test_name = tests[0]["name"]
            resource_id = tests[0]["rid"]
            spreadsheetId = get_data.delete_test_data(resource_id, test_name)
        for test in tests:
            # Compare multiple results
            # test_name = test["name"]
            # resource_id = test["rid"]
            # Get required files
            pass
        return Response({"status": "success", "resource_id": data["resource_id"]})
    except Exception as e:
        print(e)
        return Response({"status": "failed", "Exception": str(e)})
