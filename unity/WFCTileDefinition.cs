using UnityEngine;
using System.Collections.Generic;

/// <summary>
/// Unified tile definition that can be used for both WFC configuration and runtime rendering.
/// Replaces the duplicate PatternDefinition and TileMapping classes.
/// </summary>
[CreateAssetMenu(fileName = "WFCTile", menuName = "WFC/Tile Definition", order = 1)]
public class WFCTileDefinition : ScriptableObject
{
    [Header("Tile Identity")]
    [Tooltip("Unique identifier for this tile")]
    public int id;
    
    [Tooltip("Human-readable name")]
    public string tileName;
    
    [Header("Tile Properties")]
    [Tooltip("Tags for grouping tiles")]
    public List<string> tags = new List<string>();
    
    [Tooltip("Is this tile walkable?")]
    public bool isWalkable = true;
    
    [Tooltip("Weight/probability of this tile appearing")]
    public float weight = 1.0f;
    
    [Header("Adjacency Rules")]
    [Tooltip("Rules defining which tiles can be adjacent")]
    public TileRules rules = new TileRules();
    
    [Header("Visual Variants")]
    [Tooltip("Visual variants of this tile with their weights")]
    public List<WeightedSprite> spriteVariants = new List<WeightedSprite>();
    
    /// <summary>
    /// Gets a random sprite based on weighted selection
    /// </summary>
    public Sprite GetRandomSprite()
    {
        if (spriteVariants == null || spriteVariants.Count == 0)
        {
            Debug.LogWarning($"No sprite variants defined for tile {id} ({tileName})");
            return null;
        }
        
        float totalWeight = 0f;
        foreach (var variant in spriteVariants)
        {
            if (variant.sprite != null)
            {
                totalWeight += variant.weight;
            }
        }
        
        if (totalWeight <= 0f)
        {
            Debug.LogWarning($"Total weight is 0 for tile {id} ({tileName})");
            return spriteVariants[0].sprite;
        }
        
        float randomValue = Random.Range(0f, totalWeight);
        float currentWeight = 0f;
        
        foreach (var variant in spriteVariants)
        {
            if (variant.sprite != null)
            {
                currentWeight += variant.weight;
                if (randomValue <= currentWeight)
                {
                    return variant.sprite;
                }
            }
        }
        
        return spriteVariants[0].sprite;
    }
    
    /// <summary>
    /// Validates that this tile definition is properly configured
    /// </summary>
    public bool IsValid()
    {
        if (spriteVariants == null || spriteVariants.Count == 0)
        {
            return false;
        }
        
        foreach (var variant in spriteVariants)
        {
            if (variant.sprite != null && variant.weight > 0)
            {
                return true;
            }
        }
        
        return false;
    }
    
    /// <summary>
    /// Converts this tile definition to JSON format for API requests
    /// </summary>
    public PatternData ToPatternData()
    {
        PatternData data = new PatternData
        {
            id = id,
            name = tileName,
            tags = tags.ToArray(),
            is_walkable = isWalkable ? 1 : 0,
            weight = weight,
            rules = rules.ToRulesData(),
            patterns = new PatternVariantData[spriteVariants.Count]
        };

        for (int i = 0; i < spriteVariants.Count; i++)
        {
            data.patterns[i] = spriteVariants[i].ToVariantData();
        }

        return data;
    }

    /// <summary>
    /// Loads tile definition from JSON pattern data
    /// </summary>
    public void LoadFromPatternData(PatternData data)
    {
        id = data.id;
        tileName = data.name;
        tags = new List<string>(data.tags);
        isWalkable = data.is_walkable == 1;
        weight = data.weight;
        rules.LoadFromRulesData(data.rules);
        
        spriteVariants.Clear();
        foreach (var variantData in data.patterns)
        {
            WeightedSprite variant = new WeightedSprite();
            variant.LoadFromVariantData(variantData);
            spriteVariants.Add(variant);
        }
    }
}

/// <summary>
/// Represents a weighted sprite variant for a tile.
/// Replaces both PatternVariant and SpriteVariant.
/// </summary>
[System.Serializable]
public class WeightedSprite
{
    [Tooltip("The sprite to use for this variant")]
    public Sprite sprite;
    
    [Tooltip("Path to the image file (for JSON serialization)")]
    public string imagePath;
    
    [Tooltip("Weight for random selection (higher = more likely)")]
    [Min(0.01f)]
    public float weight = 1f;

    public PatternVariantData ToVariantData()
    {
        return new PatternVariantData
        {
            image_path = imagePath,
            weight = weight
        };
    }

    public void LoadFromVariantData(PatternVariantData data)
    {
        imagePath = data.image_path;
        weight = data.weight;
    }
}

/// <summary>
/// Adjacency rules for a tile
/// </summary>
[System.Serializable]
public class TileRules
{
    [Tooltip("Allowed tiles above")]
    public List<RuleOption> up = new List<RuleOption>();
    
    [Tooltip("Allowed tiles below")]
    public List<RuleOption> down = new List<RuleOption>();
    
    [Tooltip("Allowed tiles to the left")]
    public List<RuleOption> left = new List<RuleOption>();
    
    [Tooltip("Allowed tiles to the right")]
    public List<RuleOption> right = new List<RuleOption>();

    public RulesData ToRulesData()
    {
        return new RulesData
        {
            up = RuleOption.ToStringArray(up),
            down = RuleOption.ToStringArray(down),
            left = RuleOption.ToStringArray(left),
            right = RuleOption.ToStringArray(right)
        };
    }

    public void LoadFromRulesData(RulesData data)
    {
        up = RuleOption.FromStringArray(data.up);
        down = RuleOption.FromStringArray(data.down);
        left = RuleOption.FromStringArray(data.left);
        right = RuleOption.FromStringArray(data.right);
    }
}

/// <summary>
/// Rule option that can reference either a tag or a specific tile ID
/// </summary>
[System.Serializable]
public class RuleOption
{
    [Tooltip("Is this a tag reference or tile ID?")]
    public bool isTag = true;
    
    [Tooltip("Tag name (if isTag is true)")]
    public string tagName = "";
    
    [Tooltip("Tile ID (if isTag is false)")]
    public int tileId = 0;

    public static string[] ToStringArray(List<RuleOption> options)
    {
        string[] result = new string[options.Count];
        for (int i = 0; i < options.Count; i++)
        {
            result[i] = options[i].isTag ? options[i].tagName : options[i].tileId.ToString();
        }
        return result;
    }

    public static List<RuleOption> FromStringArray(string[] array)
    {
        List<RuleOption> result = new List<RuleOption>();
        foreach (string item in array)
        {
            RuleOption option = new RuleOption();
            if (int.TryParse(item, out int id))
            {
                option.isTag = false;
                option.tileId = id;
            }
            else
            {
                option.isTag = true;
                option.tagName = item;
            }
            result.Add(option);
        }
        return result;
    }
}

// JSON serialization classes (shared between WFCConfig and TileDefinition)
[System.Serializable]
public class PatternData
{
    public int id;
    public string name;
    public string[] tags;
    public int is_walkable;
    public float weight;
    public RulesData rules;
    public PatternVariantData[] patterns;
}

[System.Serializable]
public class RulesData
{
    public string[] up;
    public string[] down;
    public string[] left;
    public string[] right;
}

[System.Serializable]
public class PatternVariantData
{
    public string image_path;
    public float weight;
}