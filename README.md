Isaac Lab to MuJoCo transfer and full engineering record for a Go1 that balances and bounces a ping-pong ball on a back-mounted paddle.

<video controls muted playsinline src="videos/mujoco_mirror_paper_latest.mp4">
  <a href="videos/mujoco_mirror_paper_latest.mp4">Watch the 10-second MuJoCo demonstration.</a>
</video>

The video shows the verified analytic mirror-law controller plus a trained pi2 torso-tracking policy in MuJoCo. It is not evidence of a learned pi1 policy.

## What was built

This section records implementation scope. It does not imply that every component has a reproducible trained result in this repository.

### Isaac Lab tasks and policies

- **`ball_balance`** is an Isaac Lab ball-on-paddle task with alive, Gaussian ball-centering, lateral-velocity, trunk-tilt, body-motion, action-rate, torque, high-base, and foot-contact reward terms. It has ball-loss/height termination conditions, a curriculum, a 12,288-environment scene, and PPO configured with 24 rollout steps per environment and 10,000 maximum iterations. See [environment config](source/go1_ball_balance/go1_ball_balance/tasks/ball_balance/ball_balance_env_cfg.py), [reward terms](source/go1_ball_balance/go1_ball_balance/tasks/ball_balance/mdp/rewards.py), and [PPO config](source/go1_ball_balance/go1_ball_balance/tasks/ball_balance/agents/rsl_rl_ppo_cfg.py).

- **`torso_tracking` / pi2** is a 6D torso-command to 12D joint-target policy: height, height velocity, roll, pitch, roll rate, and pitch rate are tracked by a PPO actor. The task, command term, Kalman filter, and PPO configuration are in [the task directory](source/go1_ball_balance/go1_ball_balance/tasks/torso_tracking/). The pi2 model is exportable and runnable; its committed ONNX export drives the smoke test below.

- **`ball_juggle_hier`** implements the pi1-to-pi2 hierarchy. The learned pi1 produces a 6D torso command over a frozen pi2; its rewards include target apex height, bouncing, ball XY error, tilt, contact, and regularization. The task also contains an analytic mirror-law variant and launcher configuration. See [the hierarchy](source/go1_ball_balance/go1_ball_balance/tasks/ball_juggle_hier/), with [flat ball-juggle MDP support](source/go1_ball_balance/go1_ball_balance/tasks/ball_juggle/). The implementation exists; a reproducible trained pi1 result does not.

### Perception and deployment

- **Perception** contains ROS 1 and ROS 2 ball-perception prototypes with HSV detection, depth back-projection, Kalman filtering, and position/velocity publication. See [the perception directory](testing_codes/perception/). Its launch file retains mount-transform placeholders, so this is prototype code rather than a verified end-to-end camera policy.

- **Sim-to-real deployment** includes the pi2 ONNX export utility and deployment investigation. The key finding was that the stock Unitree controller accepts a 3D velocity command, not this policy's required 6D torso command, so it cannot directly deploy pi1-to-pi2 without an adapter or combined model. See [public deployment notes](docs/sim_to_real_setup.md) and [the export utility](scripts/tests/export_pi2_onnx.py).

### Sim-to-sim transfer

The transfer work includes a MuJoCo Go1 scene, learned-pi1/pi2 and analytic mirror-law runners, runtime joint-order conversion, pi2 isolation tests, and a fixed-base cross-simulator joint comparison. The debugging record is [here](docs/sim_to_sim_debug_log.md).

## What is verified here

- **Pi2 torso tracking:** `sim_to_real/unitree_bringup/config/go1/pi2.onnx` is a committed 39D-to-12D policy export. `scripts/play_mujoco_mirror_paper.py --headless --max_steps 20` loads it and executes the bounded MuJoCo smoke test.

- **Tuned MuJoCo transfer:** [the committed MP4](videos/mujoco_mirror_paper_latest.mp4) shows the analytic mirror law plus pi2 bouncing the ball in MuJoCo. This is not a drop-in transfer: pi2 action magnitude is scaled to 20%, torso commands are clamped, and roll/pitch-rate commands are zeroed. Those compensations are documented findings from the transfer work.

- **Cross-simulator consistency:** [the golden cases](tests_out/pi2_golden.csv) record actor observations/actions that the debugging record reports reproduced to about `5e-6`. The record also traces the reversed joint-reindex failure: the incorrect gather made a default-pose observation look up to 2.5 rad wrong; the correction is the scatter form `isaac[reindex] = mjcf` in [the runtime mapping helper](scripts/mujoco_utils.py).

Not verified here: learned pi1, a vision student, domain randomization, a hardware rollout, or balance under locomotion. There is no pi1 checkpoint, pi1 training log, or successful learned-pi1 video in this repository.

## Diagnostic artifacts

These are committed diagnostics, not polished performance claims.

![Isaac Lab pi2 tracking](videos/pi2_tracking_isaaclab.png)

Isaac Lab pi2 command-versus-actual traces: pitch follows reasonably, while height remains oscillatory and below the command.

![MuJoCo pi2 tracking](videos/pi2_tracking_mujoco.png)

MuJoCo pi2 tracking: pitch often follows, but height oscillates and roll has large excursions.

![Pi2 sweep](videos/pi2/eval_pi2_sweep.png)

The pi2 command sweep shows that only portions of the tested command range stay below the plotted 5% error threshold.

![Pi2 EMA tracking](videos/pi2/pi2_tracking.png)

Before/after EMA traces against actual torso state show residual mismatch and late instability.

![Mirror-law joint diagnostics](videos/mirror_law/joint_diag.png)

Twelve-joint desired/actual/error/torque diagnostics show persistent tracking error rather than a clean joint-level match.

![Hybrid ball trajectory](videos/hybrid/hybrid_ball_traj.png)

The hybrid trajectory misses its 0.30 m apex target: most peaks are roughly 0.05-0.15 m and the ball drops below the paddle.

![Hybrid torso command](videos/hybrid/hybrid_torso_cmd.png)

Hybrid desired-versus-actual torso channels show noise, saturation, and mismatch.

![Hybrid initial trajectory](videos/hybrid/hybrid_first5s.png)

Despite its filename, this plot covers roughly 10 seconds; ball height decays and resets near 9 seconds.

![Isaac Lab ball trace](videos/isaaclab_first5s.png)

This five-second Isaac Lab ball-position and command trace includes resets. It is a debugging trace, not a successful episode capture.

## February 2026 report

[QuadruJuggle_Research_Overview.pdf](QuadruJuggle_Research_Overview.pdf) is the authoritative February 2026 project report included in this repository. It is a status report, not a final result paper: its training metrics were not independently reproduced from committed current artifacts, and its conclusions are partly superseded by the later pi2, transfer, and deployment work above. The duplicate assistant-area PDF is intentionally not included.

## Reproduce the MuJoCo smoke test

The clean-clone MuJoCo path uses Python 3.11 and the pinned dependencies in `requirements.txt`: MuJoCo 3.3.0, NumPy 1.26.4, ONNX Runtime 1.20.1, PyTorch 2.5.1, ImageIO, and Matplotlib.

```bash
git clone <your-fork-or-clone-url> isaaclab-mujoco-transfer
cd isaaclab-mujoco-transfer
python3.11 -m venv .venv
. .venv/bin/activate
pip install -r requirements.txt

git clone https://github.com/Improbable-AI/walk-these-ways.git ../walk-these-ways
export GO1_ACTUATOR_NET="$PWD/../walk-these-ways/resources/actuator_nets/unitree_go1.pt"

python scripts/play_mujoco_mirror_paper.py --headless --max_steps 20
```

The command loads the committed pi2 ONNX model, loads the separately obtained actuator network, initializes MuJoCo, and executes 20 policy steps. To capture a longer run, add `--video --video_length 500`; this overwrites the MP4 above. The actuator model is not vendored; it comes from the MIT-licensed [Walk These Ways](https://github.com/Improbable-AI/walk-these-ways) project, and the runner fails with an actionable error if it is absent. See [artifact provenance](ARTIFACTS.md).

### Additional executable requirements

- `scripts/rsl_rl/train_torso_tracking.py` and `scripts/rsl_rl/train_pi1.py` require Isaac Lab 2.3.2 / Isaac Sim 5.1.0, Python 3.11, an NVIDIA GPU, the local task package, and `rsl-rl-lib==3.0.1`; use [requirements-isaaclab.txt](requirements-isaaclab.txt). Pi1 additionally requires a user-supplied frozen pi2 checkpoint. Neither training workflow is claimed as a fresh-clone result.
- `scripts/tests/compare_joint.py` and `scripts/tests/test_pi2_isaaclab.py` require the same Isaac Lab environment. The latter also needs a compatible pi2 PyTorch checkpoint, which is not included. Both files state this at their top level.
- `scripts/tests/export_pi2_onnx.py` requires a user-supplied pi2 PyTorch checkpoint and exports/compares an ONNX model; its `--checkpoint` argument is intentionally required.
- `scripts/test_pi2_mujoco.py` uses the committed ONNX pi2 model and the same external actuator network as the smoke test.
- `scripts/play_mujoco.py` retains the learned-pi1 runner for inspection. It requires explicit pi1 and pi2 PyTorch checkpoints that are not included because the learned-pi1 result is not verified here.
- `testing_codes/perception/` requires ROS and a compatible depth camera. Its own [setup notes](testing_codes/perception/requirements.txt) list the runtime packages and explicitly require physical camera extrinsics before use.

## Attribution

Joint project with [Daniel Grant](https://github.com/DJRGVC) — original repository: [QuadruJuggle](https://github.com/DJRGVC/QuadruJuggle). Daniel led the initial Isaac Lab environment implementation. The MuJoCo transfer, cross-simulator validation, perception prototype, and deployment work are mine.
