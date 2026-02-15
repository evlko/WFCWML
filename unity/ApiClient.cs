using UnityEngine;
using UnityEngine.Networking;
using System.Collections;
using System.Collections.Generic;
using System.Text;

public class ApiClient : MonoBehaviour
{
    [Header("API Configuration")]
    [Tooltip("Base URL of the API server")]
    public string apiBaseUrl = "http://localhost:8000";

    [Header("Generate Parameters")]
    [Tooltip("Height of the grid to generate")]
    public int height = 10;
    
    [Tooltip("Width of the grid to generate")]
    public int width = 10;
    
    [Tooltip("Number of levels/layers to generate")]
    public int levels = 1;

    [Header("Rendering")]
    [Tooltip("Grid renderer for visualizing the generated grid")]
    public GridRenderer gridRenderer;
    
    [Tooltip("Automatically render grid after generation")]
    public bool autoRender = true;

    [Header("Response")]
    [Tooltip("Last response from the server")]
    public string lastResponse = "";
    
    [Tooltip("Last generated grid data")]
    public GenerateResponse lastGeneratedGrid;

    [ContextMenu("Send Ping Request")]
    public void Ping()
    {
        StartCoroutine(SendPingRequest());
    }

    [ContextMenu("Send Generate Request")]
    public void Generate()
    {
        StartCoroutine(SendGenerateRequest());
    }

    private IEnumerator SendPingRequest()
    {
        string url = $"{apiBaseUrl}/ping";
        Debug.Log($"Sending ping request to: {url}");

        using (UnityWebRequest request = UnityWebRequest.Get(url))
        {
            yield return request.SendWebRequest();

            if (request.result == UnityWebRequest.Result.ConnectionError ||
                request.result == UnityWebRequest.Result.ProtocolError)
            {
                lastResponse = $"Error: {request.error}";
                Debug.LogError($"Ping request failed: {request.error}");
                Debug.LogError($"Response Code: {request.responseCode}");
            }
            else
            {
                lastResponse = request.downloadHandler.text;
                Debug.Log($"Ping response received: {lastResponse}");
                
                PingResponse response = JsonUtility.FromJson<PingResponse>(lastResponse);
                Debug.Log($"Message from server: {response.message}");
            }
        }
    }

    private IEnumerator SendGenerateRequest()
    {
        string url = $"{apiBaseUrl}/generate";
        Debug.Log($"Sending generate request to: {url}");
        Debug.Log($"Parameters - Height: {height}, Width: {width}, Levels: {levels}");

        GenerateRequest requestBody = new GenerateRequest
        {
            height = this.height,
            width = this.width,
            levels = this.levels
        };

        string jsonBody = JsonUtility.ToJson(requestBody);
        Debug.Log($"Request body: {jsonBody}");

        using (UnityWebRequest request = new UnityWebRequest(url, "POST"))
        {
            byte[] bodyRaw = Encoding.UTF8.GetBytes(jsonBody);
            request.uploadHandler = new UploadHandlerRaw(bodyRaw);
            request.downloadHandler = new DownloadHandlerBuffer();
            request.SetRequestHeader("Content-Type", "application/json");

            yield return request.SendWebRequest();

            if (request.result == UnityWebRequest.Result.ConnectionError ||
                request.result == UnityWebRequest.Result.ProtocolError)
            {
                lastResponse = $"Error: {request.error}";
                Debug.LogError($"Generate request failed: {request.error}");
                Debug.LogError($"Response Code: {request.responseCode}");
                if (request.downloadHandler != null)
                {
                    Debug.LogError($"Response Body: {request.downloadHandler.text}");
                }
            }
            else
            {
                lastResponse = request.downloadHandler.text;
                Debug.Log($"Generate response received successfully");
                
                try
                {
                    lastGeneratedGrid = ParseGenerateResponse(lastResponse);
                    Debug.Log($"Parsed grid: {lastGeneratedGrid.grid.Count} layers");
                    
                    if (autoRender && gridRenderer != null)
                    {
                        RenderGrid();
                    }
                    else if (autoRender && gridRenderer == null)
                    {
                        Debug.LogWarning("Auto-render enabled but GridRenderer not assigned!");
                    }
                }
                catch (System.Exception e)
                {
                    Debug.LogError($"Failed to parse generate response: {e.Message}");
                    Debug.LogError($"Response was: {lastResponse}");
                }
            }
        }
    }
    
    // Unity's JsonUtility doesn't support nested arrays, so we need custom parsing
    private GenerateResponse ParseGenerateResponse(string json)
    {
        GenerateResponse response = new GenerateResponse();
        response.grid = new List<int[][]>();
        
        int gridStart = json.IndexOf("\"grid\"");
        if (gridStart == -1)
        {
            Debug.LogError("Could not find 'grid' in response");
            return response;
        }
        
        int arrayStart = json.IndexOf("[", gridStart);
        int arrayEnd = json.LastIndexOf("]");
        
        if (arrayStart == -1 || arrayEnd == -1)
        {
            Debug.LogError("Could not find grid array in response");
            return response;
        }
        
        string gridContent = json.Substring(arrayStart + 1, arrayEnd - arrayStart - 1).Trim();
        
        List<int[]> currentLayer = new List<int[]>();
        string currentRow = "";
        int bracketDepth = 0;
        
        for (int i = 0; i < gridContent.Length; i++)
        {
            char c = gridContent[i];
            
            if (c == '[')
            {
                bracketDepth++;
                if (bracketDepth == 1)
                {
                    currentRow = "";
                }
            }
            else if (c == ']')
            {
                bracketDepth--;
                if (bracketDepth == 0 && currentRow.Length > 0)
                {
                    int[] row = ParseIntArray(currentRow);
                    currentLayer.Add(row);
                    currentRow = "";
                }
                else if (bracketDepth == -1 && currentLayer.Count > 0)
                {
                    response.grid.Add(currentLayer.ToArray());
                    currentLayer = new List<int[]>();
                    bracketDepth = 0;
                }
            }
            else if (bracketDepth == 1)
            {
                currentRow += c;
            }
        }
        
        if (currentLayer.Count > 0)
        {
            response.grid.Add(currentLayer.ToArray());
        }
        
        return response;
    }
    
    private int[] ParseIntArray(string str)
    {
        string[] parts = str.Split(',');
        List<int> result = new List<int>();
        
        foreach (string part in parts)
        {
            string trimmed = part.Trim();
            if (!string.IsNullOrEmpty(trimmed) && int.TryParse(trimmed, out int value))
            {
                result.Add(value);
            }
        }
        
        return result.ToArray();
    }
    
    [ContextMenu("Render Last Grid")]
    public void RenderGrid()
    {
        if (lastGeneratedGrid == null || lastGeneratedGrid.grid == null || lastGeneratedGrid.grid.Count == 0)
        {
            Debug.LogWarning("No grid data to render. Generate a grid first.");
            return;
        }
        
        if (gridRenderer == null)
        {
            Debug.LogError("GridRenderer not assigned!");
            return;
        }
        
        Debug.Log($"Rendering grid with {lastGeneratedGrid.grid.Count} layer(s)");
        gridRenderer.RenderMultipleLayers(lastGeneratedGrid.grid);
    }
    
    [ContextMenu("Clear Grid")]
    public void ClearGrid()
    {
        if (gridRenderer != null)
        {
            gridRenderer.ClearGrid();
        }
    }
}

[System.Serializable]
public class PingResponse
{
    public string message;
}

[System.Serializable]
public class GenerateRequest
{
    public int height;
    public int width;
    public int levels;
}

[System.Serializable]
public class GenerateResponse
{
    public List<int[][]> grid;
}