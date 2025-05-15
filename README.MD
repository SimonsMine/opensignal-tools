# Opensensor tools

Script(s) for dealing with opensensor data.


## Requirements

- [python 3.13+](https://www.python.org/downloads/)
- Open a command terminal in this project folder and type
  `pip install pyproject.toml` to install the required dependencies.


## Usage

This section describes how to use the opensensor script(s).


### Read data script

Note this script currently only supports one sensor recorded in a single file
and has only been tested with the breath sensor. There is demo data available in
the demo folder, you can provide your own recorded data as well, see options.
- Open a command terminal in this project folder and type
  `python send_recorded_data_to_osc.py` this will print out and send recorded
  opensensor data over osc.
- For all available options, open a command terminal in this project folder and
  type `python send_recorded_data_to_osc.py --help`.
- To stop the script press ctrl+c in the window where is running.


#### Usage read data script with hydra visualiser

- First run the read data script, as per instructions above, once this is
  running go the following step.
- Go to [hydra site](https://hydra.ojack.xyz)
- Delete demo text
- Type in `hush()` press ctrl+shift+enter, then remove the `hush()` text (clears the screen, optional)
- Copy and paste the following code
```javascript
await loadScript("https://cdn.jsdelivr.net/gh/ojack/hydra-osc/lib/osc.min.js")
_osc = new OSC()
_osc.open()

sensor_value = 0
_osc.on("/sensor", (m) => {
  sensor_value = m.args[0]
})

osc(10,0).scale(sensor_value).out()
```
- Press ctrl+shift+enter
- See question mark in the top right for more hydra syntax to play around with
  different ways of using `sensor_value`.