using UnityEngine;
using System.Collections.Generic;

public class GridRenderer : MonoBehaviour
{
    [Header("References")]
    [Tooltip("Repository containing tile mappings")]
    public TileMappingRepository tileMappingRepository;
    
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
    
    [Header("Debug")]
    [Tooltip("Show debug information")]
    public bool showDebugInfo = false;
    
    private List<GameObject> _tileObjects = new List<GameObject>();
    private int[,] _currentGrid;
    
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
    
    public void RenderGrid(int[][] grid, int layerIndex = 0)
    {
        if (grid == null || grid.Length == 0)
        {
            Debug.LogError("GridRenderer: Cannot render null or empty grid");
            return;
        }
        
        if (tileMappingRepository == null)
        {
            Debug.LogError("GridRenderer: TileMappingRepository not assigned!");
            return;
        }
        
        // Ensure repository is initialized
        tileMappingRepository.Initialize();
        
        int height = grid.Length;
        int width = grid[0].Length;
        
        if (showDebugInfo)
        {
            Debug.Log($"GridRenderer: Rendering grid {width}x{height} at layer {layerIndex}");
        }
        
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
        Sprite sprite = tileMappingRepository.GetSpriteForTile(tileUid);
        
        if (sprite == null)
        {
            if (showDebugInfo)
            {
                Debug.LogWarning($"GridRenderer: No sprite for UID {tileUid} at ({gridX}, {gridY})");
            }
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
        foreach (var tileObj in _tileObjects)
        {
            if (tileObj != null)
            {
                DestroyImmediate(tileObj);
            }
        }
        
        _tileObjects.Clear();
        
        if (showDebugInfo)
        {
            Debug.Log("GridRenderer: Grid cleared");
        }
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