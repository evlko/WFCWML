using UnityEngine;
using UnityEditor;

[CustomEditor(typeof(ApiClient))]
public class ApiClientEditor : Editor
{
    public override void OnInspectorGUI()
    {
        DrawDefaultInspector();
        EditorGUILayout.Space(10);

        ApiClient apiClient = (ApiClient)target;

        EditorGUILayout.LabelField("API Actions", EditorStyles.boldLabel);
        EditorGUILayout.Space(5);

        if (GUILayout.Button("Send Ping Request", GUILayout.Height(30)))
        {
            apiClient.Ping();
        }

        EditorGUILayout.Space(5);

        if (GUILayout.Button("Send Generate Request", GUILayout.Height(30)))
        {
            apiClient.Generate();
        }

        EditorGUILayout.Space(10);

        EditorGUILayout.LabelField("Grid Visualization", EditorStyles.boldLabel);
        EditorGUILayout.Space(5);

        bool hasGridData = apiClient.lastGeneratedGrid != null &&
                          apiClient.lastGeneratedGrid.grid != null &&
                          apiClient.lastGeneratedGrid.grid.Count > 0;

        EditorGUI.BeginDisabledGroup(!hasGridData || apiClient.gridRenderer == null);
        if (GUILayout.Button("Render Grid", GUILayout.Height(30)))
        {
            apiClient.RenderGrid();
        }
        EditorGUI.EndDisabledGroup();

        EditorGUILayout.Space(5);

        EditorGUI.BeginDisabledGroup(apiClient.gridRenderer == null);
        if (GUILayout.Button("Clear Grid", GUILayout.Height(30)))
        {
            apiClient.ClearGrid();
        }
        EditorGUI.EndDisabledGroup();

        EditorGUILayout.Space(10);

        if (hasGridData)
        {
            EditorGUILayout.LabelField("Grid Info", EditorStyles.boldLabel);
            int layers = apiClient.lastGeneratedGrid.grid.Count;
            int height = apiClient.lastGeneratedGrid.grid[0].Length;
            int width = apiClient.lastGeneratedGrid.grid[0][0].Length;
            
            EditorGUILayout.LabelField($"Layers: {layers}");
            EditorGUILayout.LabelField($"Size: {width} x {height}");
            EditorGUILayout.Space(5);
        }

        EditorGUILayout.HelpBox(
            "Ping: Tests the connection to the API server.",
            MessageType.Info
        );

        EditorGUILayout.HelpBox(
            "Generate: Sends a POST request with height, width, and levels parameters " +
            "to generate content. Configure the parameters in the 'Generate Parameters' section above. " +
            "If 'Auto Render' is enabled and GridRenderer is assigned, the grid will be rendered automatically.",
            MessageType.Info
        );

        if (!hasGridData)
        {
            EditorGUILayout.HelpBox(
                "No grid data available. Generate a grid first using 'Send Generate Request'.",
                MessageType.Warning
            );
        }
        else if (apiClient.gridRenderer == null)
        {
            EditorGUILayout.HelpBox(
                "GridRenderer not assigned! Assign a GridRenderer component to visualize the grid.",
                MessageType.Warning
            );
        }

        EditorGUILayout.HelpBox(
            "Make sure the API server is running at the configured URL before sending requests.",
            MessageType.Warning
        );
    }
}