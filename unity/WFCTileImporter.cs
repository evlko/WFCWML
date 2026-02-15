using UnityEngine;
using UnityEditor;
using System.Collections.Generic;
using System.IO;

/// <summary>
/// Unified tool for importing WFC tiles from JSON files.
/// Replaces both WFCConfigImporter and TileMappingGenerator.
/// </summary>
public class WFCTileImporter : EditorWindow
{
    [System.Serializable]
    private enum ImportMode
    {
        IndividualTiles,
        WFCConfig
    }
    
    private ImportMode importMode = ImportMode.IndividualTiles;
    private TextAsset jsonFile;
    private string jsonFilePath = "";
    private string spriteFolderPath = "Assets/Sprites/forest";
    private string outputFolderPath = "Assets/WFCTiles";
    private string configAssetName = "NewWFCConfig";
    private bool overwriteExisting = false;
    private Vector2 scrollPosition;
    
    [MenuItem("Tools/WFC/Tile Importer")]
    public static void ShowWindow()
    {
        GetWindow<WFCTileImporter>("WFC Tile Importer");
    }
    
    private void OnGUI()
    {
        GUILayout.Label("WFC Tile Importer", EditorStyles.boldLabel);
        EditorGUILayout.Space();
        
        EditorGUILayout.HelpBox(
            "Import WFC tiles from JSON patterns file. Choose to create individual tile assets or a complete WFCConfig.",
            MessageType.Info
        );
        
        EditorGUILayout.Space();
        
        // Import mode selection
        GUILayout.Label("Import Mode", EditorStyles.boldLabel);
        importMode = (ImportMode)EditorGUILayout.EnumPopup("Mode", importMode);
        
        EditorGUILayout.Space();
        
        // JSON source
        GUILayout.Label("JSON Source", EditorStyles.boldLabel);
        jsonFile = (TextAsset)EditorGUILayout.ObjectField("JSON TextAsset", jsonFile, typeof(TextAsset), false);
        
        GUILayout.Label("OR", EditorStyles.centeredGreyMiniLabel);
        
        GUILayout.BeginHorizontal();
        jsonFilePath = EditorGUILayout.TextField("JSON File Path", jsonFilePath);
        if (GUILayout.Button("Browse", GUILayout.Width(70)))
        {
            string path = EditorUtility.OpenFilePanel("Select JSON File", Application.dataPath, "json");
            if (!string.IsNullOrEmpty(path))
            {
                jsonFilePath = path;
            }
        }
        GUILayout.EndHorizontal();
        
        EditorGUILayout.Space();
        
        // Mode-specific settings
        if (importMode == ImportMode.IndividualTiles)
        {
            GUILayout.Label("Individual Tiles Settings", EditorStyles.boldLabel);
            spriteFolderPath = EditorGUILayout.TextField("Sprite Folder", spriteFolderPath);
            outputFolderPath = EditorGUILayout.TextField("Output Folder", outputFolderPath);
            overwriteExisting = EditorGUILayout.Toggle("Overwrite Existing", overwriteExisting);
        }
        else
        {
            GUILayout.Label("WFC Config Settings", EditorStyles.boldLabel);
            configAssetName = EditorGUILayout.TextField("Config Asset Name", configAssetName);
        }
        
        EditorGUILayout.Space();
        
        // Import button
        EditorGUI.BeginDisabledGroup(jsonFile == null && string.IsNullOrEmpty(jsonFilePath));
        if (GUILayout.Button("Import", GUILayout.Height(40)))
        {
            Import();
        }
        EditorGUI.EndDisabledGroup();
        
        if (jsonFile == null && string.IsNullOrEmpty(jsonFilePath))
        {
            EditorGUILayout.HelpBox("Please provide a JSON file via TextAsset or file path.", MessageType.Warning);
        }
        
        EditorGUILayout.Space();
        
        // Instructions
        EditorGUILayout.LabelField("Instructions:", EditorStyles.boldLabel);
        scrollPosition = EditorGUILayout.BeginScrollView(scrollPosition, GUILayout.Height(150));
        
        if (importMode == ImportMode.IndividualTiles)
        {
            EditorGUILayout.HelpBox(
                "Individual Tiles Mode:\n" +
                "• Creates separate WFCTileDefinition assets for each pattern\n" +
                "• Automatically finds and assigns sprites\n" +
                "• Useful for building a tile library\n" +
                "• Can be used with TileMappingRepository for rendering",
                MessageType.None
            );
        }
        else
        {
            EditorGUILayout.HelpBox(
                "WFC Config Mode:\n" +
                "• Creates a single WFCConfig asset containing all tiles\n" +
                "• Stores image paths (not sprite references)\n" +
                "• Used for API communication\n" +
                "• Can be sent to the Python backend for generation",
                MessageType.None
            );
        }
        
        EditorGUILayout.EndScrollView();
    }
    
    private void Import()
    {
        // Load JSON content
        string jsonContent = null;
        if (jsonFile != null)
        {
            jsonContent = jsonFile.text;
        }
        else if (!string.IsNullOrEmpty(jsonFilePath) && File.Exists(jsonFilePath))
        {
            jsonContent = File.ReadAllText(jsonFilePath);
        }
        else
        {
            EditorUtility.DisplayDialog("Error", "Please provide a valid JSON file.", "OK");
            return;
        }
        
        if (string.IsNullOrEmpty(jsonContent))
        {
            EditorUtility.DisplayDialog("Error", "JSON content is empty.", "OK");
            return;
        }
        
        try
        {
            if (importMode == ImportMode.IndividualTiles)
            {
                ImportIndividualTiles(jsonContent);
            }
            else
            {
                ImportWFCConfig(jsonContent);
            }
        }
        catch (System.Exception e)
        {
            EditorUtility.DisplayDialog("Error", $"Import failed:\n{e.Message}", "OK");
            Debug.LogError($"WFCTileImporter error: {e}");
        }
    }
    
    private void ImportIndividualTiles(string jsonContent)
    {
        PatternConfig config = JsonUtility.FromJson<PatternConfig>(jsonContent);
        
        if (config == null || config.patterns == null || config.patterns.Length == 0)
        {
            EditorUtility.DisplayDialog("Error", "Failed to parse JSON or no patterns found.", "OK");
            return;
        }
        
        // Ensure output folder exists
        EnsureFolderExists(outputFolderPath);
        
        int createdCount = 0;
        int skippedCount = 0;
        int errorCount = 0;
        
        foreach (var pattern in config.patterns)
        {
            string assetPath = $"{outputFolderPath}/WFCTile_{pattern.id:D3}_{SanitizeFileName(pattern.name)}.asset";
            
            if (!overwriteExisting && File.Exists(assetPath))
            {
                Debug.Log($"Skipping existing: {assetPath}");
                skippedCount++;
                continue;
            }
            
            WFCTileDefinition tile = ScriptableObject.CreateInstance<WFCTileDefinition>();
            tile.id = pattern.id;
            tile.tileName = pattern.name;
            tile.tags = pattern.tags != null ? new List<string>(pattern.tags) : new List<string>();
            tile.isWalkable = pattern.is_walkable == 1;
            tile.weight = pattern.weight;
            tile.spriteVariants = new List<WeightedSprite>();
            
            // Import rules
            if (pattern.rules != null)
            {
                tile.rules = new TileRules();
                tile.rules.up = ParseRuleOptions(pattern.rules.up);
                tile.rules.down = ParseRuleOptions(pattern.rules.down);
                tile.rules.left = ParseRuleOptions(pattern.rules.left);
                tile.rules.right = ParseRuleOptions(pattern.rules.right);
            }
            
            if (pattern.patterns != null)
            {
                foreach (var spritePattern in pattern.patterns)
                {
                    string spritePath = $"{spriteFolderPath}/{Path.GetFileNameWithoutExtension(spritePattern.image_path)}.png";
                    Sprite sprite = AssetDatabase.LoadAssetAtPath<Sprite>(spritePath);
                    
                    if (sprite != null)
                    {
                        WeightedSprite variant = new WeightedSprite
                        {
                            sprite = sprite,
                            imagePath = spritePattern.image_path,
                            weight = spritePattern.weight
                        };
                        tile.spriteVariants.Add(variant);
                    }
                    else
                    {
                        Debug.LogWarning($"Sprite not found: {spritePath}");
                    }
                }
            }
            
            if (tile.spriteVariants.Count > 0)
            {
                if (overwriteExisting && File.Exists(assetPath))
                {
                    AssetDatabase.DeleteAsset(assetPath);
                }
                
                AssetDatabase.CreateAsset(tile, assetPath);
                createdCount++;
                Debug.Log($"Created: {assetPath} with {tile.spriteVariants.Count} variants and rules");
            }
            else
            {
                Debug.LogError($"No sprites found for pattern {pattern.id} ({pattern.name})");
                errorCount++;
            }
        }
        
        AssetDatabase.SaveAssets();
        AssetDatabase.Refresh();
        
        string message = $"Import complete!\n\n" +
                       $"Created: {createdCount}\n" +
                       $"Skipped: {skippedCount}\n" +
                       $"Errors: {errorCount}";
        
        EditorUtility.DisplayDialog("Success", message, "OK");
        
        Object obj = AssetDatabase.LoadAssetAtPath<Object>(outputFolderPath);
        Selection.activeObject = obj;
        EditorGUIUtility.PingObject(obj);
    }
    
    private void ImportWFCConfig(string jsonContent)
    {
        PatternConfig patternConfig = JsonUtility.FromJson<PatternConfig>(jsonContent);
        
        if (patternConfig == null || patternConfig.patterns == null || patternConfig.patterns.Length == 0)
        {
            EditorUtility.DisplayDialog("Error", "Failed to parse JSON or no patterns found.", "OK");
            return;
        }
        
        WFCConfig config = ScriptableObject.CreateInstance<WFCConfig>();
        config.imagesFolder = patternConfig.images_folder;
        config.tiles = new List<WFCTileDefinition>();
        
        int importedCount = 0;
        int errorCount = 0;
        
        foreach (var pattern in patternConfig.patterns)
        {
            WFCTileDefinition tile = ScriptableObject.CreateInstance<WFCTileDefinition>();
            tile.id = pattern.id;
            tile.tileName = pattern.name;
            tile.tags = pattern.tags != null ? new List<string>(pattern.tags) : new List<string>();
            tile.isWalkable = pattern.is_walkable == 1;
            tile.weight = pattern.weight;
            tile.spriteVariants = new List<WeightedSprite>();
            
            // Import rules
            if (pattern.rules != null)
            {
                tile.rules = new TileRules();
                tile.rules.up = ParseRuleOptions(pattern.rules.up);
                tile.rules.down = ParseRuleOptions(pattern.rules.down);
                tile.rules.left = ParseRuleOptions(pattern.rules.left);
                tile.rules.right = ParseRuleOptions(pattern.rules.right);
            }
            
            // Import sprite variants (store image paths only, no sprite references)
            if (pattern.patterns != null)
            {
                foreach (var spritePattern in pattern.patterns)
                {
                    WeightedSprite variant = new WeightedSprite
                    {
                        sprite = null, // No sprite reference for API config
                        imagePath = spritePattern.image_path,
                        weight = spritePattern.weight
                    };
                    tile.spriteVariants.Add(variant);
                }
            }
            
            if (tile.spriteVariants.Count > 0)
            {
                config.tiles.Add(tile);
                importedCount++;
            }
            else
            {
                Debug.LogError($"No sprite variants found for pattern {pattern.id} ({pattern.name})");
                errorCount++;
            }
        }
        
        string assetPath = $"Assets/{configAssetName}.asset";
        assetPath = AssetDatabase.GenerateUniqueAssetPath(assetPath);
        
        AssetDatabase.CreateAsset(config, assetPath);
        
        // Save tile definitions as sub-assets
        foreach (var tile in config.tiles)
        {
            AssetDatabase.AddObjectToAsset(tile, config);
        }
        
        AssetDatabase.SaveAssets();
        AssetDatabase.Refresh();
        
        EditorUtility.FocusProjectWindow();
        Selection.activeObject = config;
        
        EditorUtility.DisplayDialog(
            "Success",
            $"WFCConfig created successfully at:\n{assetPath}\n\n" +
            $"Tiles imported: {importedCount}\n" +
            $"Errors: {errorCount}\n\n" +
            $"This config can be used with ApiClient for generation.",
            "OK"
        );
    }
    
    private List<RuleOption> ParseRuleOptions(string[] ruleStrings)
    {
        List<RuleOption> options = new List<RuleOption>();
        
        if (ruleStrings == null || ruleStrings.Length == 0)
        {
            return options;
        }
        
        foreach (string ruleStr in ruleStrings)
        {
            RuleOption option = new RuleOption();
            
            // Try to parse as integer (tile ID)
            if (int.TryParse(ruleStr, out int tileId))
            {
                option.isTag = false;
                option.tileId = tileId;
            }
            else
            {
                // It's a tag
                option.isTag = true;
                option.tagName = ruleStr;
            }
            
            options.Add(option);
        }
        
        return options;
    }
    
    private void EnsureFolderExists(string folderPath)
    {
        if (AssetDatabase.IsValidFolder(folderPath))
        {
            return;
        }
        
        string[] folders = folderPath.Split('/');
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

// JSON parsing classes
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
    public PatternRules rules;
    public SpritePattern[] patterns;
}

[System.Serializable]
public class PatternRules
{
    public string[] up;
    public string[] down;
    public string[] left;
    public string[] right;
}

[System.Serializable]
public class SpritePattern
{
    public string image_path;
    public float weight;
}