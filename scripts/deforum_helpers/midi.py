"""."""

from mido import MidiFile
import dearpygui.dearpygui as dpg

def remove_pair_between(pair):
    """Remove duplicate tuples between their start and end points (if more than 2) if index 0 value same."""
    ret = [pair[0]]
    last_val = pair[0][0]
    last_idx = -1
    for i, tup in enumerate(pair[1:-1]):
        # add to new list if value has changed
        if tup[0] == last_val:
            continue
        # verify we are within a value range
        if i-1 > last_idx:
            ret.append(pair[i])
        ret.append(tup)
        last_val = tup[0]
        last_idx = i
    ret.append(pair[-1])
    return ret

class MidiTrackCC:
    def __init__(self, eventdata):
        self.__event = eventdata.copy()

    def curve(self, control: int) -> list[tuple[float, float]]:
        """Map the control values over time.

        Args:
        ----
            track: str or int, the name or index of the track to map the control values for
            control: int, the control number to map the values for

        Returns
        -------
            list of tuples containing the time and value for each control event
        """
        if (data := self.__event.get(control, None)) is None:
            return []

        # only return the control changes at the times they change -- not every event change
        data = remove_pair_between(data)
        # re-normalize
        ret = []
        for d in data:
            v = float(d[0]) / 127.
            d = (v, d[1])
            ret.append(d)
        return ret

    def value(self, control: int, t: float=0.) -> int:
        return -1

class MidiCC:
    def __init__(self, filename):
        """Extracts control events from each track in the MIDI file.

        The control events are stored in a dictionary with the track name as key
        and a list of MidiTrackCC objects as the value.

        Args:
        ----
            filename: midi filename
        """
        mid = MidiFile(filename)
        self.__track = {}
        for track in mid.tracks:
            name = track.name
            data = {}
            runtime = {}
            for msg in track:
                # Add control event to the list for the current track name
                if msg.type == 'control_change':
                    idx = msg.control
                    runtime[idx] = runtime.get(idx, 0.) + msg.time
                    data[idx] = data.get(idx, [])
                    e = (msg.value, runtime[idx])
                    data[idx].append(e)

                # track is complete, add the data
                elif msg.type == 'end_of_track' and len(data) > 0:
                    # scan all the control channels and only take messages that matter to us
                    self.__track[name] = MidiTrackCC(data)

    def __iter__(self):
        for x in self.__track:
            yield x

    def track(self, track) -> MidiTrackCC:
        if (ret := self.__track.get(track, None)) is None:
            raise ValueError(f"no track {track}")
        return ret

def window():
    fname = "C:\\dev\\auto1111\\extensions\\deforum-for-automatic1111-webui\\test_control2.mid"
    midi = MidiCC(fname)
    track = midi.track('808 Kick')
    atay, atax = zip(*track.curve(7))

    dpg.create_context()
    with dpg.window(label="Curve", tag="win"):
        # create plot
        with dpg.plot(label="Value Curve", height=800, width=800):
            # optionally create legend
            dpg.add_plot_legend()

            # REQUIRED: create x and y axes
            dpg.add_plot_axis(dpg.mvXAxis, label="time")
            dpg.add_plot_axis(dpg.mvYAxis, label="value", tag="y_axis")

            # series belong to a y axis
            dpg.add_line_series(atax, atay, parent="y_axis")

    dpg.fit_axis_data("y_axis")
    dpg.setup_dearpygui()
    dpg.create_viewport(title='Custom Title', width=800, height=800)
    dpg.show_viewport()
    dpg.start_dearpygui()
    dpg.destroy_context()

window()
