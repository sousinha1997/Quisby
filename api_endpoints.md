# API endpoints

1. Get metric data
endpoint: http://<server>/quisby/get_metrics_data/
    Input: 
    ```json
        {
        "resource_id": [
            {
                "name": "<resource/dataset name>",
                "rid": "<resource id>"
            }]
        }
    ```
    Output:
    ```json
        {"status": "success","spreadsheetId":spreadsheetId}
    ```

2. Delete record 
endpoint: http://<server>/quisby/delete_record/
    Input:
    ```json
        {"resource_id": [
            {
                "name": "<resource/dataset name>",
                "rid": "<resource id>"
            }]
        }
    ```
    Output: 
    ```json
    {"status": "success","rid":<resource id>}
    ```