import os
import threading
import time
from enum import Enum

import mido
from music21 import note


class MidiMsg(Enum):
    NOTE_ON = 'note_on'
    NOTE_OFF = 'note_off'
    UNKNOWN = 'unknown'

    def is_note_on(self):
        return self == MidiMsg.NOTE_ON

    def is_note_off(self):
        return self == MidiMsg.NOTE_OFF

    def is_note_on_or_off(self):
        return self.is_note_on() or self.is_note_off()

    @classmethod
    def _missing_(cls, value):
        return cls.UNKNOWN


class MidiChan(Enum):
    TEN = 9
    UNKNOWN = -1

    def is_perc(self):
        return self.value == MidiChan.TEN

    @classmethod
    def _missing_(cls, value):
        return cls.UNKNOWN


class MidiNote(Enum):
    C1 = 12
    Cs1 = 13
    D1 = 14
    Ds1 = 15
    E1 = 16
    F1 = 17
    Fs1 = 18
    G1 = 19
    Gs1 = 20
    A1 = 21
    Bb1 = 22
    B1 = 23
    C2 = 24
    Cs2 = 25
    D2 = 26
    Ds2 = 27
    E2 = 28
    F2 = 29
    Fs2 = 30
    G2 = 31
    Gs2 = 32
    A2 = 33
    Bb2 = 34
    B2 = 35
    C3 = 36
    Cs3 = 37
    D3 = 38
    Ds3 = 39
    E3 = 40
    F3 = 41
    Fs3 = 42
    G3 = 43
    Gs3 = 44
    A3 = 45
    Bb3 = 46
    B3 = 47
    C4 = 48
    Cs4 = 49
    D4 = 50
    Ds4 = 51
    E4 = 52
    F4 = 53
    Fs4 = 54
    G4 = 55
    Gs4 = 56
    A4 = 57
    Bb4 = 58
    B4 = 59
    C5 = 60
    Cs5 = 61
    D5 = 62
    Ds5 = 63
    E5 = 64
    F5 = 65
    Fs5 = 66
    G5 = 67
    Gs5 = 68
    A5 = 69
    Bb5 = 70
    B5 = 71
    C6 = 72
    Cs6 = 73
    D6 = 74
    Ds6 = 75
    E6 = 76
    F6 = 77
    Fs6 = 78
    G6 = 79
    Gs6 = 80
    A6 = 81
    Bb6 = 82
    B6 = 83
    C7 = 84
    Cs7 = 85
    D7 = 86
    Ds7 = 87
    E7 = 88
    F7 = 89
    Fs7 = 90
    G7 = 91
    Gs7 = 92
    A7 = 93
    Bb7 = 94
    B7 = 95


def adjust_octave_to_x(midi_note, x):
    original_note = note.Note()
    original_note.pitch.midi = midi_note
    octave_adjusted_note = original_note.transpose((x - original_note.octave) * 12)
    return octave_adjusted_note.pitch.midi


def note_from_midi(midi_number):
    note_names = ['C', 'C#', 'D', 'D#', 'E', 'F', 'F#', 'G', 'G#', 'A', 'Bb', 'B']
    return note_names[midi_number % 12]


def closest_handpan_pitch(midi_note):
    # Define the D Kurd 9 Note handpan scale in terms of MIDI numbers
    handpan_scale = [
        # 'B', -1
        'C',  # 4
        # 'C#', -1
        'D',  # 3, 4
        # 'D#', +1
        'E',  # 4
        'F',  # 4
        # 'F#', -1
        'G',  # 4
        # 'G#', +1
        'A',  # 3, 4
        'Bb',  # 3
        # 'B', -1
    ]

    midi_note_qualifier = note_from_midi(midi_note)

    if midi_note_qualifier in ['B', 'C#', 'F#']:
        adjusted_midi_note = midi_note - 1
    elif midi_note_qualifier not in handpan_scale:
        adjusted_midi_note = midi_note + 1
    else:
        adjusted_midi_note = midi_note

    adjusted_midi_note_qualifier = note_from_midi(adjusted_midi_note)

    if adjusted_midi_note_qualifier in ['D', 'A']:
        if adjusted_midi_note <= MidiNote.A3.value:
            adjusted_midi_note = adjust_octave_to_x(adjusted_midi_note, 3)
        else:
            adjusted_midi_note = adjust_octave_to_x(adjusted_midi_note, 4)
    elif adjusted_midi_note_qualifier == 'Bb':
        adjusted_midi_note = MidiNote.Bb3.value
    else:
        adjusted_midi_note = adjust_octave_to_x(adjusted_midi_note, 4)

    return adjusted_midi_note


def convert_midi_to_handpan(input_file, output_file):
    mid = mido.MidiFile(input_file)

    start = time.time()

    for track_num, track in enumerate(mid.tracks):
        is_percussion_track = False
        for msg in track:
            if not msg.is_meta and MidiMsg(msg.type).is_note_on() and MidiChan(msg.channel).is_perc():
                is_percussion_track = True
                break
        if is_percussion_track:
            continue
        for msg in track:
            if not msg.is_meta and (MidiMsg(msg.type).is_note_on_or_off()):
                converted_note = closest_handpan_pitch(msg.note)
                msg.note = converted_note

    print(f'processed: {mid.filename} ({time.time() - start:.2f} s)')

    # Save the new MIDI file
    mid.save(output_file)


def convert_file(file_name, directory):
    if file_name.endswith('.mid'):
        input_path = os.path.join(directory, file_name)
        output_path = os.path.join('out', file_name)
        convert_midi_to_handpan(input_path, output_path)


def convert_all_midis(directory):
    start = time.time()

    threads = []
    for file_name in os.listdir(directory):
        if os.path.exists(os.path.join("out", file_name)):
            print(f'skipping {file_name}')
            continue
        thread = threading.Thread(target=convert_file, args=(file_name, directory))
        threads.append(thread)
        thread.start()

    for thread in threads:
        thread.join()

    print(f'processed all: ({time.time() - start:.2f} s)')


convert_all_midis('in')
