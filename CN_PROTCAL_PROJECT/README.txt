NETPULSE -  source files

Files:
- main.py: Tkinter GUI and dashboard. Fixed protocol window-size reset and delivered-frame denominator.
- protocols.py: ARQ simulation logic. Fixed Go-Back-N retry-limit behavior so a fully lost connection cannot schedule an endless timeout loop.
- visualization.py: Event animation window, based on the provided version.

Run on Windows:
1. Keep all three .py files in the same folder.
2. Install Matplotlib if needed: py -m pip install matplotlib
3. Run: py main.py

Syntax checks passed for all three files.
Protocol smoke tests passed for all three protocols with no loss, 100% packet loss, 100% ACK loss, and a seeded 10% packet / 5% ACK loss case.
The Tkinter window itself was not visually launched in this headless test environment.
