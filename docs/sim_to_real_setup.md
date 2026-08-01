# Sim-to-real deployment findings

This note preserves the public engineering findings from the deployment investigation. It intentionally omits robot addresses, account names, credentials, and lab-network instructions.

## Pi2 ONNX export

`scripts/tests/export_pi2_onnx.py` rebuilds a pi2 actor from a supplied RSL-RL checkpoint, exports it to ONNX, then compares five random PyTorch and ONNX evaluations. The committed export is `sim_to_real/unitree_bringup/config/go1/pi2.onnx`.

Pi2 has a 39-dimensional observation input and 12-dimensional joint-position-residual output:

- command: six normalized torso-command values;
- robot state: base linear velocity, angular velocity, projected gravity, joint-position residuals, and joint velocities;
- output: 12 joint residuals, scaled by 0.25 and added to the default pose.

## Controller-interface finding

The investigated Unitree deployment controller consumes a 3D velocity command. Pi1 produces a 6D torso command, so the stock controller cannot directly run the pi1-to-pi2 hierarchy. The viable follow-up paths identified were a controller adapter, a standalone ROS node that runs both policies, or export of a combined policy.

No hardware rollout is included or claimed in this repository.
