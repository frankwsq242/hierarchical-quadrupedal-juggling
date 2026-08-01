# Artifact provenance

`sim_to_real/unitree_bringup/config/go1/pi2.onnx` is the 179,429-byte pi2 torso-tracking policy export copied from the source project's development branch. It has one 39-dimensional observation input and one 12-dimensional joint-action output. The source audit found no corresponding committed pi2 checkpoint, training run, or TensorBoard data at that branch tip, so this repository does not make an iteration, seed, or training-performance claim for it.

`videos/mujoco_mirror_paper_latest.mp4` is a 10-second, 640x480, 50 fps local MuJoCo capture from the same branch. It shows the analytic mirror-law controller together with pi2; it is not learned pi1 evidence.

The Go1 actuator network is deliberately not copied here. The source path was an external clone of [Walk These Ways](https://github.com/Improbable-AI/walk-these-ways), whose repository license is MIT. Obtain it from that project and pass its local `resources/actuator_nets/unitree_go1.pt` path through `--actuator-net` or `GO1_ACTUATOR_NET`.
