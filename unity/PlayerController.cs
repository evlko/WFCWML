using UnityEngine;
using UnityEngine.InputSystem;

[RequireComponent(typeof(Rigidbody2D))]
public class PlayerController : MonoBehaviour
{
    [Header("Movement Settings")]
    [SerializeField] private float moveSpeed = 5f;
    [SerializeField] private float acceleration = 10f;
    [SerializeField] private float deceleration = 10f;

    [Header("Visual Settings")]
    [SerializeField] private SpriteRenderer spriteRenderer;
    [SerializeField] private float rotationSpeed = 10f;
    [SerializeField] private float scaleAmount = 0.1f;
    [SerializeField] private float scaleSpeed = 8f;

    private Rigidbody2D rb;
    private Vector2 moveInput;
    private Vector2 currentVelocity;
    private Vector3 baseScale;
    private float targetRotation;
    private float currentRotation;

    private void Awake()
    {
        rb = GetComponent<Rigidbody2D>();
        rb.gravityScale = 0f;
        rb.constraints = RigidbodyConstraints2D.FreezeRotation;

        if (spriteRenderer == null)
            spriteRenderer = GetComponent<SpriteRenderer>();

        if (spriteRenderer != null)
            baseScale = spriteRenderer.transform.localScale;
    }

    private void Update()
    {
        HandleInput();
        UpdateVisuals();
    }

    private void HandleInput()
    {
        Keyboard keyboard = Keyboard.current;
        if (keyboard != null)
        {
            Vector2 rawInput = Vector2.zero;
            
            if (keyboard.wKey.isPressed || keyboard.upArrowKey.isPressed)
                rawInput.y += 1f;
            if (keyboard.sKey.isPressed || keyboard.downArrowKey.isPressed)
                rawInput.y -= 1f;
            if (keyboard.aKey.isPressed || keyboard.leftArrowKey.isPressed)
                rawInput.x -= 1f;
            if (keyboard.dKey.isPressed || keyboard.rightArrowKey.isPressed)
                rawInput.x += 1f;

            if (Mathf.Abs(rawInput.x) > 0.1f && Mathf.Abs(rawInput.y) > 0.1f)
            {
                moveInput = rawInput.x != 0 ? new Vector2(rawInput.x, 0f) : new Vector2(0f, rawInput.y);
            }
            else
            {
                moveInput = rawInput;
            }
        }
    }

    private void UpdateVisuals()
    {
        if (spriteRenderer == null) return;

        if (moveInput.x < -0.1f)
            spriteRenderer.flipX = true;
        else if (moveInput.x > 0.1f)
            spriteRenderer.flipX = false;

        bool isMoving = moveInput.magnitude > 0.1f;
        
        if (isMoving)
        {
            targetRotation = Mathf.Sin(Time.time * rotationSpeed) * 5f;
            float targetScaleMultiplier = 1f + Mathf.Abs(Mathf.Sin(Time.time * scaleSpeed)) * scaleAmount;
            spriteRenderer.transform.localScale = Vector3.Lerp(
                spriteRenderer.transform.localScale,
                baseScale * targetScaleMultiplier,
                Time.deltaTime * scaleSpeed
            );
        }
        else
        {
            targetRotation = 0f;
            spriteRenderer.transform.localScale = Vector3.Lerp(
                spriteRenderer.transform.localScale,
                baseScale,
                Time.deltaTime * scaleSpeed
            );
        }

        currentRotation = Mathf.Lerp(currentRotation, targetRotation, Time.deltaTime * rotationSpeed);
        spriteRenderer.transform.rotation = Quaternion.Euler(0f, 0f, currentRotation);
    }

    private void FixedUpdate()
    {
        Vector2 targetVelocity = moveInput.normalized * moveSpeed;
        float lerpSpeed = moveInput.magnitude > 0.1f ? acceleration : deceleration;
        currentVelocity = Vector2.Lerp(currentVelocity, targetVelocity, lerpSpeed * Time.fixedDeltaTime);
        rb.velocity = currentVelocity;
    }

    public Vector2 GetMoveDirection() => moveInput;
    public bool IsMoving() => currentVelocity.magnitude > 0.1f;
}