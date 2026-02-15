using UnityEngine;
using System.Collections.Generic;

public class TileMappingRepository : MonoBehaviour
{
    [Header("Tile Mappings")]
    [Tooltip("List of all tile mappings. Each mapping defines sprites for a specific tile UID.")]
    public List<TileMapping> tileMappings = new List<TileMapping>();
    
    [Header("Fallback")]
    [Tooltip("Default sprite to use when a tile UID is not found")]
    public Sprite defaultSprite;
    
    private Dictionary<int, TileMapping> _mappingCache;
    
    private void Awake()
    {
        BuildCache();
    }
    
    private void BuildCache()
    {
        _mappingCache = new Dictionary<int, TileMapping>();
        
        if (tileMappings == null)
        {
            Debug.LogWarning("TileMappingRepository: No tile mappings assigned!");
            return;
        }
        
        foreach (var mapping in tileMappings)
        {
            if (mapping == null)
            {
                Debug.LogWarning("TileMappingRepository: Null mapping found in list!");
                continue;
            }
            
            if (!mapping.IsValid())
            {
                Debug.LogWarning($"TileMappingRepository: Invalid mapping for UID {mapping.tileUid}");
                continue;
            }
            
            if (_mappingCache.ContainsKey(mapping.tileUid))
            {
                Debug.LogWarning($"TileMappingRepository: Duplicate mapping for UID {mapping.tileUid}. Using first occurrence.");
                continue;
            }
            
            _mappingCache[mapping.tileUid] = mapping;
        }
        
        Debug.Log($"TileMappingRepository: Cached {_mappingCache.Count} tile mappings");
    }
    
    public Sprite GetSpriteForTile(int tileUid)
    {
        if (_mappingCache == null)
        {
            BuildCache();
        }
        
        if (_mappingCache.TryGetValue(tileUid, out TileMapping mapping))
        {
            Sprite sprite = mapping.GetRandomSprite();
            if (sprite != null)
            {
                return sprite;
            }
        }
        
        if (defaultSprite != null)
        {
            Debug.LogWarning($"TileMappingRepository: No mapping found for UID {tileUid}, using default sprite");
            return defaultSprite;
        }
        
        Debug.LogError($"TileMappingRepository: No mapping found for UID {tileUid} and no default sprite set!");
        return null;
    }
    
    public TileMapping GetMapping(int tileUid)
    {
        if (_mappingCache == null)
        {
            BuildCache();
        }
        
        _mappingCache.TryGetValue(tileUid, out TileMapping mapping);
        return mapping;
    }
    
    public bool HasMapping(int tileUid)
    {
        if (_mappingCache == null)
        {
            BuildCache();
        }
        
        return _mappingCache.ContainsKey(tileUid);
    }
    
    [ContextMenu("Rebuild Cache")]
    public void RebuildCache()
    {
        BuildCache();
    }
    
    [ContextMenu("Validate Mappings")]
    public void ValidateMappings()
    {
        if (tileMappings == null || tileMappings.Count == 0)
        {
            Debug.LogError("TileMappingRepository: No tile mappings assigned!");
            return;
        }
        
        int validCount = 0;
        int invalidCount = 0;
        HashSet<int> seenUids = new HashSet<int>();
        
        foreach (var mapping in tileMappings)
        {
            if (mapping == null)
            {
                invalidCount++;
                Debug.LogError("TileMappingRepository: Null mapping in list");
                continue;
            }
            
            if (seenUids.Contains(mapping.tileUid))
            {
                invalidCount++;
                Debug.LogError($"TileMappingRepository: Duplicate UID {mapping.tileUid}");
                continue;
            }
            
            seenUids.Add(mapping.tileUid);
            
            if (mapping.IsValid())
            {
                validCount++;
                Debug.Log($"✓ UID {mapping.tileUid} ({mapping.tileName}): {mapping.spriteVariants.Count} variants");
            }
            else
            {
                invalidCount++;
                Debug.LogError($"✗ UID {mapping.tileUid} ({mapping.tileName}): Invalid configuration");
            }
        }
        
        Debug.Log($"Validation complete: {validCount} valid, {invalidCount} invalid");
        
        if (defaultSprite == null)
        {
            Debug.LogWarning("TileMappingRepository: No default sprite set!");
        }
    }
}