using UnityEngine;
using System.Collections.Generic;

/// <summary>
/// Repository for mapping tile IDs to their visual representations.
/// Can load tiles from WFCConfig or use manually assigned tile definitions.
/// </summary>
public class TileMappingRepository : MonoBehaviour
{
    [Header("Tile Source")]
    [Tooltip("WFC Config containing tile definitions")]
    public WFCConfig wfcConfig;
    
    [Header("Fallback")]
    [Tooltip("Default sprite when tile ID not found")]
    public Sprite defaultSprite;
    
    private Dictionary<int, WFCTileDefinition> _tileCache;
    private bool _isInitialized = false;
    
    /// <summary>
    /// Ensures the repository is initialized before use.
    /// Call this before rendering or accessing tiles.
    /// </summary>
    public void Initialize()
    {
        if (_isInitialized)
        {
            return;
        }
        
        if (wfcConfig == null)
        {
            Debug.LogError("TileMappingRepository: No WFCConfig assigned!");
            return;
        }
        
        if (wfcConfig.tiles == null || wfcConfig.tiles.Count == 0)
        {
            Debug.LogError("TileMappingRepository: WFCConfig has no tiles!");
            return;
        }
        
        BuildCache();
        _isInitialized = true;
        
        Debug.Log($"TileMappingRepository: Initialized with {_tileCache.Count} tiles from WFCConfig");
    }
    
    private void BuildCache()
    {
        _tileCache = new Dictionary<int, WFCTileDefinition>();
        
        if (wfcConfig == null || wfcConfig.tiles == null)
        {
            return;
        }
        
        foreach (var tile in wfcConfig.tiles)
        {
            if (tile == null)
            {
                Debug.LogWarning("TileMappingRepository: Null tile in config");
                continue;
            }
            
            if (_tileCache.ContainsKey(tile.id))
            {
                Debug.LogWarning($"TileMappingRepository: Duplicate tile ID {tile.id}");
                continue;
            }
            
            _tileCache[tile.id] = tile;
        }
    }
    
    public Sprite GetSpriteForTile(int tileId)
    {
        if (!_isInitialized)
        {
            Debug.LogError("TileMappingRepository: Not initialized! Call Initialize() first.");
            return defaultSprite;
        }
        
        if (_tileCache.TryGetValue(tileId, out WFCTileDefinition tile))
        {
            return tile.GetRandomSprite();
        }
        
        Debug.LogWarning($"TileMappingRepository: Tile ID {tileId} not found");
        return defaultSprite;
    }
    
    [ContextMenu("Initialize Repository")]
    public void InitializeFromEditor()
    {
        _isInitialized = false;
        Initialize();
    }
}