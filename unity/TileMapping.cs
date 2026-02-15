using UnityEngine;
using System.Collections.Generic;

[CreateAssetMenu(fileName = "TileMapping", menuName = "WFC/Tile Mapping", order = 1)]
public class TileMapping : ScriptableObject
{
    [Header("Tile Configuration")]
    [Tooltip("Unique identifier for this tile type (matches the UID from the API)")]
    public int tileUid;
    
    [Tooltip("Human-readable name for this tile")]
    public string tileName;
    
    [Tooltip("List of sprite variants with their selection weights")]
    public List<SpriteVariant> spriteVariants = new List<SpriteVariant>();
    
    public Sprite GetRandomSprite()
    {
        if (spriteVariants == null || spriteVariants.Count == 0)
        {
            Debug.LogWarning($"No sprite variants defined for tile UID {tileUid}");
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
            Debug.LogWarning($"Total weight is 0 for tile UID {tileUid}");
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
}

[System.Serializable]
public class SpriteVariant
{
    [Tooltip("The sprite to use for this variant")]
    public Sprite sprite;
    
    [Tooltip("Weight for random selection (higher = more likely)")]
    [Min(0.01f)]
    public float weight = 1f;
}