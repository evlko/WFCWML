using UnityEngine;
using UnityEditor;

[CustomEditor(typeof(ApiClient))]
public class ApiClientEditor : Editor
{
    private static readonly string[] judgeOptions = new string[]
    {
        "0: Always Continue",
        "1: 90% Continue"
    };
    
    private static readonly string[] advisorOptions = new string[]
    {
        "0: Random",
        "1: Greedy"
    };

    public override void OnInspectorGUI()
    {
        // Draw default inspector but we'll override judge and advisor fields
        serializedObject.Update();
        
        // Draw all properties except judgeId and advisorId
        SerializedProperty prop = serializedObject.GetIterator();
        bool enterChildren = true;
        while (prop.NextVisible(enterChildren))
        {
            enterChildren = false;
            if (prop.name == "m_Script")
            {
                using (new EditorGUI.DisabledScope(true))
                    EditorGUILayout.PropertyField(prop, true);
            }
            else if (prop.name != "judgeId" && prop.name != "advisorId")
            {
                EditorGUILayout.PropertyField(prop, true);
            }
        }
        
        // Custom dropdowns for judge and advisor
        ApiClient apiClient = (ApiClient)target;
        
        EditorGUILayout.Space(5);
        EditorGUILayout.LabelField("Algorithm Selection", EditorStyles.boldLabel);
        
        apiClient.judgeId = EditorGUILayout.Popup("Judge", apiClient.judgeId, judgeOptions);
        apiClient.advisorId = EditorGUILayout.Popup("Advisor", apiClient.advisorId, advisorOptions);
        
        serializedObject.ApplyModifiedProperties();
        
        EditorGUILayout.Space(10);

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

        EditorGUILayout.BeginHorizontal();
        
        EditorGUI.BeginDisabledGroup(apiClient.gridRenderer == null);
        if (GUILayout.Button("Render Grid", GUILayout.Height(30)))
        {
            apiClient.RenderGrid();
        }
        EditorGUI.EndDisabledGroup();

        EditorGUI.BeginDisabledGroup(apiClient.gridRenderer == null);
        if (GUILayout.Button("Clear Grid", GUILayout.Height(30)))
        {
            apiClient.ClearGrid();
        }
        EditorGUI.EndDisabledGroup();
        
        EditorGUILayout.EndHorizontal();
    }
}