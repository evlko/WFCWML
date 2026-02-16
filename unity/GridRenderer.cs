using UnityEngine;
using System.Collections.Generic;

/// <summary>
/// Renders WFC grids by mapping tile IDs to sprites and creating GameObjects.
/// Handles both tile mapping and grid visualization.
/// </summary>
public class GridRenderer : MonoBehaviour
{
    [Header("Tile Source")]
    [Tooltip("WFC Config containing tile definitions")]
    public WFCConfig wfcConfig;
    
    [Tooltip("Default sprite when tile ID not found")]
    public Sprite defaultSprite;
    
    [Header("Grid Configuration")]
    [Tooltip("Size of each tile in world units")]
    public float tileSize = 1f;
    
    [Tooltip("Spacing between tiles")]
    public float tileSpacing = 0f;
    
    [Tooltip("Z-offset between layers (for depth sorting)")]
    public float layerZOffset = 0.1f;
    
    [Tooltip("Parent transform for all tile objects")]
    public Transform tilesParent;
    
    [Header("Rendering Options")]
    [Tooltip("Sorting layer name for tile sprites")]
    public string sortingLayerName = "Default";
    
    [Tooltip("Base sorting order for tiles")]
    public int baseSortingOrder = 0;
    
    private List<GameObject> _tileObjects = new List<GameObject>();
    private Dictionary<int, WFCTileDefinition> _tileCache;
    private bool _isInitialized = false;
    
    private void Awake()
    {
        if (tilesParent == null)
        {
            GameObject parent = new GameObject("Tiles");
            parent.transform.SetParent(transform);
            parent.transform.localPosition = Vector3.zero;
            tilesParent = parent.transform;
        }
    }
    
    /// <summary>
    /// Ensures the tile mapping is initialized before use.
    /// </summary>
    private void Initialize()
    {
        if (_isInitialized)
        {
            return;
        }
        
        if (wfcConfig == null)
        {
            Debug.LogError("GridRenderer: No WFCConfig assigned!");
            return;
        }
        
        if (wfcConfig.tiles == null || wfcConfig.tiles.Count == 0)
        {
            Debug.LogError("GridRenderer: WFCConfig has no tiles!");
            return;
        }
        
        BuildTileCache();
        _isInitialized = true;
        
        Debug.Log($"GridRenderer: Initialized with {_tileCache.Count} tiles from WFCConfig");
    }
    
    private void BuildTileCache()
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
                Debug.LogWarning("GridRenderer: Null tile in config");
                continue;
            }
            
            if (_tileCache.ContainsKey(tile.id))
            {
                Debug.LogWarning($"GridRenderer: Duplicate tile ID {tile.id}");
                continue;
            }
            
            _tileCache[tile.id] = tile;
        }
    }
    
    private Sprite GetSpriteForTile(int tileId)
    {
        if (!_isInitialized)
        {
            Debug.LogError("GridRenderer: Not initialized!");
            return defaultSprite;
        }
        
        if (_tileCache.TryGetValue(tileId, out WFCTileDefinition tile))
        {
            return tile.GetRandomSprite();
        }
        
        Debug.LogWarning($"GridRenderer: Tile ID {tileId} not found");
        return defaultSprite;
    }
    
    public void RenderGrid(int[][] grid, int layerIndex = 0)
    {
        if (grid == null || grid.Length == 0)
        {
            Debug.LogError("GridRenderer: Cannot render null or empty grid");
            return;
        }
        
        // Ensure initialized
        Initialize();
        
        if (!_isInitialized)
        {
            Debug.LogError("GridRenderer: Failed to initialize!");
            return;
        }
        
        int height = grid.Length;
        int width = grid[0].Length;
        
        float offsetX = -(width * (tileSize + tileSpacing)) / 2f + (tileSize / 2f);
        float offsetY = -(height * (tileSize + tileSpacing)) / 2f + (tileSize / 2f);
        float zPosition = -layerIndex * layerZOffset;
        
        for (int y = 0; y < height; y++)
        {
            for (int x = 0; x < width; x++)
            {
                int tileUid = grid[y][x];
                Vector3 position = new Vector3(
                    offsetX + x * (tileSize + tileSpacing),
                    offsetY + (height - 1 - y) * (tileSize + tileSpacing),
                    zPosition
                );
                
                CreateTile(tileUid, position, x, y, layerIndex);
            }
        }
    }
    
    public void RenderMultipleLayers(List<int[][]> grids)
    {
        if (grids == null || grids.Count == 0)
        {
            Debug.LogError("GridRenderer: Cannot render null or empty grid list");
            return;
        }
        
        ClearGrid();
        
        for (int i = 0; i < grids.Count; i++)
        {
            RenderGrid(grids[i], i);
        }
    }
    
    private void CreateTile(int tileUid, Vector3 position, int gridX, int gridY, int layer)
    {
        Sprite sprite = GetSpriteForTile(tileUid);
        
        if (sprite == null)
        {
            return;
        }
        
        GameObject tileObj = new GameObject($"Tile_{gridX}_{gridY}_L{layer}");
        tileObj.transform.SetParent(tilesParent);
        tileObj.transform.localPosition = position;
        tileObj.transform.localScale = Vector3.one * tileSize;
        
        SpriteRenderer spriteRenderer = tileObj.AddComponent<SpriteRenderer>();
        spriteRenderer.sprite = sprite;
        spriteRenderer.sortingLayerName = sortingLayerName;
        spriteRenderer.sortingOrder = baseSortingOrder + layer;
        
        _tileObjects.Add(tileObj);
    }
    
    [ContextMenu("Clear Grid")]
    public void ClearGrid()
    {
        // Clear tracked objects
        foreach (var tileObj in _tileObjects)
        {
            if (tileObj != null)
            {
                DestroyImmediate(tileObj);
            }
        }
        
        _tileObjects.Clear();
        
        // Also clear any remaining children of tilesParent
        // (in case objects were created but not tracked, or after stopping Play mode)
        if (tilesParent != null)
        {
            int childCount = tilesParent.childCount;
            for (int i = childCount - 1; i >= 0; i--)
            {
                DestroyImmediate(tilesParent.GetChild(i).gameObject);
            }
        }
    }
    
    [ContextMenu("Reinitialize")]
    public void Reinitialize()
    {
        _isInitialized = false;
        Initialize();
    }
    
    public Vector3 GetWorldPosition(int gridX, int gridY, int layer = 0)
    {
        float offsetX = -(gridX * (tileSize + tileSpacing)) / 2f + (tileSize / 2f);
        float offsetY = -(gridY * (tileSize + tileSpacing)) / 2f + (tileSize / 2f);
        float zPosition = -layer * layerZOffset;
        
        return new Vector3(
            offsetX + gridX * (tileSize + tileSpacing),
            offsetY + gridY * (tileSize + tileSpacing),
            zPosition
        );
    }
}