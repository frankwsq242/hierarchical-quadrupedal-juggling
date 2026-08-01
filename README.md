# Hierarchical Quadrupedal Juggling

A Unitree Go1 bounces a 40 mm ping-pong ball on a 170 mm paddle mounted to its back,
under velocity, yaw, and apex-height commands. Trained in Isaac Lab, transferred to
MuJoCo.

![Go1 juggling in MuJoCo](docs/figures/mujoco_demo.gif)

*Mirror-law planner driving a trained torso-tracking policy during a six-second MuJoCo forward-walk-and-juggle segment.*

---

## Approach

The controller is split into two layers with a 6-DOF torso command as the interface.

![Hierarchical architecture](docs/figures/architecture.png)

**π₂ — learned torso tracker.** A PPO policy mapping a 6D torso command (height,
height rate, roll, pitch, roll rate, pitch rate) to 12 joint targets. Trained once in
Isaac Lab, then frozen and reused across every task below. Observations are joint
position and velocity, base state, last action, and the torso command; the actor is
`[256, 128, 64]`.

![Four Go1 environments in Isaac Lab](docs/figures/isaaclab_demo.gif)

*Six-second crop from 31-37 s of the Isaac Lab recording. The editor and interface
areas are removed; this shows only the four-robot simulation viewport.*

**π₁ — planner.** Two interchangeable implementations on top of the same frozen π₂:

- *Mirror law* — an analytic controller that reflects the ball's incoming velocity
  about the paddle normal and adjusts mechanical energy to hit a target apex.
  Physically interpretable, no training, and the basis for the demo above.
- *Learned planner* — a PPO policy over ball and robot state, rewarding target apex
  height and successful bounces. Implemented and trainable; see
  [Limitations](#limitations) for its status.

![Mirror-law planner](docs/figures/mirror_law_planner.png)

Decoupling the layers means the planner can be swapped without retraining locomotion,
and the analytic and learned planners are directly comparable on identical dynamics.

## Sim-to-sim transfer

Getting π₂ to behave in MuJoCo was the bulk of the engineering. Full record in
[`docs/sim_to_sim_debug_log.md`](docs/sim_to_sim_debug_log.md).

**Method.** Fixed-base joint step-response comparison isolates actuator and PD
differences from policy differences. Golden-case tests pin the actor itself:
recorded observation/action pairs must reproduce across both runtimes, which they do
to ~5e-6, so any remaining divergence is attributable to physics rather than to
deserialization.

![Joint step response](docs/figures/sim_to_sim.png)

**The reindex bug.** Isaac Lab and MJCF order the 12 joints differently. The mapping
was applied as a gather where it needed to be a scatter — `isaac[reindex] = mjcf`,
not `isaac = mjcf[reindex]`. The symptom was subtle: the robot stood, then drifted.
A default-pose observation was off by up to 2.5 rad on individual joints, which the
policy partially compensated for, which is exactly what made it hard to see.

**What transfer required.** π₂ does not drop into MuJoCo unchanged. Action magnitude
is scaled to 20%, torso commands are clamped, and roll/pitch-rate commands are zeroed.
These compensate for actuator-model and contact differences between the two engines
and are documented rather than tuned away.

## Perception

An egocentric ball tracker for hardware: HSV detection in OpenCV, depth
back-projection to 3D position, and an extended Kalman filter for velocity. ROS 1 and
ROS 2 nodes in [`testing_codes/perception/`](testing_codes/perception/).

## Deployment

π₂ exports to ONNX (39D observation, 12D action) and runs standalone. The blocking
finding for hardware: the stock Unitree controller accepts a 3D velocity command, not
this policy's 6D torso command, so deploying the hierarchy requires either a command
adapter or a combined model. Notes in
[`docs/sim_to_real_setup.md`](docs/sim_to_real_setup.md).

## Run the MuJoCo demo

```bash
python3.11 -m venv .venv && . .venv/bin/activate
pip install -r requirements.txt

# actuator network, MIT-licensed, not vendored
git clone https://github.com/Improbable-AI/walk-these-ways.git ../walk-these-ways
export GO1_ACTUATOR_NET="$PWD/../walk-these-ways/resources/actuator_nets/unitree_go1.pt"

python scripts/play_mujoco_mirror_paper.py --headless --max_steps 20
```

Uses the committed `pi2.onnx`. Add `--video --video_length 500` to record.

Isaac Lab training (`scripts/rsl_rl/`) additionally requires Isaac Lab 2.3.2 /
Isaac Sim 5.1, an NVIDIA GPU, and `rsl-rl-lib==3.0.1` — see
[`requirements-isaaclab.txt`](requirements-isaaclab.txt). Individual scripts state
their additional environment and checkpoint requirements at the top of each file.

## Limitations

- **The learned π₁ is not reproducible from this repository.** The task, rewards, and
  training entrypoint are here; a converged checkpoint is not. Results shown use the
  mirror-law planner.
- **MuJoCo transfer is tuned**, per the compensations described above.
- **π₂ tracking is imperfect** — height tracking stays within 5% error over roughly
  the middle third of the commanded range and degrades at the extremes. Sweep and
  trace plots are committed at [`videos/pi2/eval_pi2_sweep.png`](videos/pi2/eval_pi2_sweep.png)
  and [`videos/pi2/pi2_tracking.png`](videos/pi2/pi2_tracking.png).
- **No vision-based policy.** The perception stack runs standalone; it is not wired
  into a trained policy's observations.
- **No hardware rollout**, for the command-interface reason above.
- **No domain randomization** beyond spawn and target variation.

## Report

[`QuadruJuggle_Research_Overview.pdf`](QuadruJuggle_Research_Overview.pdf) — February
2026 status report, partly superseded by the transfer and deployment work above.

## Attribution

Joint project with [Daniel Grant](https://github.com/DJRGVC) and Jaime de Carlos,
Hybrid Robotics Lab, UC Berkeley, advised by Prof. Koushil Sreenath. Original
repository: [QuadruJuggle](https://github.com/DJRGVC/QuadruJuggle).

Daniel wrote most of the Isaac Lab task and environment definitions. My work: the
π₁–π₂ hierarchical controller, training and exporting the π₂ torso-tracking policy,
the Isaac Lab → MuJoCo transfer and cross-simulator validation, the perception
prototype, and the deployment investigation.
