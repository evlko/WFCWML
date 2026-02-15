using UnityEngine;
using System.Collections.Generic;

[CreateAssetMenu(fileName = "WFCConfig", menuName = "WFC/Configuration", order = 2)]
public class WFCConfig : ScriptableObject
{
    [Header("Images Configuration")]
    [Tooltip("Path to the images folder (e.g., 'sprites/forest/')")]
    public string imagesFolder = "sprites/forest/";

    [Header("Tile Definitions")]
    [Tooltip("List of tile definitions (replaces old patterns)")]
    public List<WFCTileDefinition> tiles = new List<WFCTileDefinition>();

    /// <summary>
    /// Converts this ScriptableObject to JSON format for API requests
    /// </summary>
    public string ToJson()
    {
        WFCConfigData configData = new WFCConfigData
        {
            images_folder = imagesFolder,
            patterns = new List<PatternData>()
        };

        foreach (var tile in tiles)
        {
            configData.patterns.Add(tile.ToPatternData());
        }

        return JsonUtility.ToJson(configData);
    }

    /// <summary>
    /// Loads configuration from a JSON file (e.g., patterns_forest.json)
    /// </summary>
    public void LoadFromJson(string jsonText)
    {
        WFCConfigData configData = JsonUtility.FromJson<WFCConfigData>(jsonText);
        imagesFolder = configData.images_folder;
        
        tiles.Clear();
        foreach (var patternData in configData.patterns)
        {
            WFCTileDefinition tile = CreateInstance<WFCTileDefinition>();
            tile.LoadFromPatternData(patternData);
            tiles.Add(tile);
        }
    }
}

// JSON serialization class for WFC configuration
[System.Serializable]
public class WFCConfigData
{
    public string images_folder;
    public List<PatternData> patterns;
}