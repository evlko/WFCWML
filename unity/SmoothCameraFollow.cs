using UnityEngine;

public class SmoothCameraFollow : MonoBehaviour
{
    [Header("Target Settings")]
    [SerializeField] private Transform target;
    [SerializeField] private Vector3 offset = new Vector3(0f, 0f, -10f);

    [Header("Follow Settings")]
    [SerializeField] private float smoothSpeed = 5f;
    [SerializeField] private bool useFixedUpdate = false;

    [Header("Bounds (Optional)")]
    [SerializeField] private bool useBounds = false;
    [SerializeField] private Vector2 minBounds = new Vector2(-10f, -10f);
    [SerializeField] private Vector2 maxBounds = new Vector2(10f, 10f);

    [Header("Look Ahead")]
    [SerializeField] private bool useLookAhead = false;
    [SerializeField] private float lookAheadDistance = 2f;
    [SerializeField] private float lookAheadSpeed = 2f;

    private Vector3 velocity = Vector3.zero;
    private Vector3 lookAheadOffset = Vector3.zero;

    private void LateUpdate()
    {
        if (!useFixedUpdate) FollowTarget();
    }

    private void FixedUpdate()
    {
        if (useFixedUpdate) FollowTarget();
    }

    private void FollowTarget()
    {
        if (target == null) return;

        if (useLookAhead)
        {
            PlayerController player = target.GetComponent<PlayerController>();
            if (player != null)
            {
                Vector2 moveDir = player.GetMoveDirection();
                Vector3 targetLookAhead = new Vector3(moveDir.x, moveDir.y, 0f) * lookAheadDistance;
                lookAheadOffset = Vector3.Lerp(lookAheadOffset, targetLookAhead, lookAheadSpeed * Time.deltaTime);
            }
        }

        Vector3 desiredPosition = target.position + offset + lookAheadOffset;

        if (useBounds)
        {
            desiredPosition.x = Mathf.Clamp(desiredPosition.x, minBounds.x, maxBounds.x);
            desiredPosition.y = Mathf.Clamp(desiredPosition.y, minBounds.y, maxBounds.y);
        }

        Vector3 smoothedPosition = Vector3.SmoothDamp(transform.position, desiredPosition, ref velocity, 1f / smoothSpeed);
        transform.position = smoothedPosition;
    }

    public void SetTarget(Transform newTarget) => target = newTarget;

    public void SnapToTarget()
    {
        if (target != null)
        {
            transform.position = target.position + offset;
            velocity = Vector3.zero;
            lookAheadOffset = Vector3.zero;
        }
    }

    private void OnDrawGizmosSelected()
    {
        if (useBounds)
        {
            Gizmos.color = Color.yellow;
            Vector3 center = new Vector3((minBounds.x + maxBounds.x) / 2f, (minBounds.y + maxBounds.y) / 2f, 0f);
            Vector3 size = new Vector3(maxBounds.x - minBounds.x, maxBounds.y - minBounds.y, 0f);
            Gizmos.DrawWireCube(center, size);
        }

        if (target != null)
        {
            Gizmos.color = Color.cyan;
            Gizmos.DrawLine(target.position, target.position + offset);
        }
    }
}