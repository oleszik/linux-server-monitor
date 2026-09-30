# Portfolio Screenshot Guide

Take screenshots from the real application after installing it with `pip install -e ".[dev]"`. Do not screenshot the committed text files as a substitute for a live terminal run.

Before every capture, check the terminal prompt, title bar, and output for your username, hostname, home path, IP addresses, device/interface IDs, process names, tokens, or other private data. Crop or redact private details before publishing. Metrics will naturally differ from the committed snapshot.

## 1. Main status overview

```bash
python -m server_monitor --config examples/showcase/config.yaml status
```

Use a terminal about 100 columns wide and 32–40 rows tall. Show the command plus the System, CPU, Memory, and Disk sections; include Network only after reviewing every interface and address.

## 2. Health decision logic

```bash
python -m server_monitor --config examples/showcase/config-warning-demo.yaml health
```

Use a terminal about 100 columns wide and 12–16 rows tall. Show the command, `Health: WARNING`, the CPU threshold comparison, and the remaining `OK` findings. Mention in the screenshot caption that the warning threshold is intentionally lowered for demonstration.

## 3. Service inspection

```bash
python -m server_monitor --config examples/showcase/config.yaml services
```

Use a terminal about 90 columns wide and 10–12 rows tall. Show the command and service states. Confirm that the listed service names are safe to disclose; if either service is absent on the screenshot host, customize a local copy of the configuration rather than editing the committed evidence.

As an alternative third image, use `python -m server_monitor processes --sort memory --limit 5`, but inspect process names, PIDs, and the shell prompt carefully before publishing.
