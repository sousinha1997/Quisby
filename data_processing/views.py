from rest_framework.decorators import api_view
from rest_framework.response import Response

# Sample GET method.
from pquisby import get_data
from pquisby.compare_result import compare_results


@api_view(['GET'])
def get_request_data(request):
    try:
        return Response({"Project": "Quisby", "Status": "Working"})
    except Exception as e:
        print(e)
        return Response({"status": "failed", "Exception": str(e)})


@api_view(['POST'])
def get_metrics_data(request):
    print(request.data)
    try:
        data = request.data
        tests = data['resource_id']
        custom_headers = {"Authorization": request.META['HTTP_AUTHORIZATION']}
        if len(tests) == 1:
            # Process single result
            test_name = tests[0]["name"]
            resource_id = tests[0]["rid"]
            spreadsheet, json_data = get_data.fetch_test_data(resource_id,test_name,custom_headers)
            if spreadsheet is None:
                return Response({"status": "failure", "message": "Unable to chart the test"})
            print("Test chart -")
            print(f"https://docs.google.com/spreadsheets/d/{spreadsheet}")
            return Response({"status": "success","sheet_url":f"https://docs.google.com/spreadsheets/d/{spreadsheetId}", "jsonData": json_data})
        else:
            spreadsheets = []
            for test in tests:
                # Compare multiple results
                test_name = test["name"]
                resource_id = test["rid"]
                spreadsheet, json_data, benchmark_name = get_data.fetch_test_data(resource_id, test_name)
                print("Test charts -")
                print(f"https://docs.google.com/spreadsheets/d/{spreadsheet}")
                spreadsheets.append(spreadsheet)
            # Create comparison chart
            comp_spreadsheet = compare_results(spreadsheets, benchmark_name)
            print("Comparison chart -")
            print(f"https://docs.google.com/spreadsheets/d/{comp_spreadsheet}")
        return Response({"status": "success", "sheet_url":f"https://docs.google.com/spreadsheets/d/{comp_spreadsheet}"})
    except Exception as e:
        return Response({"status": "failed", "Exception": str(e)})


@api_view(['POST'])
def delete_record(request):
    try:
        data = request.data
        tests = data['resource_id']
        if len(tests) == 1:
            # Delete single result
            test_name = tests[0]["name"]
            resource_id = tests[0]["rid"]
            spreadsheet = get_data.delete_test_data(resource_id, test_name)
            print("Deleted spreadsheet -")
            print(f"https://docs.google.com/spreadsheets/d/{spreadsheet}")
        else:
            # Delete multiple result
            spreadsheet_list = []
            for test in tests:
                test_name = test[0]["name"]
                resource_id = test[0]["rid"]
                spreadsheet = get_data.delete_test_data(resource_id, test_name)
                print("Deleted spreadsheet -")
                print(f"https://docs.google.com/spreadsheets/d/{spreadsheet}")
                spreadsheet_list.append(spreadsheet)
        return Response({"status": "success", "spreadsheetId":spreadsheet_list })
    except Exception as e:
        print(e)
        return Response({"status": "failed", "Exception": str(e)})