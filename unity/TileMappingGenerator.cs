using UnityEngine;
using UnityEditor;
using System.Collections.Generic;
using System.IO;
using System.Linq;

public class TileMappingGenerator : EditorWindow
{
    private TextAsset jsonFile;
    private string spriteFolderPath = "Assets/Sprites/forest";
    private string outputFolderPath = "Assets/TileMappings";
    private bool overwriteExisting = false;
    private Vector2 scrollPosition;
    
    [MenuItem("Tools/WFC/Tile Mapping Generator")]
    public static void ShowWindow()
    {
        GetWindow<TileMappingGenerator>("Tile Mapping Generator");
    }
    
    private void OnGUI()
    {
        GUILayout.Label("Tile Mapping Generator", EditorStyles.boldLabel);
        EditorGUILayout.Space();
        
        EditorGUILayout.HelpBox(
            "This tool generates TileMapping ScriptableObjects from your patterns JSON file. " +
            "It will automatically find sprites and set up weighted variants.",
            MessageType.Info
        );
        
        EditorGUILayout.Space();

        jsonFile = (TextAsset)EditorGUILayout.ObjectField(
            "Patterns JSON File",
            jsonFile,
            typeof(TextAsset),
            false
        );
        
        spriteFolderPath = EditorGUILayout.TextField("Sprite Folder Path", spriteFolderPath);
        outputFolderPath = EditorGUILayout.TextField("Output Folder Path", outputFolderPath);
        overwriteExisting = EditorGUILayout.Toggle("Overwrite Existing", overwriteExisting);
        
        EditorGUILayout.Space();
        
        EditorGUI.BeginDisabledGroup(jsonFile == null);
        if (GUILayout.Button("Generate Tile Mappings", GUILayout.Height(40)))
        {
            GenerateTileMappings();
        }
        EditorGUI.EndDisabledGroup();
        
        if (jsonFile == null)
        {
            EditorGUILayout.HelpBox("Please assign a patterns JSON file to generate tile mappings.", MessageType.Warning);
        }
        
        EditorGUILayout.Space();

        EditorGUILayout.LabelField("Instructions:", EditorStyles.boldLabel);
        scrollPosition = EditorGUILayout.BeginScrollView(scrollPosition, GUILayout.Height(200));
        EditorGUILayout.HelpBox(
            "1. Assign your patterns JSON file (e.g., patterns_forest.json)\n" +
            "2. Set the sprite folder path where your tile sprites are located\n" +
            "3. Set the output folder where TileMappings will be created\n" +
            "4. Click 'Generate Tile Mappings'\n\n" +
            "The tool will:\n" +
            "- Parse the JSON file\n" +
            "- Find matching sprites for each pattern\n" +
            "- Create TileMapping assets with proper weights\n" +
            "- Save them to the output folder\n\n" +
            "Example JSON structure:\n" +
            "{\n" +
            "  \"patterns\": [\n" +
            "    {\n" +
            "      \"id\": 1,\n" +
            "      \"name\": \"Empty Ground\",\n" +
            "      \"patterns\": [\n" +
            "        {\"image_path\": \"tile_0048.png\", \"weight\": 15},\n" +
            "        {\"image_path\": \"tile_0049.png\", \"weight\": 2}\n" +
            "      ]\n" +
            "    }\n" +
            "  ]\n" +
            "}",
            MessageType.None
        );
        EditorGUILayout.EndScrollView();
    }
    
    private void GenerateTileMappings()
    {
        if (jsonFile == null)
        {
            EditorUtility.DisplayDialog("Error", "Please assign a JSON file.", "OK");
            return;
        }
        
        try
        {
            PatternConfig config = JsonUtility.FromJson<PatternConfig>(jsonFile.text);
            
            if (config == null || config.patterns == null || config.patterns.Length == 0)
            {
                EditorUtility.DisplayDialog("Error", "Failed to parse JSON or no patterns found.", "OK");
                return;
            }
            
            if (!AssetDatabase.IsValidFolder(outputFolderPath))
            {
                string[] folders = outputFolderPath.Split('/');
                string currentPath = folders[0];
                
                for (int i = 1; i < folders.Length; i++)
                {
                    string newPath = currentPath + "/" + folders[i];
                    if (!AssetDatabase.IsValidFolder(newPath))
                    {
                        AssetDatabase.CreateFolder(currentPath, folders[i]);
                    }
                    currentPath = newPath;
                }
            }
            
            int createdCount = 0;
            int skippedCount = 0;
            int errorCount = 0;
            
            foreach (var pattern in config.patterns)
            {
                string assetPath = $"{outputFolderPath}/TileMapping_{pattern.id:D3}_{SanitizeFileName(pattern.name)}.asset";
                
                if (!overwriteExisting && File.Exists(assetPath))
                {
                    Debug.Log($"Skipping existing: {assetPath}");
                    skippedCount++;
                    continue;
                }
                
                TileMapping tileMapping = ScriptableObject.CreateInstance<TileMapping>();
                tileMapping.tileUid = pattern.id;
                tileMapping.tileName = pattern.name;
                tileMapping.spriteVariants = new List<SpriteVariant>();
                
                if (pattern.patterns != null)
                {
                    foreach (var spritePattern in pattern.patterns)
                    {
                        string spritePath = $"{spriteFolderPath}/{Path.GetFileNameWithoutExtension(spritePattern.image_path)}.png";
                        Sprite sprite = AssetDatabase.LoadAssetAtPath<Sprite>(spritePath);
                        
                        if (sprite != null)
                        {
                            SpriteVariant variant = new SpriteVariant
                            {
                                sprite = sprite,
                                weight = spritePattern.weight
                            };
                            tileMapping.spriteVariants.Add(variant);
                        }
                        else
                        {
                            Debug.LogWarning($"Sprite not found: {spritePath}");
                        }
                    }
                }
                
                if (tileMapping.spriteVariants.Count > 0)
                {
                    if (overwriteExisting && File.Exists(assetPath))
                    {
                        AssetDatabase.DeleteAsset(assetPath);
                    }
                    
                    AssetDatabase.CreateAsset(tileMapping, assetPath);
                    createdCount++;
                    Debug.Log($"Created: {assetPath} with {tileMapping.spriteVariants.Count} variants");
                }
                else
                {
                    Debug.LogError($"No sprites found for pattern {pattern.id} ({pattern.name})");
                    errorCount++;
                }
            }
            
            AssetDatabase.SaveAssets();
            AssetDatabase.Refresh();
            
            string message = $"Generation complete!\n\n" +
                           $"Created: {createdCount}\n" +
                           $"Skipped: {skippedCount}\n" +
                           $"Errors: {errorCount}";
            
            EditorUtility.DisplayDialog("Success", message, "OK");
            
            Object obj = AssetDatabase.LoadAssetAtPath<Object>(outputFolderPath);
            Selection.activeObject = obj;
            EditorGUIUtility.PingObject(obj);
        }
        catch (System.Exception e)
        {
            EditorUtility.DisplayDialog("Error", $"Failed to generate tile mappings:\n{e.Message}", "OK");
            Debug.LogError($"TileMappingGenerator error: {e}");
        }
    }
    
    private string SanitizeFileName(string name)
    {
        string sanitized = name;
        foreach (char c in Path.GetInvalidFileNameChars())
        {
            sanitized = sanitized.Replace(c, '_');
        }
        return sanitized.Replace(" ", "_");
    }
}

[System.Serializable]
public class PatternConfig
{
    public string images_folder;
    public Pattern[] patterns;
}

[System.Serializable]
public class Pattern
{
    public int id;
    public string name;
    public string[] tags;
    public int is_walkable;
    public float weight;
    public SpritePattern[] patterns;
}

[System.Serializable]
public class SpritePattern
{
    public string image_path;
    public float weight;
}