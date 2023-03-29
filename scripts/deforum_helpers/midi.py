"""."""

from mido import MidiFile
import dearpygui.dearpygui as dpg

def remove_pair_between(pair, idx: int=1):
    """Remove duplicate tuples between their start and end points (if more than 2) if index 0 value same."""
    ret = [pair[0]]
    last_val = pair[0][idx]
    last_idx = -1
    for i, tup in enumerate(pair[1:-1]):
        if tup[idx] == last_val:
            continue
        if i > last_idx:
            ret.append(pair[i])
        ret.append(tup)
        last_val = tup[idx]
        last_idx = i
    if (last := pair[-1]) != ret[-1]:
        ret.append(last)
    return ret

class MidiTrackCC:
    def __init__(self, name, eventdata):
        self.__name = name
        self.__event = {}
        self.__runtime = 0.
        for e, data in eventdata.items():
            ret = [data[0]]
            for delta, val in data[1:]:
                if delta > 0:
                    self.__runtime += delta
                    ret.append((self.__runtime, val / 127.))

            ret = remove_pair_between(ret, 1)
            if len(ret) > 1:
                self.__event[e] = [(t / self.__runtime, v) for t, v in ret]

    def __str__(self):
        return self.__name

    def __iter__(self):
        for idx, curve in self.__event.items():
            yield idx, curve

    def controls(self):
        return self.__event.keys()

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
            # runtime = {}
            for msg in track:
                # Add control event to the list for the current track name
                if msg.type == 'control_change':
                    idx = msg.control
                    # runtime[idx] = runtime.get(idx, 0.) + msg.time
                    data[idx] = data.get(idx, [])
                    e = (msg.time, msg.value)
                    data[idx].append(e)

                # track is complete, add the data
                elif msg.type == 'end_of_track' and len(data) > 0:
                    # scan all the control channels and only take messages that matter to us
                    self.__track[name] = MidiTrackCC(track.name, data)

    def __iter__(self):
        for x in self.__track.values():
            yield x

def window():
    fname = "C:\\dev\\auto1111\\extensions\\deforum-for-automatic1111-webui\\test_control2.mid"
    midi = MidiCC(fname)

    dpg.create_context()
    with dpg.window(label="Curve", tag="win"):
        # create plot
        for track in midi:
            for ctrl, data in track:
                if len(data) < 2:
                    continue
                atax, atay = zip(*data)
                with dpg.plot(label=f"{track}_{ctrl}", height=300, width=300):
                    # optionally create legend
                    dpg.add_plot_legend()

                    # REQUIRED: create x and y axes
                    dpg.add_plot_axis(dpg.mvXAxis, label="time")
                    what = dpg.add_plot_axis(dpg.mvYAxis, label="value")
                    dpg.add_line_series(atax, atay, parent=what)

                # dpg.fit_axis_data(tag)

    dpg.create_viewport(title='Custom Title', width=600, height=600)
    dpg.setup_dearpygui()
    dpg.show_viewport()
    dpg.set_primary_window("win", True)
    dpg.start_dearpygui()
    dpg.destroy_context()

window()
